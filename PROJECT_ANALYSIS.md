# Product Intelligence Engine — Project Brief

## Purpose of this document

This is a handoff brief for an engineer or another language model that needs to understand the repository before answering questions or making changes. It describes the implementation visible in the working tree, not just the product ambitions described in the README. Treat the code as the source of truth when it disagrees with this document. The repository had pre-existing uncommitted changes during this review; inspect `git status` before editing or reverting anything.

## Executive summary

Product Intelligence Engine is a Python/FastAPI application with a plain HTML, CSS, and JavaScript browser dashboard. It accepts a product brand, manufacturer part number (MPN), and description; it returns a structured record containing identity, classification, specifications, applications, commerce copy, sources, conflicts, and confidence scores. Optional Supabase configuration enables bearer-token authentication and user-scoped run-history persistence. The application can also emit a fixed 252-column catalog-delivery CSV.

The implemented enrichment pipeline is a mixture of real search integration and deterministic heuristics. Serper is the only search provider wired into the research code. When live search is absent or returns no usable sources, the current fallback fabricates sample source records and specifications based on description keywords. Those generated facts are not verified research, despite the product's evidence-led positioning. Confidence values are heuristic scores rather than calibrated probabilities.

The current UI is a responsive dark landing and inspection experience. It contains single-product and CSV batch modes, a results view, three mock insights rendered in vanilla JavaScript, a scrollable article-reader modal, and a four-column footer. The output state expands across the page rather than remaining squeezed into the right-hand hero column. API-key issuance is not implemented; the header contains sign-in controls but no API-key action.

## Product scope and intended users

The product targets e-commerce, industrial, and catalog operations teams that need to turn incomplete supplier or manufacturer data into more consistent product records. Its main advertised outcomes are:

- Normalize product identity and common units.
- Gather source material and extract specifications.
- Track competing values and select a preferred value.
- Build taxonomy and commerce descriptions.
- Return machine-readable JSON or a flat delivery CSV.

The README calls the system “zero hallucination” and “evidence-backed.” That is an intended design principle, not a guarantee of the present implementation. The fallback research path, heuristic extraction, and generated commerce copy need to be considered before using results as verified facts.

## Technology and repository structure

### Runtime

- Python 3 with FastAPI and Uvicorn.
- Pydantic v2 request/response models.
- `httpx` for search, page retrieval, Supabase Auth validation, and Supabase REST writes.
- `python-dotenv` for local environment loading.
- Plain HTML/CSS/JavaScript for the dashboard; no React or Tailwind build pipeline is present.
- Supabase is optional and accessed through REST calls; there is no Supabase Python SDK dependency.

### Important files

| Path | Responsibility |
| --- | --- |
| `app/main.py` | FastAPI construction, static dashboard serving, auth config, enrichment and schema routes. |
| `app/config.py` | Runtime settings and environment variables. |
| `app/schemas/input_schema.py` | Required product input and optional `options` object. |
| `app/schemas/output_schema.py` | Pydantic contract for the complete intelligence response. |
| `app/services/orchestrator.py` | Runs the six enrichment stages and validates the assembled response. |
| `app/services/input_normalizer.py` | Cleans raw inputs, infers a small set of brands, creates search keys, and reports validation warnings. |
| `app/services/research_engine.py` | Serper search, source classification, and built-in fallback generation. |
| `app/services/document_processor.py` | Fetches selected HTML result pages and extracts text/table rows. |
| `app/services/spec_extractor.py` | Parses colon-delimited text into normalized specification candidates. |
| `app/utils/unit_converter.py` | Basic unit recognition and numeric/value splitting. |
| `app/services/conflict_resolver.py` | Groups specifications by normalized key and picks a winner by confidence. |
| `app/services/confidence_scorer.py` | Calculates aggregate heuristic confidence fields. |
| `app/services/commerce_synthesizer.py` | Creates identity/classification/commerce text and application templates. |
| `app/services/delivery_exporter.py` | Maps results into the fixed 252-column CSV shape. |
| `app/services/supabase.py` | Validates Supabase access tokens and persists runs with the caller's token. |
| `supabase/schema.sql` | `enrichment_runs` table, index, and row-level security policies. |
| `frontend/index.html` | Dashboard structure, auth modal, single and batch controls, output area, insights, and footer. |
| `frontend/style.css` | Base dashboard styles. |
| `frontend/overrides.css` | Dark visual system, responsive landing layout, and expanded output-state layout. |
| `frontend/app.js` | Frontend auth, theme, form submission, result rendering, CSV upload, and batch flow. |
| `frontend/config.js` | Runtime API origin configuration for static hosting. |
| `run_server.py` | Local/deployment server entry point; re-launches with `.venv` if present and chooses bind host/port. |
| `run_demo.py` | Terminal example that runs three sample products through the orchestrator. |
| `tests/` | Pipeline, normalizer, and delivery exporter tests; see test caveat below. |
| `README.md` | Setup notes, product claims, and endpoint list; parts of it are stale. |

