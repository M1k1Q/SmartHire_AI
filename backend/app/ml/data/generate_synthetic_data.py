"""
ml/data/generate_synthetic_data.py
Generates a synthetic labeled resume dataset for training and demo purposes.

Each sample is a realistic-looking resume text with:
  - Skills from a predefined pool
  - Experience years
  - Education level
  - Job roles

Labels are generated based on skill overlap ratio with a target job profile.

Usage:
    from app.ml.data.generate_synthetic_data import generate_synthetic_dataset
    docs, labels, metadata = generate_synthetic_dataset(n_samples=200)
"""
import random
from typing import List, Tuple

random.seed(42)

# ---------------------------------------------------------------------------
# Vocabulary pools
# ---------------------------------------------------------------------------

SKILL_POOL = {
    "tech": [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "Go", "Rust",
        "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
        "SQL", "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes",
        "AWS", "Azure", "GCP", "Git", "Linux", "Bash", "REST APIs", "GraphQL",
    ],
    "ml": [
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
        "scikit-learn", "TensorFlow", "PyTorch", "Keras", "Pandas", "NumPy",
        "Matplotlib", "BERT", "Transformers", "Feature Engineering",
        "Model Evaluation", "Data Preprocessing", "Statistical Analysis",
        "Random Forest", "SVM", "Logistic Regression", "XGBoost",
    ],
    "data": [
        "SQL", "Excel", "Tableau", "Power BI", "Spark", "Hadoop",
        "ETL Pipelines", "Data Modeling", "Data Warehousing", "BigQuery",
    ],
    "soft": [
        "Team Leadership", "Communication", "Problem Solving", "Agile",
        "Scrum", "Project Management", "Critical Thinking", "Collaboration",
    ],
}

UNIVERSITIES = [
    "MIT", "Stanford University", "Harvard University", "Carnegie Mellon University",
    "University of California", "Georgia Tech", "University of Toronto",
    "Imperial College London", "FAST-NUCES", "LUMS", "IIT Bombay",
    "National University", "Punjab University",
]

COMPANIES = [
    "Google", "Microsoft", "Amazon", "Meta", "Apple", "IBM", "Accenture",
    "TechCorp", "DataSystems Inc.", "InnovateTech", "Startup Hub",
    "NeuralSoft", "CloudBase", "Analytics Pro",
]

JOB_ROLES = [
    "Software Engineer", "Data Scientist", "ML Engineer", "Backend Developer",
    "Full Stack Developer", "Data Analyst", "DevOps Engineer",
    "Research Scientist", "AI Engineer", "Systems Architect",
]

DEGREES = ["B.Sc. Computer Science", "B.E. Software Engineering", "M.Sc. Data Science",
           "B.Sc. Mathematics", "M.Sc. Artificial Intelligence", "PhD Computer Science"]

# Target skills that define a "suitable" candidate (default)
TARGET_SKILLS = {
    "Python", "Machine Learning", "scikit-learn", "NLP", "SQL",
    "Flask", "REST APIs", "Docker", "Git", "Data Preprocessing",
}


