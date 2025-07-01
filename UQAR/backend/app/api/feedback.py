from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..core.database import get_db
from ..models.user import User, UserRole
from ..models import Section, ExerciseSubmission, Exercise, ChatSession, ChatMessage
from ..services.ollama_service import OllamaService
from .auth import get_current_active_user

router = APIRouter()

class StudentSummary(BaseModel):
    id: int
    full_name: str
    email: str


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
    return [StudentSummary(id=s.id, full_name=s.full_name, email=s.email) for s in students]

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
        system_prompt = "Vous êtes un tuteur bienveillant. Analysez les réponses de l'étudiant et identifiez ses lacunes principales."
        ollama = OllamaService()
        analysis = await ollama.generate_response(prompt=prompt, system_prompt=system_prompt)

        return {"analysis": analysis.strip()}
    except Exception as e:
        logger.error(f"Error in analyze_student: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse: {str(e)}"
        )