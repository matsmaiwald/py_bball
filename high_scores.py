from operator import itemgetter
from datetime import date
import pickle


def load_high_scores(path: str = "high_scores.txt") -> list:

    with open(path, "rb") as f:
        high_scores = pickle.load(f)
    return high_scores


def update_high_scores(high_scores: list, current_score: int) -> list:

    high_scores.append((current_score, date.today()))
    high_scores = sorted(high_scores, key=itemgetter(0), reverse=True)[:10]
    return high_scores


def save_high_scores(high_scores: list, path: str = "high_scores.txt"):
    with open(path, "wb") as f:
        pickle.dump(high_scores, f)

