from __future__ import annotations

from io import BytesIO
from datetime import datetime
from textwrap import wrap

from schemas.report_schemas import AdminReportDetail


def _load_reportlab():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PDF download requires the 'reportlab' package. Install backend dependencies first."
        ) from exc

    return A4, canvas


def _draw_wrapped_text(pdf, text: str, x: int, y: int, width: int = 95, line_height: int = 14) -> int:
    lines = wrap(text or "", width=width) or [""]
    for line in lines:
        pdf.drawString(x, y, line)
        y -= line_height
    return y


def generate_report_pdf(report: AdminReportDetail, *, hospital_name: str | None = None) -> bytes:
    A4, canvas = _load_reportlab()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 48

    pdf.setTitle(f"CLD Sarcopenia Patient Report {report.report_id}")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, hospital_name or "Hospital Patient Report")
    y -= 24

    pdf.setFont("Helvetica", 10)
    y = _draw_wrapped_text(
        pdf,
        f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        40,
        y,
    )
    y -= 8

    sections = [
        ("Patient Info", [
            f"Patient ID: {report.patient.get('patient_id', '-')}",
            f"Age: {report.patient.get('age', '-')}",
            f"Gender: {report.patient.get('gender', '-')}",
            f"Educational qualification: {report.patient.get('educational_qualification', '-')}",
            f"Occupation: {report.patient.get('occupation', '-')}",
            f"Diet type: {report.patient.get('diet_type', '-')}",
            f"Alcohol habit: {report.patient.get('alcohol_habit', '-')}",
            f"Smoking habit: {report.patient.get('smoking_habit', '-')}",
            f"Language: {report.patient.get('language', '-')}",
            f"CLD with Sarcopenia: {report.patient.get('cld_status', '-')}",
            f"Exercise habit: {report.patient.get('exercise_habit', '-')}",
            f"Symptoms: {', '.join(report.patient.get('symptoms', [])) or '-'}",
            f"Session ID: {report.session.get('session_id', '-')}",
            f"Date: {report.report.get('report_generated_at') or report.session.get('session_end_time') or report.session.get('session_start_time') or '-'}",
        ]),
        ("Quiz Summary", [
            f"Pre-test score: {report.report.get('pre_test_score', '-')}",
            f"Post-test score: {report.report.get('post_test_score', '-')}",
            f"Improvement: {report.report.get('improvement', '-')}",
            f"Weak topics: {', '.join(report.report.get('weak_topics', [])) or '-'}",
            f"Completion status: {report.report.get('completion_status', '-')}",
        ]),
        ("Summary", [
            report.report.get("learning_summary", "") or "-",
            f"Chat summary: {report.report.get('short_chat_summary', '') or '-'}",
        ]),
    ]

    for title, lines in sections:
        if y < 110:
            pdf.showPage()
            y = height - 48
            pdf.setFont("Helvetica", 10)

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, title)
        y -= 18
        pdf.setFont("Helvetica", 10)
        for line in lines:
            y = _draw_wrapped_text(pdf, str(line), 48, y)
            y -= 6

    pdf.save()
    return buffer.getvalue()
