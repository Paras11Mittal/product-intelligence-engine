from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger("ConfidenceScorer")

class ConfidenceScorer:
    """
    Responsibilities 9 & 12:
    - Assign confidence to individual attributes.
    - Clearly identify information that could not be verified.
    - Compute overall product intelligence confidence summary.
    """

    def compute_confidence(
        self,
        specs: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]],
        identity_verified: bool
    ) -> Dict[str, Any]:

        total_specs = len(specs)
        verified_count = sum(1 for s in specs if s.get("is_verified", False))
        unverified_count = total_specs - verified_count

        has_mfr = any(s.get("source_type") == "MANUFACTURER" for s in sources)
        identity_conf = 0.98 if (identity_verified and has_mfr) else 0.75

        if total_specs > 0:
            avg_spec_conf = sum(s.get("confidence", 0.5) for s in specs) / total_specs
        else:
            avg_spec_conf = 0.5

        # Penalty for conflicts
        conflict_penalty = len(conflicts) * 0.03
        spec_conf = max(0.1, avg_spec_conf - conflict_penalty)

        class_conf = 0.92 if has_mfr else 0.70

        # Weighted aggregate score
        overall = (identity_conf * 0.35) + (spec_conf * 0.45) + (class_conf * 0.20)
        overall_score = round(min(1.0, max(0.0, overall)), 2)

        return {
            "overall_score": overall_score,
            "identity_confidence": round(identity_conf, 2),
            "specifications_confidence": round(spec_conf, 2),
            "classification_confidence": round(class_conf, 2),
            "sources_count": len(sources),
            "verified_attributes_count": verified_count,
            "unverified_attributes_count": unverified_count
        }
