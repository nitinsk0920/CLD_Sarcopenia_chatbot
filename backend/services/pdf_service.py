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


_READABLE_VALUES = {
    "en": "English", "hi": "Hindi", "kn": "Kannada", "mr": "Marathi", "notSure": "Not sure",
    "cld": "Chronic Liver Disease", "sarcopenia": "Sarcopenia", "diet": "Diet and nutrition", "exercise": "Exercise and movement", "safety": "Safety",
    "beginner": "Beginner", "developing": "Developing", "good": "Good", "excellent": "Excellent",
    "age_18_30": "18-30 years", "age_31_45": "31-45 years", "age_46_60": "46-60 years", "age_61_plus": "61 years and above",
    "married": "Married", "unmarried": "Unmarried", "widowed": "Widowed", "divorced_separated": "Divorced / Separated",
    "nuclear": "Nuclear", "joint": "Joint", "extended": "Extended", "rural": "Rural", "urban": "Urban",
    "hindu": "Hindu", "muslim": "Muslim", "christian": "Christian", "religion_other": "Other",
    "socioeconomic_lower": "Lower", "socioeconomic_middle": "Middle", "socioeconomic_upper": "Upper",
    "vegetarian": "Vegetarian", "mixed": "Mixed (vegetarian and non-vegetarian)", "nonVegetarian": "Non-vegetarian (legacy response)",
    "alcohol": "Alcohol consumption", "smoking": "Smoking", "tobacco": "Tobacco chewing", "tobacco_chewing": "Tobacco chewing", "none": "None",
    "less_than_1_year": "Less than 1 year", "one_to_five_years": "1-5 years", "six_to_ten_years": "6-10 years", "more_than_10_years": "More than 10 years",
    "alcohol_related": "Alcohol-related liver disease", "viral_hepatitis": "Viral hepatitis (Hepatitis B/C)", "fatty_liver": "Fatty liver disease (MASLD/MASH)", "etiology_other": "Other documented cause",
    "compensated_cirrhosis": "Compensated cirrhosis", "decompensated_cirrhosis": "Decompensated cirrhosis", "stage_other": "Other documented CLD stage", "not_documented": "Not documented / unknown",
    "diabetes": "Diabetes mellitus", "hypertension": "Hypertension", "comorbidity_other": "Other comorbidity", "no_known_comorbidities": "No known comorbidities",
    "less_than_6_months": "Less than 6 months", "six_to_twelve_months": "6-12 months", "more_than_1_year": "More than 1 year",
    "medical_management_only": "Medical management only", "medical_nutrition": "Medical management with nutritional supplementation", "treatment_other": "Other treatment", "complications_management": "Management of CLD complications",
    "never": "Never", "once": "Once", "twice": "Twice", "three_or_more": "Three or more times", "yes": "Yes", "no": "No", "not_sure": "Not sure",
    "education_none": "No previous education", "education_cld": "Education about CLD only", "education_sarcopenia": "Education about sarcopenia only", "education_both": "Education about both CLD and sarcopenia",
    "male": "Male", "female": "Female", "other": "Other", "employed": "Employed", "unemployed": "Unemployed", "homemaker": "Homemaker", "retired": "Retired",
    "noFormalEducation": "No formal education", "primaryEducation": "Primary education", "secondaryEducation": "Secondary education", "higherSecondary": "Higher secondary", "graduateAndAbove": "Graduate and above",
}


