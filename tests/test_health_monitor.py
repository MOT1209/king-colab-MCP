import time

from google_colab_mcp.colab.health_monitor import HealthMonitor
from google_colab_mcp.colab.session_manager import SessionManager


def test_check_once_reconnects_unhealthy_session(ctx):
    session = ctx.session_manager.create_session(provider_id="fake", label="watched")
    session.backend.disconnect()  # simulate a dropped connection
    assert session.backend.is_connected is False

    monitor = HealthMonitor(ctx.session_manager, max_reconnect_attempts=2)
    monitor.check_once()

    refreshed = ctx.session_manager.get(session.session_id)
    assert refreshed.backend.is_connected is True


def test_check_once_gives_up_after_max_attempts(ctx, monkeypatch):
    session = ctx.session_manager.create_session(provider_id="fake", label="stubborn")

    def _always_unhealthy(session_id):
        return {"provider": "fake", "state": "failed", "healthy": False, "verification": {}}

    monkeypatch.setattr(ctx.session_manager, "health_check", _always_unhealthy)

    reconnect_calls = []
    original_reconnect = ctx.session_manager.reconnect

    def _counting_reconnect(session_id):
        reconnect_calls.append(session_id)
        return original_reconnect(session_id)

    monkeypatch.setattr(ctx.session_manager, "reconnect", _counting_reconnect)

    monitor = HealthMonitor(ctx.session_manager, max_reconnect_attempts=2)
    for _ in range(5):
        monitor.check_once()

    assert len(reconnect_calls) == 2


def test_start_and_stop_thread_lifecycle(ctx):
    monitor = HealthMonitor(ctx.session_manager, interval_seconds=0.05)
    monitor.start()
    time.sleep(0.15)
    monitor.stop()
    assert monitor._thread is None
