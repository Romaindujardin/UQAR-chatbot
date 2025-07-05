from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..core.database import get_db
from ..models.user import User, UserRole
from ..models import Section, ExerciseSubmission, Exercise, ChatSession, ChatMessage, StudentFeedback
from ..services.ollama_service import OllamaService
from .auth import get_current_active_user

router = APIRouter()

class StudentSummary(BaseModel):
    id: int
    full_name: str
    email: str
    has_feedback: bool = False
    feedback_date: Optional[datetime] = None

class FeedbackResponse(BaseModel):
    content: str
    created_at: datetime
    updated_at: datetime


@router.get("/sections/{section_id}/students", response_model=List[StudentSummary])
async def get_section_students(section_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Only teachers can request students of their sections
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès interdit")

    section = db.query(Section).filter(Section.id == section_id, Section.teacher_id == current_user.id).first()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section non trouvée")

    # Query distinct students who have submissions or chats in this section
    student_ids = set()
    for sub in db.query(ExerciseSubmission.student_id).join(ExerciseSubmission.exercise).filter(Exercise.section_id == section_id).all():
        student_ids.add(sub.student_id)
    for chat in db.query(ChatSession.user_id).filter(ChatSession.section_id == section_id).all():
        student_ids.add(chat.user_id)

    students = db.query(User).filter(User.id.in_(student_ids)).all()
    
    # Get feedback info for each student
    result = []
    for student in students:
        feedback = db.query(StudentFeedback).filter(
            StudentFeedback.student_id == student.id,
            StudentFeedback.section_id == section_id
        ).first()
        
        result.append(StudentSummary(
            id=student.id,
            full_name=student.full_name,
            email=student.email,
            has_feedback=feedback is not None,
            feedback_date=feedback.updated_at if feedback else None
        ))
    
    return result

@router.post("/sections/{section_id}/students/{student_id}/analyze")
async def analyze_student(section_id: int, student_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    try:
        if current_user.role != UserRole.TEACHER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès interdit")

        section = db.query(Section).filter(Section.id == section_id, Section.teacher_id == current_user.id).first()
        if not section:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section non trouvée")

        # Fetch exercise submissions
        submissions = db.query(ExerciseSubmission).join(ExerciseSubmission.exercise).filter(Exercise.section_id == section_id, ExerciseSubmission.student_id == student_id).all()

        # Fetch chat messages
        chats = db.query(ChatMessage).join(ChatSession).filter(ChatSession.section_id == section_id, ChatSession.user_id == student_id).order_by(ChatMessage.created_at).all()

        content = []
        for sub in submissions:
            # Calculer le total des points des questions associées à cet exercice
            total_points = sum(question.points for question in sub.exercise.questions) if sub.exercise.questions else 0
            content.append(f"Exercice {sub.exercise_id} score {sub.score}/{total_points}\n")
            for qid, ans in sub.answers.items():
                content.append(f"Q{qid}: {ans}\n")
        for msg in chats:
            role = "ETUDIANT" if not msg.is_assistant else "BOT"
            content.append(f"[{role}] {msg.content}\n")

        prompt = "\n".join(content)
        system_prompt = """Vous êtes un tuteur bienveillant et expert pédagogique. Analysez les réponses et interactions de l'étudiant pour identifier ses forces et ses lacunes principales.

Utilisez le format Markdown pour structurer votre analyse :
- **Gras** pour les points importants
- `Code` pour les termes techniques ou concepts spécifiques
- ## Titres pour organiser votre analyse (ex: ## Points forts, ## Axes d'amélioration)
- - Listes à puces pour énumérer les observations
- > Citations pour mettre en avant des recommandations importantes

Structurez votre analyse avec :
1. Un résumé de la performance globale
2. Les points forts identifiés
3. Les lacunes ou difficultés observées
4. Des recommandations concrètes pour l'amélioration

Soyez constructif et encourageant dans vos commentaires."""
        ollama = OllamaService()
        analysis = await ollama.generate_response(prompt=prompt, system_prompt=system_prompt)

        # Save or update feedback in database
        existing_feedback = db.query(StudentFeedback).filter(
            StudentFeedback.student_id == student_id,
            StudentFeedback.section_id == section_id
        ).first()
        
        if existing_feedback:
            # Update existing feedback
            existing_feedback.content = analysis.strip()
            existing_feedback.teacher_id = current_user.id
        else:
            # Create new feedback
            new_feedback = StudentFeedback(
                student_id=student_id,
                section_id=section_id,
                teacher_id=current_user.id,
                content=analysis.strip()
            )
            db.add(new_feedback)
        
        db.commit()

        return {"analysis": analysis.strip()}
    except Exception as e:
        logger.error(f"Error in analyze_student: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse: {str(e)}"
        )

@router.get("/sections/{section_id}/students/{student_id}/feedback", response_model=FeedbackResponse)
async def get_student_feedback(
    section_id: int, 
    student_id: int, 
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """Récupérer le dernier feedback d'un étudiant"""
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès interdit")

    section = db.query(Section).filter(Section.id == section_id, Section.teacher_id == current_user.id).first()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section non trouvée")

    feedback = db.query(StudentFeedback).filter(
        StudentFeedback.student_id == student_id,
        StudentFeedback.section_id == section_id
    ).first()
    
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucun feedback trouvé pour cet étudiant")
    
    return FeedbackResponse(
        content=feedback.content,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at
    )