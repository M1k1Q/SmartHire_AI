"""
tests/test_ml_pipeline.py
Unit tests for the ML pipeline components.
"""
import pytest
import numpy as np


class TestResumeParser:
    def test_clean_text(self):
        from app.ml.preprocessing.resume_parser import _clean_text
        raw = "Hello\t  World\r\n\n\nTest"
        result = _clean_text(raw)
        assert "Hello" in result
        assert "World" in result
        assert "\t" not in result
        assert "\r" not in result

    def test_parse_nonexistent_file(self):
        from app.ml.preprocessing.resume_parser import parse_resume
        with pytest.raises(FileNotFoundError):
            parse_resume("/nonexistent/path/resume.pdf")

    def test_unsupported_extension(self, tmp_path):
        from app.ml.preprocessing.resume_parser import parse_resume
        fake_file = tmp_path / "resume.txt"
        fake_file.write_text("test content")
        with pytest.raises(ValueError, match="Unsupported"):
            parse_resume(str(fake_file))


class TestNLPPipeline:
    def test_preprocess_text_basic(self):
        from app.ml.preprocessing.nlp_pipeline import preprocess_text
        text = "I am a Python developer with 5 years of experience."
        result = preprocess_text(text, use_spacy=False)
        assert isinstance(result, str)
        assert "python" in result.lower() or "develop" in result.lower()

    def test_preprocess_removes_urls(self):
        from app.ml.preprocessing.nlp_pipeline import preprocess_text
        text = "Visit https://example.com for details"
        result = preprocess_text(text, use_spacy=False)
        assert "http" not in result
        assert "example" not in result

    def test_extract_entities_skills(self):
        from app.ml.preprocessing.nlp_pipeline import extract_entities
        text = "Experienced in Python, machine learning, and Docker deployments."
        entities = extract_entities(text)
        assert "python" in entities["skills"]
        assert "machine learning" in entities["skills"]
        assert "docker" in entities["skills"]

    def test_extract_experience_years(self):
        from app.ml.preprocessing.nlp_pipeline import extract_entities
        text = "I have 7 years of experience in software development."
        entities = extract_entities(text)
        assert entities["experience_years"] == 7.0

    def test_tfidf_vectorizer_shape(self):
        from app.ml.preprocessing.nlp_pipeline import build_tfidf_vectorizer
        docs = ["python machine learning", "java web development", "data science numpy"]
        vectorizer, matrix = build_tfidf_vectorizer(docs)
        assert matrix.shape[0] == 3
        assert matrix.shape[1] > 0

    def test_bow_vectorizer(self):
        from app.ml.preprocessing.nlp_pipeline import build_bow_vectorizer
        docs = ["python developer", "java engineer", "data analyst"]
        _, matrix = build_bow_vectorizer(docs)
        assert matrix.shape[0] == 3


class TestClassifier:
    @pytest.fixture
    def sample_data(self):
        """Generate small labelled dataset."""
        from app.ml.data.generate_synthetic_data import generate_synthetic_dataset
        from app.ml.preprocessing.nlp_pipeline import preprocess_text, build_tfidf_vectorizer
        docs, labels, _ = generate_synthetic_dataset(n_samples=60)
        processed = [preprocess_text(d, use_spacy=False) for d in docs]
        vectorizer, X = build_tfidf_vectorizer(processed)
        return X, np.array(labels), vectorizer

    def test_logistic_regression_trains(self, sample_data):
        from app.ml.training.classifier import train_classifier
        X, y, _ = sample_data
        clf, params, score = train_classifier(X, y, model_name="logistic_regression")
        assert clf is not None
        assert 0.0 <= score <= 1.0

    def test_random_forest_trains(self, sample_data):
        from app.ml.training.classifier import train_classifier
        X, y, _ = sample_data
        clf, params, score = train_classifier(X, y, model_name="random_forest")
        assert clf is not None

    def test_predict_returns_correct_shape(self, sample_data):
        from app.ml.training.classifier import train_classifier, predict
        X, y, _ = sample_data
        clf, _, _ = train_classifier(X, y, model_name="logistic_regression")
        preds, probs = predict(clf, X[:10])
        assert len(preds) == 10
        assert len(probs) == 10
        assert all(p in [0, 1] for p in preds)
        assert all(0.0 <= p <= 1.0 for p in probs)

    def test_save_and_load_classifier(self, tmp_path, sample_data):
        from app.ml.training.classifier import train_classifier, save_classifier, load_classifier
        X, y, _ = sample_data
        clf, _, _ = train_classifier(X, y, model_name="logistic_regression")
        path = str(tmp_path / "test_clf.pkl")
        save_classifier(clf, path)
        loaded = load_classifier(path)
        assert loaded is not None


class TestClusterer:
    def test_find_optimal_k(self):
        from app.ml.training.clusterer import find_optimal_k
        X = np.random.rand(30, 20)
        result = find_optimal_k(X, k_range=range(2, 6))
        assert "optimal_k" in result
        assert 2 <= result["optimal_k"] <= 5

    def test_kmeans_cluster(self):
        from app.ml.training.clusterer import kmeans_cluster
        X = np.random.rand(20, 10)
        labels, sil, model = kmeans_cluster(X, n_clusters=3)
        assert len(labels) == 20
        assert -1.0 <= sil <= 1.0

    def test_reduce_to_2d_pca(self):
        from app.ml.training.clusterer import reduce_to_2d
        X = np.random.rand(15, 50)
        coords = reduce_to_2d(X, method="pca")
        assert coords.shape == (15, 2)
