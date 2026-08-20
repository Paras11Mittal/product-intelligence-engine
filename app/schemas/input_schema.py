from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ProductEnrichRequest(BaseModel):
    brand: str = Field(..., description="Brand or manufacturer name")
    mpn: str = Field(..., description="Manufacturer Part Number (MPN)")
    description: str = Field(..., description="One-line product description")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution options e.g. strict_evidence, deep_search")

    model_config = {
        "json_schema_extra": {
            "example": {
                "brand": "Bosch",
                "mpn": "GSR 18V-55",
                "description": "18V Professional Cordless Drill Driver with Brushless Motor",
                "options": {
                    "prefer_manufacturer": True,
                    "strict_evidence": True
                }
            }
        }
    }
