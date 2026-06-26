"""Streamlit frontend for the AI Quiz Generator."""

import json
import os
import tempfile
from typing import List, Dict

import streamlit as st

from app.config import MAX_FILE_SIZE_MB
from app.ppt_parser import extract_text_from_ppt
from app.prompt_builder import build_prompt
from app.deepseek_client import call_deepseek
from app.scorer import calculate_score

# ── Page Configuration ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Theme Toggle ────────────────────────────────────────────────────────────

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False


def toggle_theme() -> None:
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()


theme = "dark" if st.session_state.dark_mode else "light"

# ── Theme CSS Variables ─────────────────────────────────────────────────────

def theme_css(t: str) -> str:
    if t == "dark":
        return """
        <style>
            /* ── Base ─────────────────────────────────────────── */
            .stApp {
                background: linear-gradient(145deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
                color: #e0e0e0;
            }
            .stApp header { background: #0f0f1a !important; }
            .stApp [data-testid="stToolbar"] { background: #0f0f1a !important; }
            .stSidebar {
                background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
                border-right: 1px solid #2a2a4a;
            }
            .stSidebar .sidebar-content { background: transparent; }
            .stSelectbox label, .stSlider label, .stMarkdown, p, li, h1, h2, h3, h4, h5, h6 {
                color: #e0e0e0 !important;
            }
            .stSelectbox > div > div {
                background: #2a2a4a !important;
                border-color: #3a3a5a !important;
                color: #e0e0e0 !important;
            }
            .stSlider > div > div > div {
                background: #3a3a5a !important;
            }
            .stSlider > div > div > div > div {
                background: #6c63ff !important;
            }
            .stButton > button {
                background: linear-gradient(135deg, #6c63ff, #4834d4) !important;
                color: white !important;
                border: none !important;
                border-radius: 10px !important;
                padding: 0.6rem 1.2rem !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 4px 15px rgba(108,99,255,0.3) !important;
            }
            .stButton > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(108,99,255,0.4) !important;
            }
            .stButton > button[kind="secondary"] {
                background: #2a2a4a !important;
                box-shadow: none !important;
                border: 1px solid #3a3a5a !important;
            }
            .stButton > button[kind="secondary"]:hover {
                background: #3a3a5a !important;
            }
            .stProgress > div > div > div > div {
                background: linear-gradient(90deg, #6c63ff, #a78bfa) !important;
            }
            .stFileUploader > div {
                background: #2a2a4a !important;
                border: 2px dashed #3a3a5a !important;
                border-radius: 12px !important;
                color: #e0e0e0 !important;
            }
            .stAlert {
                background: #2a2a4a !important;
                color: #e0e0e0 !important;
                border: 1px solid #3a3a5a !important;
            }
            .stAlert [data-testid="stAlertContainer"] { color: #e0e0e0 !important; }
            ::-webkit-scrollbar-track { background: #0f0f1a !important; }
            ::-webkit-scrollbar-thumb { background: #3a3a5a !important; border-radius: 4px !important; }

            /* ── Quiz Card ────────────────────────────────────── */
            .quiz-card {
                background: linear-gradient(145deg, #1e1e3a, #25254a);
                padding: 2rem;
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(108,99,255,0.1);
                margin-bottom: 1.5rem;
                border: 1px solid #2a2a4a;
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
            }
            .quiz-card:hover {
                box-shadow: 0 12px 40px rgba(108,99,255,0.15), 0 0 0 1px rgba(108,99,255,0.2);
            }
            .question-text {
                font-size: 1.25rem;
                font-weight: 700;
                color: #f0f0ff;
                margin-bottom: 1.5rem;
                line-height: 1.7;
                letter-spacing: -0.01em;
                background: linear-gradient(135deg, #f0f0ff, #c4b5fd);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .option-btn {
                display: block;
                width: 100%;
                padding: 0.85rem 1.2rem;
                margin-bottom: 0.6rem;
                border: 2px solid #2a2a4a;
                border-radius: 10px;
                background: #25254a;
                color: #e0e0e0;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: left;
                font-size: 1rem;
            }
            .option-btn:hover {
                border-color: #6c63ff;
                background: #2a2a5a;
                transform: translateX(4px);
            }
            .correct-option {
                border-color: #10b981 !important;
                background: rgba(16, 185, 129, 0.15) !important;
                box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
            }
            .wrong-option {
                border-color: #ef4444 !important;
                background: rgba(239, 68, 68, 0.15) !important;
                box-shadow: 0 0 20px rgba(239, 68, 68, 0.15);
            }
            .score-card {
                background: linear-gradient(145deg, #1e1e3a, #25254a);
                padding: 2.5rem;
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(108,99,255,0.1);
                text-align: center;
                border: 1px solid #2a2a4a;
            }
            .score-percentage {
                font-size: 3.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, #6c63ff, #a78bfa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .score-label {
                font-size: 1.1rem;
                color: #9ca3af;
                margin-top: 0.5rem;
                font-weight: 500;
            }
            .explanation-box {
                background: rgba(245, 158, 11, 0.1);
                border-left: 4px solid #f59e0b;
                padding: 1rem 1.25rem;
                border-radius: 0 10px 10px 0;
                margin-top: 1rem;
                color: #fbbf24;
            }
            .upload-section {
                background: linear-gradient(145deg, #1e1e3a, #25254a);
                padding: 3rem;
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(108,99,255,0.1);
                text-align: center;
                border: 1px solid #2a2a4a;
            }
            .upload-icon { font-size: 4rem; margin-bottom: 1rem; }
            .theme-toggle-btn {
                background: #2a2a4a !important;
                border: 1px solid #3a3a5a !important;
                color: #fbbf24 !important;
                border-radius: 50px !important;
                padding: 0.5rem 1rem !important;
            }
            .progress-text {
                color: #9ca3af;
                font-size: 0.9rem;
                font-weight: 500;
                margin-bottom: 0.5rem;
            }
            .metric-box {
                background: #25254a;
                padding: 1rem;
                border-radius: 10px;
                text-align: center;
                border: 1px solid #2a2a4a;
            }
            .metric-value {
                font-size: 1.5rem;
                font-weight: 700;
                color: #f0f0ff;
            }
            .metric-label {
                font-size: 0.8rem;
                color: #9ca3af;
                margin-top: 0.25rem;
            }
            .header-gradient {
                background: linear-gradient(135deg, #6c63ff, #a78bfa, #f472b6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-weight: 800;
            }
            .subheader {
                color: #9ca3af;
                font-size: 1.1rem;
            }
            .footer {
                text-align: center;
                color: #4a4a6a;
                font-size: 0.85rem;
                padding: 2rem 0 0 0;
            }
            .summary-expander {
                background: #25254a !important;
                border: 1px solid #2a2a4a !important;
                border-radius: 10px !important;
                margin-bottom: 0.5rem !important;
            }
            .st-emotion-cache-1qg05tj { color: #e0e0e0 !important; }
            .st-bb { background: #2a2a4a !important; }
            .st-at { background: #2a2a4a !important; }
            div[data-testid="stMetricValue"] { color: #f0f0ff !important; }
            div[data-testid="stMetricLabel"] { color: #9ca3af !important; }
        </style>
        """
    else:
        return """
        <style>
            /* ── Base ─────────────────────────────────────────── */
            .stApp {
                background: linear-gradient(145deg, #f0f4ff 0%, #faf5ff 50%, #fdf2f8 100%);
                color: #1a1a2e;
            }
            .stSidebar {
                background: linear-gradient(180deg, #ffffff 0%, #f8f9ff 100%);
                border-right: 1px solid #e8e8f0;
            }
            .stSelectbox > div > div {
                background: white !important;
                border-color: #d0d0e0 !important;
                color: #1a1a2e !important;
            }
            .stSlider > div > div > div {
                background: #d0d0e0 !important;
            }
            .stSlider > div > div > div > div {
                background: #4a6cf7 !important;
            }
            .stButton > button {
                background: linear-gradient(135deg, #4a6cf7, #6c63ff) !important;
                color: white !important;
                border: none !important;
                border-radius: 10px !important;
                padding: 0.6rem 1.2rem !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 4px 15px rgba(74,108,247,0.25) !important;
            }
            .stButton > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(74,108,247,0.35) !important;
            }
            .stButton > button[kind="secondary"] {
                background: white !important;
                color: #4a6cf7 !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
                border: 1px solid #e0e0f0 !important;
            }
            .stButton > button[kind="secondary"]:hover {
                background: #f8f9ff !important;
            }
            .stProgress > div > div > div > div {
                background: linear-gradient(90deg, #4a6cf7, #a78bfa) !important;
            }
            .stFileUploader > div {
                background: white !important;
                border: 2px dashed #d0d0e0 !important;
                border-radius: 12px !important;
                color: #1a1a2e !important;
            }
            .stAlert {
                background: white !important;
                color: #1a1a2e !important;
                border: 1px solid #e0e0f0 !important;
            }

            /* ── Quiz Card ────────────────────────────────────── */
            .quiz-card {
                background: white;
                padding: 2rem;
                border-radius: 16px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 0 0 1px rgba(74,108,247,0.08);
                margin-bottom: 1.5rem;
                border: 1px solid #f0f0ff;
                transition: all 0.3s ease;
            }
            .quiz-card:hover {
                box-shadow: 0 8px 32px rgba(74,108,247,0.1), 0 0 0 1px rgba(74,108,247,0.15);
            }
            .question-text {
                font-size: 1.25rem;
                font-weight: 700;
                color: #1a1a2e;
                margin-bottom: 1.5rem;
                line-height: 1.7;
                letter-spacing: -0.01em;
            }
            .option-btn {
                display: block;
                width: 100%;
                padding: 0.85rem 1.2rem;
                margin-bottom: 0.6rem;
                border: 2px solid #e8e8f0;
                border-radius: 10px;
                background: white;
                color: #1a1a2e;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: left;
                font-size: 1rem;
            }
            .option-btn:hover {
                border-color: #4a6cf7;
                background: #f8f9ff;
                transform: translateX(4px);
            }
            .correct-option {
                border-color: #10b981 !important;
                background: rgba(16, 185, 129, 0.08) !important;
                box-shadow: 0 0 16px rgba(16, 185, 129, 0.1);
            }
            .wrong-option {
                border-color: #ef4444 !important;
                background: rgba(239, 68, 68, 0.08) !important;
                box-shadow: 0 0 16px rgba(239, 68, 68, 0.1);
            }
            .score-card {
                background: white;
                padding: 2.5rem;
                border-radius: 16px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 0 0 1px rgba(74,108,247,0.08);
                text-align: center;
                border: 1px solid #f0f0ff;
            }
            .score-percentage {
                font-size: 3.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, #4a6cf7, #a78bfa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .score-label {
                font-size: 1.1rem;
                color: #6b7280;
                margin-top: 0.5rem;
                font-weight: 500;
            }
            .explanation-box {
                background: #fffbeb;
                border-left: 4px solid #f59e0b;
                padding: 1rem 1.25rem;
                border-radius: 0 10px 10px 0;
                margin-top: 1rem;
                color: #92400e;
            }
            .upload-section {
                background: white;
                padding: 3rem;
                border-radius: 16px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 0 0 1px rgba(74,108,247,0.08);
                text-align: center;
                border: 1px solid #f0f0ff;
            }
            .upload-icon { font-size: 4rem; margin-bottom: 1rem; }
            .theme-toggle-btn {
                background: white !important;
                border: 1px solid #e0e0f0 !important;
                color: #6c63ff !important;
                border-radius: 50px !important;
                padding: 0.5rem 1rem !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
            }
            .progress-text {
                color: #6b7280;
                font-size: 0.9rem;
                font-weight: 500;
                margin-bottom: 0.5rem;
            }
            .metric-box {
                background: #f8f9ff;
                padding: 1rem;
                border-radius: 10px;
                text-align: center;
                border: 1px solid #e8e8f0;
            }
            .metric-value {
                font-size: 1.5rem;
                font-weight: 700;
                color: #1a1a2e;
            }
            .metric-label {
                font-size: 0.8rem;
                color: #6b7280;
                margin-top: 0.25rem;
            }
            .header-gradient {
                background: linear-gradient(135deg, #4a6cf7, #a78bfa, #f472b6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-weight: 800;
            }
            .subheader {
                color: #6b7280;
                font-size: 1.1rem;
            }
            .footer {
                text-align: center;
                color: #9ca3af;
                font-size: 0.85rem;
                padding: 2rem 0 0 0;
            }
            .summary-expander {
                background: white !important;
                border: 1px solid #e8e8f0 !important;
                border-radius: 10px !important;
                margin-bottom: 0.5rem !important;
            }
        </style>
        """