There is no frontend compilation step. The unused `frontend/3d-scene.js`, `package-lock.json`, and CSS-edit helper scripts are not runtime dependencies of either deployable service.

## Request and data flow

1. The independently hosted browser app collects `brand`, `mpn`, and `description` and posts JSON to the configured API origin at `POST /api/v1/enrich`.
2. FastAPI validates required fields with `ProductEnrichRequest`.
3. `ProductIntelligenceOrchestrator.run_pipeline()` calls `InputNormalizer`.
4. `ResearchEngine` searches Serper when `SERPER_API_KEY` is configured. It makes a second query if the first produces no sources. If neither yields sources, it uses its built-in generated fallback.
5. `DocumentProcessor` attempts to fetch up to two result pages and converts HTML title, description, text blocks, and table rows into snippets.
6. `SpecExtractor` parses each colon-separated snippet line into a candidate spec, assigns a category and source-based confidence, and attaches evidence text.
7. `ConflictResolver` groups candidates by `normalized_key`, retains a top-confidence candidate, and emits conflict records when literal values differ.
8. `CommerceSynthesizer` generates the identity, taxonomy, commerce descriptions, bullets, keywords, and applications.
9. `ConfidenceScorer` calculates summary values.
10. Pydantic validates the final response. The route optionally saves it to Supabase and returns JSON.

### Important data-flow details

- The normalizer retains raw input and creates normalized values and search keys, but the research engine builds its own two Serper queries; the normalized `search_keys` value is currently assigned but not used to drive search.
- `ProductEnrichRequest.options` accepts arbitrary keys, and its example mentions `strict_evidence` and `deep_search`; these options are not visibly consumed by the orchestrator or research engine.
- The model describes product identity and MPN normalization in prose, but actual normalization can preserve punctuation and uses straightforward uppercasing/whitespace removal.
- Unit handling is a small regex map, not a comprehensive conversion system. It often identifies units without converting equivalent measurements into a shared base unit.
- Spec evidence is a snippet line packaged with a title, not necessarily a direct quote from a retrieved document. In the fallback path, the snippet itself is generated.
- Several `SourceItem` and other schema fields are plain strings rather than constrained enums or domain-validated values.

## API surface

| Method and path | Purpose | Authentication behavior |
| --- | --- | --- |
| `GET /` | No frontend route; the API is deployed separately from the static site. | Not provided. |
| `GET /health` | Basic process health response. | Public. |
| `GET /api/v1/auth/config` | Report whether Supabase browser auth is configured and return its URL/anon key. | Public; anon key is designed to be browser-visible. |
| `GET /api/v1/auth/me` | Validate the current Supabase bearer token. | Requires token only when Supabase is configured. |
| `POST /api/v1/enrich` | Enrich one product and return the response contract. | Requires a valid bearer token when Supabase is configured; otherwise auth is disabled. |
| `POST /api/v1/enrich/batch` | Sequentially process a JSON list of products and return successful results. | Same optional Supabase behavior. Per-item exceptions are logged and omitted. |
| `POST /api/v1/enrich/batch/delivery` | Process a JSON list and return a 252-column CSV attachment. | Same optional Supabase behavior. Failure counts are returned in headers; failed rows are not represented in the CSV. |
| `POST /api/v1/pipeline/normalize` | Return the normalizer's input cleanup/search-key result. | No user dependency in this route. |
| `GET /api/v1/schema` | Return the generated JSON Schema for the response model. | Public. |
| `GET /docs`, `GET /redoc` | FastAPI API documentation. | Enabled by FastAPI defaults. |

## Response contract

`ProductIntelligenceResponse` contains these top-level keys:

- `identity`: original/normalized brand and MPN, canonical product name, optional series and GTIN, and verification status.
- `classification`: category path, optional UNSPSC/HS code, and target market.
- `specifications`: display/canonical key, value/unit, raw value, category, confidence, source ID, evidence, and verification flag.
- `applications`: use case, environment, and suitability.
- `commerce`: title, short description, feature bullets, SEO keywords, and unverified claims.
- `sources`: source identity, domain/URL/type, reliability score, and retrieval time.
- `conflicts`: competing values with source and reliability, selected value, and resolution reason.
- `confidence`: overall, identity, specification, and classification scores, source count, and verified/unverified attribute counts.

The delivery exporter declares `DELIVERY_COLUMNS` and tests expect exactly 252 ordered columns. Unknown output fields are intentionally emitted blank. Specification slots are populated from the first 50 specs and feature fields from the first 20 bullets.

## Frontend behavior and design

