from __future__ import annotations

import io
import os
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from reportlab.graphics.shapes import Circle, Drawing, Line, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.security import check_password_hash, generate_password_hash

INSTANCE_DIR = BASE_DIR / "instance"
DATABASE_PATH = INSTANCE_DIR / "healthcare.db"

DOCTORS = [
    {
        "name": "Dr. Aarav Mehta",
        "specialization": "General Physician",
        "contact": "+91 98765 12001",
        "tags": ["fever", "normal", "mild", "general"],
    },
    {
        "name": "Dr. Nisha Kapoor",
        "specialization": "Cardiologist",
        "contact": "+91 98765 12002",
        "tags": ["tachycardia", "bradycardia", "heart", "critical"],
    },
    {
        "name": "Dr. Rohan Iyer",
        "specialization": "Emergency Medicine",
        "contact": "+91 98765 12003",
        "tags": ["critical", "hypothermia", "high-fever", "emergency"],
    },
    {
        "name": "Dr. Kavya Sharma",
        "specialization": "Ayurvedic Consultant",
        "contact": "+91 98765 12004",
        "tags": ["ayurvedic", "general", "recovery"],
    },
]


app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "college-exhibition-secret-key")
app.config["DATABASE"] = str(DATABASE_PATH)


def get_db() -> sqlite3.Connection:
    """Return one SQLite connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error: Exception | None) -> None:
    """Close the database when Flask finishes the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Create tables and sample records the first time the project runs."""
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    schema_path = BASE_DIR / "schema.sql"
    db.executescript(schema_path.read_text(encoding="utf-8"))
    seed_demo_data(db)
    db.commit()
    db.close()


def seed_demo_data(db: sqlite3.Connection) -> None:
    """Insert beginner-friendly demo accounts and health records."""
    existing_users = db.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    if existing_users == 0:
        db.execute(
            """
            INSERT INTO users (full_name, username, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Demo Doctor",
                "doctor_demo",
                generate_password_hash("doctor123"),
                "Doctor",
            ),
        )
        db.execute(
            """
            INSERT INTO users (full_name, username, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Demo Patient",
                "patient_demo",
                generate_password_hash("patient123"),
                "Patient",
            ),
        )

    existing_records = db.execute("SELECT COUNT(*) AS count FROM health_records").fetchone()["count"]
    if existing_records == 0:
        patient = db.execute(
            "SELECT id, full_name FROM users WHERE username = ?",
            ("patient_demo",),
        ).fetchone()
        sample_inputs = [
            ("Mild cold and cough", 98.4, 74, "Allopathy", "2026-04-14 09:30:00"),
            ("Body ache and tiredness", 99.2, 88, "Ayurvedic", "2026-04-15 10:10:00"),
            ("Fever with fast pulse", 101.4, 108, "Allopathy", "2026-04-16 18:20:00"),
        ]
        for symptoms, temperature, heart_rate, preference, created_at in sample_inputs:
            analysis = analyze_vitals(temperature, heart_rate)
            suggestions = generate_suggestions(preference, analysis["condition"])
            db.execute(
                """
                INSERT INTO health_records (
                    user_id, patient_name, age, gender, symptoms,
                    body_temperature, heart_rate, preference, created_at,
                    temp_category, heart_category, status, condition, explanation, suggestions
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient["id"],
                    patient["full_name"],
                    21,
                    "Female",
                    symptoms,
                    temperature,
                    heart_rate,
                    preference,
                    created_at,
                    analysis["temperature_category"],
                    analysis["heart_rate_category"],
                    analysis["status"],
                    analysis["condition"],
                    analysis["explanation"],
                    suggestions,
                ),
            )


def login_required(view_function):
    """Protect dashboard routes from anonymous access."""

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)

    return wrapped_view