st.markdown(theme_css(theme), unsafe_allow_html=True)

# ── Session State Initialization ────────────────────────────────────────────

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "file_processed" not in st.session_state:
    st.session_state.file_processed = False
if "slide_text" not in st.session_state:
    st.session_state.slide_text = []
if "generating" not in st.session_state:
    st.session_state.generating = False

# ── Helper Functions ────────────────────────────────────────────────────────


def reset_quiz() -> None:
    """Reset all quiz-related session state."""
    st.session_state.quiz_questions = []
    st.session_state.current_q = 0
    st.session_state.user_answers = []
    st.session_state.quiz_submitted = False
    st.session_state.quiz_started = False
    st.session_state.generating = False


def generate_quiz(
    file_path: str, difficulty: str, question_count: int
) -> List[Dict[str, object]]:
    """Generate quiz questions from a PPT file."""
    st.session_state.generating = True
    try:
        slide_texts = extract_text_from_ppt(file_path)
        st.session_state.slide_text = slide_texts
        prompt = build_prompt(slide_texts, difficulty, question_count)
        raw_response = call_deepseek(prompt)

        # Attempt to parse JSON; handle markdown code fences
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

        questions = json.loads(cleaned)
        if isinstance(questions, dict) and "questions" in questions:
            questions = questions["questions"]

        st.session_state.quiz_questions = questions
        st.session_state.quiz_started = True
        st.session_state.current_q = 0
        st.session_state.user_answers = [None] * len(questions)
        st.session_state.quiz_submitted = False
    except Exception as e:
        st.error(f"Failed to generate quiz: {e}")
        st.session_state.generating = False
        return []
    finally:
        st.session_state.generating = False

    return st.session_state.quiz_questions


