import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from ..core.database import get_db
from ..models import User, Exercise, Question, Section, ExerciseSubmission
from ..models.user import UserRole
from ..models.exercise import ExerciseStatus
from ..schemas.exercise_schemas import (
    ExerciseGenerateRequest, ExerciseResponse, ExerciseValidate,
    ExerciseSubmission as ExerciseSubmissionSchema, ExerciseResult,
    QuestionType, DifficultyLevel, AnswerFeedback, QuestionUpdate
)
from ..services.exercise_service import ExerciseGenerationService, ExerciseFeedbackService
from .auth import get_current_active_user

router = APIRouter()


# Teacher endpoints

@router.post("/sections/{section_id}/exercises/generate", response_model=ExerciseResponse)
async def generate_exercises(
    section_id: int,
    request: ExerciseGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Générer des exercices automatiquement pour une section (Enseignant seulement)"""
    
    # Check permissions
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les enseignants peuvent générer des exercices"
        )
    
    # Check if user owns the section
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section non trouvée"
        )
    
    if section.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez générer des exercices que pour vos propres sections"
        )
    
    # Check if section has documents
    if not section.documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette section n'a pas de documents. Veuillez d'abord télécharger du contenu."
        )
    
    # Generate exercises
    try:
        service = ExerciseGenerationService()
        
        # Détecter le mode de génération
        if request.custom_prompt:
            # Mode avancé
            exercise = await service.generate_exercises_advanced(
                db=db,
                section_id=section_id,
                custom_prompt=request.custom_prompt,
                temp_content=request.temp_content,
                use_specific_documents=request.use_specific_documents
            )
        else:
            # Mode simple
            exercise = await service.generate_exercises(
                db=db,
                section_id=section_id,
                num_questions=request.num_questions or 5,
                difficulty=request.difficulty or DifficultyLevel.MEDIUM,
                exercise_type=request.exercise_type or QuestionType.MCQ,
                use_specific_documents=request.use_specific_documents
            )
        
        try:
            # The 'exercise' object returned by the service should now have 'questions' eagerly loaded.
            # The db.refresh(exercise) call here is likely redundant and potentially problematic if 'exercise' 
            # is from a different session than 'db' in this router. Let's remove it.
            response_data = ExerciseResponse.from_orm(exercise)
            return response_data
        except Exception as pydantic_exc:
            # Log the specific error during Pydantic conversion
            # It's important to get the logger instance first.
            # import logging # This is already imported at the top of the file
            logger = logging.getLogger(__name__)
            logger.error(
                f"Error during Pydantic conversion (ExerciseResponse.from_orm) for exercise ID {exercise.id if exercise else 'Unknown'}: {pydantic_exc}",
                exc_info=True
            )
            # Re-raise as an HTTPException to be handled by FastAPI's error handling
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la préparation de la réponse de l'exercice: {str(pydantic_exc)}"
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération des exercices: {str(e)}"
        )


@router.get("/sections/{section_id}/exercises", response_model=List[ExerciseResponse])
async def get_section_exercises(
    section_id: int,
    validated_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir tous les exercices d'une section"""
    
    # Check if section exists
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section non trouvée"
        )
    
    # Build query
    query = db.query(Exercise).options(
        joinedload(Exercise.questions)
    ).filter(Exercise.section_id == section_id)
    
    # Filter based on user role
    if current_user.role == UserRole.STUDENT:
        # Students can only see validated exercises
        query = query.filter(Exercise.status == ExerciseStatus.VALIDATED)
    elif current_user.role == UserRole.TEACHER:
        # Teachers see all their exercises, or validated ones from other teachers
        if section.teacher_id != current_user.id:
            query = query.filter(Exercise.status == ExerciseStatus.VALIDATED)
        elif validated_only:
            query = query.filter(Exercise.status == ExerciseStatus.VALIDATED)
    
    exercises = query.order_by(Exercise.created_at.desc()).all()
    
    return [ExerciseResponse.from_orm(ex) for ex in exercises]


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir un exercice spécifique"""
    
    exercise = db.query(Exercise).options(
        joinedload(Exercise.questions)
    ).filter(Exercise.id == exercise_id).first()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercice non trouvé"
        )
    
    # Check permissions
    if current_user.role == UserRole.STUDENT:
        if exercise.status != ExerciseStatus.VALIDATED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cet exercice n'est pas encore disponible"
            )
    elif current_user.role == UserRole.TEACHER:
        if exercise.section.teacher_id != current_user.id and exercise.status != ExerciseStatus.VALIDATED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez voir que vos propres exercices ou les exercices validés"
            )
    
    return ExerciseResponse.from_orm(exercise)


@router.put("/exercises/{exercise_id}/validate", response_model=ExerciseResponse)
async def validate_exercise(
    exercise_id: int,
    validation: ExerciseValidate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Valider un exercice (Enseignant seulement)"""
    
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les enseignants peuvent valider des exercices"
        )
    
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercice non trouvé"
        )
    
    # Check if teacher owns the section
    if exercise.section.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez valider que les exercices de vos sections"
        )
    
    # Validate the exercise
    exercise.validate(
        teacher_id=current_user.id,
        notes=validation.validation_notes
    )
    
    db.commit()
    db.refresh(exercise)
    
    return ExerciseResponse.from_orm(exercise)


