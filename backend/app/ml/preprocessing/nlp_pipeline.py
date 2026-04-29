"""
ml/preprocessing/nlp_pipeline.py
Full NLP processing pipeline:
  1. Tokenization
  2. Stopword removal
  3. Lemmatization (spaCy)
  4. NER: skills, organizations, experience years
  5. TF-IDF vectorization (with bigrams)
  6. Bag-of-Words comparison utility
"""
import re
import logging
from typing import List, Dict, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Skill keyword dictionary for rule-based NER fallback
# ---------------------------------------------------------------------------
SKILL_KEYWORDS = [
    # Programming
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "swift", "kotlin", "ruby", "php", "scala", "r",
    # Web
    "react", "angular", "vue", "node", "express", "django", "flask", "fastapi",
    "html", "css", "sass", "rest", "graphql",
    # Data / ML
    "machine learning", "deep learning", "nlp", "natural language processing",
    "scikit-learn", "tensorflow", "pytorch", "keras", "pandas", "numpy",
    "matplotlib", "seaborn", "sql", "nosql", "mongodb", "postgresql", "mysql",
    "spark", "hadoop", "tableau", "power bi", "excel",
    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "ci/cd", "git",
    "linux", "bash",
    # Soft skills
    "communication", "teamwork", "leadership", "problem solving", "agile", "scrum",
]

EXPERIENCE_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)",
    re.IGNORECASE,
)


def preprocess_text(text: str, use_spacy: bool = True) -> str:
    """
    Full NLP preprocessing:
      - Lowercase
      - Remove URLs, emails, special chars
      - Tokenize → remove stopwords → lemmatize

    Args:
        text: Raw resume text.
        use_spacy: Whether to use spaCy for lemmatization (fallback: simple split).

    Returns:
        Preprocessed text string (space-joined tokens).
    """
    if not text:
        return ""

    # Lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)
    # Remove email addresses
    text = re.sub(r"\S+@\S+", "", text)
    # Remove non-alphanumeric except spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if use_spacy:
        tokens = _spacy_lemmatize(text)
    else:
        tokens = _simple_tokenize(text)

    return " ".join(tokens)


def _spacy_lemmatize(text: str) -> List[str]:
    """Tokenize and lemmatize using spaCy; remove stopwords."""
    try:
        import spacy
        # Load small English model (en_core_web_sm must be installed)
        nlp = _get_spacy_model()
        doc = nlp(text)
        return [
            token.lemma_
            for token in doc
            if not token.is_stop and not token.is_punct and len(token.lemma_) > 2
        ]
    except Exception as e:
        logger.warning(f"spaCy unavailable, falling back to simple tokenizer: {e}")
        return _simple_tokenize(text)


_spacy_nlp_cache = None


def _get_spacy_model():
    """Load and cache the spaCy model."""
    global _spacy_nlp_cache
    if _spacy_nlp_cache is None:
        import spacy
        try:
            _spacy_nlp_cache = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("en_core_web_sm not found. Run: python -m spacy download en_core_web_sm")
            # Use blank model as fallback
            _spacy_nlp_cache = spacy.blank("en")
    return _spacy_nlp_cache


def _simple_tokenize(text: str) -> List[str]:
    """Fallback tokenizer using NLTK stopwords."""
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        try:
            stop_words = set(stopwords.words("english"))
        except LookupError:
            nltk.download("stopwords", quiet=True)
            nltk.download("wordnet", quiet=True)
            stop_words = set(stopwords.words("english"))
        lemmatizer = WordNetLemmatizer()
        tokens = text.split()
        return [
            lemmatizer.lemmatize(t)
            for t in tokens
            if t not in stop_words and len(t) > 2
        ]
    except Exception:
        return [t for t in text.split() if len(t) > 2]


# ---------------------------------------------------------------------------
# Named Entity Recognition (NER)
# ---------------------------------------------------------------------------

def extract_entities(text: str) -> Dict:
    """
    Extract structured entities from resume text:
      - skills: matched against SKILL_KEYWORDS
      - organizations: spaCy ORG entities
      - experience_years: regex pattern

    Returns:
        dict with keys 'skills', 'organizations', 'experience_years'
    """
    lower_text = text.lower()
    entities = {
        "skills": [],
        "organizations": [],
        "experience_years": 0.0,
    }

    # Skills: rule-based keyword matching
    found_skills = []
    for skill in SKILL_KEYWORDS:
        if re.search(r"\b" + re.escape(skill) + r"\b", lower_text):
            found_skills.append(skill)
    entities["skills"] = found_skills

    # Experience years: regex
    matches = EXPERIENCE_PATTERN.findall(text)
    if matches:
        entities["experience_years"] = max(float(m) for m in matches)

    # Organizations: spaCy NER
    try:
        nlp = _get_spacy_model()
        if nlp.pipe_names:  # real model, not blank
            doc = nlp(text[:5000])  # limit for speed
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            entities["organizations"] = list(set(orgs))[:10]
    except Exception as e:
        logger.debug(f"NER org extraction failed: {e}")

    return entities


# ---------------------------------------------------------------------------
# TF-IDF Vectorizer (fit + transform)
# ---------------------------------------------------------------------------

def build_tfidf_vectorizer(documents: List[str], ngram_range=(1, 2), max_features=5000):
    """
    Fit a TF-IDF vectorizer on a corpus of documents.

    Args:
        documents: List of preprocessed text strings.
        ngram_range: Tuple (min_n, max_n) for n-grams.
        max_features: Maximum vocabulary size.

    Returns:
        Tuple of (fitted TfidfVectorizer, feature matrix as np.ndarray)
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(
        ngram_range=ngram_range,
        max_features=max_features,
        sublinear_tf=True,          # Apply log normalization to TF
        strip_accents="unicode",
        analyzer="word",
        min_df=1,
    )
    matrix = vectorizer.fit_transform(documents)
    return vectorizer, matrix


def transform_with_vectorizer(vectorizer, documents: List[str]):
    """Transform new documents using a fitted TF-IDF vectorizer."""
    return vectorizer.transform(documents)


# ---------------------------------------------------------------------------
# Bag-of-Words comparison (BoW vs TF-IDF)
# ---------------------------------------------------------------------------

def build_bow_vectorizer(documents: List[str], max_features=5000):
    """
    Fit a BoW (CountVectorizer) for comparison against TF-IDF.

    Returns:
        Tuple of (fitted CountVectorizer, feature matrix)
    """
    from sklearn.feature_extraction.text import CountVectorizer

    vectorizer = CountVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        min_df=1,
        strip_accents="unicode",
    )
    matrix = vectorizer.fit_transform(documents)
    return vectorizer, matrix


def compare_bow_vs_tfidf(corpus: List[str]) -> Dict:
    """
    Compare BoW and TF-IDF statistics on a corpus.

    Returns:
        dict with vocabulary sizes and top terms for each method.
    """
    _, tfidf_matrix = build_tfidf_vectorizer(corpus)
    bow_vec, bow_matrix = build_bow_vectorizer(corpus)

    return {
        "bow_vocab_size": bow_matrix.shape[1],
        "tfidf_vocab_size": tfidf_matrix.shape[1],
        "bow_matrix_shape": list(bow_matrix.shape),
        "tfidf_matrix_shape": list(tfidf_matrix.shape),
        "top_bow_terms": bow_vec.get_feature_names_out()[:20].tolist(),
    }