def analyze_vitals(temperature: float, heart_rate: int) -> dict[str, str]:
    """Categorize vitals and produce a simple rule-based health explanation."""
    if temperature < 97:
        temperature_category = "Low"
    elif temperature <= 99.5:
        temperature_category = "Normal"
    elif temperature <= 102:
        temperature_category = "High"
    else:
        temperature_category = "Very High"

    if heart_rate < 60:
        heart_rate_category = "Low"
    elif heart_rate <= 100:
        heart_rate_category = "Normal"
    elif heart_rate <= 120:
        heart_rate_category = "High"
    else:
        heart_rate_category = "Very High"

    abnormal_parts = []
    if temperature_category == "Low":
        abnormal_parts.append("body temperature is below the normal range")
    elif temperature_category == "High":
        abnormal_parts.append("body temperature suggests fever")
    elif temperature_category == "Very High":
        abnormal_parts.append("body temperature is dangerously high")

    if heart_rate_category == "Low":
        abnormal_parts.append("heart rate is lower than expected")
    elif heart_rate_category == "High":
        abnormal_parts.append("heart rate is above the normal range")
    elif heart_rate_category == "Very High":
        abnormal_parts.append("heart rate is dangerously high")

    if temperature_category in {"Very High"} or heart_rate_category in {"Very High"}:
        status = "Critical"
        condition = "critical"
    elif temperature_category == "Low" and heart_rate_category == "Low":
        status = "Critical"
        condition = "hypothermia"
    elif temperature_category == "High" and heart_rate_category in {"High", "Very High"}:
        status = "Critical"
        condition = "high-fever"
    elif temperature_category == "High":
        status = "Warning"
        condition = "fever"
    elif heart_rate_category == "High":
        status = "Warning"
        condition = "tachycardia"
    elif heart_rate_category == "Low":
        status = "Warning"
        condition = "bradycardia"
    elif temperature_category == "Low":
        status = "Warning"
        condition = "mild"
    else:
        status = "Normal"
        condition = "normal"

    if abnormal_parts:
        explanation = (
            f"Detected status: {status}. The analysis shows that "
            + " and ".join(abnormal_parts)
            + ". Please monitor the patient closely and consult a qualified doctor if symptoms continue."
        )
    else:
        explanation = (
            "Detected status: Normal. The entered body temperature and heart rate are both within the normal range."
        )

    return {
        "temperature_category": temperature_category,
        "heart_rate_category": heart_rate_category,
        "status": status,
        "condition": condition,
        "explanation": explanation,
    }


def generate_suggestions(preference: str, condition: str) -> str:
    """Return text suggestions based on the user's treatment preference."""
    if preference == "Ayurvedic":
        remedies = [
            "Drink warm water regularly to stay hydrated.",
            "Tulsi and ginger tea may help with mild cold-like symptoms.",
            "Take light homemade food and enough rest.",
            "Steam inhalation can help if there is congestion.",
            "Consult a qualified Ayurvedic practitioner before using herbal formulations regularly.",
        ]
    else:
        remedies = [
            "Take rest, drink fluids, and continue monitoring temperature and pulse.",
            "For mild fever or body ache, paracetamol may be commonly used, but only as advised by a doctor.",
            "Avoid self-medicating with antibiotics without medical guidance.",
            "If fever remains high or symptoms worsen, visit a hospital or clinic.",
        ]

    if condition in {"critical", "high-fever", "hypothermia"}:
        remedies.insert(0, "Seek urgent medical help immediately instead of relying only on home care.")
    elif condition in {"tachycardia", "bradycardia"}:
        remedies.insert(0, "Avoid heavy physical activity until a doctor reviews the condition.")

    remedies.append(
        "Disclaimer: This system is for educational purposes only and not a replacement for professional medical advice."
    )
    return " ".join(remedies)


def get_recommended_doctors(condition: str, preference: str) -> list[dict[str, str]]:
    """Filter the static doctor list according to the detected condition."""
    matched = []
    for doctor in DOCTORS:
        if condition in doctor["tags"]:
            matched.append(doctor)

    if preference == "Ayurvedic":
        matched.extend(doctor for doctor in DOCTORS if "ayurvedic" in doctor["tags"])

    if not matched:
        matched.extend(doctor for doctor in DOCTORS if "general" in doctor["tags"])

    unique = []
    seen_names = set()
    for doctor in matched:
        if doctor["name"] not in seen_names:
            unique.append(doctor)
            seen_names.add(doctor["name"])
    return unique


def current_user() -> sqlite3.Row | None:
    """Read the currently logged-in user from the database."""
    if session.get("user_id") is None:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()


def fetch_records_for_user(user: sqlite3.Row) -> list[sqlite3.Row]:
    """Patients see their own records while doctors see everything."""
    db = get_db()
    if user["role"] == "Doctor":
        query = """
            SELECT health_records.*, users.full_name AS entered_by_name
            FROM health_records
            JOIN users ON users.id = health_records.user_id
            ORDER BY datetime(health_records.created_at) ASC, health_records.id ASC
        """
        return db.execute(query).fetchall()

    query = """
        SELECT health_records.*, users.full_name AS entered_by_name
        FROM health_records
        JOIN users ON users.id = health_records.user_id
        WHERE user_id = ?
        ORDER BY datetime(health_records.created_at) ASC, health_records.id ASC
    """
    return db.execute(query, (user["id"],)).fetchall()


