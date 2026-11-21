from __future__ import annotations

import os
from datetime import datetime, timezone


_DEPLOYMENT_MARKERS = (
    "RENDER",
    "RENDER_SERVICE_ID",
    "RENDER_INSTANCE_ID",
    "DYNO",
    "HEROKU_APP_NAME",
    "K_SERVICE",
    "VERCEL",
    "VERCEL_ENV",
    "RAILWAY_ENVIRONMENT",
    "FLY_APP_NAME",
    "AWS_EXECUTION_ENV",
    "AWS_LAMBDA_FUNCTION_NAME",
    "CF_PAGES",
)


def loadtest_mock_mode_enabled() -> bool:
    """Allow mocks only when explicitly opted into on a local development process."""
    requested = os.getenv("LOADTEST_MOCK_MODE", "").strip().lower()
    if requested not in {"1", "true", "yes"}:
        return False

    deployment = [name for name in _DEPLOYMENT_MARKERS if os.getenv(name)]
    if os.getenv("APP_ENV", "").strip().lower() != "local" or deployment:
        marker_text = ", ".join(deployment) if deployment else "APP_ENV is not local"
        raise RuntimeError(
            "LOADTEST_MOCK_MODE is restricted to local development; refusing to start "
            f"with mock providers ({marker_text})."
        )
    return True


def loadtest_request_requires_mock_rejection(header_value: str, mock_mode_enabled: bool) -> bool:
    """The test header is a reject-only assertion; it never enables mock mode."""
    return header_value.strip().lower() == "true" and not mock_mode_enabled


def build_report_save_payload(
    *,
    session_id: str,
    patient: dict,
    quiz: dict,
    session_started_at: str,
) -> dict:
    """Build the same report request shape and quiz labels used by the frontend."""
    ended_at = datetime.now(timezone.utc).isoformat()
    pre_test = {**quiz["pre_test"], "submitted_at": ended_at}
    post_test = {**quiz["post_test"], "submitted_at": ended_at}
    return {
        "session_id": session_id,
        "session_started_at": session_started_at,
        "session_ended_at": ended_at,
        "patient": patient,
        "pre_test": pre_test,
        "post_test": post_test,
        "learning_summary": "",
        "completion_status": "completed",
        "doctor_note": "",
    }
