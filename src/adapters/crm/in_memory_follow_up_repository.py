from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.domain.auth import User
from src.domain.crm import LeadFollowUp


class InMemoryLeadFollowUpRepository:
    def __init__(self, now: callable | None = None) -> None:
        self.now = now or (lambda: datetime.now(tz=UTC))

    def list_lead_follow_ups(self, user: User) -> list[LeadFollowUp]:
        current_time = self.now()
        owner = user.given_name or user.display_name or user.email or "You"
        return [
            LeadFollowUp(
                id="lead-amber-studio",
                lead_name="Amber Flores",
                company_name="Northstar Studio",
                stage="Discovery",
                priority="high",
                contact_channel="email",
                last_contacted_at=current_time - timedelta(days=5),
                next_follow_up_at=current_time - timedelta(hours=4),
                next_step=f"Send {owner}'s concise recap and propose two call slots.",
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