def metric_cards(records: list[sqlite3.Row]) -> dict[str, str]:
    """Create dashboard card values from the newest record."""
    latest = records[-1] if records else None
    return {
        "records_count": str(len(records)),
        "latest_temperature": f"{latest['body_temperature']:.1f} °F" if latest else "--",
        "latest_heart_rate": f"{latest['heart_rate']} bpm" if latest else "--",
        "latest_status": latest["status"] if latest else "No Data",
    }


def build_chart_payload(records: list[sqlite3.Row]) -> dict[str, list]:
    """Convert database rows to chart-friendly arrays."""
    labels = [row["created_at"] for row in records]
    temperatures = [row["body_temperature"] for row in records]
    heart_rates = [row["heart_rate"] for row in records]
    return {
        "labels": labels,
        "temperatures": temperatures,
        "heart_rates": heart_rates,
    }


def fetch_report_history(record: sqlite3.Row) -> list[sqlite3.Row]:
    """Load records for the same patient to include trend graphs in the PDF."""
    db = get_db()
    return db.execute(
        """
        SELECT *
        FROM health_records
        WHERE patient_name = ?
        ORDER BY datetime(created_at) ASC, id ASC
        """,
        (record["patient_name"],),
    ).fetchall()


def create_line_chart_drawing(title: str, labels: list[str], values: list[float], color: colors.Color) -> Drawing:
    """Draw a simple line chart directly in the PDF so no internet is required."""
    width = 460
    height = 190
    left = 45
    bottom = 35
    plot_width = 380
    plot_height = 105
    drawing = Drawing(width, height)
    drawing.add(String(8, 170, title, fontSize=12, fillColor=colors.HexColor("#0f172a")))
    drawing.add(Line(left, bottom, left, bottom + plot_height))
    drawing.add(Line(left, bottom, left + plot_width, bottom))
    drawing.add(String(left - 10, bottom + plot_height + 5, "Value", fontSize=8))
    drawing.add(String(left + plot_width - 10, 15, "Time", fontSize=8))

    if not values:
        drawing.add(String(120, 95, "No data available for this chart.", fontSize=10))
        return drawing

    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        min_value -= 1
        max_value += 1

    for step in range(5):
        y = bottom + (plot_height / 4) * step
        value = min_value + ((max_value - min_value) / 4) * step
        drawing.add(Line(left - 3, y, left + plot_width, y, strokeColor=colors.HexColor("#dbe4f0")))
        drawing.add(String(5, y - 3, f"{value:.1f}", fontSize=7, fillColor=colors.HexColor("#475569")))

    total_points = len(values)
    previous_point = None
    for index, value in enumerate(values):
        x = left if total_points == 1 else left + (plot_width / (total_points - 1)) * index
        y = bottom + ((value - min_value) / (max_value - min_value)) * plot_height
        drawing.add(Circle(x, y, 3, fillColor=color, strokeColor=color))
        if previous_point:
            drawing.add(Line(previous_point[0], previous_point[1], x, y, strokeColor=color, strokeWidth=2))
        label_text = labels[index].split(" ")[0] if labels[index] else f"P{index + 1}"
        drawing.add(String(x - 14, 20, label_text, fontSize=7, fillColor=colors.HexColor("#475569")))
        previous_point = (x, y)

    return drawing


def build_pdf(record: sqlite3.Row, history: list[sqlite3.Row]) -> bytes:
    """Generate the downloadable PDF report."""
    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=32, leftMargin=32, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
            alignment=TA_LEFT,
        )
    )

    content = []
    content.append(Paragraph("Smart Healthcare System Report", styles["Title"]))
    content.append(Spacer(1, 8))
    content.append(
        Paragraph(
            "This system is for educational purposes only and not a replacement for professional medical advice.",
            styles["BodySmall"],
        )
    )
    content.append(Spacer(1, 16))

    details = [
        ["Patient Name", record["patient_name"]],
        ["Age", str(record["age"])],
        ["Gender", record["gender"]],
        ["Symptoms", record["symptoms"]],
        ["Body Temperature", f"{record['body_temperature']:.1f} °F"],
        ["Heart Rate", f"{record['heart_rate']} bpm"],
        ["Date / Time", record["created_at"]],
        ["Preference", record["preference"]],
        ["Status", record["status"]],
        ["Condition", record["condition"].replace("-", " ").title()],
    ]

    details_table = Table(details, colWidths=[130, 360])
    details_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    content.append(details_table)
    content.append(Spacer(1, 16))

    content.append(Paragraph("Analysis", styles["Heading2"]))
    content.append(Paragraph(record["explanation"], styles["BodySmall"]))
    content.append(Spacer(1, 12))
    content.append(Paragraph("Suggestions", styles["Heading2"]))
    content.append(Paragraph(record["suggestions"], styles["BodySmall"]))
    content.append(Spacer(1, 16))

    history_labels = [row["created_at"] for row in history]
    history_temperatures = [row["body_temperature"] for row in history]
    history_heart_rates = [row["heart_rate"] for row in history]

    content.append(Paragraph("Temperature vs Time", styles["Heading2"]))
    content.append(create_line_chart_drawing("Temperature Trend", history_labels, history_temperatures, colors.red))
    content.append(Spacer(1, 10))
    content.append(Paragraph("Heart Rate vs Time", styles["Heading2"]))
    content.append(create_line_chart_drawing("Heart Rate Trend", history_labels, history_heart_rates, colors.blue))

    document.build(content)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


