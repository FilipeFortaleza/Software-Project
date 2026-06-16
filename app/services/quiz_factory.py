# app/services/quiz_factory.py

from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Word, Mistake, Progress

# 1. Interface Abstrata da Fábrica
class QuizFactory(ABC):
    @abstractmethod
    async def generate_quiz(self, db: AsyncSession, user_id: int) -> list[Word]:
        pass

# 2. Fábrica Concreta 1: Treino Diário (Palavras Novas)
class DailyQuizFactory(QuizFactory):
    async def generate_quiz(self, db: AsyncSession, user_id: int) -> list[Word]:
        # Busca os IDs das palavras que o utilizador já aprendeu
        learned_query = await db.execute(select(Progress.word_id).where(Progress.user_id == user_id))
        learned_ids = [row[0] for row in learned_query.fetchall()]
        
        # Filtra as palavras novas
        query = select(Word)
        if learned_ids:
            query = query.where(Word.id.notin_(learned_ids))
        
        result = await db.execute(query.limit(10))
        return list(result.scalars().all())

# 3. Fábrica Concreta 2: Treino de Revisão (Erros Anteriores)
class ReviewQuizFactory(QuizFactory):
    async def generate_quiz(self, db: AsyncSession, user_id: int) -> list[Word]:
        # Busca os IDs das palavras que o utilizador errou
        mistakes_query = await db.execute(select(Mistake.word_id).where(Mistake.user_id == user_id))
        mistake_ids = [row[0] for row in mistakes_query.fetchall()]
        
        if not mistake_ids:
            return [] # Se não tem erros, devolve lista vazia
            
        result = await db.execute(select(Word).where(Word.id.in_(mistake_ids)).limit(10))
        return list(result.scalars().all())