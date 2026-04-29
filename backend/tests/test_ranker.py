"""
tests/test_ranker.py
Unit tests for the candidate ranking system.
"""
import pytest
import numpy as np


class TestRanker:
    def test_cosine_similarity_identical_vectors(self):
        """Identical vectors should return similarity of 1.0."""
        from app.ml.training.ranker import compute_cosine_similarity
        from sklearn.feature_extraction.text import TfidfVectorizer
        vect = TfidfVectorizer()
        X = vect.fit_transform(["python machine learning"])
        sim = compute_cosine_similarity(X, X)
        assert abs(sim - 1.0) < 1e-6

    def test_cosine_similarity_different_vectors(self):
        """Completely different vocabulary should give low similarity."""
        from app.ml.training.ranker import compute_cosine_similarity
        from sklearn.feature_extraction.text import TfidfVectorizer
        vect = TfidfVectorizer()
        X = vect.fit_transform(["python machine learning", "cooking recipes kitchen"])
        sim = compute_cosine_similarity(X[0], X[1])
        assert sim < 0.1

    def test_skill_overlap_full_match(self):
        """All required skills present gives overlap of 1.0."""
        from app.ml.training.ranker import compute_skill_overlap
        candidate = ["python", "sql", "docker"]
        required = ["python", "sql", "docker"]
        assert compute_skill_overlap(candidate, required) == 1.0

    def test_skill_overlap_no_match(self):
        """No matching skills gives overlap of 0.0."""
        from app.ml.training.ranker import compute_skill_overlap
        assert compute_skill_overlap(["java"], ["python", "sql"]) == 0.0

    def test_skill_overlap_partial(self):
        """Partial match gives value between 0 and 1."""
        from app.ml.training.ranker import compute_skill_overlap
        val = compute_skill_overlap(["python", "java"], ["python", "sql", "docker"])
        assert 0.0 < val < 1.0

    def test_skill_overlap_empty_required(self):
        """Empty required skills returns neutral score 0.5."""
        from app.ml.training.ranker import compute_skill_overlap
        assert compute_skill_overlap(["python"], []) == 0.5

    def test_normalize_experience(self):
        from app.ml.training.ranker import normalize_experience
        assert normalize_experience(0) == 0.0
        assert normalize_experience(20) == 1.0
        assert 0 < normalize_experience(5) < 1

    def test_normalize_experience_capped(self):
        """Experience beyond max is capped at 1.0."""
        from app.ml.training.ranker import normalize_experience
        assert normalize_experience(100) == 1.0

    def test_composite_score_range(self):
        """Composite score must always be between 0 and 1."""
        from app.ml.training.ranker import compute_composite_score
        for _ in range(20):
            sim = np.random.random()
            exp = np.random.randint(0, 15)
            skills = ["python", "sql"]
            required = ["python", "docker", "machine learning"]
            score = compute_composite_score(sim, exp, skills, required)
            assert 0.0 <= score <= 1.0

    def test_rank_candidates_order(self):
        """Rank should assign rank=1 to the highest scoring candidate."""
        from app.ml.training.ranker import rank_candidates
        from app.ml.preprocessing.nlp_pipeline import build_tfidf_vectorizer, preprocess_text

        candidates = [
            {"id": "c1", "resume_text": "python machine learning data science nlp", "experience_years": 5, "skills": ["python", "machine learning"]},
            {"id": "c2", "resume_text": "cooking baking recipes kitchen restaurant", "experience_years": 1, "skills": ["cooking"]},
        ]
        job_desc = "We need a python machine learning engineer"
        required = ["python", "machine learning"]

        all_texts = [preprocess_text(c["resume_text"], use_spacy=False) for c in candidates] + [preprocess_text(job_desc, use_spacy=False)]
        vectorizer, _ = build_tfidf_vectorizer(all_texts)

        ranked = rank_candidates(candidates, job_desc, vectorizer, required)
        assert ranked[0]["id"] == "c1"  # Should rank the ML candidate first
        assert ranked[0]["rank"] == 1
        assert ranked[1]["rank"] == 2

    def test_rank_candidates_empty(self):
        """Empty candidates list returns empty list."""
        from app.ml.training.ranker import rank_candidates
        from app.ml.preprocessing.nlp_pipeline import build_tfidf_vectorizer
        _, vect = build_tfidf_vectorizer(["dummy text"])
        result = rank_candidates([], "job desc", vect, ["python"])
        assert result == []
