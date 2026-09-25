import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from database import (
    init_db,
    create_user,
    authenticate_user,
    save_profile,
    get_profile,
    create_interview,
    save_interview_answers,
    save_interview_evaluation,
    get_user_interviews,
    get_interview,
    delete_interview,
    get_interview_count,
    get_average_score,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Career",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DATABASE
# =========================================================

init_db()


# =========================================================
# ENVIRONMENT / OPENROUTER
# =========================================================

load_dotenv(".env", override=True)

api_key = os.getenv("OPENROUTER_API_KEY")

if api_key:
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
else:
    client = None

MODEL_NAME = "openai/gpt-4o-mini"


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "logged_in": False,
    "user": None,
    "auth_mode": False,
    "page": "Dashboard",
    "landing_section": "home",
    "current_interview_id": None,
    "questions": [],
    "answers": {},
    "evaluation": None,
    "interview_started": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       GLOBAL
       ===================================================== */

    .stApp {
        background:
            radial-gradient(
                circle at 10% 0%,
                rgba(80, 70, 180, 0.14),
                transparent 32%
            ),
            radial-gradient(
                circle at 90% 10%,
                rgba(20, 130, 180, 0.10),
                transparent 30%
            ),
            #07090d;
        color: #f5f7fa;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3, h4 {
        color: #f5f7fa !important;
        letter-spacing: -0.025em;
    }

    p, label, .stMarkdown {
        color: #aeb6c2;
    }

    /* =====================================================
       SIDEBAR
       ===================================================== */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #090b10 0%,
                #07090d 100%
            );
        border-right: 1px solid rgba(255,255,255,0.07);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
    }

    .sidebar-brand {
        font-size: 1.2rem;
        font-weight: 800;
        letter-spacing: 0.18em;
        color: #ffffff;
        margin-bottom: 1.8rem;
    }

    .sidebar-user {
        padding: 14px 15px;
        border: 1px solid rgba(255,255,255,0.07);
        background: rgba(255,255,255,0.025);
        border-radius: 14px;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .sidebar-user-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #697383;
    }

    .sidebar-user-name {
        font-size: 0.95rem;
        font-weight: 700;
        color: #f5f7fa;
        margin-top: 5px;
        word-break: break-word;
    }

    /* =====================================================
       BUTTONS
       ===================================================== */

    .stButton > button {
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.035);
        color: #f5f7fa;
        min-height: 42px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        border-color: rgba(255,255,255,0.25);
        background: rgba(255,255,255,0.07);
        color: #ffffff;
    }

    .stButton > button[kind="primary"] {
        background:
            linear-gradient(
                135deg,
                #6d5dfc 0%,
                #4d8dff 100%
            );
        border: none;
        color: #ffffff;
        box-shadow:
            0 8px 25px rgba(87, 91, 220, 0.24);
    }

    .stButton > button[kind="primary"]:hover {
        filter: brightness(1.08);
        box-shadow:
            0 12px 30px rgba(87, 91, 220, 0.32);
    }

    /* =====================================================
       INPUTS
       ===================================================== */

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"],
    .stNumberInput input {
        background: rgba(255,255,255,0.035) !important;
        color: #f5f7fa !important;
        border-color: rgba(255,255,255,0.10) !important;
        border-radius: 10px !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: rgba(109,93,252,0.65) !important;
        box-shadow: 0 0 0 1px rgba(109,93,252,0.2) !important;
    }

    /* =====================================================
       CONTAINERS
       ===================================================== */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.018);
        border-color: rgba(255,255,255,0.075);
        border-radius: 16px;
    }

    /* =====================================================
       METRICS
       ===================================================== */

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 15px;
    }

    div[data-testid="stMetricLabel"] {
        color: #7f8998 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #f5f7fa !important;
    }

    /* =====================================================
       TABS
       ===================================================== */

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.025);
        border-radius: 9px;
        padding: 9px 18px;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(109,93,252,0.16);
    }

    /* =====================================================
       PROGRESS
       ===================================================== */

    .stProgress > div > div {
        border-radius: 999px;
    }

    /* =====================================================
       LANDING
       ===================================================== */

    .landing-brand {
        font-size: 1.05rem;
        font-weight: 900;
        letter-spacing: 0.18em;
        color: #ffffff;
        padding-top: 7px;
    }

    .hero-label {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.18em;
        color: #8d83ff;
        margin-bottom: 15px;
    }

    .hero-title {
        font-size: clamp(3.2rem, 6vw, 6.4rem);
        line-height: 0.94;
        font-weight: 900;
        letter-spacing: -0.065em;
        color: #ffffff;
        max-width: 900px;
    }

    .hero-description {
        max-width: 720px;
        margin-top: 25px;
        font-size: 1.12rem;
        line-height: 1.75;
        color: #929baa;
    }

    .auth-title {
        font-size: 2.2rem;
        font-weight: 850;
        text-align: center;
        letter-spacing: -0.04em;
        color: #ffffff;
    }

    .auth-subtitle {
        text-align: center;
        color: #7e8795;
        margin-top: 8px;
        margin-bottom: 25px;
    }

    .section-label {
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #7468ff;
    }

    .big-number {
        font-size: 4rem;
        line-height: 1;
        font-weight: 900;
        letter-spacing: -0.06em;
        color: #ffffff;
    }

    .muted {
        color: #737d8d;
    }

    /* =====================================================
       CARDS
       ===================================================== */

    .stat-card {
        padding: 20px;
        border-radius: 16px;
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(255,255,255,0.07);
    }

    .stat-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.13em;
        color: #697383;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 850;
        color: #ffffff;
        margin-top: 8px;
    }

    .stat-description {
        color: #7d8795;
        font-size: 0.84rem;
        margin-top: 4px;
    }

    /* =====================================================
       INTERVIEW
       ===================================================== */

    .question-number {
        color: #776dff;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
    }

    .question-text {
        color: #ffffff;
        font-size: 1.12rem;
        line-height: 1.6;
        font-weight: 650;
        margin-top: 7px;
    }

    /* =====================================================
       SCORE
       ===================================================== */

    .score-big {
        font-size: 5rem;
        font-weight: 900;
        line-height: 1;
        letter-spacing: -0.07em;
        color: #ffffff;
    }

    .performance {
        font-size: 1.15rem;
        font-weight: 750;
        color: #8e84ff;
        margin-top: 10px;
    }

    /* =====================================================
       FOOTER
       ===================================================== */

    .footer-text {
        color: #505968;
        font-size: 0.78rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def safe_value(value, default=""):
    if value is None:
        return default
    return value


def normalize_score(value):
    try:
        score = float(value)

        if score <= 1:
            score *= 100

        return max(0, min(100, score))

    except (TypeError, ValueError):
        return 0


def get_user_name():
    user = st.session_state.get("user")

    if not user:
        return "User"

    return (
        user.get("name")
        or user.get("full_name")
        or user.get("username")
        or "User"
    )


def profile_value(profile, key, default=""):
    if not profile:
        return default

    value = profile.get(key)

    if value is None:
        return default

    return value


def calculate_profile_completion(profile):
    if not profile:
        return 0

    fields = [
        "name",
        "email",
        "phone",
        "education",
        "university",
        "target_role",
        "skills",
        "experience",
        "bio",
    ]

    completed = 0

    for field in fields:
        value = profile.get(field)

        if value is not None and str(value).strip():
            completed += 1

    return int((completed / len(fields)) * 100)


def extract_interview_score(interview):
    if not interview:
        return 0

    for key in [
        "overall_score",
        "score",
        "final_score",
    ]:
        if key in interview:
            return normalize_score(interview[key])

    evaluation = interview.get("evaluation")

    if isinstance(evaluation, dict):
        return normalize_score(
            evaluation.get("overall_score", 0)
        )

    return 0


def safe_json_load(value, default=None):

    if default is None:
        default = {}

    if value is None:
        return default

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(value)
    except Exception:
        return default


# =========================================================
# AI — GENERATE QUESTIONS
# =========================================================

def generate_interview_questions(
    profile,
    focus,
    number_of_questions,
):

    if client is None:
        return []

    profile_text = json.dumps(
        profile or {},
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are a senior technical interviewer.

Create a realistic professional mock interview.

Candidate profile:
{profile_text}

Interview focus:
{focus}

Number of questions:
{number_of_questions}

Requirements:
- Questions must match the candidate's target role.
- Questions should be realistic for an actual interview.
- Mix technical, practical, behavioral and problem-solving questions when appropriate.
- Avoid generic filler questions.
- Make every question answerable by the candidate.
- Do not provide answers.
- Return ONLY valid JSON.
- JSON format must be:
[
  "Question 1",
  "Question 2",
  "Question 3"
]
"""

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert technical interviewer "
                        "and career coach."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content.strip()

        questions = safe_json_load(
            content,
            default=[],
        )

        if isinstance(questions, list):
            return [
                str(q).strip()
                for q in questions
                if str(q).strip()
            ]

    except Exception as e:
        st.error(
            f"AI interview generation failed: {e}"
        )

    return []


# =========================================================
# AI — EVALUATE INTERVIEW
# =========================================================

def evaluate_interview(
    profile,
    questions,
    answers,
):

    if client is None:
        return None

    interview_payload = []

    for index, question in enumerate(questions):

        answer = answers.get(
            index,
            "",
        )

        interview_payload.append(
            {
                "question": question,
                "answer": answer,
            }
        )

    profile_text = json.dumps(
        profile or {},
        ensure_ascii=False,
        indent=2,
    )

    interview_text = json.dumps(
        interview_payload,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are a senior technical interviewer and career coach.

Evaluate the candidate's interview.

Candidate profile:
{profile_text}

Interview:
{interview_text}

Evaluate:

1. Technical knowledge
2. Communication
3. Problem solving
4. Answer quality
5. Relevance
6. Clarity
7. Confidence based only on the written answer

For every question provide:
- score from 0 to 100
- strengths
- weaknesses
- feedback

Also provide:
- overall_score
- technical_score
- communication_score
- problem_solving_score
- answer_quality_score
- strengths
- areas_to_improve
- recommendations
- performance_level

Performance levels:
85-100 = Strong
70-84 = Good
50-69 = Developing
0-49 = Needs Improvement

Return ONLY valid JSON.

Expected structure:

{{
    "overall_score": 0,
    "technical_score": 0,
    "communication_score": 0,
    "problem_solving_score": 0,
    "answer_quality_score": 0,
    "performance_level": "",
    "strengths": [],
    "areas_to_improve": [],
    "recommendations": [],
    "questions": [
        {{
            "question": "",
            "score": 0,
            "strengths": "",
            "weaknesses": "",
            "feedback": ""
        }}
    ]
}}
"""

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an objective senior interviewer."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content.strip()

        evaluation = safe_json_load(
            content,
            default=None,
        )

        if not isinstance(evaluation, dict):
            return None

        question_scores = []

        for item in evaluation.get(
            "questions",
            [],
        ):

            question_scores.append(
                normalize_score(
                    item.get("score", 0)
                )
            )

        if question_scores:

            evaluation["overall_score"] = round(
                sum(question_scores)
                / len(question_scores),
                1,
            )

        else:

            evaluation["overall_score"] = normalize_score(
                evaluation.get(
                    "overall_score",
                    0,
                )
            )

        for field in [
            "technical_score",
            "communication_score",
            "problem_solving_score",
            "answer_quality_score",
        ]:

            evaluation[field] = normalize_score(
                evaluation.get(field, 0)
            )

        score = normalize_score(
            evaluation.get(
                "overall_score",
                0,
            )
        )

        if score >= 85:
            evaluation["performance_level"] = "Strong"

        elif score >= 70:
            evaluation["performance_level"] = "Good"

        elif score >= 50:
            evaluation["performance_level"] = "Developing"

        else:
            evaluation["performance_level"] = (
                "Needs Improvement"
            )

        return evaluation

    except Exception as e:

        st.error(
            f"AI evaluation failed: {e}"
        )

        return None


# =========================================================
# AUTHENTICATION PAGE
# =========================================================

def render_authentication():

    top_left, top_right = st.columns(
        [4, 1]
    )

    with top_left:

        st.markdown(
            '<div class="landing-brand">AI CAREER</div>',
            unsafe_allow_html=True,
        )

    with top_right:

        if st.button(
            "Back to Home",
            key="auth_back_home",
            use_container_width=True,
        ):

            st.session_state.auth_mode = False
            st.session_state.landing_section = "home"

            st.rerun()

    st.divider()

    left_space, center, right_space = st.columns(
        [1, 1.5, 1]
    )

    with center:

        st.markdown(
            '<div class="auth-title">Welcome to AI Career</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="auth-subtitle">'
            'Sign in or create your career workspace.'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):

            sign_in_tab, create_tab = st.tabs(
                [
                    "Sign In",
                    "Create Account",
                ]
            )

            # =================================================
            # SIGN IN
            # =================================================

            with sign_in_tab:

                st.subheader(
                    "Welcome back"
                )

                login_email = st.text_input(
                    "Email",
                    key="login_email",
                    placeholder="you@example.com",
                )

                login_password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
                    placeholder="Enter your password",
                )

                st.write("")

                if st.button(
                    "Sign In",
                    key="auth_sign_in",
                    type="primary",
                    use_container_width=True,
                ):

                    if not login_email.strip():

                        st.error(
                            "Please enter your email."
                        )

                    elif not login_password:

                        st.error(
                            "Please enter your password."
                        )

                    else:

                        user = authenticate_user(
                            login_email.strip(),
                            login_password,
                        )

                        if user:

                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.session_state.page = "Dashboard"
                            st.session_state.auth_mode = False
                            st.session_state.current_interview_id = None
                            st.session_state.questions = []
                            st.session_state.answers = {}
                            st.session_state.evaluation = None
                            st.session_state.interview_started = False

                            st.rerun()

                        else:

                            st.error(
                                "Invalid email or password."
                            )

            # =================================================
            # CREATE ACCOUNT
            # =================================================

            with create_tab:

                st.subheader(
                    "Create your workspace"
                )

                register_name = st.text_input(
                    "Full Name",
                    key="register_name",
                    placeholder="Your full name",
                )

                register_email = st.text_input(
                    "Email",
                    key="register_email",
                    placeholder="you@example.com",
                )

                register_password = st.text_input(
                    "Password",
                    type="password",
                    key="register_password",
                    placeholder="Create a password",
                )

                register_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    key="register_confirm",
                    placeholder="Repeat your password",
                )

                st.write("")

                if st.button(
                    "Create Account",
                    key="auth_create_account",
                    type="primary",
                    use_container_width=True,
                ):

                    if not register_name.strip():

                        st.error(
                            "Please enter your name."
                        )

                    elif not register_email.strip():

                        st.error(
                            "Please enter your email."
                        )

                    elif not register_password:

                        st.error(
                            "Please create a password."
                        )

                    elif len(register_password) < 6:

                        st.error(
                            "Password must be at least 6 characters."
                        )

                    elif register_password != register_confirm:

                        st.error(
                            "Passwords do not match."
                        )

                    else:

                        try:

                            result = create_user(
                                register_name.strip(),
                                register_email.strip(),
                                register_password,
                            )

                            if result:

                                st.success(
                                    "Account created successfully. "
                                    "You can now sign in."
                                )

                            else:

                                st.error(
                                    "Could not create the account."
                                )

                        except Exception as e:

                            st.error(
                                f"Account creation failed: {e}"
                            )

    st.divider()

    st.caption(
        "AI Career — Intelligent preparation for your next opportunity."
    )


