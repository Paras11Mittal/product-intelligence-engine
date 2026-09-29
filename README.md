# AI Product Intelligence Engine

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

## Quick Start

### 1. Installation

```bash
cd product_intelligence_engine
pip install -r requirements.txt
```

### 2. Run Terminal Demo Script

```bash
python run_demo.py
```

### Run the API

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
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

### Run the frontend locally

The frontend is a standalone static site in `frontend/`. Set `apiBaseUrl` in `frontend/config.js` to `http://127.0.0.1:8000`, then serve the directory with any static server, for example:

```bash
cd frontend
python -m http.server 5500
```

Open `http://127.0.0.1:5500`. The frontend can also use an empty `apiBaseUrl` when the API is hosted on the same origin. Do not open `index.html` directly as a `file://` URL.

## Separate Deployment (Vercel + Render)

The API and frontend are independently deployable:

1. **Deploy the API to Render** from the repository root. Use build command `pip install -r requirements.txt` and start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
2. In the API service environment, set `CORS_ALLOWED_ORIGINS` to the exact frontend origin, such as `https://your-product-intel.vercel.app` (comma-separated for multiple domains). Origins include the scheme and do not include a path or trailing slash. Set `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and the required research provider keys there as well.
3. **Deploy the `frontend/` directory to Vercel** by setting its project Root Directory to `frontend`. It is a static site: no build command or framework is required.
4. Set `frontend/config.js` `apiBaseUrl` to the public Render API origin, such as `https://your-product-intel-api.onrender.com` (no trailing slash), then deploy the frontend. This is a public URL, not a secret.
5. In Supabase Auth URL Configuration, add the Vercel site URL to the allowed site/redirect URLs. Supabase URL and anon key are intentionally delivered to the browser through `/api/v1/auth/config`; never put a service-role key in the frontend.

For Vercel preview URLs, either add each preview origin to `CORS_ALLOWED_ORIGINS` or set a narrowly scoped `CORS_ALLOWED_ORIGIN_REGEX`. Keep production origins explicit. CORS controls which browser origins can read responses; it is not a replacement for API authentication or rate limiting.

The API serves only API endpoints, health, and OpenAPI documentation. It does not serve the frontend. The frontend calls the API through the runtime configuration in `frontend/config.js`.

### Run Automated Test Suite

```bash
pytest tests/ -v
```

### 5. Connect Supabase (authentication + enrichment history)

1. Create a Supabase project, then run [`supabase/schema.sql`](supabase/schema.sql) in its SQL Editor.
2. Copy `.env.example` to `.env` and set `SUPABASE_URL` plus `SUPABASE_ANON_KEY` from **Project Settings → API**.
3. In Supabase **Authentication → URL Configuration**, add the frontend URL (for local use, `http://127.0.0.1:5500`; in production, the Vercel site URL) to the allowed site and redirect URLs.
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

**API deployment:** [https://product-intelligence-engine-3unc.onrender.com](https://product-intelligence-engine-3unc.onrender.com)