def submit_quiz() -> None:
    """Mark the quiz as submitted."""
    if None in st.session_state.user_answers:
        st.warning("Please answer all questions before submitting.")
        return
    st.session_state.quiz_submitted = True


# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🧠</div>
            <h3 style="margin: 0; {'color: #f0f0ff;' if theme == 'dark' else 'color: #1a1a2e;'}">
                AI Quiz Generator
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Theme toggle button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("")
    with col2:
        icon = "🌙" if not st.session_state.dark_mode else "☀️"
        if st.button(icon, key="theme_toggle", help="Toggle dark/light mode"):
            toggle_theme()

    st.markdown("---")
    st.markdown(
        "Upload a PowerPoint presentation and let AI generate "
        "interactive multiple-choice quiz questions for you."
    )

    difficulty = st.selectbox(
        "🎯 Difficulty Level",
        options=["simple", "medium", "complex"],
        index=1,
        format_func=lambda x: x.capitalize(),
        disabled=st.session_state.quiz_started,
    )

    question_count = st.slider(
        "📝 Number of Questions",
        min_value=5,
        max_value=30,
        value=10,
        step=1,
        disabled=st.session_state.quiz_started,
    )

    st.markdown("---")
    st.markdown(f"📦 **Max file size:** {MAX_FILE_SIZE_MB} MB")
    st.markdown("📄 **Supported:** PPT, PPTX")

    if st.session_state.quiz_started:
        st.markdown("---")
        if st.button("🔄 Start Over", type="primary", use_container_width=True):
            reset_quiz()
            st.rerun()

