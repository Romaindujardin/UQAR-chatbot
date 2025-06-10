import asyncio
import unittest
from unittest.mock import patch, MagicMock, call, AsyncMock # Ensure AsyncMock is imported
import re

from UQAR.backend.app.services.exercise_service import ExerciseGenerationService, QuestionType, DifficultyLevel
from UQAR.backend.app.services.ollama_service import OllamaService

class TestExerciseGenerationService(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.service = ExerciseGenerationService()
        self.service.chroma_client = MagicMock()
        # Mock the ollama_service instance within our service instance
        self.service.ollama_service = MagicMock(spec=OllamaService)
        # Specifically mock its async method generate_response using AsyncMock
        # This will be reassigned in tests if specific side_effects are needed
        self.service.ollama_service.generate_response = AsyncMock()


    def test_parse_valid_json_array(self):
        json_string = '[{"text": "Q1", "options": ["A", "B"], "correct_answer": "A", "explanation": "Expl1"}]'
        questions = self.service._parse_generated_questions(json_string, QuestionType.MCQ)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['text'], 'Q1')

    def test_parse_json_with_leading_text(self):
        json_string = 'Some preamble text... [{"text": "Q1", "options": ["A", "B"], "correct_answer": "A", "explanation": "Expl1"}]'
        questions = self.service._parse_generated_questions(json_string, QuestionType.MCQ)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['text'], 'Q1')

    def test_parse_json_with_trailing_text(self):
        json_string = '[{"text": "Q1", "options": ["A", "B"], "correct_answer": "A", "explanation": "Expl1"}] ...some trailing notes.'
        questions = self.service._parse_generated_questions(json_string, QuestionType.MCQ)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['text'], 'Q1')

    def test_parse_json_with_leading_and_trailing_text(self):
        json_string = 'Preamble... [{"text": "Q1", "options": ["A", "B"], "correct_answer": "A", "explanation": "Expl1"}] ...Postamble.'
        questions = self.service._parse_generated_questions(json_string, QuestionType.MCQ)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['text'], 'Q1')

    def test_parse_json_with_internal_brackets_in_text(self):
        json_string = 'Text with [some brackets] and [other brackets]. [{"text": "Question [with detail]", "options": ["A", "B"], "correct_answer": "A", "explanation": "Expl1"}] Text with [final brackets].'
        questions = self.service._parse_generated_questions(json_string, QuestionType.MCQ)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['text'], 'Question [with detail]')

    def test_parse_malformed_json(self):
        json_string = '[{"text": "Q1", "options": ["A", "B"], "correct_answer": "A", "explanation": "Expl1"' # Missing closing brace and bracket
        questions = self.service._parse_generated_questions(json_string, QuestionType.MCQ)
        self.assertEqual(len(questions), 0)

    def test_parse_empty_string_or_not_json(self):
        questions = self.service._parse_generated_questions("", QuestionType.MCQ)
        self.assertEqual(len(questions), 0)
        questions = self.service._parse_generated_questions("This is not JSON.", QuestionType.MCQ)
        self.assertEqual(len(questions), 0)

    def test_parse_valid_json_but_wrong_structure(self):
        json_string = '[{"title": "Q1"}]'
        questions = self.service._parse_generated_questions(json_string, QuestionType.MCQ)
        self.assertEqual(len(questions), 0)

    @patch.object(ExerciseGenerationService, '_get_fallback_questions')
    async def test_generate_questions_success_first_try(self, mock_get_fallback_questions):
        self.service.ollama_service.generate_response.return_value = '[{"text": "Q1", "options": ["A"], "correct_answer": "A", "explanation": "E1"}, {"text": "Q2", "options": ["B"], "correct_answer": "B", "explanation": "E2"}]'

        result_questions = await self.service._generate_questions(
            content_chunks=[{"text": "chunk1"}],
            num_questions=2,
            difficulty=DifficultyLevel.EASY,
            exercise_type=QuestionType.MCQ,
            section_name="Test Section"
        )

        self.service.ollama_service.generate_response.assert_called_once()
        self.assertEqual(len(result_questions), 2)
        self.assertEqual(result_questions[0]['text'], 'Q1')
        mock_get_fallback_questions.assert_not_called()

    @patch.object(ExerciseGenerationService, '_get_fallback_questions')
    async def test_generate_questions_success_on_retry(self, mock_get_fallback_questions):
        self.service.ollama_service.generate_response.side_effect = [
            Exception("Ollama unavailable"),
            '[{"text": "Q1 - Attempt 2", "options": ["A"], "correct_answer": "A", "explanation": "E_A2"}, {"text": "Q2 - Attempt 2", "options": ["B"], "correct_answer": "B", "explanation": "E_B2"}]'
        ]

        result_questions = await self.service._generate_questions(
            content_chunks=[{"text": "chunk1"}],
            num_questions=2,
            difficulty=DifficultyLevel.EASY,
            exercise_type=QuestionType.MCQ,
            section_name="Test Section"
        )

        self.assertEqual(self.service.ollama_service.generate_response.call_count, 2)
        self.assertEqual(len(result_questions), 2)
        self.assertEqual(result_questions[0]['text'], 'Q1 - Attempt 2')
        mock_get_fallback_questions.assert_not_called()

    @patch.object(ExerciseGenerationService, '_get_fallback_questions')
    async def test_generate_questions_fail_all_retries_uses_fallback(self, mock_get_fallback_questions):
        self.service.ollama_service.generate_response.side_effect = [
            Exception("Ollama unavailable"),
            Exception("Ollama still unavailable"),
            Exception("Ollama persistently unavailable")
        ]
        mock_fallback_question_data = [{"text": "Fallback Q1", "options": [], "correct_answer": "", "explanation": ""}]
        mock_get_fallback_questions.return_value = mock_fallback_question_data

        result_questions = await self.service._generate_questions(
            content_chunks=[{"text": "chunk1"}],
            num_questions=1,
            difficulty=DifficultyLevel.EASY,
            exercise_type=QuestionType.MCQ,
            section_name="Test Section"
        )

        self.assertEqual(self.service.ollama_service.generate_response.call_count, 3)
        mock_get_fallback_questions.assert_called_once_with(1, QuestionType.MCQ)
        self.assertEqual(result_questions, mock_fallback_question_data)

    @patch.object(ExerciseGenerationService, '_get_fallback_questions')
    async def test_generate_questions_parse_fail_all_retries_uses_fallback(self, mock_get_fallback_questions):
        self.service.ollama_service.generate_response.return_value = "This is not valid JSON and never will be" # Ensure AsyncMock handles non-exception side effects correctly for return_value

        mock_fallback_question_data = [{"text": "Fallback Q1 - Parse Fail", "options": [], "correct_answer": "", "explanation": ""}]
        mock_get_fallback_questions.return_value = mock_fallback_question_data

        result_questions = await self.service._generate_questions(
            content_chunks=[{"text": "chunk1"}],
            num_questions=1,
            difficulty=DifficultyLevel.EASY,
            exercise_type=QuestionType.MCQ,
            section_name="Test Section"
        )

        self.assertEqual(self.service.ollama_service.generate_response.call_count, 3)
        mock_get_fallback_questions.assert_called_once_with(1, QuestionType.MCQ)
        self.assertEqual(result_questions, mock_fallback_question_data)

if __name__ == '__main__':
    unittest.main()
