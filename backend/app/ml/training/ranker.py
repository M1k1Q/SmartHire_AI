"""
ml/training/ranker.py
Candidate ranking system based on:
  - Cosine similarity between resume TF-IDF and job description TF-IDF
  - Experience year weighting bonus
  - Skill overlap bonus

Returns a ranked list of candidates with composite scores.
"""
import logging
from typing import List, Dict

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Weight constants for composite ranking score
# Weight constants for composite ranking score
SIMILARITY_WEIGHT = 0.40    # TF-IDF cosine similarity (was 0.70)
EXPERIENCE_WEIGHT = 0.20    # Normalized experience years (was 0.15)
SKILL_WEIGHT      = 0.40    # Skill overlap ratio (was 0.15)


def compute_cosine_similarity(resume_vector, job_vector) -> float:
    """
    Compute cosine similarity between a resume vector and a job description vector.

    Args:
        resume_vector: Sparse or dense vector for the resume.
        job_vector: Sparse or dense vector for the job description.

    Returns:
        Float in [0.0, 1.0]
    """
    try:
        sim = cosine_similarity(resume_vector, job_vector)
        return float(np.clip(sim[0][0], 0.0, 1.0))
    except Exception as e:
        logger.error(f"Cosine similarity computation failed: {e}")
        return 0.0


def compute_skill_overlap(candidate_skills: List[str], required_skills: List[str]) -> float:
    """
    Compute ratio of required job skills found in candidate's resume.

    Returns:
        Float in [0.0, 1.0] (1.0 = all required skills matched)
    """
    if not required_skills:
        return 0.5  # Neutral if no skills specified
    candidate_lower = {s.lower() for s in candidate_skills}
    required_lower = {s.lower() for s in required_skills}
    if not required_lower:
        return 0.5
    matched = candidate_lower.intersection(required_lower)
    return len(matched) / len(required_lower)


def normalize_experience(years: float, max_years: float = 20.0) -> float:
    """Normalize experience years to [0.0, 1.0] range."""
    return float(np.clip(years / max_years, 0.0, 1.0))


def compute_composite_score(
    similarity: float,
    experience_years: float,
    candidate_skills: List[str],
    required_skills: List[str],
) -> float:
    """
    Compute a weighted composite ranking score.

    Formula:
        score = (sim * 0.70) + (norm_exp * 0.15) + (skill_overlap * 0.15)

    Returns:
        Float in [0.0, 1.0]
    """
    skill_score = compute_skill_overlap(candidate_skills, required_skills)
    exp_score = normalize_experience(experience_years)
    composite = (
        SIMILARITY_WEIGHT * similarity
        + EXPERIENCE_WEIGHT * exp_score
        + SKILL_WEIGHT * skill_score
    )
    return round(float(np.clip(composite, 0.0, 1.0)), 4)


def rank_candidates(candidates: List[Dict], job_description: str, vectorizer, required_skills: List[str]) -> List[Dict]:
    """
    Rank a list of candidates against a job description.

    Args:
        candidates: List of dicts with 'resume_text', 'experience_years', 'skills', 'id'.
        job_description: Raw job description text.
        vectorizer: Fitted TF-IDF vectorizer.
        required_skills: List of required skill strings from the job posting.

    Returns:
        Candidates list sorted by composite score descending, each enriched with
        'rank_score', 'similarity', 'skill_overlap', 'rank'.
    """
    if not candidates:
        return []

    # Vectorize job description
    from ..preprocessing.nlp_pipeline import preprocess_text
    job_text_processed = preprocess_text(job_description)
    job_vector = vectorizer.transform([job_text_processed])

    scored = []
    for candidate in candidates:
        resume_text = candidate.get("resume_text", "")
        processed = preprocess_text(resume_text)
        resume_vector = vectorizer.transform([processed])

        sim = compute_cosine_similarity(resume_vector, job_vector)
        skill_overlap = compute_skill_overlap(
            candidate.get("skills", []), required_skills
        )
        exp_years = candidate.get("experience_years", 0.0)
        composite = compute_composite_score(sim, exp_years, candidate.get("skills", []), required_skills)

        scored.append({
            **candidate,
            "similarity": round(sim, 4),
            "skill_overlap": round(skill_overlap, 4),
            "rank_score": composite,
        })

    # Sort by composite score descending
    scored.sort(key=lambda x: x["rank_score"], reverse=True)

    # Assign ranks
    for i, c in enumerate(scored):
        c["rank"] = i + 1

    logger.info(f"Ranked {len(scored)} candidates.")
    return scored
