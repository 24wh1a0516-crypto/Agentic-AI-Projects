from typing import List


def build_prompt(slide_texts: List[str], difficulty: str, question_count: int) -> str:
    content = "\n\n".join(slide_texts)
    return f"""
Create {question_count} multiple-choice quiz questions from the following presentation content.
Difficulty: {difficulty}
Requirements:
- Exactly 4 options per question
- One correct answer
- Return valid JSON with an array of questions
- Each question should include: question, options, correctAnswer, explanation

Presentation content:
{content}
"""
