import json
from typing import List, Dict

from app.deepseek_client import call_deepseek
from app.ppt_parser import extract_text_from_ppt
from app.prompt_builder import build_prompt


def generate_quiz_from_ppt(file_path: str, difficulty: str = "medium", question_count: int = 5) -> List[Dict[str, object]]:
    slide_texts = extract_text_from_ppt(file_path)
    prompt = build_prompt(slide_texts, difficulty, question_count)
    raw_response = call_deepseek(prompt)
    return json.loads(raw_response)
