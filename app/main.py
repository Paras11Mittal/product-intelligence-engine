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
STATIC_DIR = _LOCAL_STATIC_DIR
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", tags=["Frontend Web App"])
async def serve_frontend():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        # Serve the marketing and inspection page directly; API routes enforce auth.
        with open(index_path, "r", encoding="utf-8") as file:
            html = file.read()
        return HTMLResponse(
            html,
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
        try:
            res = await orchestrator.run_pipeline(req)
            await save_enrichment(user, req, res, authorization)
            results.append(res)
        except Exception as error:
            logger.error("Batch enrichment failed for %s: %s", req.mpn, error)
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
    failures = []
    for request in requests:
        try:
            result = await orchestrator.run_pipeline(request)
            await save_enrichment(user, request, result, authorization)
            results.append(result)
        except Exception as error:
            logger.error("Delivery enrichment failed for %s: %s", request.mpn, error)
            failures.append(f"{request.mpn}: {error}")
    return Response(
        content=delivery_csv(results),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="product-intelligence-delivery.csv"',
            "X-Delivery-Submitted": str(len(requests)),
            "X-Delivery-Successful": str(len(results)),
            "X-Delivery-Failed": str(len(failures)),
        },
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
    import os
    
    # Render assigns the port dynamically via the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=False
    )