@router.put("/questions/{question_id}")
async def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Modifier une question (Enseignant seulement)"""
    
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les enseignants peuvent modifier des questions"
        )
    
    # Get the question with its exercise
    question = db.query(Question).options(
        joinedload(Question.exercise).joinedload(Exercise.section)
    ).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question non trouvée"
        )
    
    # Check if teacher owns the section
    if question.exercise.section.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez modifier que les questions de vos sections"
        )
    
    # Update the question fields
    update_data = question_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)
    
    # Update the exercise's updated_at timestamp
    question.exercise.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(question)
    
    return {"message": "Question mise à jour avec succès", "question_id": question_id}


@router.delete("/exercises/{exercise_id}")
async def delete_exercise(
    exercise_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Supprimer un exercice (Enseignant seulement)"""
    
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les enseignants peuvent supprimer des exercices"
        )
    
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercice non trouvé"
        )
    
    # Check if teacher owns the section
    if exercise.section.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que les exercices de vos sections"
        )
    
    db.delete(exercise)
    db.commit()
    
    return {"message": "Exercice supprimé avec succès"}


@router.get("/students/stats")
async def get_student_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir les statistiques de l'étudiant connecté"""
    
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les étudiants peuvent accéder à ces statistiques"
        )
    
    try:
        # Compter les exercices disponibles (validés)
        total_exercises = db.query(Exercise).filter(
            Exercise.status == ExerciseStatus.VALIDATED
        ).count()
        
        # Compter les exercices complétés par l'étudiant
        # IMPORTANT: Ne compter que les exercices distincts complétés (pas le nombre de tentatives)
        completed_exercises = db.query(ExerciseSubmission.exercise_id).join(
            Exercise, ExerciseSubmission.exercise_id == Exercise.id
        ).filter(
            ExerciseSubmission.student_id == current_user.id,
            Exercise.status == ExerciseStatus.VALIDATED
        ).distinct().count()
        
        # Compter les sessions de chat de l'étudiant
        from ..models.chat import ChatSession
        chat_sessions = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).count()
        
        return {
            "total_exercises": total_exercises,
            "completed_exercises": completed_exercises,
            "chat_sessions": chat_sessions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )


# Student endpoints