# =========================================================
# LANDING PAGE
# =========================================================

def render_landing_page():

    # =====================================================
    # NAVBAR
    # =====================================================

    nav1, nav2, nav3, nav4 = st.columns(
        [3.3, 1, 1.2, 1.3]
    )

    with nav1:

        st.markdown(
            '<div class="landing-brand">AI CAREER</div>',
            unsafe_allow_html=True,
        )

    with nav2:

        if st.button(
            "Home",
            key="landing_home",
            use_container_width=True,
        ):

            st.session_state.landing_section = "home"
            st.rerun()

    with nav3:

        if st.button(
            "Features",
            key="landing_features",
            use_container_width=True,
        ):

            st.session_state.landing_section = "features"
            st.rerun()

    with nav4:

        if st.button(
            "How It Works",
            key="landing_workflow",
            use_container_width=True,
        ):

            st.session_state.landing_section = "workflow"
            st.rerun()

    st.divider()

    # =====================================================
    # HERO
    # =====================================================

    hero_left, hero_right = st.columns(
        [1.4, 0.8],
        gap="large",
    )

    with hero_left:

        st.markdown(
            '<div class="hero-label">'
            'AI-POWERED CAREER PREPARATION'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="hero-title">
                Your Career,<br>
                Powered by Intelligence.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="hero-description">
                Prepare smarter. Practice realistic interviews.
                Understand your performance. Build the skills
                that move your career forward.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        # =================================================
        # ONLY LANDING CTA
        # =================================================

        if st.button(
            "Get Started",
            key="landing_get_started",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.auth_mode = True
            st.rerun()

        st.write("")

        p1, p2, p3 = st.columns(3)

        with p1:

            st.caption(
                "Role-Specific AI"
            )

        with p2:

            st.caption(
                "Realistic Interviews"
            )

        with p3:

            st.caption(
                "Intelligent Feedback"
            )

    # =====================================================
    # READINESS CARD
    # =====================================================

    with hero_right:

        with st.container(border=True):

            st.caption(
                "AI CAREER READINESS"
            )

            st.subheader(
                "Interview Intelligence"
            )

            st.markdown(
                '<div class="big-number">87</div>',
                unsafe_allow_html=True,
            )

            st.caption(
                "Example readiness score"
            )

            st.progress(0.87)

            st.write("")

            m1, m2 = st.columns(2)

            with m1:

                st.metric(
                    "Technical",
                    "91",
                )

            with m2:

                st.metric(
                    "Communication",
                    "84",
                )

            m3, m4 = st.columns(2)

            with m3:

                st.metric(
                    "Problem Solving",
                    "88",
                )

            with m4:

                st.metric(
                    "Answer Quality",
                    "85",
                )

    st.divider()

    # =====================================================
    # FEATURES
    # =====================================================

    st.markdown(
        '<div class="section-label">'
        'THE AI CAREER ADVANTAGE'
        '</div>',
        unsafe_allow_html=True,
    )

    st.header(
        "Everything you need to prepare with purpose."
    )

    feature_columns = st.columns(3)

    features = [
        (
            "01 / AI MOCK INTERVIEWS",
            "Practice Like It's Real",
            "Generate realistic interview questions based on "
            "your target role, technical skills, experience, "
            "and career goals.",
        ),
        (
            "02 / INTELLIGENT EVALUATION",
            "Know Exactly Where You Stand",
            "Receive structured feedback across technical "
            "knowledge, communication, problem solving, "
            "and answer quality.",
        ),
        (
            "03 / CAREER INTELLIGENCE",
            "Turn Feedback Into Progress",
            "Identify strengths, discover weaknesses, and "
            "understand what to practice next.",
        ),
    ]

    for column, feature in zip(
        feature_columns,
        features,
    ):

        with column:

            with st.container(border=True):

                st.caption(
                    feature[0]
                )

                st.subheader(
                    feature[1]
                )

                st.write(
                    feature[2]
                )

    st.divider()

    # =====================================================
    # WORKFLOW
    # =====================================================

    st.markdown(
        '<div class="section-label">'
        'HOW IT WORKS'
        '</div>',
        unsafe_allow_html=True,
    )

    st.header(
        "From preparation to career readiness."
    )

    workflow = [
        (
            "STEP 01",
            "Build Your Profile",
            "Add your education, experience, skills, "
            "and target career role.",
        ),
        (
            "STEP 02",
            "Practice With AI",
            "Generate a personalized mock interview "
            "based on your career profile.",
        ),
        (
            "STEP 03",
            "Get Evaluated",
            "Submit your answers and receive detailed "
            "AI-powered performance analysis.",
        ),
        (
            "STEP 04",
            "Improve",
            "Use your insights to focus your next "
            "practice session.",
        ),
    ]

    workflow_columns = st.columns(4)

    for column, item in zip(
        workflow_columns,
        workflow,
    ):

        with column:

            with st.container(border=True):

                st.caption(
                    item[0]
                )

                st.subheader(
                    item[1]
                )

                st.write(
                    item[2]
                )

    st.divider()

    # =====================================================
    # FINAL MESSAGE — NO EXTRA CTA
    # =====================================================

    cta_left, cta_right = st.columns(
        [2.3, 1]
    )

    with cta_left:

        st.markdown(
            '<div class="section-label">'
            'BUILD YOUR NEXT MOVE'
            '</div>',
            unsafe_allow_html=True,
        )

        st.header(
            "Your next interview deserves better preparation."
        )

        st.write(
            "AI Career combines realistic practice, "
            "structured evaluation, and actionable insights "
            "inside one intelligent career workspace."
        )

    with cta_right:

        with st.container(border=True):

            st.subheader(
                "Start when you're ready."
            )

            st.caption(
                "Use the Get Started button above to "
                "create your AI Career workspace."
            )

    st.divider()

    # =====================================================
    # FOOTER
    # =====================================================

    footer_left, footer_right = st.columns(2)

    with footer_left:

        st.markdown(
            '<div class="footer-text">'
            'AI CAREER — Career Intelligence Platform'
            '</div>',
            unsafe_allow_html=True,
        )

    with footer_right:

        st.markdown(
            '<div class="footer-text">'
            'Built for students, graduates & early-career professionals.'
            '</div>',
            unsafe_allow_html=True,
        )


# =========================================================
# SIDEBAR
# =========================================================

def render_sidebar():

    with st.sidebar:

        st.markdown(
            '<div class="sidebar-brand">AI CAREER</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "CAREER INTELLIGENCE PLATFORM"
        )

        st.write("")

        pages = [
            "Dashboard",
            "Profile",
            "Mock Interview",
            "Interview History",
            "Evaluation",
        ]

        current_page = st.session_state.page

        selected_page = st.radio(
            "Navigation",
            pages,
            index=(
                pages.index(current_page)
                if current_page in pages
                else 0
            ),
            key="sidebar_navigation",
            label_visibility="collapsed",
        )

        if selected_page != st.session_state.page:

            st.session_state.page = selected_page

            st.rerun()

        st.markdown(
            """
            <div class="sidebar-user">
                <div class="sidebar-user-label">
                    SIGNED IN AS
                </div>
                <div class="sidebar-user-name">
            """,
            unsafe_allow_html=True,
        )

        st.write(
            get_user_name()
        )

        st.markdown(
            """
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Sign Out",
            key="sidebar_sign_out",
            use_container_width=True,
        ):

            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.auth_mode = False
            st.session_state.page = "Dashboard"
            st.session_state.current_interview_id = None
            st.session_state.questions = []
            st.session_state.answers = {}
            st.session_state.evaluation = None
            st.session_state.interview_started = False

            st.rerun()


# =========================================================
# USER PROFILE
# =========================================================

def get_current_user_id():

    user = st.session_state.get("user")

    if not user:
        return None

    return (
        user.get("id")
        or user.get("user_id")
    )


def load_current_profile():

    user_id = get_current_user_id()

    if not user_id:
        return {}

    try:

        profile = get_profile(
            user_id
        )

        return profile or {}

    except Exception:

        return {}


# =========================================================
# DASHBOARD
# =========================================================

def render_dashboard():

    profile = load_current_profile()

    user_id = get_current_user_id()

    st.markdown(
        '<div class="section-label">DASHBOARD</div>',
        unsafe_allow_html=True,
    )

    header_left, header_right = st.columns(
        [3, 1]
    )

    with header_left:

        st.title(
            f"Welcome back, {get_user_name().split()[0]}"
        )

        st.write(
            "Track your preparation, practice interviews, "
            "and turn feedback into measurable progress."
        )

    with header_right:

        if st.button(
            "Start New Interview",
            key="dashboard_start_new_interview",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.page = "Mock Interview"
            st.session_state.questions = []
            st.session_state.answers = {}
            st.session_state.evaluation = None
            st.session_state.interview_started = False

            st.rerun()

    st.write("")

    # =====================================================
    # DATABASE STATS
    # =====================================================

    try:

        interview_count = get_interview_count(
            user_id
        )

    except Exception:

        interview_count = 0

    try:

        average_score = normalize_score(
            get_average_score(
                user_id
            )
        )

    except Exception:

        average_score = 0

    profile_completion = calculate_profile_completion(
        profile
    )

    st.subheader(
        "Your Progress"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Interviews",
            interview_count,
        )

    with c2:

        st.metric(
            "Average Score",
            f"{average_score:.0f}%",
        )

    with c3:

        st.metric(
            "Profile Completion",
            f"{profile_completion}%",
        )

    with c4:

        readiness = round(
            (average_score * 0.7)
            + (profile_completion * 0.3)
        )

        st.metric(
            "Career Readiness",
            f"{readiness}%",
        )

    st.write("")

    # =====================================================
    # PROFILE READINESS
    # =====================================================

    left, right = st.columns(
        [1.3, 0.7],
        gap="large",
    )

    with left:

        with st.container(border=True):

            st.markdown(
                '<div class="section-label">'
                'PROFILE READINESS'
                '</div>',
                unsafe_allow_html=True,
            )

            st.subheader(
                "Complete your career profile"
            )

            st.progress(
                profile_completion / 100
            )

            st.write(
                f"{profile_completion}% complete"
            )

            missing_items = []

            profile_checks = [
                (
                    "Target Role",
                    profile_value(
                        profile,
                        "target_role",
                    ),
                ),
                (
                    "Education",
                    profile_value(
                        profile,
                        "education",
                    ),
                ),
                (
                    "Skills",
                    profile_value(
                        profile,
                        "skills",
                    ),
                ),
                (
                    "Experience",
                    profile_value(
                        profile,
                        "experience",
                    ),
                ),
            ]

            for label, value in profile_checks:

                if not str(value).strip():

                    missing_items.append(
                        label
                    )

            if missing_items:

                st.caption(
                    "Recommended next steps:"
                )

                for item in missing_items:

                    st.write(
                        f"• Add {item}"
                    )

            else:

                st.success(
                    "Your core career profile is ready."
                )

    with right:

        with st.container(border=True):

            st.markdown(
                '<div class="section-label">'
                'AI INSIGHT'
                '</div>',
                unsafe_allow_html=True,
            )

            if average_score >= 85:

                st.subheader(
                    "Strong momentum"
                )

                st.write(
                    "Your recent performance indicates "
                    "strong interview readiness. Keep "
                    "practicing with role-specific questions."
                )

            elif average_score >= 70:

                st.subheader(
                    "Good progress"
                )

                st.write(
                    "You have a solid foundation. "
                    "Use your next interview to improve "
                    "the areas where your answers lose points."
                )

            elif interview_count > 0:

                st.subheader(
                    "Keep building"
                )

                st.write(
                    "You have started practicing. "
                    "Review your evaluation feedback and "
                    "repeat the areas that need improvement."
                )

            else:

                st.subheader(
                    "Start your first interview"
                )

                st.write(
                    "Complete your profile and run your "
                    "first AI-powered mock interview."
                )

    st.write("")

    # =====================================================
    # PERFORMANCE
    # =====================================================

    st.subheader(
        "Performance Overview"
    )

    if interview_count > 0:

        try:

            interviews = get_user_interviews(
                user_id
            )

        except Exception:

            interviews = []

        scores = []

        for interview in interviews or []:

            score = extract_interview_score(
                interview
            )

            if score > 0:

                scores.append(score)

        if scores:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    y=scores,
                    x=list(
                        range(
                            1,
                            len(scores) + 1,
                        )
                    ),
                    mode="lines+markers",
                    line=dict(
                        width=3
                    ),
                    marker=dict(
                        size=8
                    ),
                )
            )

            fig.update_layout(
                height=340,
                margin=dict(
                    l=20,
                    r=20,
                    t=20,
                    b=20,
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    color="#8e98a8"
                ),
                xaxis=dict(
                    title="Interview",
                    gridcolor="rgba(255,255,255,0.05)",
                ),
                yaxis=dict(
                    title="Score",
                    range=[0, 100],
                    gridcolor="rgba(255,255,255,0.05)",
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        else:

            st.info(
                "Your interview scores will appear here "
                "after completing an evaluated interview."
            )

    else:

        with st.container(border=True):

            st.subheader(
                "No interviews yet"
            )

            st.write(
                "Your performance chart will appear here "
                "after your first completed interview."
            )

            if st.button(
                "Start Your First Interview",
                key="dashboard_start_first_interview",
                type="primary",
            ):

                st.session_state.page = "Mock Interview"
                st.rerun()

    st.write("")

    # =====================================================
    # QUICK ACTIONS
    # =====================================================

    st.subheader(
        "Quick Actions"
    )

    q1, q2, q3 = st.columns(3)

    with q1:

        with st.container(border=True):

            st.caption(
                "PROFILE"
            )

            st.subheader(
                "Improve your profile"
            )

            st.write(
                "Keep your career information "
                "updated for better AI interviews."
            )

            if st.button(
                "Open Profile",
                key="dashboard_open_profile",
                use_container_width=True,
            ):

                st.session_state.page = "Profile"
                st.rerun()

    with q2:

        with st.container(border=True):

            st.caption(
                "PRACTICE"
            )

            st.subheader(
                "Practice Interview"
            )

            st.write(
                "Generate a new personalized "
                "AI interview session."
            )

            if st.button(
                "Start Practice",
                key="dashboard_start_practice",
                use_container_width=True,
            ):

                st.session_state.page = "Mock Interview"
                st.rerun()

    with q3:

        with st.container(border=True):

            st.caption(
                "HISTORY"
            )

            st.subheader(
                "Review Performance"
            )

            st.write(
                "Explore your previous interview "
                "sessions and evaluations."
            )

            if st.button(
                "View History",
                key="dashboard_view_history",
                use_container_width=True,
            ):

                st.session_state.page = "Interview History"
                st.rerun()


# =========================================================
# PROFILE PAGE
# =========================================================

def render_profile():

    profile = load_current_profile()

    st.markdown(
        '<div class="section-label">PROFILE</div>',
        unsafe_allow_html=True,
    )

    st.title(
        "Career Profile"
    )

    st.write(
        "Your profile helps AI Career generate "
        "more relevant interview experiences."
    )

    with st.container(border=True):

        st.subheader(
            "Personal Information"
        )

        c1, c2 = st.columns(2)

        with c1:

            full_name = st.text_input(
                "Full Name",
                value=profile_value(
                    profile,
                    "name",
                    get_user_name(),
                ),
                key="profile_full_name",
            )

        with c2:

            email = st.text_input(
                "Email",
                value=profile_value(
                    profile,
                    "email",
                    st.session_state.user.get(
                        "email",
                        "",
                    ),
                ),
                key="profile_email",
            )

        c3, c4 = st.columns(2)

        with c3:

            phone = st.text_input(
                "Phone",
                value=profile_value(
                    profile,
                    "phone",
                ),
                key="profile_phone",
            )

        with c4:

            university = st.text_input(
                "University",
                value=profile_value(
                    profile,
                    "university",
                ),
                key="profile_university",
            )

    st.write("")

    with st.container(border=True):

        st.subheader(
            "Career Information"
        )

        target_role = st.text_input(
            "Target Role",
            value=profile_value(
                profile,
                "target_role",
            ),
            placeholder="e.g. Data Scientist",
            key="profile_target_role",
        )

        education = st.text_input(
            "Education",
            value=profile_value(
                profile,
                "education",
            ),
            placeholder="e.g. B.Sc. Computer Science",
            key="profile_education",
        )

        skills = st.text_area(
            "Skills",
            value=profile_value(
                profile,
                "skills",
            ),
            placeholder=(
                "Python, SQL, Machine Learning, "
                "Data Analysis..."
            ),
            key="profile_skills",
        )

        experience = st.text_area(
            "Experience",
            value=profile_value(
                profile,
                "experience",
            ),
            placeholder=(
                "Describe your projects, internships, "
                "work experience..."
            ),
            key="profile_experience",
        )

        bio = st.text_area(
            "Professional Summary",
            value=profile_value(
                profile,
                "bio",
            ),
            placeholder=(
                "Tell AI Career about your professional "
                "background and career goals."
            ),
            key="profile_bio",
        )

    st.write("")

    if st.button(
        "Save Profile",
        key="profile_save",
        type="primary",
        use_container_width=True,
    ):

        user_id = get_current_user_id()

        profile_data = {
            "name": full_name,
            "email": email,
            "phone": phone,
            "university": university,
            "education": education,
            "target_role": target_role,
            "skills": skills,
            "experience": experience,
            "bio": bio,
        }

        try:

            save_profile(
                user_id,
                profile_data,
            )

            st.success(
                "Profile saved successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Could not save profile: {e}"
            )

    st.write("")

    completion = calculate_profile_completion(
        profile
    )

    with st.container(border=True):

        st.markdown(
            '<div class="section-label">'
            'PROFILE COMPLETION'
            '</div>',
            unsafe_allow_html=True,
        )

        st.progress(
            completion / 100
        )

        st.subheader(
            f"{completion}% complete"
        )

        st.caption(
            "A more complete profile helps generate "
            "more personalized interviews."
        )


# =========================================================
# MOCK INTERVIEW
# =========================================================

def render_mock_interview():

    profile = load_current_profile()

    st.markdown(
        '<div class="section-label">'
        'AI MOCK INTERVIEW'
        '</div>',
        unsafe_allow_html=True,
    )

    st.title(
        "Practice Interview"
    )

    st.write(
        "Run a realistic AI-generated interview "
        "based on your career profile."
    )

    if not profile:

        with st.container(border=True):

            st.subheader(
                "Complete your profile first"
            )

            st.write(
                "AI Career needs your career information "
                "to create a personalized interview."
            )

            if st.button(
                "Open Profile",
                key="mock_open_profile",
                type="primary",
            ):

                st.session_state.page = "Profile"
                st.rerun()

        return

    # =====================================================
    # SETUP
    # =====================================================

    if not st.session_state.questions:

        with st.container(border=True):

            st.subheader(
                "Interview Setup"
            )

            st.caption(
                f"Target role: "
                f"{profile_value(profile, 'target_role', 'Not specified')}"
            )

            focus = st.selectbox(
                "Interview Focus",
                [
                    "Technical",
                    "Behavioral",
                    "Problem Solving",
                    "Mixed",
                ],
                key="mock_focus",
            )

            number_of_questions = st.slider(
                "Number of Questions",
                min_value=3,
                max_value=10,
                value=5,
                key="mock_number_questions",
            )

            st.write("")

            if st.button(
                "Generate Interview",
                key="mock_generate_interview",
                type="primary",
                use_container_width=True,
            ):

                with st.spinner(
                    "AI is preparing your interview..."
                ):

                    questions = generate_interview_questions(
                        profile,
                        focus,
                        number_of_questions,
                    )

                if questions:

                    st.session_state.questions = questions
                    st.session_state.answers = {}
                    st.session_state.evaluation = None
                    st.session_state.interview_started = True

                    st.rerun()

                else:

                    st.error(
                        "Could not generate interview questions. "
                        "Check your OpenRouter API key and try again."
                    )

        return

    # =====================================================
    # INTERVIEW QUESTIONS
    # =====================================================

    st.subheader(
        "Interview Session"
    )

    st.caption(
        f"{len(st.session_state.questions)} questions"
    )

    answers = {}

    for index, question in enumerate(
        st.session_state.questions
    ):

        with st.container(border=True):

            st.markdown(
                f'<div class="question-number">'
                f'QUESTION {index + 1}'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="question-text">'
                f'{question}'
                f'</div>',
                unsafe_allow_html=True,
            )

            answers[index] = st.text_area(
                "Your Answer",
                value=st.session_state.answers.get(
                    index,
                    "",
                ),
                key=f"answer_{index}",
                height=170,
                placeholder=(
                    "Write your answer as if you were "
                    "speaking to the interviewer..."
                ),
            )

    st.write("")

    if st.button(
        "Submit Interview",
        key="mock_submit_interview",
        type="primary",
        use_container_width=True,
    ):

        empty_answers = [
            i + 1
            for i, answer in answers.items()
            if not answer.strip()
        ]

        if empty_answers:

            st.warning(
                "Please answer all questions before submitting."
            )

        else:

            st.session_state.answers = answers

            with st.spinner(
                "AI is evaluating your interview..."
            ):

                evaluation = evaluate_interview(
                    profile,
                    st.session_state.questions,
                    answers,
                )

            if evaluation:

                user_id = get_current_user_id()

                try:

                    interview_id = create_interview(
                        user_id,
                        json.dumps(
                            st.session_state.questions,
                            ensure_ascii=False,
                        ),
                    )

                    save_interview_answers(
                        interview_id,
                        json.dumps(
                            answers,
                            ensure_ascii=False,
                        ),
                    )

                    save_interview_evaluation(
                        interview_id,
                        json.dumps(
                            evaluation,
                            ensure_ascii=False,
                        ),
                    )

                    st.session_state.current_interview_id = interview_id

                except Exception as e:

                    st.warning(
                        f"Evaluation generated, but could not "
                        f"save the interview: {e}"
                    )

                st.session_state.evaluation = evaluation
                st.session_state.page = "Evaluation"

                st.rerun()

            else:

                st.error(
                    "The interview could not be evaluated."
                )


# =========================================================
# INTERVIEW HISTORY
# =========================================================

def render_interview_history():

    user_id = get_current_user_id()

    st.markdown(
        '<div class="section-label">'
        'INTERVIEW HISTORY'
        '</div>',
        unsafe_allow_html=True,
    )

    st.title(
        "Your Interviews"
    )

    st.write(
        "Review previous practice sessions "
        "and their performance."
    )

    if st.button(
        "Start New Interview",
        key="history_start_interview",
        type="primary",
    ):

        st.session_state.page = "Mock Interview"
        st.session_state.questions = []
        st.session_state.answers = {}
        st.session_state.evaluation = None

        st.rerun()

    st.write("")

    try:

        interviews = get_user_interviews(
            user_id
        )

    except Exception as e:

        st.error(
            f"Could not load interview history: {e}"
        )

        return

    if not interviews:

        with st.container(border=True):

            st.subheader(
                "No interviews yet"
            )

            st.write(
                "Your completed interviews will appear here."
            )

        return

    for index, interview in enumerate(
        interviews
    ):

        interview_id = interview.get(
            "id",
            index,
        )

        score = extract_interview_score(
            interview
        )

        date_value = (
            interview.get("created_at")
            or interview.get("date")
            or "Interview"
        )

        with st.container(border=True):

            c1, c2, c3, c4 = st.columns(
                [2.8, 1, 1, 1]
            )

            with c1:

                st.subheader(
                    f"Interview #{index + 1}"
                )

                st.caption(
                    str(date_value)
                )

            with c2:

                st.metric(
                    "Score",
                    f"{score:.0f}%",
                )

            with c3:

                if st.button(
                    "View",
                    key=f"history_view_{interview_id}",
                    use_container_width=True,
                ):

                    st.session_state.current_interview_id = interview_id
                    st.session_state.page = "Evaluation"
                    st.rerun()

            with c4:

                if st.button(
                    "Delete",
                    key=f"history_delete_{interview_id}",
                    use_container_width=True,
                ):

                    try:

                        delete_interview(
                            interview_id
                        )

                        st.success(
                            "Interview deleted."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Could not delete interview: {e}"
                        )


# =========================================================
# EVALUATION PAGE
# =========================================================

def render_evaluation():

    st.markdown(
        '<div class="section-label">'
        'AI EVALUATION'
        '</div>',
        unsafe_allow_html=True,
    )

    st.title(
        "Interview Evaluation"
    )

    evaluation = st.session_state.get(
        "evaluation"
    )

    interview_id = st.session_state.get(
        "current_interview_id"
    )

    # =====================================================
    # LOAD FROM DATABASE IF NEEDED
    # =====================================================

    if evaluation is None and interview_id:

        try:

            interview = get_interview(
                interview_id
            )

        except Exception:

            interview = None

        if interview:

            raw_evaluation = interview.get(
                "evaluation"
            )

            evaluation = safe_json_load(
                raw_evaluation,
                default=None,
            )

            if evaluation:

                st.session_state.evaluation = evaluation

    # =====================================================
    # NO EVALUATION
    # =====================================================

    if not evaluation:

        with st.container(border=True):

            st.subheader(
                "No evaluation available"
            )

            st.write(
                "Complete a mock interview to see "
                "your AI-powered evaluation."
            )

            if st.button(
                "Start Interview",
                key="evaluation_start_interview",
                type="primary",
            ):

                st.session_state.page = "Mock Interview"
                st.session_state.questions = []
                st.session_state.answers = {}
                st.session_state.evaluation = None

                st.rerun()

        return

    # =====================================================
    # SCORE
    # =====================================================

    score = normalize_score(
        evaluation.get(
            "overall_score",
            0,
        )
    )

    performance = evaluation.get(
        "performance_level",
        "Developing",
    )

    score_left, score_right = st.columns(
        [1, 2]
    )

    with score_left:

        with st.container(border=True):

            st.caption(
                "OVERALL SCORE"
            )

            st.markdown(
                f'<div class="score-big">'
                f'{score:.0f}'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.caption(
                "out of 100"
            )

            st.markdown(
                f'<div class="performance">'
                f'{performance}'
                f'</div>',
                unsafe_allow_html=True,
            )

    with score_right:

        with st.container(border=True):

            st.caption(
                "PERFORMANCE BREAKDOWN"
            )

            b1, b2 = st.columns(2)

            with b1:

                st.metric(
                    "Technical",
                    f"{normalize_score(evaluation.get('technical_score', 0)):.0f}%",
                )

                st.metric(
                    "Problem Solving",
                    f"{normalize_score(evaluation.get('problem_solving_score', 0)):.0f}%",
                )

            with b2:

                st.metric(
                    "Communication",
                    f"{normalize_score(evaluation.get('communication_score', 0)):.0f}%",
                )

                st.metric(
                    "Answer Quality",
                    f"{normalize_score(evaluation.get('answer_quality_score', 0)):.0f}%",
                )

    st.write("")

    # =====================================================
    # STRENGTHS / IMPROVEMENT
    # =====================================================

    left, right = st.columns(2)

    with left:

        with st.container(border=True):

            st.caption(
                "STRENGTHS"
            )

            strengths = evaluation.get(
                "strengths",
                [],
            )

            if isinstance(
                strengths,
                str,
            ):

                strengths = [
                    strengths
                ]

            if strengths:

                for item in strengths:

                    st.write(
                        f"• {item}"
                    )

            else:

                st.caption(
                    "No strengths were provided."
                )

    with right:

        with st.container(border=True):

            st.caption(
                "AREAS TO IMPROVE"
            )

            areas = evaluation.get(
                "areas_to_improve",
                [],
            )

            if isinstance(
                areas,
                str,
            ):

                areas = [
                    areas
                ]

            if areas:

                for item in areas:

                    st.write(
                        f"• {item}"
                    )

            else:

                st.caption(
                    "No improvement areas were provided."
                )

    st.write("")

    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    with st.container(border=True):

        st.caption(
            "AI RECOMMENDATIONS"
        )

        recommendations = evaluation.get(
            "recommendations",
            [],
        )

        if isinstance(
            recommendations,
            str,
        ):

            recommendations = [
                recommendations
            ]

        if recommendations:

            for item in recommendations:

                st.write(
                    f"• {item}"
                )

        else:

            st.write(
                "Keep practicing with targeted questions "
                "based on your weakest areas."
            )

    st.write("")

    # =====================================================
    # QUESTION-BY-QUESTION
    # =====================================================

    st.subheader(
        "Question-by-Question Analysis"
    )

    question_results = evaluation.get(
        "questions",
        [],
    )

    for index, item in enumerate(
        question_results
    ):

        with st.container(border=True):

            st.markdown(
                f'<div class="question-number">'
                f'QUESTION {index + 1}'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.subheader(
                item.get(
                    "question",
                    f"Question {index + 1}",
                )
            )

            q_score = normalize_score(
                item.get(
                    "score",
                    0,
                )
            )

            st.progress(
                q_score / 100
            )

            st.caption(
                f"Score: {q_score:.0f}%"
            )

            c1, c2 = st.columns(2)

            with c1:

                st.markdown(
                    "**Strengths**"
                )

                st.write(
                    item.get(
                        "strengths",
                        "No specific strengths provided.",
                    )
                )

            with c2:

                st.markdown(
                    "**Weaknesses**"
                )

                st.write(
                    item.get(
                        "weaknesses",
                        "No specific weaknesses provided.",
                    )
                )

            st.markdown(
                "**Feedback**"
            )

            st.write(
                item.get(
                    "feedback",
                    "No additional feedback provided.",
                )
            )

    st.write("")

    # =====================================================
    # ACTIONS
    # =====================================================

    a1, a2, a3 = st.columns(3)

    with a1:

        if st.button(
            "New Interview",
            key="evaluation_new_interview",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.page = "Mock Interview"
            st.session_state.questions = []
            st.session_state.answers = {}
            st.session_state.evaluation = None
            st.session_state.current_interview_id = None

            st.rerun()

    with a2:

        if st.button(
            "View History",
            key="evaluation_open_history",
            use_container_width=True,
        ):

            st.session_state.page = "Interview History"
            st.rerun()

    with a3:

        if st.button(
            "Dashboard",
            key="evaluation_open_dashboard",
            use_container_width=True,
        ):

            st.session_state.page = "Dashboard"
            st.rerun()


# =========================================================
# APP ROUTER
# =========================================================

if not st.session_state.logged_in:

    if st.session_state.auth_mode:

        render_authentication()

    else:

        render_landing_page()

    st.stop()


# =========================================================
# AUTHENTICATED APP
# =========================================================

render_sidebar()

current_page = st.session_state.page


if current_page == "Dashboard":

    render_dashboard()

elif current_page == "Profile":

    render_profile()

elif current_page == "Mock Interview":

    render_mock_interview()

elif current_page == "Interview History":

    render_interview_history()

elif current_page == "Evaluation":

    render_evaluation()

else:

    st.session_state.page = "Dashboard"
    st.rerun()