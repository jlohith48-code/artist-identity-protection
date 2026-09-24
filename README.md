# 🎵 Artist Identity & Ownership Protection System (v2.0)

A full-stack, enterprise-grade platform combining cryptographic timestamped registration, multi-stanza semantic vector search, YouTube ownership credit evidence, machine learning fraud risk scoring, and structured admin conflict resolution workflows to protect independent lyricists and musicians from identity theft, lyric plagiarism, and streaming royalty fraud.

---

## 💡 The Story Behind This Project

This project was inspired by a real incident within my family. A lyricist with over 15 years of experience and 300+ published songs discovered that a fraudulent Spotify profile had been created using his identity — accumulating over 300,000 monthly listeners without his knowledge or consent. While his authorship was never in dispute (his name is credited through production houses and YouTube), there was no system in place to prevent someone else from hijacking his platform presence and streaming revenue.

This exposed a real, industry-wide gap: platforms like Spotify don't verify songwriter identity before generating an artist profile, and there's no accessible tool for independent artists to (1) create timestamped proof of authorship the moment they write something, or (2) detect when their identity or lyrics are being impersonated or plagiarized elsewhere.

---

## 🎯 System Capabilities

1. **Cryptographic Ownership Registry**: Artists register songs with SHA-256 hashes of normalized lyrics, timestamped at registration. Exact duplicates are automatically detected and blocked (`HTTP 409 Conflict`).
2. **Semantic Lyric Similarity Engine**: Uses `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`) to compute 384-dimensional dense vector embeddings for whole songs and stanza chunks. Leverages native PostgreSQL **`pgvector` with HNSW cosine distance indexing (`Vector(384)`)** for sub-linear nearest-neighbor similarity search. Supports regional Indic scripts (Kannada, Hindi, Tamil, Telugu) and cross-lingual matching.
3. **Decoupled Service Layer**: Clear separation of concerns between API Controllers (`app/routes/`) and Business Services (`app/services/`):
   - `SongService`: Atomic song creation, SHA-256 checks, vector storage, and automatic similarity conflict detection.
   - `EvidenceService`: External credit evidence management, status transitions, and reviewer attribution.
   - `ReportService`: Impersonation report creation and conflict linking.
   - `ConflictService`: Deduplicated `OwnershipConflict` lifecycle, state machine, and reviewer resolution.
   - `SimilarityService`: SentenceTransformers model caching, deterministic normalization, verse chunking, and pgvector query execution.
4. **OwnershipConflict Resolution Domain**: Automatically connects high-similarity signals ($\ge 0.70$), confirmed external credit evidence, and impersonation reports into an auditable conflict lifecycle:
   - State machine: `detected` / `pending_review` $\rightarrow$ `under_review` $\rightarrow$ `confirmed` / `rejected` $\rightarrow$ `resolved`.
   - Reviewer attribution (`reviewed_by_user_id`, `reviewed_at`) for admin auditability.
5. **ML-Powered Fraud Risk Scoring**: Platform profiles are evaluated for impersonation risk using a trained Random Forest classifier and engineered features (name similarity, catalog velocity, listener-to-follower ratio, metadata completeness).
6. **JWT Authentication & IDOR Hardening**: Native `bcrypt` password hashing, signed JWT Bearer tokens, artist self-ownership verification (`sub == artist_id`), and role-based access control (`require_admin` for resolution routes).

---

## 🏗️ Architecture & Technology Stack

```text
[Streamlit Frontend UI]
          │  (HTTP REST + Bearer JWT)
          ▼
[FastAPI Backend Gateway]
   ├── Auth & Security (JWT, bcrypt, IDOR Guard)
   └── Service Layer (app/services/)
          ├── SongService
          ├── EvidenceService
          ├── ReportService
          ├── ConflictService
          └── SimilarityService
                 ├── sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
                 └── PostgreSQL pgvector (HNSW Index Vector(384))
```

- **Backend**: FastAPI (Python 3.13) + SQLAlchemy + Alembic Migrations + PyTorch + sentence-transformers
- **Database**: PostgreSQL 15 with `pgvector` extension (`pgvector/pgvector:pg15` container image)
- **Frontend**: Streamlit
- **ML / Data Science**: scikit-learn (Random Forest), NumPy, PyTorch

---

## 🚀 Docker Quickstart

Run the complete containerized stack (PostgreSQL with `pgvector`, FastAPI backend, Streamlit frontend):

```bash
docker-compose up --build
```

- **Backend API**: http://localhost:8000
- **Frontend Ledger UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs

---

## 🧪 Testing & Verification

Run the complete automated test suite (20 unit, similarity, security regression, and service layer tests):

```bash
cd backend
python tests/run_tests.py
python tests/test_security_regression.py
python tests/test_similarity.py
python tests/test_phase3_services_and_conflicts.py
```

---

## 👤 Author

Built by **Lohith J** as a placement-ready system combining full-stack API design, vector database indexing, applied machine learning, and a real-world legal tech problem statement.
