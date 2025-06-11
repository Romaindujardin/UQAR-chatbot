import logging
import json
import re
import asyncio
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
        
        questions: List[Dict] = []
        max_retries = 3
        retry_delay_seconds = 2

        for attempt in range(max_retries):
            try:
                # Generate with Ollama
                logger.info(f"Attempt {attempt + 1}/{max_retries}: Calling Ollama to generate questions...")
                response = await self.ollama_service.generate_response(
                    prompt=user_prompt,
                    system_prompt=system_prompt
                )
                
                logger.info(f"Ollama response received (length: {len(response)})")
                logger.debug(f"Ollama response: {response[:500]}...")

                # Parse the response
                questions = self._parse_generated_questions(response, exercise_type)
                logger.info(f"Parsed {len(questions)} questions from Ollama response on attempt {attempt + 1}")

                # Check if enough questions were generated
                if len(questions) >= num_questions:
                    logger.info(f"Successfully generated {len(questions)} questions.")
                    break  # Exit loop if successful
                else:
                    logger.warning(f"Generated {len(questions)}/{num_questions} questions on attempt {attempt + 1}.")
                    if attempt < max_retries - 1:
                        logger.warning(f"Retrying in {retry_delay_seconds}s...")
                        await asyncio.sleep(retry_delay_seconds)
                    else:
                        # This is the final attempt and still not enough questions
                        logger.error(
                            f"Final attempt {attempt + 1}/{max_retries} failed to generate and parse enough questions. "
                            f"Got {len(questions)} out of {num_questions}."
                        )
                        logger.debug(f"Raw Ollama response on final attempt: {response}")

            except Exception as e:
                logger.error(f"Error generating questions with Ollama on attempt {attempt + 1}: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    logger.warning(f"Retrying in {retry_delay_seconds}s...")
                    await asyncio.sleep(retry_delay_seconds)
                else:
                    logger.error(f"Failed to generate questions after {max_retries} attempts due to error.")
                    # Also log the response if available and an error occurred on the last attempt
                    if 'response' in locals() and response:
                         logger.debug(f"Raw Ollama response on final failed attempt (exception): {response}")

        # Ensure we have the requested number of questions, otherwise use fallback
        if len(questions) < num_questions:
            logger.warning(
                f"Generated only {len(questions)} questions instead of {num_questions} after all retries. "
                f"Using fallback questions."
            )
            logger.critical(f"CRITICAL: Using fallback questions for section {section_name} as all Ollama generation attempts failed.")
            # Fallback questions are returned, no need to log 'response' here again as it was logged above if it was the last attempt.
            return self._get_fallback_questions(num_questions, exercise_type)
            
        return questions[:num_questions]

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
            
            # Try to extract JSON from the response using regex
            match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
            
            if match:
                json_str = match.group(0)
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
        base_explanation = "Explication: La génération automatique de cette question a échoué. L'enseignant doit la compléter ou la remplacer."
        
        for i in range(num_questions):
            question_text_prefix = f"ATTENTION: Génération automatique échouée. Question {i+1}: "

            if exercise_type == QuestionType.MCQ:
                question = {
                    "text": question_text_prefix + "Veuillez reformuler cette question basée sur le contenu du cours.",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A",
                    "explanation": base_explanation,
                    "points": 1
                }
            elif exercise_type == QuestionType.OPEN_ENDED:
                question = {
                    "text": question_text_prefix + "Analysez et expliquez un concept important du cours.",
                    "expected_keywords": ["concept", "analyse", "explication"],
                    "explanation": base_explanation,
                    "points": 2
                }
            elif exercise_type == QuestionType.TRUE_FALSE: # Added specific handling for TRUE_FALSE
                question = {
                    "text": question_text_prefix + "Affirmez ou niez la déclaration suivante basée sur le contenu du cours.",
                    "correct_answer": "true", # Default to true, teacher should verify
                    "explanation": base_explanation,
                    "points": 1
                }
            else:  # Handles FILL_BLANK and any other types
                question = {
                    "text": question_text_prefix + "[À compléter par l'enseignant]",
                    "correct_answer": "Réponse à définir", # More generic than "true"
                    "explanation": base_explanation,
                    "points": 1
                }
                
            fallback_questions.append(question)
            
        return fallback_questions
        
        
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