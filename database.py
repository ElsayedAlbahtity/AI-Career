import sqlite3
import bcrypt
import json
from datetime import datetime


DB_NAME = "career.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    # =====================================================
    # USERS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # =====================================================
    # PROFILES TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            major TEXT,
            skills TEXT,
            target_role TEXT,
            job_description TEXT,
            cv_summary TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # =====================================================
    # INTERVIEWS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            interview_type TEXT DEFAULT 'AI Mock Interview',
            focus TEXT,
            questions TEXT NOT NULL,
            answers TEXT,
            evaluation TEXT,
            overall_score REAL,
            technical_score REAL,
            communication_score REAL,
            problem_solving_score REAL,
            answer_quality_score REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# USER FUNCTIONS
# =========================================================

def create_user(name, email, password):

    conn = get_connection()
    cursor = conn.cursor()

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    try:

        cursor.execute("""
            INSERT INTO users (
                name,
                email,
                password_hash,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            password_hash,
            datetime.now().isoformat()
        ))

        user_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return user_id

    except sqlite3.IntegrityError:

        conn.close()

        return None


def authenticate_user(email, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            email,
            password_hash
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    conn.close()

    if user is None:
        return None

    try:

        valid_password = bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8")
        )

    except Exception:

        return None

    if valid_password:

        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }

    return None


# =========================================================
# PROFILE FUNCTIONS
# =========================================================

def save_profile(
    user_id,
    major,
    skills,
    target_role,
    job_description,
    cv_summary
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO profiles (
            user_id,
            major,
            skills,
            target_role,
            job_description,
            cv_summary
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        major,
        skills,
        target_role,
        job_description,
        cv_summary
    ))

    conn.commit()
    conn.close()


def get_profile(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            major,
            skills,
            target_role,
            job_description,
            cv_summary
        FROM profiles
        WHERE user_id = ?
    """, (user_id,))

    profile = cursor.fetchone()

    conn.close()

    if profile is None:
        return None

    return {
        "major": profile["major"],
        "skills": profile["skills"],
        "target_role": profile["target_role"],
        "job_description": profile["job_description"],
        "cv_summary": profile["cv_summary"]
    }


# =========================================================
# INTERVIEW FUNCTIONS
# =========================================================

def create_interview(
    user_id,
    questions,
    focus="General",
    interview_type="AI Mock Interview"
):

    conn = get_connection()
    cursor = conn.cursor()

    questions_json = json.dumps(
        questions,
        ensure_ascii=False
    )

    cursor.execute("""
        INSERT INTO interviews (
            user_id,
            interview_type,
            focus,
            questions,
            answers,
            evaluation,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        interview_type,
        focus,
        questions_json,
        json.dumps({}, ensure_ascii=False),
        None,
        datetime.now().isoformat()
    ))

    interview_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return interview_id


def save_interview_answers(
    interview_id,
    answers
):

    conn = get_connection()
    cursor = conn.cursor()

    answers_json = json.dumps(
        answers,
        ensure_ascii=False
    )

    cursor.execute("""
        UPDATE interviews
        SET answers = ?
        WHERE id = ?
    """, (
        answers_json,
        interview_id
    ))

    conn.commit()
    conn.close()


def save_interview_evaluation(
    interview_id,
    evaluation
):

    conn = get_connection()
    cursor = conn.cursor()

    evaluation_json = json.dumps(
        evaluation,
        ensure_ascii=False
    )

    overall_score = evaluation.get(
        "overall_score",
        0
    )

    technical_score = evaluation.get(
        "technical_score",
        0
    )

    communication_score = evaluation.get(
        "communication_score",
        0
    )

    problem_solving_score = evaluation.get(
        "problem_solving_score",
        0
    )

    answer_quality_score = evaluation.get(
        "answer_quality_score",
        0
    )

    cursor.execute("""
        UPDATE interviews
        SET
            evaluation = ?,
            overall_score = ?,
            technical_score = ?,
            communication_score = ?,
            problem_solving_score = ?,
            answer_quality_score = ?
        WHERE id = ?
    """, (
        evaluation_json,
        overall_score,
        technical_score,
        communication_score,
        problem_solving_score,
        answer_quality_score,
        interview_id
    ))

    conn.commit()
    conn.close()


# =========================================================
# GET INTERVIEWS
# =========================================================

def get_user_interviews(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            interview_type,
            focus,
            overall_score,
            technical_score,
            communication_score,
            problem_solving_score,
            answer_quality_score,
            created_at
        FROM interviews
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    interviews = cursor.fetchall()

    conn.close()

    return [
        dict(row)
        for row in interviews
    ]


def get_interview(
    interview_id,
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM interviews
        WHERE id = ?
        AND user_id = ?
    """, (
        interview_id,
        user_id
    ))

    interview = cursor.fetchone()

    conn.close()

    if interview is None:
        return None

    result = dict(interview)

    # Questions
    try:

        result["questions"] = json.loads(
            result["questions"]
        )

    except Exception:

        result["questions"] = []

    # Answers
    try:

        result["answers"] = (
            json.loads(result["answers"])
            if result["answers"]
            else {}
        )

    except Exception:

        result["answers"] = {}

    # Evaluation
    try:

        result["evaluation"] = (
            json.loads(result["evaluation"])
            if result["evaluation"]
            else None
        )

    except Exception:

        result["evaluation"] = None

    return result


# =========================================================
# DELETE INTERVIEW
# =========================================================

def delete_interview(
    interview_id,
    user_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM interviews
        WHERE id = ?
        AND user_id = ?
    """, (
        interview_id,
        user_id
    ))

    conn.commit()

    deleted = cursor.rowcount > 0

    conn.close()

    return deleted


# =========================================================
# STATISTICS
# =========================================================

def get_interview_count(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM interviews
        WHERE user_id = ?
    """, (user_id,))

    count = cursor.fetchone()[0]

    conn.close()

    return count


def get_average_score(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT AVG(overall_score)
        FROM interviews
        WHERE user_id = ?
        AND overall_score IS NOT NULL
    """, (user_id,))

    result = cursor.fetchone()[0]

    conn.close()

    if result is None:
        return 0

    return result