- The dashboard uses plain HTML with DOM-driven JavaScript and CSS. It loads Google Fonts (Inter, Plus Jakarta Sans, and JetBrains Mono) and Supabase JS v2 from a CDN.
- The header has brand, navigation, sign-in/sign-out, and theme controls. There is no API key management endpoint or key provisioning workflow.
- The hero and inspection form are arranged as a two-column desktop layout; they stack at smaller widths.
- Single inspection has four quick-load presets and renders specification evidence in a modal.
- Batch mode parses a CSV in the browser, requires `Mfg_Part_Num` and `Part_Desc`, previews records, and enriches selected rows one at a time.
- Results have a full-width state: the hero is hidden after output appears, the stage spans the content width, specifications and commerce copy sit in a desktop grid, and the result grid stacks on narrow viewports. The selector uses CSS `:has()`, supported by current Chromium-based browsers and modern Safari; check target browser support if expanding it.
- The insights section renders three mock editorial cards through a simulated asynchronous fetch in `frontend/app.js`; it is not connected to a live blog/CMS. Links are placeholders to page anchors.
- The footer contains placeholder company/legal/contact destinations. `hello@productintel.example` is not a production contact address.
- The dashboard is not gated by a server-injected landing screen. API access is still checked server-side when Supabase is configured. With no Supabase configuration, auth is disabled and the enrichment endpoints accept unauthenticated requests.

## Authentication and persistence

- `SUPABASE_URL` and `SUPABASE_ANON_KEY` enable auth. The browser receives these public settings from the API's `/api/v1/auth/config` endpoint and uses Supabase JS sign-in/sign-up. `CORS_ALLOWED_ORIGINS` controls which separately hosted frontends can call the API.
- `get_current_user()` validates bearer tokens against Supabase Auth's `/auth/v1/user` endpoint.
- `save_enrichment()` writes to `public.enrichment_runs` with the caller's access token and anon key; row-level security is intended to constrain access to the signed-in user.
- Persistence errors are intentionally ignored so they do not fail completed enrichment requests.
- No service-role key should be used or exposed. `.env` is ignored by Git; do not copy its contents into prompts, generated documentation, logs, or commits.
- The README refers to `.env.example`, but that file is not present in the repository listing at the time of review.

## Configuration and local operation

Settings are read in `app/config.py` using `python-dotenv`:

