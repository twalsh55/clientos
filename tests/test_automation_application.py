from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.application.automation import (
    AutomationHeartbeat,
    AutomationJob,
    AutomationJobResult,
    RunAutomationTickUseCase,
)


class FakeStateStore:
    def __init__(self, state: dict[str, dict[str, object]] | None = None) -> None:
        self.state = state or {}

    def read_state(self) -> dict[str, dict[str, object]]:
        return dict(self.state)

    def write_state(self, state: dict[str, dict[str, object]]) -> None:
        self.state = state


class FakeHeartbeatStore:
    def __init__(self) -> None:
        self.beats: list[AutomationHeartbeat] = []

    def write_heartbeat(self, beat: AutomationHeartbeat) -> None:
        self.beats.append(beat)


def test_run_automation_tick_executes_due_jobs_and_persists_state() -> None:
    times = iter(
        [
            datetime(2026, 5, 16, 10, 0, tzinfo=UTC),
            datetime(2026, 5, 16, 10, 0, tzinfo=UTC),
            datetime(2026, 5, 16, 10, 1, tzinfo=UTC),
            datetime(2026, 5, 16, 10, 2, tzinfo=UTC),
        ]
    )
    state_store = FakeStateStore()
    heartbeat_store = FakeHeartbeatStore()
    seen: list[str] = []

    use_case = RunAutomationTickUseCase(
        state_port=state_store,
        heartbeat_port=heartbeat_store,
        now=lambda: next(times),
    )
    result = use_case.execute(
        (
            AutomationJob(
                name="prospect",
                interval=timedelta(hours=1),
                runner=lambda: seen.append("prospect") or AutomationJobResult(status="ok", detail="done"),
            ),
        ),
        process_id=123,
    )

    assert seen == ["prospect"]
    assert heartbeat_store.beats[0].process_id == 123
    assert result.executed_jobs[0].name == "prospect"
    assert state_store.state["prospect"]["last_status"] == "ok"
    assert result.next_due_job_names == ()


def test_run_automation_tick_skips_recent_job_and_handles_invalid_or_missing_state() -> None:
    recent = datetime(2026, 5, 16, 10, 0, tzinfo=UTC)
    state_store = FakeStateStore(
        {
            "prospect": {"last_started_at": recent.isoformat(), "last_status": "ok"},
            "broken": {"last_started_at": ""},
        }
    )
    heartbeat_store = FakeHeartbeatStore()
    seen: list[str] = []
    use_case = RunAutomationTickUseCase(
        state_port=state_store,
        heartbeat_port=heartbeat_store,
        now=lambda: recent + timedelta(minutes=30),
    )
    result = use_case.execute(
        (
            AutomationJob(
                name="prospect",
                interval=timedelta(hours=1),
                runner=lambda: seen.append("prospect") or AutomationJobResult(status="ok", detail="done"),
            ),
            AutomationJob(
                name="broken",
                interval=timedelta(hours=1),
                runner=lambda: seen.append("broken") or AutomationJobResult(status="ok", detail="recovered"),
            ),
        ),
        process_id=999,
    )

    assert seen == ["broken"]
    assert result.executed_jobs[0].name == "broken"
    assert result.next_due_job_names == ()


def test_run_automation_tick_converts_runner_exception_to_failed_result() -> None:
    state_store = FakeStateStore()
    heartbeat_store = FakeHeartbeatStore()
    use_case = RunAutomationTickUseCase(
        state_port=state_store,
        heartbeat_port=heartbeat_store,
        now=lambda: datetime(2026, 5, 16, 10, 0, tzinfo=UTC),
    )
    result = use_case.execute(
        (
            AutomationJob(
                name="failing",
                interval=timedelta(hours=1),
                runner=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
            ),
        ),
        process_id=55,
    )

    assert result.executed_jobs[0].result.status == "failed"
    assert result.executed_jobs[0].result.detail == "boom"
