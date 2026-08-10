from app.modules.analytics.service import AnalyticsService


class FakeAnalyticsRepo:
    def __init__(self, counts: dict[str, int]):
        self._counts = counts

    async def get_status_counts(self, user_id):
        return self._counts

    async def get_avg_ats_score(self, user_id):
        return 72.5

    async def get_distinct_company_count(self, user_id):
        return 3

    async def get_top_skills(self, user_id, limit=50):
        return []

    async def get_top_companies(self, user_id, limit=20):
        return []


async def test_active_pipeline_excludes_all_terminal_statuses_including_offer():
    """Regression test for the bug found in Phase 6: OFFER was missing from
    the backend's TERMINAL_STATUSES, so an active offer was silently counted
    as 'still in progress.' See jobs/enums.py for the fix and the
    frontend-consistency comment."""
    counts = {"wishlist": 10, "applied": 5, "interview_1": 3, "offer": 1, "rejected": 1}
    service = AnalyticsService(FakeAnalyticsRepo(counts))

    summary = await service.get_dashboard_summary("fake-user-id")

    assert summary.total_applications == 20
    assert summary.active_pipeline == 18  # wishlist + applied + interview_1 only
    assert summary.offers == 1
    assert summary.rejected == 1


async def test_response_rate_excludes_wishlist_from_denominator():
    # 10 applied-or-later, 5 of which never moved past "applied" (no response yet)
    counts = {"wishlist": 3, "applied": 5, "interview_1": 3, "offer": 1, "rejected": 1}
    service = AnalyticsService(FakeAnalyticsRepo(counts))

    summary = await service.get_dashboard_summary("fake-user-id")

    # applied_or_later = 10 - 3 = ... wait: total=13, wishlist=3, applied_or_later=10
    # responded = 10 - applied(5) = 5 -> 50%
    assert summary.response_rate_pct == 50.0


async def test_empty_account_does_not_divide_by_zero():
    service = AnalyticsService(FakeAnalyticsRepo({}))

    summary = await service.get_dashboard_summary("fake-user-id")

    assert summary.total_applications == 0
    assert summary.response_rate_pct == 0.0
    assert summary.active_pipeline == 0
