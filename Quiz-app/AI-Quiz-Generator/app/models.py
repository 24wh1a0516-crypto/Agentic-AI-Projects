from dataclasses import dataclass
from typing import List


@dataclass
class QuizQuestion:
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str
