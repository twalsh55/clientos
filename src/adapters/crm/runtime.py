from __future__ import annotations

from src.adapters.crm.in_memory_follow_up_repository import InMemoryLeadFollowUpRepository


_repository: InMemoryLeadFollowUpRepository | None = None


def build_lead_follow_up_repository() -> InMemoryLeadFollowUpRepository:
    global _repository
    if _repository is None:
        _repository = InMemoryLeadFollowUpRepository()
    return _repository
