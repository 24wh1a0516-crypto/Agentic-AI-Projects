from app.scorer import calculate_score


def test_calculate_score():
    result = calculate_score(
        [{"selectedOption": "A"}, {"selectedOption": "B"}],
        ["A", "C"],
    )
    assert result["correctAnswers"] == 1
    assert result["wrongAnswers"] == 1
    assert result["percentage"] == 50.0
