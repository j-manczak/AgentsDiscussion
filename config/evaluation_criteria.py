import math


EVALUATION_CRITERIA: tuple[tuple[str, float], ...] = (
    ("Individual skill and technique", 0.20),
    ("Statistics and achievements", 0.20),
    ("Team impact and contribution to team play", 0.15),
    ("Peak performance", 0.15),
    ("Longevity and consistency", 0.10),
    ("Performance in the most important matches", 0.10),
    ("Historical impact on football", 0.10),
)

TIE_THRESHOLD = 0.15

if not math.isclose(sum(weight for _, weight in EVALUATION_CRITERIA), 1.0):
    raise ValueError("Evaluation criterion weights must sum to 1.0.")