def _display(value) -> str:
    if value in (None, "", []):
        return "Not recorded"
    if isinstance(value, (list, tuple)):
        return ", ".join(_display(item) for item in value) if value else "Not recorded"
    text = str(value)
    return _READABLE_VALUES.get(text, text.replace("_", " "))


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

    patient = report.patient
    pre = report.pre_test
    post = report.post_test
    sections = [
        ("Patient Info", [
            f"Patient ID: {_display(patient.get('patient_id'))}",
            f"Legacy exact age: {_display(patient.get('age'))}",
            f"Language: {_display(patient.get('language'))}",
            f"CLD with Sarcopenia: {_display(patient.get('cld_status'))}",
            f"Exercise habit: {_display(patient.get('exercise_habit'))}",
            f"Symptoms: {_display(patient.get('symptoms'))}",
            f"Session ID: {_display(report.session.get('session_id'))}",
            f"Date: {_display(report.report.get('report_generated_at') or report.session.get('session_end_time') or report.session.get('session_start_time'))}",
        ]),
        ("Socio-Demographic Information", [
            f"Age group: {_display(patient.get('ageGroup'))}",
            f"Gender: {_display(patient.get('gender'))}",
            f"Marital status: {_display(patient.get('maritalStatus'))}",
            f"Educational status: {_display(patient.get('educational_qualification'))}",
            f"Occupation: {_display(patient.get('occupation'))}",
            f"Type of family: {_display(patient.get('familyType'))}",
            f"Place of residence: {_display(patient.get('residence'))}",
            f"Religion: {_display(patient.get('religion'))}",
            f"Dietary pattern: {_display(patient.get('diet_type'))}",
            f"Habits: {_display(patient.get('habits'))}",
            f"Socioeconomic status: {_display(patient.get('socioeconomicStatus'))}",
        ]),
        ("Clinical Information", [
            f"CLD duration: {_display(patient.get('cldDuration'))}",
            f"CLD etiology: {_display(patient.get('cldEtiology'))}{' - ' + str(patient.get('cldEtiologyOther')) if patient.get('cldEtiologyOther') else ''}",
            f"CLD stage: {_display(patient.get('cldStage'))}{' - ' + str(patient.get('cldStageOther')) if patient.get('cldStageOther') else ''}",
            f"Comorbidities: {_display(patient.get('comorbidities'))}{' - ' + str(patient.get('comorbiditiesOther')) if patient.get('comorbiditiesOther') else ''}",
            f"Sarcopenia duration: {_display(patient.get('sarcopeniaDuration'))}",
            f"Current CLD treatment: {_display(patient.get('cldTreatment'))}{' - ' + str(patient.get('cldTreatmentOther')) if patient.get('cldTreatmentOther') else ''}",
            f"Hospitalizations due to CLD: {_display(patient.get('hospitalizationHistory'))}",
            f"Nutritional counselling: {_display(patient.get('nutritionalCounselling'))}",
            f"Previous health education: {_display(patient.get('previousHealthEducation'))}",
        ]),
        ("Pre-Test Results", [
            f"Score: {pre.score if pre else 'Not recorded'} / {pre.total_questions if pre else 'Not recorded'}",
            f"Performance level: {_display(pre.score_level if pre else None)}",
            f"Weak topics: {_display(pre.weak_topics if pre else None)}",
        ]),
        ("Post-Test Results", [
            f"Score: {post.score if post else 'Not recorded'} / {post.total_questions if post else 'Not recorded'}",
            f"Performance level: {_display(post.score_level if post else None)}",
        ]),
        ("Educational Improvement", [
            f"Pre-test versus post-test: {report.report.get('pre_test_score', 'Not recorded')} -> {report.report.get('post_test_score', 'Not recorded')}",
            f"Score improvement: {_display(report.report.get('improvement'))}",
            f"Weak topics requiring further education: {_display(report.report.get('weak_topics'))}",
        ]),
        ("Programme Completion", [
            f"Completion status: {_display(report.report.get('completion_status'))}",
            f"Session started: {_display(report.session.get('session_start_time'))}",
            f"Session ended: {_display(report.session.get('session_end_time'))}",
        ]),
        ("Learning Summary", [
            report.report.get("learning_summary", "") or "-",
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
            wrapped = wrap(str(line) or "", width=95) or [""]
            for wrapped_line in wrapped:
                if y < 48:
                    pdf.showPage()
                    y = height - 48
                    pdf.setFont("Helvetica", 10)
                pdf.drawString(48, y, wrapped_line)
                y -= 14
            y -= 6

    pdf.save()
    return buffer.getvalue()