# ── Main Content Area ───────────────────────────────────────────────────────

st.markdown(
    f'<h1 class="header-gradient" style="font-size: 2.5rem; margin-bottom: 0.25rem;">'
    f"🧠 AI Quiz Generator</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="subheader">'
    "Turn your PowerPoint presentations into interactive quizzes powered by AI.</p>",
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# ── Upload Section ──────────────────────────────────────────────────────────

if not st.session_state.quiz_started:
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.markdown(
            '<div class="upload-icon">📤</div>', unsafe_allow_html=True
        )
        st.markdown(
            f"<h3 style='{'color: #f0f0ff;' if theme == 'dark' else 'color: #1a1a2e;'}"
            f" margin-bottom: 1rem;'>Upload Your Presentation</h3>",
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Choose a PPT or PPTX file",
            type=["ppt", "pptx"],
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            # Validate file size
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                st.error(
                    f"File size ({file_size_mb:.1f} MB) exceeds the "
                    f"maximum allowed size of {MAX_FILE_SIZE_MB} MB."
                )
            else:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pptx"
                ) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                st.success(
                    f"✅ **{uploaded_file.name}** uploaded successfully "
                    f"({file_size_mb:.1f} MB)"
                )

                if st.button(
                    "🚀 Generate Quiz",
                    type="primary",
                    use_container_width=True,
                    disabled=st.session_state.generating,
                ):
                    with st.spinner(
                        "📖 Extracting slides and generating quiz questions..."
                    ):
                        questions = generate_quiz(
                            tmp_path, difficulty, question_count
                        )
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

                    if questions:
                        st.success(
                            f"✅ Generated {len(questions)} questions!"
                        )
                        st.rerun()
                    else:
                        st.error(
                            "Failed to generate quiz. Check your API key "
                            "and try again."
                        )

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            "💡 **Tip:** Place your `.ppt` or `.pptx` files in the "
            "`sample-data/` folder for quick access."
        )

