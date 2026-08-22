import os
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, Response
from typing import List
from app.config import settings
from app.schemas.input_schema import ProductEnrichRequest
from app.schemas.output_schema import ProductIntelligenceResponse
from app.services.orchestrator import ProductIntelligenceOrchestrator
from app.services.input_normalizer import InputNormalizer
from app.utils.logger import get_logger
from app.services.supabase import get_current_user, is_configured, save_enrichment
from app.services.delivery_exporter import delivery_csv

logger = get_logger("MainAPI")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Orchestration & Product-Intelligence Engine REST API. Normalizes input, researches official manufacturer sources, extracts specs, resolves conflicts, and outputs commerce-ready product intelligence.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prevent_dashboard_caching(request: Request, call_next):
    """Always serve the latest local dashboard files during development."""
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Clear-Site-Data"] = '"cache"'
    return response

orchestrator = ProductIntelligenceOrchestrator()
normalizer = InputNormalizer()

# Static files directory
# Keep the legacy launch folder in sync with the actively maintained dashboard.
# This workspace contains both project copies; the main copy owns the frontend.
_LOCAL_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
_SHARED_STATIC_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "product-intelligence-engine-main", "app", "static")
)
STATIC_DIR = _SHARED_STATIC_DIR if os.path.exists(_SHARED_STATIC_DIR) else _LOCAL_STATIC_DIR
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", tags=["Frontend Web App"])
async def serve_frontend():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        # This inline gate is intentionally served with each page response so the
        # dashboard cannot flash before the browser has loaded cached JavaScript.
        with open(index_path, "r", encoding="utf-8") as file:
            html = file.read()
        auth_gate = """
<style>
#authGate{min-height:calc(100vh - 68px);display:grid;place-items:center;padding:48px 20px;background:radial-gradient(circle at 15% 85%,#16b99828,transparent 32%),radial-gradient(circle at 85% 15%,#635bff36,transparent 35%)}
.auth-gate-card{width:min(620px,100%);padding:clamp(32px,6vw,64px);border:1px solid var(--line);border-radius:24px;background:var(--surface);box-shadow:var(--shadow);text-align:center}.auth-gate-card h1{font-size:clamp(34px,5vw,58px);line-height:1.05;letter-spacing:-.06em;margin:10px 0 18px}.auth-gate-card>p:not(.eyebrow){color:var(--muted);font-size:16px;line-height:1.7;margin:0 auto 28px;max-width:510px}.auth-gate-card .primary{margin:auto}
#authModal{background:radial-gradient(circle at 50% 18%,#8178ff30,transparent 38%),rgba(5,9,22,.9);backdrop-filter:blur(14px)}#authModal .modal-card{width:min(480px,calc(100vw - 32px));padding:42px;background:linear-gradient(145deg,rgba(29,38,70,.98),rgba(16,22,45,.99));border:1px solid rgba(160,154,255,.28);box-shadow:0 28px 90px rgba(0,0,0,.52)}#authModal .modal-card:before{content:'PRODUCTINTEL';display:block;color:var(--accent);font:600 10px 'JetBrains Mono';letter-spacing:.14em;margin-bottom:22px}#authModal .modal-card h2{font-size:32px;margin-bottom:4px}#authModal .modal-card h2:after{content:'Secure access to your intelligence workspace';display:block;color:var(--muted);font:400 13px 'Plus Jakarta Sans';letter-spacing:0;margin-top:10px}#authModal .auth-form{gap:17px;margin-top:30px}#authModal .auth-form label{gap:9px}#authModal .primary{margin-top:10px;padding:15px}#authModal .text-button{padding:10px}
</style>
<script>
(() => {
  const agent = document.querySelector('main.shell');
  if (!agent) return;
  let gate = document.querySelector('#authGate');
  if (!gate) {
    gate = document.createElement('section');
    gate.id = 'authGate';
    gate.innerHTML = '<div class="auth-gate-card"><p class="eyebrow">PRODUCTINTEL WORKSPACE</p><h1>Your product intelligence agent is ready.</h1><p>Sign in to research products, run the enrichment pipeline, and securely save your results.</p><button class="primary" id="landingAuthButton" type="button">Sign in to continue <b>→</b></button></div>';
    agent.before(gate);
  }
  const updateGate = () => {
    const key = Object.keys(localStorage).find((item) => /^sb-.*-auth-token$/.test(item));
    let session = null;
    try { session = key ? JSON.parse(localStorage.getItem(key)) : null; } catch (_) {}
    const signedIn = Boolean(session && session.access_token);
    agent.hidden = !signedIn;
    gate.hidden = signedIn;
  };
  document.addEventListener('click', (event) => {
    if (event.target.closest('#landingAuthButton') || event.target.closest('#authButton')) {
      const modal = document.querySelector('#authModal');
      if (modal) { gate.hidden = true; modal.hidden = false; }
    }
    if (event.target.closest('#closeAuthModal')) {
      gate.hidden = false;
    }
  });
  const batchControls = document.querySelector('.batch-controls');
  if (batchControls && !document.querySelector('#downloadDelivery')) {
    const download = document.createElement('button');
    download.id = 'downloadDelivery';
    download.className = 'small-button';
    download.type = 'button';
    download.textContent = 'Download delivery CSV';
    batchControls.append(download);
    download.addEventListener('click', async () => {
      const start = Math.max(1, Number(document.querySelector('#startRow').value || 1)) - 1;
      const size = Number(document.querySelector('#batchSize').value);
      const rows = state.csvRows.slice(start, start + size);
      if (!rows.length) { alert('Upload a valid CSV before downloading the delivery file.'); return; }
      download.disabled = true;
      download.textContent = 'Preparing delivery CSV…';
      try {
        const headers = { 'Content-Type': 'application/json' };
        if (typeof authHeaders === 'function') Object.assign(headers, await authHeaders());
        const response = await fetch('/api/v1/enrich/batch/delivery', {
          method: 'POST', headers,
          body: JSON.stringify(rows.map((row) => ({
            brand: row.Brand || row.brand || 'Unknown',
            mpn: row.Mfg_Part_Num,
            description: row.Part_Desc,
          }))),
        });
        if (!response.ok) { const error = await response.json().catch(() => ({})); throw new Error(error.detail || 'Could not create delivery CSV.'); }
        const url = URL.createObjectURL(await response.blob());
        const link = document.createElement('a');
        link.href = url; link.download = 'product-intelligence-delivery.csv'; link.click();
        URL.revokeObjectURL(url);
      } catch (error) { alert(error.message); }
      finally { download.disabled = false; download.textContent = 'Download delivery CSV'; }
    });
  }
  updateGate();
  window.addEventListener('storage', updateGate);
  window.setInterval(updateGate, 500);
})();
</script>
"""
        return HTMLResponse(
            html.replace("</body>", f"{auth_gate}</body>"),
            headers={"Cache-Control": "no-store, max-age=0", "Clear-Site-Data": '"cache"'},
        )
    return {"message": "AI Product Intelligence Backend API is running."}

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

