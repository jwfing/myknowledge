"""Three-dimensional scoring algorithm for memory retrieval."""

import math
from datetime import datetime, timezone

from rememberit.config import settings


def calculate_score(
    similarity: float,
    importance: float,
    created_at: datetime,
) -> float:
    """
    Calculate final relevance score combining three dimensions:
      score = α × similarity + β × importance + γ × time_decay

    Where time_decay = e^(-λ × age_days)
    """
    age_days = (datetime.now(timezone.utc) - created_at).total_seconds() / 86400.0
    time_decay = math.exp(-settings.TIME_DECAY_LAMBDA * age_days)

    score = (
        settings.SCORE_WEIGHT_SEMANTIC * similarity
        + settings.SCORE_WEIGHT_IMPORTANCE * importance
        + settings.SCORE_WEIGHT_TIME * time_decay
    )
    return round(score, 4)