# ── Quiz Interface ──────────────────────────────────────────────────────────

if st.session_state.quiz_started and st.session_state.quiz_questions:
    questions = st.session_state.quiz_questions
    total_q = len(questions)
    current_idx = st.session_state.current_q

    # Progress indicator
    st.markdown(
        f'<div class="progress-text">Question {current_idx + 1} of {total_q}</div>',
        unsafe_allow_html=True,
    )
    progress = (current_idx + 1) / total_q
    st.progress(progress)

    # Quiz card
    st.markdown('<div class="quiz-card">', unsafe_allow_html=True)

    question_data = questions[current_idx]
    st.markdown(
        f'<div class="question-text">{question_data["question"]}</div>',
        unsafe_allow_html=True,
    )

    options = question_data.get("options", [])
    selected = st.session_state.user_answers[current_idx]

    if not st.session_state.quiz_submitted:
        # Active quiz mode
        for i, option in enumerate(options):
            option_key = f"q_{current_idx}_opt_{i}"
            if selected == option:
                btn_type = "primary"
            else:
                btn_type = "secondary"

            if st.button(
                option,
                key=option_key,
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.user_answers[current_idx] = option
                st.rerun()
    else:
        # Review mode (submitted)
        correct_answer = question_data.get("correctAnswer", "")
        user_answer = st.session_state.user_answers[current_idx]

        for option in options:
            is_correct = option == correct_answer
            is_selected = option == user_answer

            if is_correct:
                st.markdown(
                    f'<div class="option-btn correct-option">'
                    f"✅ {option}</div>",
                    unsafe_allow_html=True,
                )
            elif is_selected and not is_correct:
                st.markdown(
                    f'<div class="option-btn wrong-option">'
                    f"❌ {option}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="option-btn">{option}</div>',
                    unsafe_allow_html=True,
                )

        # Show explanation
        if "explanation" in question_data and user_answer != correct_answer:
            st.markdown(
                f'<div class="explanation-box">'
                f"<strong>💡 Explanation:</strong><br>"
                f"{question_data['explanation']}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col1:
        if current_idx > 0:
            st.button("⬅ Previous", key="prev_btn", use_container_width=True,
                       on_click=lambda: setattr(st.session_state, 'current_q', current_idx - 1))

    with col2:
        if not st.session_state.quiz_submitted:
            if current_idx < total_q - 1:
                st.button("Next ➡", key="next_btn", use_container_width=True,
                           on_click=lambda: setattr(st.session_state, 'current_q', current_idx + 1))
            else:
                st.button("📝 Submit Quiz", type="primary",
                           key="submit_btn", use_container_width=True,
                           on_click=submit_quiz)
        else:
            st.button("🔄 Try Again", key="try_again_btn",
                       use_container_width=True, on_click=reset_quiz)

    with col3:
        if st.session_state.quiz_submitted and current_idx < total_q - 1:
            st.button("Next ➡", key="next_btn2", use_container_width=True,
                       on_click=lambda: setattr(st.session_state, 'current_q', current_idx + 1))

    # Quick jump to question (only in review mode)
    if st.session_state.quiz_submitted:
        st.markdown("---")
        st.markdown("**🔍 Jump to question:**")
        cols_per_row = min(total_q, 10)
        rows_needed = (total_q + cols_per_row - 1) // cols_per_row
        for row in range(rows_needed):
            cols = st.columns(cols_per_row)
            for col_idx in range(cols_per_row):
                q_idx = row * cols_per_row + col_idx
                if q_idx < total_q:
                    with cols[col_idx]:
                        answered = st.session_state.user_answers[q_idx] is not None
                        is_current = q_idx == current_idx
                        btn_type = "primary" if is_current else ("secondary" if answered else "tertiary")
                        label_text = f"Q{q_idx+1}"
                        if st.button(label_text, key=f"jump_{q_idx}",
                                      use_container_width=True, type=btn_type):
                            st.session_state.current_q = q_idx
                            st.rerun()

    # ── Score Display ──────────────────────────────────────────────────────

    if st.session_state.quiz_submitted:
        st.markdown("---")
        st.markdown("## 📊 Quiz Results")

        correct_answers_list = [
            q.get("correctAnswer", "") for q in questions
        ]
        answer_dicts = [
            {"selectedOption": ans} for ans in st.session_state.user_answers
        ]
        score = calculate_score(answer_dicts, correct_answers_list)

        col1, col2, col3, col4 = st.columns(4)
        metrics = [
            ("📋 Total", score["totalQuestions"]),
            ("✅ Correct", score["correctAnswers"]),
            ("❌ Wrong", score["wrongAnswers"]),
            ("📈 Score", f"{score['percentage']}%"),
        ]
        for col, (label, value) in zip([col1, col2, col3, col4], metrics):
            with col:
                st.markdown(
                    f'<div class="metric-box">'
                    f'<div class="metric-value">{value}</div>'
                    f'<div class="metric-label">{label}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # Score card
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="score-card">
                <div class="score-percentage">{score['percentage']}%</div>
                <div class="score-label">Overall Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Grade
        pct = score['percentage']
        if pct >= 90:
            grade = "🌟 Excellent!"
        elif pct >= 75:
            grade = "👏 Great job!"
        elif pct >= 50:
            grade = "👍 Good effort!"
        elif pct >= 30:
            grade = "📚 Keep practicing!"
        else:
            grade = "💪 Review and try again!"

        st.markdown(
            f'<div style="text-align: center; font-size: 1.2rem; '
            f'font-weight: 600; margin-top: 0.5rem; '
            f'{"color: #f0f0ff;" if theme == "dark" else "color: #1a1a2e;"}">'
            f"{grade}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("### 📋 Summary")
        for i, q in enumerate(questions):
            user_ans = st.session_state.user_answers[i]
            correct_ans = q.get("correctAnswer", "")
            is_correct = user_ans == correct_ans

            marker = "✅" if is_correct else "❌"
            q_short = q['question'][:80] + "..." if len(q['question']) > 80 else q['question']
 
            with st.expander(f"{marker} Q{i+1}: {q_short}",
                             expanded=not is_correct):
                st.markdown(f"**Your answer:** {user_ans}")
                st.markdown(f"**Correct answer:** {correct_ans}")
                if "explanation" in q:
                    st.markdown(f"**Explanation:** {q['explanation']}")

# ── Footer ──────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    '<div class="footer">'
    "Powered by OpenRouter AI &nbsp;|&nbsp; Built with Streamlit"
    "</div>",
    unsafe_allow_html=True,
)