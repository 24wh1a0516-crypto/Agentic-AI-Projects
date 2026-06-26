from typing import List, Dict


def calculate_score(answers: List[Dict[str, object]], correct_answers: List[str]) -> Dict[str, float]:
    total = len(answers)
    correct = sum(1 for answer, expected in zip(answers, correct_answers) if answer.get("selectedOption") == expected)
    percentage = (correct / total * 100) if total else 0.0
    return {
        "totalQuestions": total,
        "correctAnswers": correct,
        "wrongAnswers": total - correct,
        "percentage": round(percentage, 2),
    }
