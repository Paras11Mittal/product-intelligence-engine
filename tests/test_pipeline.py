import pytest
import asyncio
from app.schemas.input_schema import ProductEnrichRequest
from app.services.normalizer import InputNormalizer
from app.services.conflict_resolver import ConflictResolver
from app.services.orchestrator import ProductIntelligenceOrchestrator
from app.utils.unit_converter import extract_numeric_and_unit, normalize_unit

def test_input_normalization():
    normalizer = InputNormalizer()
    res = normalizer.normalize("Bosch Tools GmbH", "gsr 18v-55", "Cordless drill")
    assert res["normalized_brand"] == "Bosch"
    assert res["normalized_mpn"] == "GSR18V55"
    assert len(res["search_queries"]) >= 3

def test_unit_converter():
    val, unit = extract_numeric_and_unit("55 Newton meters")
    assert val == "55"
    assert unit == "Nm"

    val2, unit2 = extract_numeric_and_unit("1800 rpm")
    assert val2 == "1800"
    assert unit2 == "RPM"

def test_conflict_resolution():
    resolver = ConflictResolver()
    extracted_specs = [
        {
            "key": "Max Speed",
            "normalized_key": "max_speed",
            "value": "1800",
            "unit": "RPM",
            "raw_value": "1800 RPM",
            "category": "Performance",
            "confidence": 0.95,
            "source_id": "src_mfr_1",
            "evidence": "Snippet from official datasheet",
            "is_verified": True
        },
        {
            "key": "Max Speed",
            "normalized_key": "max_speed",
            "value": "1750",
            "unit": "RPM",
            "raw_value": "1750 RPM",
            "category": "Performance",
            "confidence": 0.75,
            "source_id": "src_dist_1",
            "evidence": "Snippet from catalog",
            "is_verified": False
        }
    ]
    sources_map = {
        "src_mfr_1": {"source_type": "MANUFACTURER", "reliability_score": 0.95},
        "src_dist_1": {"source_type": "DISTRIBUTOR", "reliability_score": 0.75}
    }

    final_specs, conflicts = resolver.resolve_conflicts(extracted_specs, sources_map)

    assert len(final_specs) == 1
    assert final_specs[0]["value"] == "1800"
    assert len(conflicts) == 1
    assert conflicts[0]["attribute"] == "Max Speed"
    assert conflicts[0]["resolved_value"] == "1800 RPM"

def test_end_to_end_pipeline():
    orchestrator = ProductIntelligenceOrchestrator()
    req = ProductEnrichRequest(
        brand="DeWalt",
        mpn="DCD791B",
        description="20V MAX XR Li-Ion Brushless Compact Drill/Driver"
    )
    result = asyncio.run(orchestrator.run_pipeline(req))

    # Check top-level JSON keys required by prompt
    assert "identity" in result
    assert "classification" in result
    assert "specifications" in result
    assert "applications" in result
    assert "commerce" in result
    assert "sources" in result
    assert "conflicts" in result
    assert "confidence" in result

    # Check identity
    assert result["identity"]["normalized_brand"] == "Dewalt"
    assert result["identity"]["normalized_mpn"] == "DCD791B"
