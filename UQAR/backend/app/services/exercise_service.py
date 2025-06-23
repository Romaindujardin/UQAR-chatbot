import logging
import json
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session, joinedload

from ..models import Exercise, Question, Section, Document
from ..models.exercise import ExerciseStatus
from ..services.ollama_service import OllamaService
from ..services.chroma_service import ChromaService
from ..schemas.exercise_schemas import QuestionType, DifficultyLevel

logger = logging.getLogger(__name__)


class ExerciseGenerationService:
    """Service pour la génération automatique d'exercices"""
    
    def __init__(self):
        self.ollama_service = OllamaService()
        # Initialize ChromaDB client if available
        self.chroma_client = None
        try:
            import chromadb
            # Try different initialization methods
            try:
                self.chroma_client = chromadb.HttpClient(
                    host="localhost",
                    port=8001
                )
                logger.info("ChromaDB HttpClient initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB HttpClient: {e}")
                # Try PersistentClient
                try:
                    self.chroma_client = chromadb.PersistentClient(path="./chroma_data")
                    logger.info("ChromaDB PersistentClient initialized successfully")
                except Exception as e2:
                    logger.error(f"Failed to initialize ChromaDB PersistentClient: {e2}")
        except (ImportError, RuntimeError) as e:
            logger.warning(f"ChromaDB not available: {e}. Will use document text directly")
        
    async def generate_exercises(
        self,
        db: Session,
        section_id: int,
        num_questions: int = 5,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        exercise_type: QuestionType = QuestionType.MCQ,
        use_specific_documents: Optional[List[int]] = None
    ) -> Exercise:
        """Générer des exercices basés sur le contenu de la section"""
        
        logger.info(f"Starting exercise generation for section {section_id}")
        logger.info(f"Parameters: num_questions={num_questions}, difficulty={difficulty}, exercise_type={exercise_type}")
        
        try:
            # Create exercise with generating status
            exercise = Exercise(
                section_id=section_id,
                status=ExerciseStatus.GENERATING,
                generation_params={
                    "num_questions": num_questions,
                    "difficulty": difficulty.value,
                    "exercise_type": exercise_type.value,
                    "use_specific_documents": use_specific_documents
                }
            )
            db.add(exercise)
            db.commit()
            db.refresh(exercise)
            logger.info(f"Created exercise with ID {exercise.id}")
            
            # Get section and its documents
            section = db.query(Section).filter(Section.id == section_id).first()
            if not section:
                raise ValueError(f"Section {section_id} not found")
            
            logger.info(f"Found section: {section.name}")
                
            # Get relevant content
            content_chunks = await self._get_relevant_content(
                section=section,
                db=db,
                num_chunks=num_questions * 3,  # Get more chunks for variety
                specific_document_ids=use_specific_documents
            )
            
            if not content_chunks:
                logger.warning("No content found for exercise generation")
                # Try to get content directly from documents
                content_chunks = await self._get_content_from_documents(
                    section=section,
                    db=db,
                    specific_document_ids=use_specific_documents
                )
                
            if not content_chunks:
                raise ValueError("No content found for exercise generation")
                
            logger.info(f"Retrieved {len(content_chunks)} content chunks")
                
            # Generate questions
            questions = await self._generate_questions(
                content_chunks=content_chunks,
                num_questions=num_questions,
                difficulty=difficulty,
                exercise_type=exercise_type,
                section_name=section.name
            )
            
            logger.info(f"Generated {len(questions)} questions")
            
            # Save questions to database
            for idx, question_data in enumerate(questions):
                question = Question(
                    exercise_id=exercise.id,
                    text=question_data.get("text", ""),
                    question_type=exercise_type.value,
                    options=question_data.get("options"),
                    correct_answer=question_data.get("correct_answer"),
                    expected_keywords=question_data.get("expected_keywords"),
                    explanation=question_data.get("explanation"),
                    points=question_data.get("points", 1),
                    order_index=idx
                )
                db.add(question)
                logger.info(f"Added question {idx + 1}: {question.text[:50]}...")
            
            # Update exercise status
            exercise.status = ExerciseStatus.PENDING
            exercise.source_documents = [doc.get("document_id") for doc in content_chunks if "document_id" in doc]
            
            db.commit()
            db.refresh(exercise)
            
            # Ensure questions are loaded for the response model
            loaded_exercise = db.query(Exercise).options(
                joinedload(Exercise.questions)
            ).filter(Exercise.id == exercise.id).first()
            
            if not loaded_exercise:
                # This should ideally not happen if the exercise was just committed and refreshed
                logger.error(f"Failed to reload exercise {exercise.id} with its questions.")
                # Fallback to returning the original exercise object, though it might cause issues downstream
                return exercise 

            logger.info(f"Exercise {loaded_exercise.id} reloaded with {len(loaded_exercise.questions)} questions for response serialization.")
            return loaded_exercise
            
        except Exception as e:
            logger.error(f"Error generating exercises: {e}", exc_info=True)
            if 'exercise' in locals() and exercise.id:
                exercise.status = ExerciseStatus.PENDING  # Set to pending even on error
                db.commit()
            raise
            
    async def generate_exercises_advanced(
        self,
        db: Session,
        section_id: int,
        custom_prompt: str,
        temp_content: Optional[str] = None,
        use_specific_documents: Optional[List[int]] = None
    ) -> Exercise:
        """Générer des exercices en mode avancé avec un prompt personnalisé"""
        
        logger.info(f"Starting advanced exercise generation for section {section_id}")
        logger.info(f"Custom prompt: {custom_prompt[:100]}...")
        
        try:
            # Create exercise with generating status
            exercise = Exercise(
                section_id=section_id,
                status=ExerciseStatus.GENERATING,
                generation_params={
                    "mode": "advanced",
                    "custom_prompt": custom_prompt,
                    "temp_content": temp_content[:500] if temp_content else None,  # Save first 500 chars for reference
                    "use_specific_documents": use_specific_documents
                }
            )
            db.add(exercise)
            db.commit()
            db.refresh(exercise)
            logger.info(f"Created advanced exercise with ID {exercise.id}")
            
            # Get section and its documents
            section = db.query(Section).filter(Section.id == section_id).first()
            if not section:
                raise ValueError(f"Section {section_id} not found")
            
            logger.info(f"Found section: {section.name}")
                
            # Get relevant content
            content_chunks = await self._get_relevant_content(
                section=section,
                db=db,
                num_chunks=20,  # Get more chunks for advanced mode
                specific_document_ids=use_specific_documents
            )
            
            if not content_chunks:
                logger.warning("No content found for exercise generation")
                # Try to get content directly from documents
                content_chunks = await self._get_content_from_documents(
                    section=section,
                    db=db,
                    specific_document_ids=use_specific_documents
                )
                
            if not content_chunks:
                raise ValueError("No content found for exercise generation")
                
            logger.info(f"Retrieved {len(content_chunks)} content chunks for advanced generation")
                
            # Generate questions using custom prompt
            questions = await self._generate_questions_advanced(
                content_chunks=content_chunks,
                custom_prompt=custom_prompt,
                temp_content=temp_content,
                section_name=section.name
            )
            
            logger.info(f"Generated {len(questions)} questions using advanced mode")
            
            # Save questions to database
            for idx, question_data in enumerate(questions):
                question = Question(
                    exercise_id=exercise.id,
                    text=question_data.get("text", ""),
                    question_type=question_data.get("question_type", "mcq"),
                    options=question_data.get("options"),
                    correct_answer=question_data.get("correct_answer"),
                    expected_keywords=question_data.get("expected_keywords"),
                    explanation=question_data.get("explanation"),
                    points=question_data.get("points", 1),
                    order_index=idx
                )
                db.add(question)
                logger.info(f"Added question {idx + 1}: {question.text[:50]}...")
            
            # Update exercise status
            exercise.status = ExerciseStatus.PENDING
            exercise.source_documents = [doc.get("document_id") for doc in content_chunks if "document_id" in doc]
            
            db.commit()
            db.refresh(exercise)
            
            # Ensure questions are loaded for the response model
            loaded_exercise = db.query(Exercise).options(
                joinedload(Exercise.questions)
            ).filter(Exercise.id == exercise.id).first()
            
            if not loaded_exercise:
                logger.error(f"Failed to reload exercise {exercise.id} with its questions.")
                return exercise 

            logger.info(f"Advanced exercise {loaded_exercise.id} reloaded with {len(loaded_exercise.questions)} questions for response serialization.")
            return loaded_exercise
            
        except Exception as e:
            logger.error(f"Error generating advanced exercises: {e}", exc_info=True)
            if 'exercise' in locals() and exercise.id:
                exercise.status = ExerciseStatus.PENDING  # Set to pending even on error
                db.commit()
            raise
            
    async def _get_relevant_content(
        self,
        section: Section,
        db: Session,
        num_chunks: int = 15,
        specific_document_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """Récupérer le contenu pertinent depuis ChromaDB"""
        
        logger.info(f"Attempting to get content from ChromaDB for section {section.id}")
        
        if not self.chroma_client:
            logger.warning("ChromaDB client not initialized")
            return []
            
        try:
            # Get collection
            collection = None
            if section.chroma_collection_name:
                try:
                    collection = self.chroma_client.get_collection(name=section.chroma_collection_name)
                    logger.info(f"Got ChromaDB collection: {section.chroma_collection_name}")
                except Exception as e:
                    logger.error(f"Failed to get collection {section.chroma_collection_name}: {e}")
                    return []
            else:
                logger.warning(f"Section {section.id} has no chroma_collection_name")
                return []
                
            # Query the collection
            if specific_document_ids:
                # Query with document filter
                where_clause = {"document_id": {"$in": [str(doc_id) for doc_id in specific_document_ids]}}
                results = collection.query(
                    query_texts=[section.name + " " + (section.description or "")],
                    n_results=num_chunks,
                    where=where_clause
                )
            else:
                # General query
                results = collection.query(
                    query_texts=[section.name + " " + (section.description or "")],
                    n_results=num_chunks
                )
                
            # Format results
            chunks = []
            if results and results.get("documents") and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    chunk = {
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "document_id": results["metadatas"][0][i].get("document_id") if results.get("metadatas") else None
                    }
                    chunks.append(chunk)
                    
            logger.info(f"Retrieved {len(chunks)} chunks from ChromaDB")
            return chunks
                
        except Exception as e:
            logger.error(f"Error getting content from ChromaDB: {e}", exc_info=True)
            return []
            
    async def _get_content_from_documents(
        self,
        section: Section,
        db: Session,
        specific_document_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """Get content directly from documents if ChromaDB is not available"""
        
        logger.info(f"Getting content directly from documents for section {section.id}")
        
        # Get documents
        query = db.query(Document).filter(
            Document.section_id == section.id
        )
        
        if specific_document_ids:
            query = query.filter(Document.id.in_(specific_document_ids))
            
        documents = query.all()
        logger.info(f"Found {len(documents)} processed documents")
        
        chunks = []
        for doc in documents:
            if doc.extracted_text:
                # Split text into chunks
                text_chunks = self._chunk_text(doc.extracted_text)
                for chunk_text in text_chunks[:3]:  # Take first 3 chunks per document
                    chunks.append({
                        "text": chunk_text,
                        "document_id": str(doc.id),
                        "metadata": {
                            "document_id": str(doc.id),
                            "filename": doc.original_filename
                        }
                    })
                    
        logger.info(f"Created {len(chunks)} chunks from document texts")
        return chunks
        
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into chunks"""
        chunks = []
        
        if len(text) <= chunk_size:
            chunks.append(text)
        else:
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                if chunk:
                    chunks.append(chunk)
                    
        return chunks
            
    async def _generate_questions(
        self,
        content_chunks: List[Dict],
        num_questions: int,
        difficulty: DifficultyLevel,
        exercise_type: QuestionType,
        section_name: str
    ) -> List[Dict]:
        """Générer les questions en utilisant Ollama"""
        
        logger.info(f"Generating {num_questions} {exercise_type.value} questions")
        
        # Prepare content for generation
        content_text = "\n\n".join([chunk["text"] for chunk in content_chunks[:10]])  # Limit content size
        logger.info(f"Using {len(content_text)} characters of content for generation")
        
        # Build the generation prompt
        system_prompt = self._build_system_prompt(exercise_type, difficulty, section_name)
        user_prompt = self._build_user_prompt(
            content_text=content_text,
            num_questions=num_questions,
            exercise_type=exercise_type,
            difficulty=difficulty
        )
        
        try:
            # Generate with Ollama
            logger.info("Calling Ollama to generate questions...")
            response = await self.ollama_service.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            logger.info(f"Ollama response received (length: {len(response)})")
            logger.debug(f"Ollama response: {response[:500]}...")
            
            # Parse the response
            questions = self._parse_generated_questions(response, exercise_type)
            
            logger.info(f"Parsed {len(questions)} questions from Ollama response")
            
            # Ensure we have the requested number of questions
            if len(questions) < num_questions:
                logger.warning(f"Generated only {len(questions)} questions instead of {num_questions}")
                
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error generating questions with Ollama: {e}", exc_info=True)
            # Return fallback questions
            return self._get_fallback_questions(num_questions, exercise_type)
            
    def _build_system_prompt(self, exercise_type: QuestionType, difficulty: DifficultyLevel, section_name: str) -> str:
        """Construire le prompt système pour la génération"""
        
        difficulty_guidelines = {
            DifficultyLevel.EASY: "questions simples et directes, testant la compréhension basique",
            DifficultyLevel.MEDIUM: "questions nécessitant de la réflexion et de la compréhension approfondie",
            DifficultyLevel.HARD: "questions complexes nécessitant analyse, synthèse et application des concepts"
        }
        
        return f"""Tu es un expert pédagogique créant des exercices pour le cours "{section_name}".
        
Crée des {difficulty_guidelines[difficulty]} adaptées au niveau universitaire.

IMPORTANT: Tu dois répondre UNIQUEMENT avec un tableau JSON valide contenant les questions.
Aucun texte avant ou après le JSON.

Pour les questions de type {exercise_type.value}, utilise exactement ce format JSON:"""
        
    def _build_user_prompt(
        self,
        content_text: str,
        num_questions: int,
        exercise_type: QuestionType,
        difficulty: DifficultyLevel
    ) -> str:
        """Construire le prompt utilisateur pour la génération"""
        
        if exercise_type == QuestionType.MCQ:
            format_example = """[
    {
        "text": "Question claire et précise basée sur le contenu",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A",
        "explanation": "Explication pédagogique de pourquoi c'est la bonne réponse",
        "points": 1
    }
]"""
        elif exercise_type == QuestionType.OPEN_ENDED:
            format_example = """[
    {
        "text": "Question ouverte stimulante basée sur le contenu",
        "expected_keywords": ["concept1", "concept2", "concept3"],
        "explanation": "Guide de correction avec les éléments attendus dans la réponse",
        "points": 2
    }
]"""
        elif exercise_type == QuestionType.TRUE_FALSE:
            format_example = """[
    {
        "text": "Affirmation à évaluer comme vraie ou fausse",
        "correct_answer": "true",
        "explanation": "Explication détaillée",
        "points": 1
    }
]"""
        else:  # FILL_BLANK
            format_example = """[
    {
        "text": "Phrase avec un _____ à compléter",
        "correct_answer": "mot manquant",
        "explanation": "Explication du terme correct",
        "points": 1
    }
]"""
            
        return f"""Basé sur ce contenu du cours:

{content_text}

Génère exactement {num_questions} questions de type {exercise_type.value} de niveau {difficulty.value}.

Format JSON attendu:
{format_example}

Assure-toi que:
1. Les questions sont directement liées au contenu fourni
2. Les questions sont variées et couvrent différents aspects
3. Les explications sont pédagogiques et aident à l'apprentissage
4. Le JSON est valide et suit exactement le format

Génère les {num_questions} questions maintenant:"""
        
    def _parse_generated_questions(self, response: str, exercise_type: QuestionType) -> List[Dict]:
        """Parser la réponse générée par Ollama"""
        
        try:
            # Clean the response
            response = response.strip()
            
            # Try to extract JSON from the response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                questions = json.loads(json_str)
                
                # Validate and clean questions
                valid_questions = []
                for q in questions:
                    if isinstance(q, dict) and 'text' in q:
                        # Ensure required fields based on type
                        if exercise_type == QuestionType.MCQ:
                            if 'options' in q and 'correct_answer' in q:
                                valid_questions.append(q)
                        elif exercise_type == QuestionType.OPEN_ENDED:
                            if 'expected_keywords' not in q:
                                q['expected_keywords'] = []
                            valid_questions.append(q)
                        else:
                            if 'correct_answer' in q:
                                valid_questions.append(q)
                                
                return valid_questions
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Ollama response: {e}")
            logger.debug(f"Response was: {response}")
            
        return []
        
    def _get_fallback_questions(self, num_questions: int, exercise_type: QuestionType) -> List[Dict]:
        """Générer des questions de secours en cas d'échec"""
        
        fallback_questions = []
        
        for i in range(num_questions):
            if exercise_type == QuestionType.MCQ:
                question = {
                    "text": f"Question {i+1}: Veuillez reformuler cette question basée sur le contenu du cours.",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A",
                    "explanation": "Cette question doit être reformulée par l'enseignant.",
                    "points": 1
                }
            elif exercise_type == QuestionType.OPEN_ENDED:
                question = {
                    "text": f"Question {i+1}: Analysez et expliquez un concept important du cours.",
                    "expected_keywords": ["concept", "analyse", "explication"],
                    "explanation": "Cette question doit être adaptée par l'enseignant.",
                    "points": 2
                }
            else:
                question = {
                    "text": f"Question {i+1}: [À compléter par l'enseignant]",
                    "correct_answer": "true",
                    "explanation": "Cette question doit être complétée par l'enseignant.",
                    "points": 1
                }
                
            fallback_questions.append(question)
            
        return fallback_questions
        
    async def _generate_questions_advanced(
        self,
        content_chunks: List[Dict],
        custom_prompt: str,
        temp_content: Optional[str] = None,
        section_name: str = "cours"
    ) -> List[Dict]:
        """Générer les questions en mode avancé avec un agent extracteur en deux étapes"""
        
        logger.info(f"Starting advanced generation with custom prompt (length: {len(custom_prompt)})")
        
        # ÉTAPE 1: Extraction des paramètres via l'agent extracteur
        params = await self._extract_prompt_parameters(custom_prompt)
        logger.info(f"Extracted parameters: {params}")
        
        # ÉTAPE 2: Prepare content for generation
        if temp_content:
            # Si on a un contenu temporaire, on l'utilise comme source principale
            content_text = temp_content
            logger.info(f"Using temporary content ({len(temp_content)} chars) as primary source")
        else:
            # Sinon on utilise le contenu de la section, filtré par sujet si spécifié
            content_text = "\n\n".join([chunk["text"] for chunk in content_chunks[:15]])
            
            # Si un sujet spécifique est mentionné, on filtre le contenu
            if params["sujet"] != "contenu du cours":
                sujet_keywords = params["sujet"].lower().split()
                # Filtrer les chunks qui contiennent les mots-clés du sujet
                filtered_chunks = []
                for chunk in content_chunks:
                    chunk_text_lower = chunk["text"].lower()
                    if any(keyword in chunk_text_lower for keyword in sujet_keywords):
                        filtered_chunks.append(chunk)
                
                if filtered_chunks:
                    content_text = "\n\n".join([chunk["text"] for chunk in filtered_chunks[:10]])
                    logger.info(f"Filtered content for subject '{params['sujet']}': {len(filtered_chunks)} relevant chunks")
                else:
                    logger.warning(f"No content found for subject '{params['sujet']}', using all content")
            
            logger.info(f"Using section content ({len(content_text)} chars) for advanced generation")
        
        # ÉTAPE 3: Générer avec les paramètres extraits en utilisant le mode basique
        from ..schemas.exercise_schemas import QuestionType, DifficultyLevel
        
        # Conversion des paramètres
        question_type_map = {
            "mcq": QuestionType.MCQ,
            "open_ended": QuestionType.OPEN_ENDED,
            "true_false": QuestionType.TRUE_FALSE,
            "fill_blank": QuestionType.FILL_BLANK
        }
        
        difficulty_map = {
            "easy": DifficultyLevel.EASY,
            "medium": DifficultyLevel.MEDIUM,
            "hard": DifficultyLevel.HARD
        }
        
        exercise_type = question_type_map.get(params["type"], QuestionType.MCQ)
        difficulty = difficulty_map.get(params["difficulte"], DifficultyLevel.MEDIUM)
        num_questions = params["nombre"]
        
        logger.info(f"Generating {num_questions} {exercise_type.value} questions on '{params['sujet']}' at {difficulty.value} level")
        
        # Utiliser la logique du mode basique mais avec un prompt adapté au sujet
        system_prompt = self._build_system_prompt(exercise_type, difficulty, section_name)
        user_prompt = self._build_user_prompt_with_subject(
            content_text=content_text,
            num_questions=num_questions,
            exercise_type=exercise_type,
            difficulty=difficulty,
            subject=params["sujet"]
        )
        
        try:
            # Generate with Ollama using the basic mode logic
            logger.info("Calling Ollama to generate questions with extracted parameters...")
            response = await self.ollama_service.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            logger.info(f"Ollama response received for advanced mode (length: {len(response)})")
            logger.debug(f"Ollama response: {response[:500]}...")
            
            # Parse the response using basic mode logic
            questions = self._parse_generated_questions(response, exercise_type)
            
            logger.info(f"Parsed {len(questions)} questions from advanced mode response")
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions with extracted parameters: {e}", exc_info=True)
            # Return fallback questions
            return self._get_fallback_questions(num_questions, exercise_type)
    
    def _build_system_prompt_advanced(self, section_name: str) -> str:
        """Construire le prompt système pour le mode avancé"""
        
        return f"""Tu es un expert pédagogique créant des exercices pour le cours "{section_name}".

Tu dois interpréter et suivre EXACTEMENT les instructions de l'enseignant pour créer des exercices personnalisés.

IMPORTANT: Tu dois répondre UNIQUEMENT avec un tableau JSON valide contenant les questions.
Aucun texte avant ou après le JSON.

Formats JSON supportés:

Pour QCM/MCQ:
[{{"text": "Question", "question_type": "mcq", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "Explication", "points": 1}}]

Pour questions ouvertes:
[{{"text": "Question", "question_type": "open_ended", "expected_keywords": ["mot1", "mot2"], "explanation": "Guide de correction", "points": 2}}]

Pour vrai/faux:
[{{"text": "Affirmation", "question_type": "true_false", "correct_answer": "true", "explanation": "Explication", "points": 1}}]

Pour compléter:
[{{"text": "Phrase avec un _____ à compléter", "question_type": "fill_blank", "correct_answer": "mot manquant", "explanation": "Explication", "points": 1}}]"""
    
    def _build_user_prompt_advanced(self, content_text: str, custom_prompt: str) -> str:
        """Construire le prompt utilisateur pour le mode avancé"""
        
        return f"""INSTRUCTIONS DE L'ENSEIGNANT:
{custom_prompt}

CONTENU DU COURS DISPONIBLE:
{content_text}

Génère les exercices selon les instructions exactes de l'enseignant ci-dessus.

RÈGLES IMPORTANTES:
1. Respecte EXACTEMENT le nombre de questions demandé par l'enseignant
2. Respecte EXACTEMENT le type de questions demandé (QCM, ouverte, etc.)
3. Respecte EXACTEMENT le sujet/thème demandé (par ex: "uniquement sur la boucle FOR")
4. Base tes questions UNIQUEMENT sur le contenu fourni ci-dessus
5. Assure-toi que le JSON est valide et suit exactement les formats proposés
6. Inclus TOUJOURS les champs requis: text, question_type, explanation, points
7. Pour les QCM: inclus options et correct_answer
8. Pour les questions ouvertes: inclus expected_keywords
9. Pour vrai/faux et compléter: inclus correct_answer

Génère maintenant les exercices selon les instructions de l'enseignant:"""
    
    def _parse_advanced_questions(self, response: str) -> List[Dict]:
        """Parser la réponse générée en mode avancé - utilise la même logique que le mode basique"""
        
        try:
            # Clean the response
            response = response.strip()
            
            # Try to extract JSON from the response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                questions = json.loads(json_str)
                
                # Validate and clean questions
                valid_questions = []
                for q in questions:
                    if isinstance(q, dict) and 'text' in q:
                        # Ensure question_type is set (default to mcq if not specified)
                        if 'question_type' not in q:
                            q['question_type'] = 'mcq'
                        
                        # Normalize question type
                        qtype = q.get('question_type', 'mcq').lower()
                        if qtype in ['qcm', 'choix_multiple', 'multiple_choice']:
                            qtype = 'mcq'
                        elif qtype in ['ouverte', 'open', 'essay']:
                            qtype = 'open_ended'
                        elif qtype in ['vrai_faux', 'true_false', 'boolean']:
                            qtype = 'true_false'
                        elif qtype in ['completé', 'completer', 'fill', 'blank', 'fill_blank']:
                            qtype = 'fill_blank'
                        
                        q['question_type'] = qtype
                        
                        # Validate and complete based on question type
                        if qtype == 'mcq':
                            # Ensure we have options and correct_answer
                            if 'options' not in q or not q['options']:
                                q['options'] = ["Option A", "Option B", "Option C", "Option D"]
                            if 'correct_answer' not in q and q.get('options'):
                                q['correct_answer'] = q['options'][0]
                            # Validate that correct_answer is in options
                            if q.get('correct_answer') not in q.get('options', []):
                                if q.get('options'):
                                    q['correct_answer'] = q['options'][0]
                                    
                        elif qtype == 'open_ended':
                            # Ensure we have expected_keywords
                            if 'expected_keywords' not in q:
                                q['expected_keywords'] = []
                                
                        elif qtype in ['true_false', 'fill_blank']:
                            # Ensure we have correct_answer
                            if 'correct_answer' not in q:
                                q['correct_answer'] = "true" if qtype == 'true_false' else "réponse"
                        
                        # Ensure required fields
                        if 'explanation' not in q:
                            q['explanation'] = "Explication à compléter"
                        if 'points' not in q:
                            q['points'] = 1
                            
                        valid_questions.append(q)
                        
                        logger.debug(f"Validated question: {q['text'][:50]}... (type: {qtype})")
                                
                return valid_questions
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from advanced mode response: {e}")
            logger.debug(f"Response was: {response}")
            
        return []
    
    def _get_fallback_questions_advanced(self, custom_prompt: str) -> List[Dict]:
        """Générer des questions de secours pour le mode avancé"""
        
        # Try to extract number from custom prompt
        import re
        numbers = re.findall(r'\d+', custom_prompt)
        num_questions = int(numbers[0]) if numbers else 2
        
        # Detect question type from prompt
        question_type = "mcq"
        if any(word in custom_prompt.lower() for word in ["qcm", "choix multiple", "mcq"]):
            question_type = "mcq"
        elif any(word in custom_prompt.lower() for word in ["ouverte", "open", "rédaction"]):
            question_type = "open_ended"
        elif any(word in custom_prompt.lower() for word in ["vrai", "faux", "true", "false"]):
            question_type = "true_false"
        
        fallback_questions = []
        for i in range(min(num_questions, 5)):  # Limit to 5 fallback questions
            if question_type == "mcq":
                question = {
                    "text": f"Question {i+1} basée sur la demande: {custom_prompt[:100]}...",
                    "question_type": "mcq",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A",
                    "explanation": "Cette question doit être reformulée par l'enseignant selon sa demande personnalisée.",
                    "points": 1
                }
            elif question_type == "open_ended":
                question = {
                    "text": f"Question ouverte {i+1} basée sur: {custom_prompt[:100]}...",
                    "question_type": "open_ended",
                    "expected_keywords": ["concept", "explication"],
                    "explanation": "Cette question doit être reformulée par l'enseignant selon sa demande personnalisée.",
                    "points": 2
                }
            else:  # true_false
                question = {
                    "text": f"Affirmation {i+1} à évaluer (basée sur: {custom_prompt[:50]}...)",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "explanation": "Cette question doit être reformulée par l'enseignant selon sa demande personnalisée.",
                    "points": 1
                }
            
            fallback_questions.append(question)
        
        return fallback_questions
            
    async def _extract_prompt_parameters(self, custom_prompt: str) -> Dict[str, Any]:
        """Extraire les paramètres du prompt personnalisé via un agent LLM"""
        
        logger.info(f"Extracting parameters from custom prompt: {custom_prompt[:100]}...")
        
        system_prompt = """Tu es un agent spécialisé dans l'extraction de paramètres pédagogiques.
        
Ton rôle est d'analyser les instructions d'un enseignant et d'extraire les paramètres de façon structurée.

Tu dois répondre UNIQUEMENT avec un JSON valide contenant les paramètres extraits.
Aucun texte avant ou après le JSON.

Format de réponse attendu:
{
    "nombre": 5,
    "type": "mcq",
    "sujet": "description du sujet spécifique",
    "difficulte": "medium"
}

Types acceptés: "mcq", "open_ended", "true_false", "fill_blank"
Difficultés acceptées: "easy", "medium", "hard"
"""
        
        user_prompt = f"""Analyse ces instructions d'enseignant et extrait les paramètres:

INSTRUCTIONS: "{custom_prompt}"

Extrait:
- Le NOMBRE de questions demandées (si non spécifié, utilise 5)
- Le TYPE de questions (QCM=mcq, questions ouvertes=open_ended, vrai/faux=true_false, à compléter=fill_blank)
- Le SUJET spécifique mentionné (par ex: "boucle FOR", "variables Python", etc.)
- LA DIFFICULTÉ si mentionnée (facile=easy, moyen=medium, difficile=hard, sinon medium)

Exemples:
- "2 QCM sur les boucles FOR" → {{"nombre": 2, "type": "mcq", "sujet": "boucles FOR", "difficulte": "medium"}}
- "5 questions ouvertes difficiles sur les variables" → {{"nombre": 5, "type": "open_ended", "sujet": "variables", "difficulte": "hard"}}

Analyse maintenant:"""
        
        try:
            response = await self.ollama_service.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            logger.info(f"Parameter extraction response: {response[:200]}...")
            
            # Parse la réponse JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                params = json.loads(json_str)
                
                # Validation et nettoyage
                cleaned_params = {
                    "nombre": max(1, min(20, params.get("nombre", 5))),  # Entre 1 et 20
                    "type": params.get("type", "mcq").lower(),
                    "sujet": params.get("sujet", "contenu du cours"),
                    "difficulte": params.get("difficulte", "medium").lower()
                }
                
                # Normalisation des types
                if cleaned_params["type"] in ["qcm", "choix_multiple"]:
                    cleaned_params["type"] = "mcq"
                elif cleaned_params["type"] in ["ouverte", "open"]:
                    cleaned_params["type"] = "open_ended"
                elif cleaned_params["type"] in ["vrai_faux", "vf"]:
                    cleaned_params["type"] = "true_false"
                elif cleaned_params["type"] in ["completer", "fill"]:
                    cleaned_params["type"] = "fill_blank"
                
                # Normalisation des difficultés
                if cleaned_params["difficulte"] in ["facile", "simple"]:
                    cleaned_params["difficulte"] = "easy"
                elif cleaned_params["difficulte"] in ["moyen", "normal"]:
                    cleaned_params["difficulte"] = "medium"
                elif cleaned_params["difficulte"] in ["difficile", "dur", "complexe"]:
                    cleaned_params["difficulte"] = "hard"
                
                logger.info(f"Extracted parameters: {cleaned_params}")
                return cleaned_params
                
        except Exception as e:
            logger.error(f"Error extracting parameters: {e}")
        
        # Fallback: analyse simple par mots-clés
        return self._extract_parameters_fallback(custom_prompt)
    
    def _extract_parameters_fallback(self, custom_prompt: str) -> Dict[str, Any]:
        """Extraction de paramètres en fallback avec analyse par mots-clés"""
        
        logger.info("Using fallback parameter extraction")
        
        prompt_lower = custom_prompt.lower()
        
        # Extraction du nombre
        import re
        numbers = re.findall(r'\b(\d+)\b', custom_prompt)
        nombre = int(numbers[0]) if numbers else 5
        nombre = max(1, min(20, nombre))  # Entre 1 et 20
        
        # Extraction du type
        type_question = "mcq"  # par défaut
        if any(word in prompt_lower for word in ["qcm", "choix multiple", "multiple choice"]):
            type_question = "mcq"
        elif any(word in prompt_lower for word in ["ouverte", "open", "rédaction", "essay"]):
            type_question = "open_ended"
        elif any(word in prompt_lower for word in ["vrai", "faux", "true", "false", "vf"]):
            type_question = "true_false"
        elif any(word in prompt_lower for word in ["compléter", "completer", "fill", "blanc", "blank"]):
            type_question = "fill_blank"
        
        # Extraction du sujet (après "sur", "à propos", "basé sur", etc.)
        sujet = "contenu du cours"
        sujet_patterns = [
             r'(?:basé uniquement sur|basé seulement sur|basé exclusivement sur|uniquement sur|seulement sur|exclusivement sur)\s+(.+?)(?:$|,|\.|!|\?)',
             r'(?:sur|à propos de|basé sur|concernant|relatif à)\s+(.+?)(?:$|,|\.|!|\?)',
             r'(?:thème|sujet|topic)\s*:\s*(.+?)(?:$|,|\.|!|\?)'
         ]
        
        for pattern in sujet_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                sujet = match.group(1).strip()
                break
        
        # Extraction de la difficulté
        difficulte = "medium"  # par défaut
        if any(word in prompt_lower for word in ["facile", "simple", "easy"]):
            difficulte = "easy"
        elif any(word in prompt_lower for word in ["difficile", "dur", "complexe", "hard"]):
            difficulte = "hard"
        
        params = {
            "nombre": nombre,
            "type": type_question,
            "sujet": sujet,
            "difficulte": difficulte
        }
        
        logger.info(f"Fallback extracted parameters: {params}")
        return params
            
    def _build_user_prompt_with_subject(
        self,
        content_text: str,
        num_questions: int,
        exercise_type: QuestionType,
        difficulty: DifficultyLevel,
        subject: str
    ) -> str:
        """Construire le prompt utilisateur avec focus sur un sujet spécifique"""
        
        if exercise_type == QuestionType.MCQ:
            format_example = """[
    {
        "text": "Question claire et précise basée sur le contenu",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A",
        "explanation": "Explication pédagogique de pourquoi c'est la bonne réponse",
        "points": 1
    }
]"""
        elif exercise_type == QuestionType.OPEN_ENDED:
            format_example = """[
    {
        "text": "Question ouverte stimulante basée sur le contenu",
        "expected_keywords": ["concept1", "concept2", "concept3"],
        "explanation": "Guide de correction avec les éléments attendus dans la réponse",
        "points": 2
    }
]"""
        elif exercise_type == QuestionType.TRUE_FALSE:
            format_example = """[
    {
        "text": "Affirmation à évaluer comme vraie ou fausse",
        "correct_answer": "true",
        "explanation": "Explication détaillée",
        "points": 1
    }
]"""
        else:  # FILL_BLANK
            format_example = """[
    {
        "text": "Phrase avec un _____ à compléter",
        "correct_answer": "mot manquant",
        "explanation": "Explication du terme correct",
        "points": 1
    }
]"""
            
        return f"""Basé sur ce contenu du cours:

{content_text}

Génère exactement {num_questions} questions de type {exercise_type.value} de niveau {difficulty.value}.

FOCUS SPÉCIAL: Les questions doivent porter EXCLUSIVEMENT sur le sujet suivant: "{subject}"

Format JSON attendu:
{format_example}

Assure-toi que:
1. TOUTES les questions portent UNIQUEMENT sur "{subject}"
2. Les questions sont directement liées au contenu fourni concernant "{subject}"
3. Aucune question ne doit traiter d'autres sujets que "{subject}"
4. Les explications sont pédagogiques et aident à l'apprentissage
5. Le JSON est valide et suit exactement le format

Génère exactement {num_questions} questions sur "{subject}" maintenant:"""
            
class ExerciseFeedbackService:
    """Service pour générer du feedback pédagogique sur les réponses des étudiants"""
    
    def __init__(self):
        self.ollama_service = OllamaService()
        
    async def generate_feedback(
        self,
        question: Question,
        student_answer: str,
        is_correct: bool
    ) -> str:
        """Générer un feedback pédagogique pour une réponse d'étudiant"""
        
        system_prompt = """Tu es un tuteur pédagogique bienveillant.
Fournis un feedback constructif et encourageant pour aider l'étudiant à progresser.
Sois précis, pédagogique et positif dans ton approche."""
        
        if question.question_type == QuestionType.MCQ.value:
            user_prompt = f"""
Question: {question.text}
Options: {json.dumps(question.options)}
Réponse correcte: {question.correct_answer}
Réponse de l'étudiant: {student_answer}
Correct: {'Oui' if is_correct else 'Non'}

{question.explanation or ''}

Fournis un feedback pédagogique bref (2-3 phrases) qui:
- Confirme si la réponse est correcte ou non
- Explique pourquoi de manière claire
- Encourage l'étudiant à continuer
"""
        else:  # Open-ended
            user_prompt = f"""
Question: {question.text}
Mots-clés attendus: {json.dumps(question.expected_keywords or [])}
Réponse de l'étudiant: {student_answer}

{question.explanation or ''}

Fournis un feedback pédagogique (3-4 phrases) qui:
- Évalue la qualité de la réponse
- Identifie les points forts et les points à améliorer
- Suggère des pistes d'approfondissement
- Encourage l'étudiant
"""
        
        try:
            feedback = await self.ollama_service.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            return feedback.strip()
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            if is_correct:
                return "Excellente réponse ! Vous avez bien compris ce concept."
            else:
                return "Ce n'est pas tout à fait correct. Revoyez ce concept et n'hésitez pas à poser des questions." 