from __future__ import annotations

from src.adapters.crm.in_memory_follow_up_repository import InMemoryLeadFollowUpRepository


def build_lead_follow_up_repository() -> InMemoryLeadFollowUpRepository:
    return InMemoryLeadFollowUpRepository()
