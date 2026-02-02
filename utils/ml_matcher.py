from typing import Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def tfidf_similarity(text_a: str, text_b: str) -> float:
    if not text_a or not text_b:
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform([text_a, text_b])
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return round(float(score) * 100, 2)


def match_skills(
    resume_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str],
) -> Tuple[List[str], List[str]]:
    resume_set = {s.lower() for s in resume_skills}
    required_set = {s.lower() for s in required_skills}
    preferred_set = {s.lower() for s in preferred_skills}

    matched = sorted({s for s in resume_set if s in required_set or s in preferred_set})
    missing = sorted({s for s in required_set if s not in resume_set})
    return matched, missing


def skill_match_score(
    resume_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str],
) -> float:
    if not required_skills and not preferred_skills:
        return 0.0

    resume_set = {s.lower() for s in resume_skills}
    required_set = {s.lower() for s in required_skills}
    preferred_set = {s.lower() for s in preferred_skills}

    required_hits = len(required_set & resume_set)
    preferred_hits = len(preferred_set & resume_set)

    required_score = required_hits / max(len(required_set), 1)
    preferred_score = preferred_hits / max(len(preferred_set), 1)

    # Emphasize required skills more.
    final_score = (0.7 * required_score + 0.3 * preferred_score) * 100
    return round(final_score, 2)