@app.get(f"{settings.API_V1_STR}/auth/config", tags=["Authentication"])
async def auth_config():
    """Public settings consumed by the browser to initialize Supabase Auth."""
    return {
        "enabled": is_configured(),
        "url": settings.SUPABASE_URL if is_configured() else None,
        "anon_key": settings.SUPABASE_ANON_KEY if is_configured() else None,
    }

@app.get(f"{settings.API_V1_STR}/auth/me", tags=["Authentication"])
async def current_user(user=Depends(get_current_user)):
    return {"user": user}

@app.post(
    f"{settings.API_V1_STR}/enrich",
    response_model=ProductIntelligenceResponse,
    tags=["Product Intelligence"],
    summary="Transform minimal product info into rich, evidence-backed product intelligence"
)
async def enrich_product(
    request: ProductEnrichRequest,
    user=Depends(get_current_user),
    authorization: str | None = Header(default=None),
):
    """
    Enriches a single product input consisting of:
    1. Brand
    2. Manufacturer Part Number (MPN)
    3. One-line product description
    """
    try:
        result = await orchestrator.run_pipeline(request)
        await save_enrichment(user, request, result, authorization)
        return result
    except Exception as e:
        logger.error(f"Error enriching product: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")

@app.post(
    f"{settings.API_V1_STR}/enrich/batch",
    response_model=List[ProductIntelligenceResponse],
    tags=["Product Intelligence"],
    summary="Batch enrich multiple products concurrently"
)
async def enrich_product_batch(
    requests: List[ProductEnrichRequest],
    user=Depends(get_current_user),
    authorization: str | None = Header(default=None),
):
    results = []
    for req in requests:
        res = await orchestrator.run_pipeline(req)
        await save_enrichment(user, req, res, authorization)
        results.append(res)
    return results


@app.post(
    f"{settings.API_V1_STR}/enrich/batch/delivery",
    tags=["Product Intelligence"],
    summary="Enrich products and download the exact Unihack delivery-format CSV",
)
async def enrich_product_batch_delivery(
    requests: List[ProductEnrichRequest],
    user=Depends(get_current_user),
    authorization: str | None = Header(default=None),
):
    """Produces the flat delivery CSV while retaining blank fields for unknown facts."""
    results = []
    for request in requests:
        result = await orchestrator.run_pipeline(request)
        await save_enrichment(user, request, result, authorization)
        results.append(result)
    return Response(
        content=delivery_csv(results),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="product-intelligence-delivery.csv"'},
    )

@app.post(
    f"{settings.API_V1_STR}/pipeline/normalize",
    tags=["Pipeline Inspection"],
    summary="Inspect Stage 1: Input Normalization & Query Generation"
)
async def inspect_normalization(request: ProductEnrichRequest):
    return normalizer.normalize(request.brand, request.mpn, request.description)

@app.get(
    f"{settings.API_V1_STR}/schema",
    tags=["Schema Specification"],
    summary="Get full JSON Schema for product intelligence output"
)
async def get_output_schema():
    return ProductIntelligenceResponse.model_json_schema()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
