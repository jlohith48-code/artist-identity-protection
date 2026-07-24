# 🎵 Artist Identity & Ownership Protection System


# 🎵 Artist Identity & Ownership Protection System


A full-stack platform combining cryptographic ownership verification with machine learning-based fraud detection, built to protect independent lyricists and musicians from identity theft and streaming fraud on platforms like Spotify.

## 💡 The Story Behind This Project

This project was inspired by a real incident within my family. A lyricist with over 15 years of experience and 300+ published songs discovered that a fraudulent Spotify profile had been created using his identity — accumulating over 300,000 monthly listeners without his knowledge or consent. While his authorship was never in dispute (his name is credited through production houses and YouTube), there was no system in place to prevent someone else from hijacking his platform presence and streaming revenue.

This exposed a real, industry-wide gap: platforms like Spotify don't verify songwriter identity before generating an artist profile, and there's no accessible tool for independent artists to (1) create timestamped proof of authorship the moment they write something, or (2) detect when their identity is being impersonated elsewhere.

## 🎯 What This System Does

1. **Ownership Registry** — Artists register songs with cryptographic (SHA-256) proof of authorship, timestamped at registration. Duplicate detection automatically blocks exact re-registration of the same lyrics under a different name.
2. **Semantic Similarity Detection** — Beyond exact matches, the system detects paraphrased or partially reworded lyrics using vectorized text similarity (cosine similarity on hashed text vectors), without ever storing the original raw lyrics.
3. **ML-Powered Fraud Detection** — Platform profiles are scored for impersonation risk using a trained Random Forest classifier and an Isolation Forest anomaly detector, based on engineered features (name similarity, catalog velocity, growth velocity, metadata completeness).
4. **Fraud Dashboard** — Visual dashboard showing risk distribution and flagged accounts, highlighting patterns like the "high listeners, low followers" signature typical of bot-driven streaming fraud.
5. **Impersonation Reporting** — Artists can file structured reports against profiles flagged by the model, closing the loop between detection and action.

## 🏗️ Architecture

**Backend:** FastAPI (Python) + PostgreSQL + SQLAlchemy + Alembic migrations
**Frontend:** Streamlit
**ML:** scikit-learn (Random Forest, Isolation Forest), pandas, HashingVectorizer for text similarity

**Database schema:** Artists to Songs (with ownership hash + similarity vector) to Artist Profiles (platform presence) to Fraud Scores (ML output) to Impersonation Reports

## 🤖 Machine Learning Approach

Since real-world platform fraud data isn't publicly available (for good reason - privacy and platform security), a synthetic dataset was generated using Faker, deliberately engineered with realistic fraud signatures based on documented 2026 Spotify impersonation patterns:

- Legitimate profiles: consistent naming, organic listener-to-follower ratios, account creation predating their song catalog (with some realistic exceptions - e.g., artists who join a platform late with their full back-catalog)
- Fraudulent profiles: subtly altered names (e.g., "Official" suffixes, character swaps), disproportionate listener-to-follower ratios (a bot-fraud signature), and rapid catalog accumulation on newly created accounts

Features engineered:
- Name similarity (fuzzy string matching)
- Catalog velocity (songs claimed per day since account creation - replacing a naive "account age" feature that incorrectly penalized artists who legitimately join platforms late)
- Growth velocity (listener-to-follower ratio)
- Metadata completeness

Models trained and compared:
- Isolation Forest (unsupervised anomaly detection): 94% accuracy, 84% recall on fraud cases
- Random Forest (supervised classification): Mean F1 of 0.978 across 5-fold cross-validation

An initial Random Forest run scored a suspicious 100% accuracy - investigated and traced to overly clean synthetic data separability, not genuine model performance. Fixed by introducing realistic noise (late-joining legitimate artists, more "patient" fraud accounts) and validating with cross-validation instead of a single train/test split, which better reflects a defensible real-world evaluation approach given the modest dataset size.

Known limitation: the text similarity feature uses bag-of-words hashing, which captures structural paraphrasing but underweights synonym-level rewording. A future iteration could use sentence embeddings (e.g., sentence-transformers) for genuine semantic similarity.

## 🚀 Running This Project

Backend:

    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Frontend:

    cd frontend
    streamlit run app.py

Requires a local PostgreSQL database named artist_protection and a .env file with DATABASE_URL configured.

## 📌 Future Improvements

- Sentence embedding-based similarity for stronger paraphrase detection
- LLM-generated plain-English fraud explanations for non-technical users
- Real Spotify public API integration for legitimate-profile baseline comparisons
- Multi-platform support beyond Spotify

## 👤 Author

Built by Lohith J as a placement-ready project combining full-stack development, applied machine learning, and a real-world problem statement.