init_db()


@app.route("/")
def index():
    """Send logged-in users to the dashboard and others to login."""
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Register a new doctor or patient account."""
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "Patient")

        if not full_name or not username or not password or role not in {"Doctor", "Patient"}:
            flash("Please fill all fields correctly.", "danger")
            return render_template("signup.html")

        db = get_db()
        exists = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            flash("Username already exists. Please choose another one.", "danger")
            return render_template("signup.html")

        db.execute(
            """
            INSERT INTO users (full_name, username, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (full_name, username, generate_password_hash(password), role),
        )
        db.commit()
        flash("Signup successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a saved user and start a session."""
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["full_name"] = user["full_name"]
        flash(f"Welcome back, {user['full_name']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clear the session and return to the login page."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    """Show the main healthcare dashboard."""
    user = current_user()
    records = fetch_records_for_user(user)
    cards = metric_cards(records)
    latest_record = records[-1] if records else None

    recommended_doctors = []
    if latest_record:
        recommended_doctors = get_recommended_doctors(latest_record["condition"], latest_record["preference"])

    return render_template(
        "dashboard.html",
        user=user,
        records=list(reversed(records)),
        cards=cards,
        latest_record=latest_record,
        doctors=recommended_doctors,
        chart_payload=build_chart_payload(records),
    )


@app.route("/add-record", methods=["POST"])
@login_required
def add_record():
    """Save a health record locally in SQLite."""
    user = current_user()
    patient_name = request.form.get("patient_name", "").strip() or user["full_name"]
    age = request.form.get("age", "").strip()
    gender = request.form.get("gender", "").strip()
    symptoms = request.form.get("symptoms", "").strip()
    preference = request.form.get("preference", "Allopathy").strip()

    try:
        body_temperature = float(request.form.get("body_temperature", "0"))
        heart_rate = int(request.form.get("heart_rate", "0"))
        age_number = int(age)
    except ValueError:
        flash("Age, body temperature, and heart rate must be valid numbers.", "danger")
        return redirect(url_for("dashboard"))

    if preference not in {"Allopathy", "Ayurvedic"}:
        flash("Please select a valid treatment preference.", "danger")
        return redirect(url_for("dashboard"))

    analysis = analyze_vitals(body_temperature, heart_rate)
    suggestions = generate_suggestions(preference, analysis["condition"])
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    db.execute(
        """
        INSERT INTO health_records (
            user_id, patient_name, age, gender, symptoms,
            body_temperature, heart_rate, preference, created_at,
            temp_category, heart_category, status, condition, explanation, suggestions
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user["id"],
            patient_name,
            age_number,
            gender,
            symptoms,
            body_temperature,
            heart_rate,
            preference,
            created_at,
            analysis["temperature_category"],
            analysis["heart_rate_category"],
            analysis["status"],
            analysis["condition"],
            analysis["explanation"],
            suggestions,
        ),
    )
    db.commit()

    if analysis["status"] == "Critical":
        flash("Emergency! Seek medical help. SMS alert sent to emergency contact.", "danger")
    elif analysis["status"] == "Warning":
        flash("Health record saved. Warning signs detected, so monitoring is recommended.", "warning")
    else:
        flash("Health record saved successfully.", "success")

    return redirect(url_for("dashboard"))


@app.route("/download-report/<int:record_id>")
@login_required
def download_report(record_id: int):
    """Download a PDF report for one selected record."""
    user = current_user()
    db = get_db()
    record = db.execute("SELECT * FROM health_records WHERE id = ?", (record_id,)).fetchone()

    if record is None:
        flash("Record not found.", "danger")
        return redirect(url_for("dashboard"))

    if user["role"] != "Doctor" and record["user_id"] != user["id"]:
        flash("You do not have permission to access this report.", "danger")
        return redirect(url_for("dashboard"))

    history = fetch_report_history(record)
    pdf_bytes = build_pdf(record, history)
    filename = f"health_report_{record['patient_name'].replace(' ', '_').lower()}_{record['id']}.pdf"

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
