from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Callable

from src.application.ports import LeadFollowUpRepositoryPort
from src.domain.auth import User
from src.domain.crm import LeadFollowUp, LeadFollowUpOverview


class GetLeadFollowUpOverviewUseCase:
    def __init__(
        self,
        repository: LeadFollowUpRepositoryPort,
        now: Callable[[], datetime],
    ) -> None:
        self.repository = repository
        self.now = now

    def execute(self, user: User) -> LeadFollowUpOverview:
        current_time = self.now()
        items = self.repository.list_lead_follow_ups(user)
        ordered_items = sorted(items, key=lambda item: (item.next_follow_up_at, item.priority != "high", item.lead_name))
        current_date = current_time.date()

        return LeadFollowUpOverview(
            generated_at=current_time,
            total_open=len(ordered_items),
            due_today=sum(1 for item in ordered_items if item.next_follow_up_at.date() == current_date),
            overdue=sum(1 for item in ordered_items if item.next_follow_up_at < current_time),
            high_priority=sum(1 for item in ordered_items if item.priority == "high"),
            items=[_clone_follow_up(item) for item in ordered_items],
        )


def _clone_follow_up(item: LeadFollowUp) -> LeadFollowUp:
    return replace(item)
