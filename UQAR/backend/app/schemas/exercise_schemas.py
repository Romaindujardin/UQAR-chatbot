from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class QuestionType(str, Enum):
    MCQ = "mcq"
    OPEN_ENDED = "open_ended"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionBase(BaseModel):
    text: str = Field(..., description="The question text")
    question_type: QuestionType
    options: Optional[List[str]] = Field(None, description="Options for MCQ questions")
    correct_answer: Optional[str] = Field(None, description="Correct answer for MCQ/True-False")
    expected_keywords: Optional[List[str]] = Field(None, description="Keywords for open-ended questions")
    explanation: Optional[str] = Field(None, description="Explanation of the answer")
    points: Optional[int] = Field(1, description="Points for this question")


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    text: Optional[str] = Field(None, description="The question text")
    question_type: Optional[QuestionType] = None
    options: Optional[List[str]] = Field(None, description="Options for MCQ questions")
    correct_answer: Optional[str] = Field(None, description="Correct answer for MCQ/True-False")
    expected_keywords: Optional[List[str]] = Field(None, description="Keywords for open-ended questions")
    explanation: Optional[str] = Field(None, description="Explanation of the answer")
    points: Optional[int] = Field(None, description="Points for this question")


class QuestionInDB(QuestionBase):
    id: int
    
    class Config:
        from_attributes = True


class ExerciseGenerateRequest(BaseModel):
    # Mode simple (valeurs par défaut)
    num_questions: Optional[int] = Field(5, ge=1, le=20, description="Number of questions to generate")
    difficulty: Optional[DifficultyLevel] = Field(DifficultyLevel.MEDIUM)
    exercise_type: Optional[QuestionType] = Field(QuestionType.MCQ)
    use_specific_documents: Optional[List[int]] = Field(None, description="Specific document IDs to use")
    
    # Mode avancé
    custom_prompt: Optional[str] = Field(None, description="Custom prompt for advanced mode")
    temp_content: Optional[str] = Field(None, description="Temporary content for advanced mode")
    
    @validator('num_questions')
    def validate_num_questions(cls, v):
        if v is not None and (v < 1 or v > 20):
            raise ValueError('Number of questions must be between 1 and 20')
        return v
    
    @validator('custom_prompt')
    def validate_advanced_mode(cls, v, values):
        # Si custom_prompt est fourni, on est en mode avancé
        if v is not None:
            if not v.strip():
                raise ValueError('Custom prompt cannot be empty')
        return v


class ExerciseBase(BaseModel):
    section_id: int
    status: str = Field("pending", description="Exercise status: pending, validated, generating")


class ExerciseCreate(ExerciseBase):
    questions: List[QuestionCreate]


class ExerciseUpdate(BaseModel):
    status: Optional[str] = None
    questions: Optional[List[QuestionCreate]] = None


class ExerciseValidate(BaseModel):
    validation_notes: Optional[str] = Field(None, description="Notes from the teacher")


class ExerciseInDB(ExerciseBase):
    id: int
    questions: List[QuestionInDB]
    created_at: datetime
    updated_at: datetime
    validated_by_id: Optional[int] = None
    validated_at: Optional[datetime] = None
    validation_notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class ExerciseResponse(ExerciseInDB):
    """Response model for exercises"""
    pass


class ExerciseListResponse(BaseModel):
    exercises: List[ExerciseResponse]
    total: int
    page: int
    per_page: int


class StudentAnswerSubmit(BaseModel):
    question_id: int
    answer: str
    
    
class ExerciseSubmission(BaseModel):
    exercise_id: int
    answers: List[StudentAnswerSubmit]
    
    
class AnswerFeedback(BaseModel):
    question_id: int
    is_correct: bool
    feedback: str
    earned_points: int
    
    
class ExerciseResult(BaseModel):
    exercise_id: int
    total_points: int
    earned_points: int
    percentage: float
    feedback: List[AnswerFeedback]
    overall_feedback: str 