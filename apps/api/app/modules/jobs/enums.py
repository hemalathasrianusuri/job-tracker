from enum import StrEnum


class JobStatus(StrEnum):
    WISHLIST = "wishlist"
    APPLIED = "applied"
    OA_SCHEDULED = "oa_scheduled"
    OA_COMPLETED = "oa_completed"
    INTERVIEW_1 = "interview_1"
    INTERVIEW_2 = "interview_2"
    INTERVIEW_3 = "interview_3"
    HR_ROUND = "hr_round"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    GHOSTED = "ghosted"


class WorkMode(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


# Terminal states — once here, the application record is closed. Used by the
# dashboard to compute "active pipeline" counts vs. resolved outcomes.
# OFFER is included: once an offer is extended, the applicant is at a decision
# point, not still progressing through interview rounds — this matches the
# frontend's ACTIVE_PIPELINE (which stops at HR_ROUND) and TERMINAL_STATUSES
# (which lists offer as a "success" terminal state). Keep these in sync if
# either side changes.
TERMINAL_STATUSES = {
    JobStatus.OFFER,
    JobStatus.ACCEPTED,
    JobStatus.REJECTED,
    JobStatus.WITHDRAWN,
    JobStatus.GHOSTED,
}
