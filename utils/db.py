import json
import os
import sqlite3
from datetime import datetime


def init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            role TEXT,
            resume_score REAL,
            skill_match REAL,
            similarity_score REAL,
            matched_skills TEXT,
            missing_skills TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_analysis(
    db_path: str,
    filename: str,
    role: str,
    resume_score: float,
    skill_match: float,
    similarity_score: float,
    matched_skills,
    missing_skills,
):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO analyses
        (filename, role, resume_score, skill_match, similarity_score, matched_skills, missing_skills, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            filename,
            role,
            resume_score,
            skill_match,
            similarity_score,
            json.dumps(matched_skills),
            json.dumps(missing_skills),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()

