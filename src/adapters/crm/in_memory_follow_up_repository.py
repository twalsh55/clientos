from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from src.domain.auth import User
from src.domain.crm import LeadFollowUp


class InMemoryLeadFollowUpRepository:
    def __init__(self, now: callable | None = None) -> None:
        self.now = now or (lambda: datetime.now(tz=UTC))
        self._items = self._build_seed_data()

    def list_lead_follow_ups(self, user: User) -> list[LeadFollowUp]:
        return [replace(item) for item in self._items.values()]

    def complete_lead_follow_up(self, user: User, follow_up_id: str, completed_at: datetime) -> None:
        if follow_up_id not in self._items:
            raise KeyError(follow_up_id)
        del self._items[follow_up_id]

    def snooze_lead_follow_up(self, user: User, follow_up_id: str, next_follow_up_at: datetime) -> None:
        item = self._items.get(follow_up_id)
        if item is None:
            raise KeyError(follow_up_id)
        self._items[follow_up_id] = replace(item, next_follow_up_at=next_follow_up_at)

    def _build_seed_data(self) -> dict[str, LeadFollowUp]:
        current_time = self.now()
        items = [
            LeadFollowUp(
                id="lead-amber-studio",
                lead_name="Amber Flores",
                company_name="Northstar Studio",
                stage="Discovery",
                priority="high",
                contact_channel="email",
                last_contacted_at=current_time - timedelta(days=5),
                next_follow_up_at=current_time - timedelta(hours=4),
                next_step="Send a concise recap and propose two call slots.",
                notes="Interested, but waiting on a clearer summary of timeline and scope.",
            ),
            LeadFollowUp(
                id="lead-riverbridge",
                lead_name="Marcus Chen",
                company_name="Riverbridge Ops",
                stage="Proposal",
                priority="high",
                contact_channel="linkedin",
                last_contacted_at=current_time - timedelta(days=2),
                next_follow_up_at=current_time + timedelta(hours=2),
                next_step="Follow up on proposal review and confirm who signs off internally.",
                notes="Opened the proposal twice. Mentioned concern about rollout burden.",
            ),
            LeadFollowUp(
                id="lead-lattice",
                lead_name="Priya Nair",
                company_name="Lattice Lane",
                stage="Qualification",
                priority="medium",
                contact_channel="email",
                last_contacted_at=current_time - timedelta(days=1),
                next_follow_up_at=current_time + timedelta(days=1),
                next_step="Share two examples of similar results and ask for current CRM workflow pain.",
                notes="Strong fit if lead capture and follow-up remain spreadsheet based.",
            ),
            LeadFollowUp(
                id="lead-cedar",
                lead_name="Jordan Pike",
                company_name="Cedar Peak Agency",
                stage="Negotiation",
                priority="medium",
                contact_channel="phone",
                last_contacted_at=current_time - timedelta(days=3),
                next_follow_up_at=current_time + timedelta(days=2),
                next_step="Confirm decision deadline and check whether they need a lighter pilot option.",
                notes="Likes the direction, but comparing against doing it manually one more quarter.",
            ),
        ]
        return {item.id: item for item in items}
