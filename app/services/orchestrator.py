from typing import Dict, Any, List
from app.schemas.input_schema import ProductEnrichRequest
from app.schemas.output_schema import ProductIntelligenceResponse
from app.services.input_normalizer import InputNormalizer
from app.services.research_engine import ResearchEngine
from app.services.spec_extractor import SpecExtractor
from app.services.conflict_resolver import ConflictResolver
from app.services.confidence_scorer import ConfidenceScorer
from app.services.commerce_synthesizer import CommerceSynthesizer
from app.utils.logger import get_logger

logger = get_logger("ProductIntelligenceOrchestrator")

class ProductIntelligenceOrchestrator:
    """
    Main orchestration engine executing the 6-stage product intelligence pipeline.
    """

    def __init__(self):
        self.normalizer = InputNormalizer()
        self.research_engine = ResearchEngine()
        self.spec_extractor = SpecExtractor()
        self.conflict_resolver = ConflictResolver()
        self.confidence_scorer = ConfidenceScorer()
        self.commerce_synthesizer = CommerceSynthesizer()

    async def run_pipeline(self, request: ProductEnrichRequest) -> Dict[str, Any]:
        logger.info(f"Received request: Brand='{request.brand}', MPN='{request.mpn}'")

        # Stage 1: Input Normalization & Identity Identification
        norm_input = self.normalizer.normalize(request.brand, request.mpn, request.description)

        # Stage 2: Multi-Source Web Research & Manufacturer Source Prioritization
        research_data = await self.research_engine.research_product(norm_input)
        sources = research_data["sources"]
        raw_documents = research_data["raw_documents"]

        sources_map = {s["id"]: s for s in sources}

        # Stage 3: Specification Extraction & Unit Normalization
        extracted_specs = self.spec_extractor.extract_specs(raw_documents, sources_map)

        # Stage 4: Conflict Detection & Reliability Resolution
        final_specs, conflicts = self.conflict_resolver.resolve_conflicts(extracted_specs, sources_map)

        # Stage 5: Commerce Information & Taxonomy Synthesis
        commerce_data = self.commerce_synthesizer.synthesize(norm_input, final_specs, conflicts)

        # Stage 6: Multi-Factor Confidence Matrix Computation
        is_identity_verified = norm_input["normalized_brand"].lower() in [s["domain"].lower() for s in sources] or any(s["source_type"] == "MANUFACTURER" for s in sources)
        confidence_summary = self.confidence_scorer.compute_confidence(
            specs=final_specs,
            sources=sources,
            conflicts=conflicts,
            identity_verified=is_identity_verified
        )

        # Assemble Final Machine-Readable Output Payload
        response_payload = {
            "identity": commerce_data["identity"],
            "classification": commerce_data["classification"],
            "specifications": final_specs,
            "applications": commerce_data["applications"],
            "commerce": commerce_data["commerce"],
            "sources": sources,
            "conflicts": conflicts,
            "confidence": confidence_summary
        }

        # Validate with Pydantic Schema before returning
        validated_response = ProductIntelligenceResponse(**response_payload)
        return validated_response.model_dump()