- `SERPER_API_KEY`: only live search provider currently used.
- `TAVILY_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`: defined but not wired into this implementation.
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`: optional auth and persistence configuration.
- Source reliability values and numeric conflict tolerance currently have defaults in code.

README-described commands:

```powershell
pip install -r requirements.txt
python run_server.py
```

The server entry point reads `PORT` (defaults to 8000); with `PORT` set it binds `0.0.0.0`, otherwise `127.0.0.1`. Direct Uvicorn invocation is also documented. The demo is run with `python run_demo.py`. The current code was not executed as part of preparing this brief.

## Current implementation limitations and risks

### Data correctness — highest priority

1. **Generated fallback masquerades as research.** `_get_builtin_research()` creates manufacturer/distributor source objects, URLs, and keyword-selected specs. `ResearchEngine.research_product()` uses it whenever live search produces no sources. The orchestrator's identity check considers the presence of a manufacturer source enough for verification, which can make generated data appear authoritative. This is the largest mismatch between product promise and implementation. A handoff LLM should not describe default results as real retrieved facts.
2. **Source authority is a domain heuristic.** `classify_source_type()` uses brand/domain substring matching and a short hard-coded distributor list. It does not prove a domain is owned by a manufacturer or that a distributor is authorized. Search snippets are trusted as evidence without stronger identity checks.
3. **Extraction is line-oriented.** A line containing a colon can become a specification. Table/page text can be noisy, values can be truncated or mislabeled, and no semantic product identity check is performed.
4. **No real unit conversion/conflict tolerance.** Conflict resolution groups by normalized key and compares rendered string values. Equivalent values in different units may conflict; tolerance settings are not visibly used in the resolver. Numeric parsing does not cover common formats such as comma-separated thousands.
5. **Confidence scores are heuristic.** The scorer applies fixed weighted values and fixed source-type confidence. These should not be presented as calibrated probabilities or quality guarantees.
6. **Commerce output may overstate certainty.** Some title/description text is copied from user input; taxonomy and application content rely on keywords/templates. “Unverified claims” only flags a few subjective words, not all unsupported claims.

### Security, reliability, and API behavior

1. **Fetched-page URL safety needs review.** `DocumentProcessor` fetches URLs from search results, follows redirects, and has no visible allowlist or private-IP/metadata-address protection. This can create server-side request forgery exposure. The domain skip list is not a network safety control.
2. **Production authentication policy remains an operator decision.** Supabase auth is optional in the current API; deployments that require accounts should configure Supabase and decide whether unauthenticated enrichment should be rejected.
3. **Auth is optional by design.** If Supabase environment values are absent, enrichment routes do not require authentication. That is suitable only if intentionally acceptable for the deployment.
4. **Batch errors are lossy.** The JSON batch endpoint silently omits failed records; delivery only supplies submitted/successful/failed counts in headers. Clients cannot reliably map all errors to original input rows from the API response.
5. **Batch processing is serial.** Both server-side batch routes iterate sequentially. The current browser batch UI also calls single enrichment serially. Its CSV download then calls the delivery route with successful inputs, running enrichment a second time and potentially duplicating Supabase history entries.
6. **Search/provider resilience is limited.** Only Serper is integrated; API failures/no key lead to generated fallback instead of a clearly unavailable or unverified state. No explicit provider rate limiting, retry policy, result cache, or request budget is apparent.
7. **Caching behavior is unusual.** The root/static middleware adds `Clear-Site-Data: "cache"` and `Cache-Control: no-store`, which can make browser caching ineffective on every dashboard/static response.

### Product completeness and maintenance

- API-key provisioning, billing/pricing, published blog content, legal pages, contact destination, and real integration flows are placeholders or absent.
- README component paths and setup references are stale: for example it names `app/services/normalizer.py` although the implementation is `input_normalizer.py`, and it tells users to copy `.env.example`, which is absent.
- Tests appear partly stale: `tests/test_pipeline.py` imports `app.services.normalizer`, while `tests/test_normalizer.py` imports a top-level `input_normalizer`; neither path matches the listed current module `app/services/input_normalizer.py`. Tests were not run during this review, so treat this as a likely collection issue requiring confirmation.
- Some generated Python bytecode files appear tracked and modified in the working tree. Generally, source files should be versioned and `__pycache__` artifacts ignored/untracked.
- `CONFLICT_NUMERIC_TOLERANCE_PCT` and provider keys for Tavily/OpenAI/Gemini are configured but appear unused in the described code paths.

## Existing project rules

The repository's `AGENTS.md` contains design constraints that future agents should follow. Key requirements include: avoid emoji; avoid pure white/black primary surfaces; use subdued neutrals; avoid heavy shadows and colored status borders; keep spacing on an 8px/4px grid; use rem typography; use clear focus states; keep mobile controls at least 44px high; and stack columns on mobile. Read the full `AGENTS.md` before substantial UI changes because it has additional details.

## Working-tree context at the time this brief was written

The tree has included user-authored frontend assets and helper files during prior work. Keep the frontend assets in `frontend/` as the static deployment root and avoid reverting unrelated work when updating them.

This document itself is a new file. It should be maintained as architecture changes, routes, setup, and known limitations change.

## Suggested roadmap for a future implementation agent

1. Replace synthetic fallback research with an explicit unavailable/unverified state or a clearly labeled demo fixture mode. Keep provenance true to the actual retrieval path.
2. Add source validation and safe outbound-fetch controls (scheme, hostname, DNS/IP ranges, redirect revalidation, response size/content limits, and timeout budget).
3. Normalize and validate manufacturer identity and product matching before extracting or claiming facts.
4. Improve extraction into typed candidates; add canonical attribute definitions, robust numeric parsing, unit conversion, and explicit equivalence/tolerance handling.
5. Calibrate confidence against labeled outcomes or rename scores to make their heuristic nature clear.
6. Redesign batch APIs to return row-correlated success/error records and avoid re-enriching products during CSV export. Apply concurrency limits and provider rate limits.
7. Decide whether auth is mandatory in production and add rate limiting or quotas appropriate to the exposed enrichment API.
8. Reconcile tests and README imports/commands with the current code, then add deterministic tests around no-search mode, fabricated-data prevention, auth config states, unsafe URLs, conflict/unit equivalence, batch failures, and CSV ordering.
9. Replace placeholder API-key/blog/legal/company links with real routes or clearly non-interactive placeholders before public launch.
10. Remove/ignore generated bytecode and clarify whether root helper scripts, the unused 3D asset, and the minimal npm lockfile are intentional.

## Guidance for another LLM working in this repository

- Read this file and the repository's `AGENTS.md` first, then inspect the current Git status and relevant diffs.
- Treat the present working tree as user work. Do not reset, clean, or broadly overwrite it.
- Do not assume README claims match current runtime behavior; verify the implementation path before asserting evidence, verification, auth, or confidence properties.
- Keep credentials out of output and never read/copy `.env` values into generated files.
- The backend uses ordinary Python modules and the frontend is static HTML/CSS/JS. Avoid adding a frontend framework/build tool unless the user explicitly wants that migration.
- Do not claim tests pass unless actually run and observed. This brief was created without running tests or starting the service.
