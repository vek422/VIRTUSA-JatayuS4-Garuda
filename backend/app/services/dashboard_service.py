from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.test import Test
from app.models.candidate_application import CandidateApplication
from datetime import datetime

async def get_dashboard_summary(db: AsyncSession, recruiter_id: int):
    # Scheduled, completed, draft, ongoing, etc.
    test_query = select(Test).where(Test.created_by == recruiter_id)
    tests = (await db.execute(test_query)).scalars().all()

    draft_tests = sum(1 for t in tests if t.status == 'draft')
    preparing_tests = sum(1 for t in tests if t.status == 'preparing')
    scheduled_tests = sum(1 for t in tests if t.status == 'scheduled')
    live_tests = sum(1 for t in tests if t.status == 'live')
    ended_tests = sum(1 for t in tests if t.status == 'ended')
    # For dashboard, ongoing = live, completed = ended
    ongoing_tests = live_tests
    completed_tests = ended_tests
    total_tests = len(tests)
    active_tests = ongoing_tests + scheduled_tests
    avg_duration = int(sum(t.time_limit_minutes or 0 for t in tests) / total_tests) if total_tests else 0

    # Recent tests (last 5 by created_at)
    recent_tests = sorted(tests, key=lambda t: t.created_at or datetime.min, reverse=True)[:5]
    recent_tests_data = [
        {
            "name": t.test_name,
            "status": t.status,
            "test_id": t.test_code if hasattr(t, 'test_code') else t.test_id,
            "candidate_count": await _get_candidate_count(db, t.test_id),
            "duration_minutes": t.time_limit_minutes,
            "date": t.created_at.date().isoformat() if t.created_at else None
        }
        for t in recent_tests
    ]

    # Test distribution
    test_distribution = [
        {"label": "Draft", "count": draft_tests},
        {"label": "Preparing", "count": preparing_tests},
        {"label": "Scheduled", "count": scheduled_tests},
        {"label": "Live", "count": live_tests},
        {"label": "Ended", "count": ended_tests}
    ]

    # Total candidates
    candidate_query = select(func.count()).select_from(CandidateApplication).where(CandidateApplication.test_id.in_([t.test_id for t in tests]))
    total_candidates = (await db.execute(candidate_query)).scalar() or 0

    return {
        "draft_tests": draft_tests,
        "preparing_tests": preparing_tests,
        "scheduled_tests": scheduled_tests,
        "live_tests": live_tests,
        "ended_tests": ended_tests,
        "total_candidates": total_candidates,
        "recent_tests": recent_tests_data,
        "test_distribution": test_distribution,
        "quick_stats": {
            "active_tests": live_tests + scheduled_tests,
            "draft_tests": draft_tests,
            "preparing_tests": preparing_tests,
            "scheduled_tests": scheduled_tests,
            "live_tests": live_tests,
            "ended_tests": ended_tests,
            "avg_duration_minutes": avg_duration,
            "total_tests": total_tests
        }
    }

async def _get_candidate_count(db: AsyncSession, test_id: int) -> int:
    from app.models.candidate_application import CandidateApplication
    q = select(func.count()).select_from(CandidateApplication).where(CandidateApplication.test_id == test_id)
    return (await db.execute(q)).scalar() or 0
