import httpx
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator
import aiohttp
from ..core.config import get_ollama_config

logger = logging.getLogger(__name__)


class OllamaService:
    """Service pour interagir avec Ollama"""

    def __init__(self):
        self.config = get_ollama_config()
        self.base_url = self.config["base_url"]
        self.model = self.config["model"]
        self.max_tokens = self.config["max_tokens"]
        self.temperature = self.config["temperature"]
        self.timeout = self.config.get("timeout", 300)
        logger.info(f"OllamaService initialized with model: {self.model} at {self.base_url}")

    async def generate_response(
        self,
        prompt: str,
        context: Optional[List[str]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Générer une réponse avec Ollama"""

        full_prompt = self._build_prompt(prompt, context, system_prompt)

        try:
            timeout = self.timeout
            is_healthy = await self.health_check()
            if not is_healthy:
                logger.error("Ollama service is not healthy.")
                return "Désolé, le service de génération de texte n'est pas accessible. Veuillez vérifier la configuration."
            
            logger.info(f"Ollama full_prompt to be sent: {full_prompt}")


            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "num_predict": self.max_tokens
                        }
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                elif response.status_code == 404:
                    logger.error(f"Modèle {self.model} non trouvé.")
                    return "Désolé, le modèle demandé n'est pas disponible actuellement."
                elif response.status_code == 500:
                    logger.error(f"Ollama returned 500 Internal Server Error for the preceding logged prompt. Ollama response: {response.text}")
                    return "Désolé, le service de génération de texte a rencontré une erreur interne."
                else:
                    logger.error(f"Erreur Ollama: {response.status_code} - {response.text}")
                    return "Désolé, je ne peux pas répondre pour le moment. Veuillez réessayer plus tard."

        except httpx.ReadTimeout:
            logger.error("Timeout lors de l'appel à Ollama.")
            return "Désolé, la génération de réponse a pris trop de temps. Veuillez essayer une question plus courte."
        except httpx.ConnectTimeout:
            logger.error("Impossible de se connecter au serveur Ollama.")
            return "Désolé, le service de génération de texte n'est pas accessible actuellement."
        except httpx.ConnectError:
            logger.error(f"Erreur de connexion à Ollama à {self.base_url}")
            return "Désolé, le service de génération de texte n'est pas accessible. Veuillez vérifier la configuration."
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            return "Désolé, une erreur s'est produite lors de la génération de la réponse."

    async def generate_streaming_response(
        self,
        prompt: str,
        context: Optional[List[str]] = None,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Générer une réponse en streaming avec Ollama"""

        full_prompt = self._build_prompt(prompt, context, system_prompt)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": True,
                        "options": {
                            "temperature": self.temperature,
                            "num_predict": self.max_tokens
                        }
                    }
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        yield data["response"]
                                    if data.get("done", False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                    else:
                        yield "Erreur lors de la génération de la réponse."

        except Exception as e:
            logger.error(f"Erreur lors du streaming Ollama: {e}")
            yield "Désolé, une erreur s'est produite."

    def _build_prompt(
        self,
        user_prompt: str,
        context: Optional[List[str]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Construire le prompt complet avec contexte"""

        system = system_prompt or (
            "Tu es un assistant éducatif pour l'UQAR. Réponds de manière pédagogique et précise. "
            "Si tu utilises des informations du contexte, cite tes sources."
        )

        prompt = f"### Instruction:\n{system}\n\n"

        if context:
            prompt += "### Contexte:\n"
            for i, ctx in enumerate(context, 1):
                prompt += f"[{i}] {ctx}\n"
            prompt += "\n"

        prompt += f"### Question:\n{user_prompt}\n\n### Réponse:\n"
        return prompt

    async def generate_exercise(
        self,
        content: str,
        exercise_type: str = "qcm",
        difficulty: str = "medium"
    ) -> Dict:
        """Générer un exercice à partir du contenu"""

        system_prompt = (
            "Tu es un générateur d'exercices pédagogiques. "
            f"Génère un exercice de type '{exercise_type}' "
            f"de difficulté '{difficulty}' basé sur le contenu fourni. "
            "Réponds uniquement en JSON valide."
        )

        if exercise_type == "qcm":
            user_prompt = f"""
            Basé sur ce contenu: {content[:1000]}...

            Génère un QCM au format JSON:
            {{
                "question": "Question claire et précise",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option A",
                "explanation": "Explication de la bonne réponse"
            }}
            """
        else:
            user_prompt = f"""
            Basé sur ce contenu: {content[:1000]}...

            Génère une question ouverte au format JSON:
            {{
                "question": "Question ouverte stimulante",
                "expected_keywords": ["mot-clé1", "mot-clé2"],
                "sample_answer": "Exemple de réponse attendue"
            }}
            """

        try:
            response = await self.generate_response(user_prompt, system_prompt=system_prompt)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            return json.loads(response)
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'exercice: {e}")
            return {
                "question": "Erreur lors de la génération",
                "options": ["A", "B", "C", "D"] if exercise_type == "qcm" else [],
                "correct_answer": "A" if exercise_type == "qcm" else "",
                "explanation": "Une erreur s'est produite"
            }

    async def check_relevance(self, query: str, context: str) -> bool:
        """Vérifie si la question est pertinente pour le contexte donné"""

        logger.info(f"Checking relevance for query: '{query[:50]}...' with context: '{context[:50]}...'")

        try:
            system_prompt = """
            Tu es un système de filtrage pour questions éducatives. 
            Ta tâche est de déterminer si une question est pertinente au contexte fourni.
            Réponds UNIQUEMENT par "oui" ou "non".
            - "oui" si la question est liée au contexte ou domaine fourni
            - "non" si la question est complètement hors sujet
            En cas de doute, réponds "oui".
            """

            payload = {
                "model": self.model,
                "prompt": f"Contexte: {context}\n\nQuestion: {query}\n\nCette question est-elle pertinente au contexte fourni? Réponds uniquement par oui ou non.",
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 10,
                },
            }

            url = f"{self.base_url}/api/generate"
            logger.info(f"Sending relevance check request to Ollama at {url}")

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API error: {response.status} - {error_text}")
                        return True

                    data = await response.json()
                    response_text = data.get("response", "").strip().lower()
                    logger.info(f"Relevance check raw response: '{response_text}'")

                    if "non" in response_text:
                        return False
                    return True
        except Exception as e:
            logger.error(f"Error in check_relevance: {e}", exc_info=True)
            return True
    
    async def generate_title(self, question: str) -> str:
        """Génère un titre court résumant la question"""

        try:
            system_prompt = (
                "Tu es un générateur de titres. "
                "À partir de la question de l'utilisateur, réponds uniquement "
                "par un court titre de six mots maximum décrivant son sujet. "
                "N'ajoute pas de ponctuation et ne produis aucune phrase."
            )
            raw = await self.generate_response(
                prompt=question,
                system_prompt=system_prompt,
            )

            title_line = raw.strip().split("\n")[0]
            words = title_line.split()
            cleaned = " ".join(words[:6]).strip().rstrip(".?!")
            return cleaned[:60] if cleaned else "Conversation"
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return "Conversation"

    async def health_check(self) -> bool:
        """Vérifier si Ollama est disponible et si le modèle est chargé"""

        logger.info(f"Checking Ollama health at {self.base_url}")
        try:
            endpoints_to_check = [
                ("/api/version", "Check API version"),
                ("/api/tags", "Check available models"),
            ]

            async with httpx.AsyncClient(timeout=10.0) as client:
                for endpoint, description in endpoints_to_check:
                    try:
                        response = await client.get(f"{self.base_url}{endpoint}")
                        if response.status_code != 200:
                            logger.error(f"{description} failed: {response.status_code} - {response.text}")
                            return False
                        logger.info(f"{description} successful")
                    except Exception as e:
                        logger.error(f"{description} failed: {e}")
                        return False

                # Vérifier si le modèle est présent
                tags_response = await client.get(f"{self.base_url}/api/tags")
                if tags_response.status_code == 200:
                    tags_data = tags_response.json()
                    models = [model.get("name") for model in tags_data.get("models", [])]
                    if self.model in models:
                        logger.info(f"Model {self.model} is available")
                        return True
                    else:
                        logger.error(f"Model {self.model} not in available models: {models}")
                        return False
                return False
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
