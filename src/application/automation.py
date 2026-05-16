from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol


class AutomationStatePort(Protocol):
    def read_state(self) -> dict[str, dict[str, object]]:
        """Return persisted automation state keyed by job name."""

    def write_state(self, state: dict[str, dict[str, object]]) -> None:
        """Persist automation state."""


class AutomationHeartbeatPort(Protocol):
    def write_heartbeat(self, beat: "AutomationHeartbeat") -> None:
        """Persist the latest worker heartbeat."""


@dataclass(frozen=True, slots=True)
class AutomationJobResult:
    status: str
    detail: str


@dataclass(frozen=True, slots=True)
class AutomationJob:
    name: str
    interval: timedelta
    runner: Callable[[], AutomationJobResult]


@dataclass(frozen=True, slots=True)
class AutomationHeartbeat:
    generated_at: datetime
    process_id: int
    active_job_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExecutedAutomationJob:
    name: str
    started_at: datetime
    finished_at: datetime
    result: AutomationJobResult


@dataclass(frozen=True, slots=True)
class AutomationTickResult:
    executed_jobs: tuple[ExecutedAutomationJob, ...]
    next_due_job_names: tuple[str, ...]


class RunAutomationTickUseCase:
    def __init__(
        self,
        state_port: AutomationStatePort,
        heartbeat_port: AutomationHeartbeatPort,
        now: Callable[[], datetime] = lambda: datetime.now(tz=UTC),
    ) -> None:
        self.state_port = state_port
        self.heartbeat_port = heartbeat_port
        self.now = now

    def execute(self, jobs: tuple[AutomationJob, ...], process_id: int) -> AutomationTickResult:
        started_at = self.now()
        state = self.state_port.read_state()
        self.heartbeat_port.write_heartbeat(
            AutomationHeartbeat(
                generated_at=started_at,
                process_id=process_id,
                active_job_names=tuple(job.name for job in jobs),
            )
        )

        executed_jobs: list[ExecutedAutomationJob] = []
        for job in jobs:
            if not _job_is_due(job, state.get(job.name), started_at):
                continue

            job_started_at = self.now()
            try:
                result = job.runner()
            except Exception as exc:  # pragma: no cover - covered via tests calling fake runner
                result = AutomationJobResult(status="failed", detail=str(exc))
            job_finished_at = self.now()
            executed_jobs.append(
                ExecutedAutomationJob(
                    name=job.name,
                    started_at=job_started_at,
                    finished_at=job_finished_at,
                    result=result,
                )
            )
            state[job.name] = {
                "last_started_at": job_started_at.isoformat(),
                "last_finished_at": job_finished_at.isoformat(),
                "last_status": result.status,
                "last_detail": result.detail,
            }

        self.state_port.write_state(state)
        next_due_job_names = tuple(job.name for job in jobs if _job_is_due(job, state.get(job.name), self.now()))
        return AutomationTickResult(executed_jobs=tuple(executed_jobs), next_due_job_names=next_due_job_names)


def _job_is_due(job: AutomationJob, job_state: dict[str, object] | None, now: datetime) -> bool:
    if not job_state:
        return True
    last_started_at = _parse_datetime(job_state.get("last_started_at"))
    if last_started_at is None:
        return True
    return now >= last_started_at + job.interval


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return datetime.fromisoformat(value)
