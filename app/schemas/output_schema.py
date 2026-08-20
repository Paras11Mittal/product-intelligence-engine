from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class ProductIdentity(BaseModel):
    brand: str = Field(..., description="Original brand input")
    normalized_brand: str = Field(..., description="Cleaned, standardized brand name")
    mpn: str = Field(..., description="Original Manufacturer Part Number input")
    normalized_mpn: str = Field(..., description="Cleaned, alphanumeric-only MPN")
    product_name: str = Field(..., description="Full canonical product title")
    model_series: Optional[str] = Field(None, description="Product line or series")
    upc_gtin: Optional[str] = Field(None, description="UPC, EAN, or GTIN identifier if discovered")
    verification_status: str = Field(..., description="VERIFIED_MANUFACTURER | VERIFIED_DISTRIBUTOR | PARTIALLY_VERIFIED | UNVERIFIED")

class ProductClassification(BaseModel):
    category_path: List[str] = Field(..., description="Hierarchical taxonomy e.g. ['Tools', 'Power Tools', 'Drills']")
    unspsc_code: Optional[str] = Field(None, description="UNSPSC taxonomy code")
    hs_code: Optional[str] = Field(None, description="Harmonized System (HS) code for trade")
    target_market: str = Field(..., description="Professional, Commercial, Industrial, or Consumer")

class SpecificationItem(BaseModel):
    key: str = Field(..., description="Human readable spec label e.g. Max Torque")
    normalized_key: str = Field(..., description="Snake_case canonical key e.g. max_torque")
    value: str = Field(..., description="Cleaned spec value e.g. 55")
    unit: Optional[str] = Field(None, description="Standardized SI/Imperial unit e.g. Nm")
    raw_value: str = Field(..., description="Original text value as stated in source document")
    category: str = Field(default="General", description="Grouping category e.g. Performance, Electrical, Physical")
    confidence: float = Field(..., description="Attribute confidence score (0.0 - 1.0)")
    source_id: str = Field(..., description="Reference ID pointing to item in sources array")
    evidence: str = Field(..., description="Direct quote or snippet supporting this spec claim")
    is_verified: bool = Field(..., description="True if backed by official/high-authority evidence")

class ApplicationItem(BaseModel):
    use_case: str = Field(..., description="Primary application or task")
    recommended_environment: str = Field(..., description="Environment where product excels")
    suitability_rating: str = Field(..., description="High, Medium, or Specialized")

class CommerceData(BaseModel):
    title: str = Field(..., description="Optimized, commerce-ready product title")
    short_description: str = Field(..., description="Fact-checked short marketing overview")
    feature_bullets: List[str] = Field(..., description="Bullet points derived strictly from verified features")
    seo_keywords: List[str] = Field(..., description="Target search terms")
    unverified_claims: List[str] = Field(default_factory=list, description="Claims from description/web that lacked strict evidence")

class SourceItem(BaseModel):
    id: str = Field(..., description="Unique source identifier e.g. src_mfr_1")
    name: str = Field(..., description="Display name of source website/document")
    domain: str = Field(..., description="Website domain e.g. bosch-professional.com")
    url: str = Field(..., description="Full URL to source page or document")
    source_type: str = Field(..., description="MANUFACTURER | DISTRIBUTOR | THIRD_PARTY | FORUM")
    reliability_score: float = Field(..., description="Authority score from 0.0 to 1.0")
    retrieved_at: str = Field(..., description="ISO 8601 timestamp")

class CompetingValue(BaseModel):
    value: str
    source_id: str
    reliability: float

class ConflictItem(BaseModel):
    attribute: str = Field(..., description="Attribute key where conflict occurred")
    competing_values: List[CompetingValue] = Field(..., description="Conflicting values with source references")
    resolved_value: str = Field(..., description="Value selected based on reliability rules")
    resolution_reason: str = Field(..., description="Explanation for how conflict was resolved")

class ConfidenceSummary(BaseModel):
    overall_score: float = Field(..., description="Aggregated confidence score (0.0 to 1.0)")
    identity_confidence: float
    specifications_confidence: float
    classification_confidence: float
    sources_count: int
    verified_attributes_count: int
    unverified_attributes_count: int

class ProductIntelligenceResponse(BaseModel):
    identity: ProductIdentity
    classification: ProductClassification
    specifications: List[SpecificationItem]
    applications: List[ApplicationItem]
    commerce: CommerceData
    sources: List[SourceItem]
    conflicts: List[ConflictItem]
    confidence: ConfidenceSummary
