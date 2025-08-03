from sqlalchemy import select
from app.models.candidate_application import CandidateApplication

async def count_candidates_by_test_id(db, test_id: int) -> int:
    result = await db.execute(
        select(CandidateApplication).where(CandidateApplication.test_id == test_id)
    )
    return len(result.scalars().all())
