"""
IQ score calculation.

Maps a raw score (0-20 correct out of 20) to a standard IQ value and category label.
Distribution follows a rough normal curve around mean=100.
"""

import math

IQ_CATEGORIES = [
    (130, "Gifted / Very Superior"),
    (120, "Superior"),
    (110, "High Average"),
    (90,  "Average"),
    (80,  "Low Average"),
    (70,  "Below Average"),
    (0,   "Borderline"),
]

# Per-question difficulty weights
DIFFICULTY_WEIGHTS = {1: 1.0, 2: 1.5, 3: 2.0}


def calculate_iq(questions: list, answers: dict) -> dict:
    """
    questions  – list of question dicts (including 'correct' and 'difficulty')
    answers    – {question_id: chosen_option, ...}

    Returns a dict with iq_score, category, correct_count, total, breakdown.
    """
    total_weight   = 0.0
    earned_weight  = 0.0
    correct_count  = 0
    breakdown: dict[str, dict] = {}

    for q in questions:
        qid        = q["id"]
        difficulty = q.get("difficulty", 1)
        weight     = DIFFICULTY_WEIGHTS.get(difficulty, 1.0)
        total_weight += weight

        chosen   = answers.get(qid, "")
        is_right = chosen == q["correct"]

        if is_right:
            earned_weight += weight
            correct_count += 1

        cat = q["category"]
        if cat not in breakdown:
            breakdown[cat] = {"correct": 0, "total": 0}
        breakdown[cat]["total"]   += 1
        breakdown[cat]["correct"] += int(is_right)

    # Weighted percentage → IQ range 60–145
    ratio    = earned_weight / total_weight if total_weight > 0 else 0
    # Sigmoid-like mapping: low scorers cluster around 85, high around 135
    raw_iq   = 60 + (ratio ** 0.7) * 85
    iq_score = int(round(raw_iq))

    category = "Borderline"
    for threshold, label in IQ_CATEGORIES:
        if iq_score >= threshold:
            category = label
            break

    # Percentile approximation (normal distribution with mean=100, sd=15)
    z         = (iq_score - 100) / 15
    percentile = _normal_cdf(z) * 100
    percentile = max(1, min(99, round(percentile)))

    return {
        "iq_score":     iq_score,
        "category":     category,
        "percentile":   percentile,
        "correct_count": correct_count,
        "total":        len(questions),
        "breakdown":    breakdown,
    }


def _normal_cdf(z: float) -> float:
    """Approximation of the standard normal CDF using math.erf."""
    return (1.0 + math.erf(z / math.sqrt(2))) / 2.0
