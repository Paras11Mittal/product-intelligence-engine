import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
from app.config import settings
from app.schemas.input_schema import ProductEnrichRequest
from app.schemas.output_schema import ProductIntelligenceResponse
from app.services.orchestrator import ProductIntelligenceOrchestrator
from app.services.input_normalizer import InputNormalizer
from app.utils.logger import get_logger

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
        return FileResponse(index_path)
    return {"message": "AI Product Intelligence Backend API is running."}

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

@app.post(
    f"{settings.API_V1_STR}/enrich",
    response_model=ProductIntelligenceResponse,
    tags=["Product Intelligence"],
    summary="Transform minimal product info into rich, evidence-backed product intelligence"
)
async def enrich_product(request: ProductEnrichRequest):
    """
    Enriches a single product input consisting of:
    1. Brand
    2. Manufacturer Part Number (MPN)
    3. One-line product description
    """
    try:
        result = await orchestrator.run_pipeline(request)
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
async def enrich_product_batch(requests: List[ProductEnrichRequest]):
    results = []
    for req in requests:
        res = await orchestrator.run_pipeline(req)
        results.append(res)
    return results

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