@router.post("/exercises/{exercise_id}/submit", response_model=ExerciseResult)
async def submit_exercise(
    exercise_id: int,
    submission: ExerciseSubmissionSchema,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Soumettre les réponses à un exercice (Étudiant seulement)"""
    
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les étudiants peuvent soumettre des exercices"
        )
    
    # Get exercise with questions
    exercise = db.query(Exercise).options(
        joinedload(Exercise.questions)
    ).filter(Exercise.id == exercise_id).first()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercice non trouvé"
        )
    
    if exercise.status != ExerciseStatus.VALIDATED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cet exercice n'est pas encore disponible"
        )
    
    # Process answers and generate feedback
    feedback_service = ExerciseFeedbackService()
    total_points = 0
    earned_points = 0
    feedback_list = []
    
    # Create a map of question_id to answer
    answer_map = {ans.question_id: ans.answer for ans in submission.answers}
    
    for question in exercise.questions:
        total_points += question.points
        student_answer = answer_map.get(question.id, "")
        
        # Check if answer is correct
        is_correct = False
        if question.question_type == QuestionType.MCQ.value:
            is_correct = student_answer == question.correct_answer
        elif question.question_type == QuestionType.TRUE_FALSE.value:
            is_correct = student_answer.lower() == question.correct_answer.lower()
        elif question.question_type == QuestionType.OPEN_ENDED.value:
            # For open-ended, check if keywords are present
            if question.expected_keywords and student_answer:
                matched_keywords = sum(1 for kw in question.expected_keywords if kw.lower() in student_answer.lower())
                is_correct = matched_keywords >= len(question.expected_keywords) * 0.5  # At least 50% keywords
        
        # Generate feedback
        feedback_text = await feedback_service.generate_feedback(
            question=question,
            student_answer=student_answer,
            is_correct=is_correct
        )
        
        question_points = question.points if is_correct else 0
        earned_points += question_points
        
        feedback_list.append(AnswerFeedback(
            question_id=question.id,
            is_correct=is_correct,
            feedback=feedback_text,
            earned_points=question_points
        ))
    
    # Calculate percentage
    percentage = (earned_points / total_points * 100) if total_points > 0 else 0
    
    # Save submission to database
    db_submission = ExerciseSubmission(
        exercise_id=exercise_id,
        student_id=current_user.id,
        answers=answer_map,
        score=earned_points,
        percentage=percentage,
        feedback=[fb.dict() for fb in feedback_list]
    )
    db.add(db_submission)
    db.commit()
    
    # Generate overall feedback
    overall_feedback = f"Vous avez obtenu {earned_points}/{total_points} points ({percentage:.1f}%). "
    if percentage >= 80:
        overall_feedback += "Excellent travail ! Vous maîtrisez bien les concepts."
    elif percentage >= 60:
        overall_feedback += "Bon travail ! Continuez à réviser pour renforcer vos connaissances."
    else:
        overall_feedback += "Continuez vos efforts ! N'hésitez pas à revoir le cours et poser des questions."
    
    return ExerciseResult(
        exercise_id=exercise_id,
        total_points=total_points,
        earned_points=earned_points,
        percentage=percentage,
        feedback=feedback_list,
        overall_feedback=overall_feedback
    )


@router.get("/exercises/{exercise_id}/submissions")
async def get_exercise_submissions(
    exercise_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtenir les soumissions d'un exercice"""
    
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercice non trouvé"
        )
    
    if current_user.role == UserRole.STUDENT:
        # Students can only see their own submissions
        submissions = db.query(ExerciseSubmission).filter(
            ExerciseSubmission.exercise_id == exercise_id,
            ExerciseSubmission.student_id == current_user.id
        ).order_by(ExerciseSubmission.submitted_at.desc()).all()
    elif current_user.role == UserRole.TEACHER:
        # Teachers can see all submissions for their sections
        if exercise.section.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez voir que les soumissions de vos sections"
            )
        submissions = db.query(ExerciseSubmission).filter(
            ExerciseSubmission.exercise_id == exercise_id
        ).order_by(ExerciseSubmission.submitted_at.desc()).all()
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    return submissions 