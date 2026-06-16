# app/routers/words.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.auth import get_current_user
from app.models import Word, User
from app.schemas import WordCreate, WordResponse
from app.services.quiz_factory import DailyQuizFactory, ReviewQuizFactory

router = APIRouter(prefix="/words", tags=["Words"])

@router.post("/", response_model=WordResponse)
async def create_word(word: WordCreate, db: AsyncSession = Depends(get_db)):
    """Usado pelo script inserir_palavras.py para popular o banco"""
    new_word = Word(**word.model_dump())
    db.add(new_word)
    await db.commit()
    await db.refresh(new_word)
    return new_word

@router.get("/", response_model=list[WordResponse])
async def get_all_words(
    db: AsyncSession = Depends(get_db), 
    current_user_email: str = Depends(get_current_user)
):
    """Usado pelo Glossário para listar todas as palavras"""
    result = await db.execute(select(Word))
    return list(result.scalars().all())

@router.get("/quiz", response_model=list[WordResponse])
async def get_quiz(
    quiz_type: str = "daily",
    db: AsyncSession = Depends(get_db),
    current_user_email: str = Depends(get_current_user)
):
    """Gera o Quiz usando o Padrão Abstract Factory"""
    # 1. Busca o ID do utilizador logado
    user_query = await db.execute(select(User).where(User.email == current_user_email))
    user = user_query.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    # 2. Instancia a Fábrica correta dependendo do pedido
    if quiz_type == "review":
        factory = ReviewQuizFactory()
    else:
        factory = DailyQuizFactory()
        
    # 3. Gera as palavras delegando para a Fábrica
    words = await factory.generate_quiz(db, user.id)
    return words