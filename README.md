# Smart Recruitment & Candidate Evaluation Platform

An end-to-end AI-powered hiring solution featuring automated resume parsing, skill-based candidate ranking, population clustering, and algorithmic fairness auditing.

## 🚀 Key Features

-   **AI-Powered Resume Parsing**: Extraction of skills, experience, and education from PDF and DOCX files.
-   **Intelligent Ranking**: Advanced matching system using TF-IDF and Cosine Similarity to find the best fit for specific job roles.
-   **Predictive Classification**: Machine Learning models (Random Forest, SVM) trained to predict candidate suitability.
-   **Talent Clustering**: Unsupervised K-Means clustering with t-SNE 2D visualization to group candidates by skill pools.
-   **Fairness Auditing**: Built-in bias detection reports and blind screening principles.
-   **Modern Dashboards**: Real-time HR and Candidate interfaces built with React and Glassmorphism design.

## 🛠️ Technology Stack

-   **Backend**: Flask (Python), MongoDB (Database), JWT (Auth).
-   **Machine Learning**: Scikit-Learn, spaCy, NLTK, SHAP, Imbalanced-Learn (SMOTE).
-   **Frontend**: React, Recharts (Data Viz), Lucide Icons, Axios.
-   **Styling**: Vanilla CSS (Rich Dark Fluid Design).

## 📦 Installation & Setup

### Prerequisites
-   Python 3.9+
-   Node.js 18+
-   MongoDB (Running locally on default port 27017)

### Backend Setup
1.  `cd backend`
2.  `python -m venv venv`
3.  `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4.  `pip install -r requirements.txt`
5.  `python run.py` (Runs on http://localhost:5000)

### Frontend Setup
1.  `cd frontend`
2.  `npm install`
3.  `npm start` (Runs on http://localhost:3000)

## 📁 Project Structure

```text
├── backend/
│   ├── app/
│   │   ├── auth/          # Authentication & RBAC
│   │   ├── ml/            # NLP, Classifiers, Clusterer, Metrics
│   │   ├── models/        # MongoDB document helpers
│   │   ├── routes/        # API endpoints
│   │   └── services/      # Business logic & Pipeline bridge
│   └── tests/             # Pytest unit tests
├── frontend/
│   ├── src/
│   │   ├── components/    # Shared UI & Charts
│   │   ├── pages/         # Dashboard & Auth views
│   │   └── api/           # Axios configuration
└── docs/                  # API, ML, and UML Documentation
```

## ⚖️ Ethics & Fairness
This platform implements **Blind Screening** by excluding sensitive demographic data from models. It uses **SHAP** values for transparency and **SMOTE** to handle class imbalance, ensuring a fair and technical evaluation for every applicant.

---
*Created by the SmartHire AI Engineering Team*
