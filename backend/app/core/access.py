"""Visibility and manage rights for Cultural Objects.

The public archive shows published objects only. A creator's own objects at any
other lifecycle stage (draft, processing, review, verified, restricted,
withdrawn) are visible ONLY through their personal account — never in the
archive listing or archive search. Accepted reviewers (and admins) see the
review pipeline through an explicit status filter (the review queue); manage
rights belong to the object's creator account or a reviewer/admin.
"""

from app.models import CulturalObject, User
from app.models.enums import ObjectStatus

PUBLIC_STATUSES = frozenset({ObjectStatus.PUBLISHED.value})
REVIEW_STATUSES = frozenset({ObjectStatus.PROCESSING.value, ObjectStatus.REVIEW.value})
MANAGER_ROLES = frozenset({"reviewer", "admin"})


def visible_statuses(
    user: User | None, requested_status: str | None = None
) -> frozenset[str]:
    """Statuses visible through the archive listing / search.

    Everyone sees only ``published``. A reviewer/admin may additionally query a
    review-pipeline status explicitly (the review queue is an opt-in filter, not
    part of the archive listing).
    """
    if (
        requested_status in REVIEW_STATUSES
        and user is not None
        and user.role in MANAGER_ROLES
    ):
        return frozenset({requested_status})
    return PUBLIC_STATUSES


def can_view(user: User | None, obj: CulturalObject) -> bool:
    if obj.status in PUBLIC_STATUSES:
        return True
    if user is None:
        return False
    if obj.user_id is not None and obj.user_id == user.id:
        return True
    if user.role in MANAGER_ROLES and obj.status in REVIEW_STATUSES:
        return True
    return False


def can_manage(user: User | None, obj: CulturalObject) -> bool:
    if user is None:
        return False
    if obj.user_id is not None and obj.user_id == user.id:
        return True
    return user.role in MANAGER_ROLES


def can_review(user: User | None) -> bool:
    return user is not None and user.role in MANAGER_ROLES