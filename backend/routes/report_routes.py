from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import Response
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from auth.subscription import get_current_active_admin
from database import db_session_scope
from models.report_models import HospitalAdmin
from schemas.report_schemas import AdminReportDetail
from schemas.report_schemas import AdminReportListItem
from schemas.report_schemas import FinalReportSaveRequest
from schemas.report_schemas import ReportSaveResponse
from schemas.report_schemas import SessionEndRequest
from schemas.report_schemas import SessionEndResponse
from schemas.report_schemas import SessionResumeResponse
from schemas.report_schemas import SessionStartRequest
from schemas.report_schemas import SessionStartResponse
from services.report_service import ReportService


router = APIRouter(tags=["reports"])
logger = logging.getLogger(__name__)


def _same_postgres_database(first_url: str, second_url: str) -> bool:
    """Compare database targets without exposing credentials or query parameters."""
    try:
        first = make_url(first_url)
        second = make_url(second_url)
    except (TypeError, ValueError):
        return False
    return (
        first.drivername.split("+", 1)[0] == second.drivername.split("+", 1)[0]
        and (first.host or "").lower() == (second.host or "").lower()
        and (first.port or 5432) == (second.port or 5432)
        and first.database == second.database
    )


@router.get("/session/{session_id}/resume", response_model=SessionResumeResponse)
def resume_session(
    session_id: str,
    current_admin: HospitalAdmin = Depends(get_current_active_admin),
) -> SessionResumeResponse:
    try:
        with db_session_scope() as db:
            state = ReportService(db).get_active_session_state(
                session_id, admin_id=current_admin.id
            )
            if state is None:
                raise HTTPException(status_code=404, detail="Active patient session was not found.")
            return SessionResumeResponse(**state)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Active patient session was not found.") from exc


@router.post("/session/start", response_model=SessionStartResponse)
def start_session(
    payload: SessionStartRequest,
    current_admin: HospitalAdmin = Depends(get_current_active_admin),
) -> SessionStartResponse:
    try:
        with db_session_scope() as db:
            service = ReportService(db)
            session_record = service.start_draft_session(
                payload.session_id,
                payload.patient,
                admin_id=current_admin.id,
                started_at=payload.started_at,
            )
            return SessionStartResponse(
                session_id=str(session_record["session_id"]),
                patient_id=str(session_record["patient_id"]),
                status="started",
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/session/end", response_model=SessionEndResponse)
def end_session(
    payload: SessionEndRequest,
    current_admin: HospitalAdmin = Depends(get_current_active_admin),
) -> SessionEndResponse:
    try:
        with db_session_scope() as db:
            service = ReportService(db)
            session_record = service.end_session(
                payload.session_id,
                admin_id=current_admin.id,
                ended_at=payload.ended_at,
                completion_status=payload.completion_status,
            )
            return SessionEndResponse(
                session_id=str(session_record["session_id"]),
                status="ended",
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/reports/save-final", response_model=ReportSaveResponse)
def save_final_report(
    payload: FinalReportSaveRequest,
    current_admin: HospitalAdmin = Depends(get_current_active_admin),
) -> ReportSaveResponse:
    try:
        with db_session_scope() as db:
            service = ReportService(db)
            report_id = service.save_patient_report(payload, admin_id=current_admin.id)
            return ReportSaveResponse(
                report_id=report_id,
                session_id=payload.session_id,
                status="saved",
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/report/save", response_model=ReportSaveResponse)
def save_patient_report(
    payload: FinalReportSaveRequest,
    current_admin: HospitalAdmin = Depends(get_current_active_admin),
) -> ReportSaveResponse:
    try:
        with db_session_scope() as db:
            service = ReportService(db)
            report_id = service.save_patient_report(payload, admin_id=current_admin.id)
            return ReportSaveResponse(
                report_id=report_id,
                session_id=payload.session_id,
                status="saved",
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/admin/reports", response_model=list[AdminReportListItem])
def get_admin_reports(
    current_admin: HospitalAdmin = Depends(get_current_active_admin),
) -> list[AdminReportListItem]:
    try:
        with db_session_scope() as db:
            service = ReportService(db)
            return service.fetch_all_reports_for_admin(current_admin.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.delete("/admin/patients/{patient_code}")
def delete_admin_patient(
    patient_code: str,
    request: Request,
    current_admin: HospitalAdmin = Depends(get_current_active_admin),
) -> dict[str, str | int]:
    resources = getattr(request.app.state, "checkpointer_resources", None)
    settings = getattr(request.app.state, "settings", None)
    if (
        getattr(resources, "backend_name", None) == "postgres"
        and not _same_postgres_database(
            getattr(settings, "database_url", ""),
            getattr(settings, "postgres_url", ""),
        )
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "Patient deletion is disabled because chat history is stored in a separate "
                "database. Configure the patient database and LangGraph checkpointer to use "
                "the same PostgreSQL database, then retry."
            ),
        )

    try:
        with db_session_scope() as db:
            deleted = ReportService(db).delete_patient_data(
                patient_code,
                admin_id=current_admin.id,
            )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Patient record was not found for this account.") from exc
    except SQLAlchemyError as exc:
        logger.exception("Patient deletion transaction failed; database changes were rolled back.")
        raise HTTPException(
            status_code=409,
            detail="Patient data could not be fully deleted. No database changes were committed.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Patient deletion is temporarily unavailable.") from exc

    audio_service = getattr(request.app.state, "audio_service", None)
    if audio_service is not None:
        for session_id in deleted["session_ids"]:
            try:
                audio_service.clear_session_cache(session_id)
            except OSError:
                # The database/checkpoint deletion is committed; stale generated TTS is
                # noncanonical cache data and must not turn success into a false failure.
                logger.exception("Could not remove one generated session-audio cache directory.")

    if getattr(resources, "backend_name", None) == "memory":
        delete_thread = getattr(getattr(resources, "saver", None), "delete_thread", None)
        if callable(delete_thread):
            for session_id in deleted["session_ids"]:
                try:
                    delete_thread(session_id)
                except Exception:
                    logger.exception("Could not clear an in-memory LangGraph thread after deletion.")

    return {
        "status": "deleted",
        "patient_id": deleted["patient_code"],
        "deleted_reports": deleted["deleted_report_count"],
    }


@router.get("/admin/reports/{report_id}", response_model=AdminReportDetail)
def get_admin_report_detail(
    report_id: str,
    current_admin: HospitalAdmin = Depends(get_current_active_admin),
) -> AdminReportDetail:
    try:
        with db_session_scope() as db:
            service = ReportService(db)
            return service.fetch_single_report(report_id, current_admin.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/admin/reports/{report_id}/download")
def download_admin_report(
    report_id: str,
    current_admin: HospitalAdmin = Depends(get_current_active_admin),
) -> Response:
    try:
        from services.pdf_service import generate_report_pdf

        with db_session_scope() as db:
            service = ReportService(db)
            report = service.fetch_single_report(report_id, current_admin.id)
            pdf_bytes = generate_report_pdf(report, hospital_name=current_admin.hospital_name)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="patient-report-{report_id}.pdf"'
                },
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