def _generate_resume(skills: List[str], experience_years: int, index: int, name_hint: str = None) -> str:
    """Generate a realistic synthetic resume text."""
    name = name_hint if name_hint else f"Candidate_{index:03d}"
    university = random.choice(UNIVERSITIES)
    degree = random.choice(DEGREES)
    company1 = random.choice(COMPANIES)
    company2 = random.choice(COMPANIES)
    role1 = random.choice(JOB_ROLES)
    role2 = random.choice(JOB_ROLES)

    skills_str = ", ".join(skills)

    template = f"""
{name}
Email: candidate{index}@email.com | Phone: +1-555-{random.randint(1000,9999)}

SUMMARY
Experienced {role1} with {experience_years} years of experience in software development
and data engineering. Passionate about building scalable systems and ML solutions.

EDUCATION
{degree} — {university} ({2024 - experience_years - random.randint(0,2)})
GPA: {random.uniform(2.8, 4.0):.2f}/4.0

EXPERIENCE
{role1} — {company1} ({experience_years - random.randint(0, min(experience_years,2))} - {experience_years} years)
- Developed and maintained production systems using {random.choice(skills) if skills else 'various tools'}
- Collaborated with cross-functional teams using Agile/Scrum methodology
- Improved system performance by {random.randint(10,50)}%

{role2} — {company2} (Internship / Junior Role)
- Built REST APIs and integrated third-party services
- Worked on data pipelines and reporting dashboards

TECHNICAL SKILLS
{skills_str}

CERTIFICATIONS
- {random.choice(['AWS Certified Developer', 'Google Cloud Professional', 'TensorFlow Developer Certificate', 'Python Institute PCEP', 'Scrum Master Certified'])}

PROJECTS
- {random.choice(['Sentiment Analysis Engine', 'Resume Parser', 'E-commerce Platform', 'ML Pipeline Framework', 'Real-time Chat Application', 'Fraud Detection System'])}
  Technologies: {", ".join(random.sample(skills, min(3, len(skills))))}
"""
    return template.strip()


def generate_synthetic_dataset(n_samples: int = 200, target_skills: set = None) -> Tuple[List[str], List[int], List[dict]]:
    """
    Generate a synthetic labeled resume dataset.

    Labeling strategy:
      - suitable (1) if ≥ 40% of target_skills appear in candidate's skills
      - not suitable (0) otherwise

    Args:
        n_samples: Number of resume samples to generate.
        target_skills: Set of skills to aim for (defaults to TARGET_SKILLS).

    Returns:
        Tuple of (documents: List[str], labels: List[int], metadata: List[dict])
    """
    if target_skills is None:
        target_skills = TARGET_SKILLS

    documents = []
    labels = []
    metadata = []

    all_skills = SKILL_POOL["tech"] + SKILL_POOL["ml"] + SKILL_POOL["data"] + SKILL_POOL["soft"]

    for i in range(n_samples):
        # Randomly select 6-18 skills
        n_skills = random.randint(6, 18)
        
        # Mix in target skills if we want a suitable candidate (coin flip)
        is_suitable_attempt = random.random() < 0.6
        if is_suitable_attempt and target_skills:
            # Pick majority of target skills
            sampled_target = random.sample(list(target_skills), k=min(len(target_skills), random.randint(4, 10)))
            # Pad with other skills
            padding_skills = random.sample(all_skills, max(0, n_skills - len(sampled_target)))
            skills = list(set(sampled_target + padding_skills))
        else:
            skills = random.sample(all_skills, n_skills)
            
        experience_years = random.randint(0, 12)

        # Determine label by skill overlap with target
        target_match = len(set(s.lower() for s in skills) & {t.lower() for t in target_skills})
        overlap_ratio = target_match / len(target_skills) if target_skills else 0.5

        # Add some noise to avoid perfect separation
        noise = random.uniform(-0.1, 0.1)
        effective_overlap = overlap_ratio + noise

        label = 1 if effective_overlap >= 0.35 else 0

        resume_text = _generate_resume(skills, experience_years, i)
        documents.append(resume_text)
        labels.append(label)
        metadata.append({
            "index": i,
            "skills": skills,
            "experience_years": experience_years,
            "overlap_ratio": round(overlap_ratio, 3),
            "label": label,
        })

    suitable_count = sum(labels)
    print(f"Generated {n_samples} samples: {suitable_count} suitable, {n_samples - suitable_count} not suitable.")
    return documents, labels, metadata


if __name__ == "__main__":
    # Run standalone to preview generated data
    docs, labels, meta = generate_synthetic_dataset(n_samples=10)
    for i, (doc, label) in enumerate(zip(docs, labels)):
        print(f"\n--- Sample {i} | Label: {'Suitable' if label else 'Not Suitable'} ---")
        print(doc[:300])
        print("...")
