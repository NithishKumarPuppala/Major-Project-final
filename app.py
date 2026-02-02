import os
import uuid
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, send_file, flash

from utils.db import init_db, save_analysis
from utils.data_loader import load_roles, load_skills, load_job_descriptions
from utils.resume_parser import is_allowed_file, extract_text
from utils.nlp_extractor import build_summary
from utils.ml_matcher import tfidf_similarity, match_skills, skill_match_score
from utils.recommendation_engine import load_courses, recommend_courses, recommend_career_path


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "datasets")
DB_DIR = os.path.join(BASE_DIR, "database")
UPLOAD_DIR = os.path.join(DB_DIR, "uploads")
REPORT_DIR = os.path.join(DB_DIR, "reports")
DB_PATH = os.path.join(DB_DIR, "resume_analysis.db")


app = Flask(__name__)
app.config["SECRET_KEY"] = "resume-analyzer-local"
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR


def setup_app():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    init_db(DB_PATH)


setup_app()

ROLES = load_roles(os.path.join(DATA_DIR, "job_roles.json"))
SKILL_LIST = load_skills(os.path.join(DATA_DIR, "skills.json"))
JOB_DESCRIPTIONS = load_job_descriptions(os.path.join(DATA_DIR, "job_descriptions.csv"))
COURSES = load_courses(os.path.join(DATA_DIR, "courses.csv"))


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", roles=ROLES, job_descriptions=JOB_DESCRIPTIONS)


@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume_file" not in request.files:
        flash("Please upload a resume file.")
        return redirect(url_for("index"))

    resume_file = request.files["resume_file"]
    role_key = request.form.get("role_key")
    job_description_text = request.form.get("job_description", "").strip()

    if resume_file.filename == "":
        flash("No file selected.")
        return redirect(url_for("index"))

    if not is_allowed_file(resume_file.filename):
        flash("Only PDF or DOCX files are supported.")
        return redirect(url_for("index"))

    role = next((r for r in ROLES if r["key"] == role_key), None)
    if not role:
        flash("Please select a job role.")
        return redirect(url_for("index"))

    file_id = uuid.uuid4().hex
    _, ext = os.path.splitext(resume_file.filename)
    safe_name = f"{file_id}{ext.lower()}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
    resume_file.save(save_path)

    resume_text = extract_text(save_path)
    summary = build_summary(resume_text, set(SKILL_LIST))

    required_skills = role.get("required_skills", [])
    preferred_skills = role.get("preferred_skills", [])

    matched_skills, missing_skills = match_skills(
        summary["skills"], required_skills, preferred_skills
    )
    skill_score = skill_match_score(summary["skills"], required_skills, preferred_skills)

    if not job_description_text:
        job_description_text = JOB_DESCRIPTIONS.get(role_key, "")
    similarity_score = tfidf_similarity(resume_text, job_description_text)

    resume_score = round(0.6 * skill_score + 0.4 * similarity_score, 2)

    course_recos = recommend_courses(missing_skills, COURSES, top_n=5)
    career_message = recommend_career_path(role, missing_skills)

    report_text = _build_report(
        role=role,
        summary=summary,
        resume_score=resume_score,
        skill_score=skill_score,
        similarity_score=similarity_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        course_recos=course_recos,
        career_message=career_message,
    )
    report_name = f"report_{file_id}.txt"
    report_path = os.path.join(REPORT_DIR, report_name)
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write(report_text)

    save_analysis(
        DB_PATH,
        safe_name,
        role["title"],
        resume_score,
        skill_score,
        similarity_score,
        matched_skills,
        missing_skills,
    )

    return render_template(
        "result.html",
        role=role,
        summary=summary,
        resume_score=resume_score,
        skill_score=skill_score,
        similarity_score=similarity_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        course_recos=course_recos,
        career_message=career_message,
        report_name=report_name,
    )


@app.route("/download/<report_name>")
def download_report(report_name):
    report_path = os.path.join(REPORT_DIR, report_name)
    if not os.path.exists(report_path):
        flash("Report not found.")
        return redirect(url_for("index"))
    return send_file(report_path, as_attachment=True)


def _build_report(
    role,
    summary,
    resume_score,
    skill_score,
    similarity_score,
    matched_skills,
    missing_skills,
    course_recos,
    career_message,
):
    lines = [
        "Intelligent Resume Analysis Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"Target Role: {role['title']}",
        f"Resume Score: {resume_score}%",
        f"Skill Match: {skill_score}%",
        f"Job Description Similarity: {similarity_score}%",
        "",
        "Matched Skills:",
        ", ".join(matched_skills) if matched_skills else "None",
        "",
        "Missing Skills:",
        ", ".join(missing_skills) if missing_skills else "None",
        "",
        "Education:",
        " | ".join(summary["education"]) if summary["education"] else "Not detected",
        "",
        "Experience:",
        " | ".join(summary["experience"]) if summary["experience"] else "Not detected",
        "",
        "Projects:",
        " | ".join(summary["projects"]) if summary["projects"] else "Not detected",
        "",
        "Recommended Courses:",
    ]

    for course in course_recos:
        lines.append(
            f"- {course.get('course_title')} ({course.get('provider')}) - "
            f"Skill: {course.get('skill')}"
        )

    lines.extend(
        [
            "",
            "Recommended Certifications:",
            ", ".join(role.get("certifications", [])) or "Not available",
        ]
    )
    lines.extend(["", "Career Guidance:", career_message])
    return "\n".join(lines)


if __name__ == "__main__":
    app.run(debug=True)

