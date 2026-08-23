# 🧠 AI Product Intelligence Orchestration Engine (Backend)

An AI-powered product intelligence engine built for e-commerce and industrial cataloging. It accepts minimal inputs (**Brand**, **MPN**, **Description**) and transforms them into rich, evidence-backed, commerce-ready structured JSON product intelligence.

---

## 📌 Key Architectural Principles

1. **Zero Hallucination / Evidence-Backed**: Factual specs are tied directly to explicit quotes/snippets retrieved from verified documents.
2. **Manufacturer Prioritization**: Manufacturer official datasheets (authority score ~0.95–0.98) override distributor or 3rd-party claims.
3. **Explicit Conflict Tracking**: Discrepancies between sources (e.g. 1800 RPM vs 1750 RPM) are logged in the `conflicts` array with resolution reasoning.
4. **Unit & Name Standardization**: Standardizes keys into canonical `snake_case` and converts values/units into consistent formats (`Nm`, `RPM`, `V`, `W`, `kg`, `dB(A)`).
5. **Schema Compliance**: Guaranteed output matching the required contract:

```json
{
  "identity": {},
  "classification": {},
  "specifications": [],
  "applications": [],
  "commerce": {},
  "sources": [],
  "conflicts": [],
  "confidence": {}
}
```

---

## ⚙️ 12 Core Responsibilities Map

| # | Responsibility | Component / Module |
|---|----------------|--------------------|
| 1 | Understand and normalize input | `InputNormalizer` (`app/services/normalizer.py`) |
| 2 | Identify exact product | `ResearchEngine` (`app/services/research_engine.py`) |
| 3 | Research reliable sources | `ResearchEngine` (`app/services/research_engine.py`) |
| 4 | Prioritize manufacturer sources | `ResearchEngine.classify_source_type()` |
| 5 | Extract relevant product specifications | `SpecExtractor` (`app/services/spec_extractor.py`) |
| 6 | Normalize names and units | `unit_converter.py` & `SpecExtractor` |
| 7 | Detect conflicts between sources | `ConflictResolver` (`app/services/conflict_resolver.py`) |
| 8 | Determine source reliability | `ConflictResolver` weighted scoring |
| 9 | Assign confidence to attributes | `ConfidenceScorer` (`app/services/confidence_scorer.py`) |
| 10 | Generate commerce-ready output | `CommerceSynthesizer` (`app/services/commerce_synthesizer.py`) |
| 11 | Preserve evidence supporting claims | `SpecExtractor` evidence snippets |
| 12 | Identify unverified information | `CommerceSynthesizer.unverified_claims` & `ConfidenceSummary` |

---

## 🚀 Quick Start & How to Run

### 1. Installation

```bash
cd product_intelligence_engine
pip install -r requirements.txt
```

### 2. Run Terminal Demo Script

```bash
python run_demo.py
```

### 3. Run FastAPI Server

You can start the server using either of these commands:

```bash
python run_server.py
```
*or*
```bash
python -m uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI JSON Schema: [http://localhost:8000/api/v1/schema](http://localhost:8000/api/v1/schema)

### 4. Run Automated Test Suite

```bash
pytest tests/ -v
```

### 5. Connect Supabase (authentication + enrichment history)

1. Create a Supabase project, then run [`supabase/schema.sql`](supabase/schema.sql) in its SQL Editor.
2. Copy `.env.example` to `.env` and set `SUPABASE_URL` plus `SUPABASE_ANON_KEY` from **Project Settings → API**.
3. In Supabase **Authentication → URL Configuration**, add your local URL (for example `http://127.0.0.1:8000`) as a redirect URL.
4. Restart the FastAPI server. The dashboard will show **Sign in**, where users can create an account or sign in. Each completed enrichment is saved to `enrichment_runs` and remains visible only to its owner through Supabase Row Level Security.

When Supabase environment variables are absent, the app remains usable locally but authentication and persistence are disabled. Never expose a Supabase `service_role` key in this project.

---

## 📡 API Endpoints

- `POST /api/v1/enrich`: Main enrichment endpoint.
- `POST /api/v1/enrich/batch`: Batch enrichment for multiple products.
- `POST /api/v1/enrich/batch/delivery`: Batch enrichment returned as the exact 252-column delivery CSV.
- `POST /api/v1/pipeline/normalize`: Inspect Stage 1 query generation.
- `GET /api/v1/schema`: OpenAPI / Output schema specification.
- `GET /health`: System health check.
# Product Intelligence Engine

🚀 **Live Prototype:** [https://product-intelligence-engine-3unc.onrender.com](https://product-intelligence-engine-3unc.onrender.com)
