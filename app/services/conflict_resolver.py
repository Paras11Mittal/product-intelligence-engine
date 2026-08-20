from typing import List, Dict, Any, Tuple
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("ConflictResolver")

class ConflictResolver:
    """
    Responsibilities 7 & 8:
    - Detect conflicts between sources.
    - Determine which source/value is more reliable.
    - Report conflicts explicitly in final schema output.
    """

    def resolve_conflicts(
        self,
        extracted_specs: List[Dict[str, Any]],
        sources_map: Dict[str, Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:

        # Group by normalized_key
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for spec in extracted_specs:
            nk = spec["normalized_key"]
            if nk not in grouped:
                grouped[nk] = []
            grouped[nk].append(spec)

        final_specs = []
        conflicts = []

        for nk, spec_list in grouped.items():
            if len(spec_list) == 1:
                final_specs.append(spec_list[0])
                continue

            # Compare spec values across sources
            distinct_values: Dict[str, List[Dict[str, Any]]] = {}
            for s in spec_list:
                v_str = f"{s['value']} {s['unit']}".strip() if s['unit'] else s['value']
                if v_str not in distinct_values:
                    distinct_values[v_str] = []
                distinct_values[v_str].append(s)

            if len(distinct_values) == 1:
                # Perfect agreement among sources - boost confidence
                best_spec = max(spec_list, key=lambda x: x["confidence"])
                best_spec["confidence"] = min(1.0, best_spec["confidence"] + 0.05)
                final_specs.append(best_spec)
            else:
                # Conflict detected!
                competing_list = []
                for val_str, s_items in distinct_values.items():
                    top_item = max(s_items, key=lambda x: x["confidence"])
                    competing_list.append({
                        "value": val_str,
                        "source_id": top_item["source_id"],
                        "reliability": top_item["confidence"]
                    })

                # Sort by reliability score descending
                competing_list.sort(key=lambda c: c["reliability"], reverse=True)
                winning_comp = competing_list[0]
                winning_spec = next(s for s in spec_list if s["source_id"] == winning_comp["source_id"])

                w_source_type = sources_map.get(winning_comp["source_id"], {}).get("source_type", "UNKNOWN")
                reason = (
                    f"Selected '{winning_comp['value']}' from source ID '{winning_comp['source_id']}' "
                    f"({w_source_type}) because it holds higher authority score ({winning_comp['reliability']:.2f}) "
                    f"than competing values: {[c['value'] for c in competing_list[1:]]}."
                )

                conflicts.append({
                    "attribute": spec_list[0]["key"],
                    "competing_values": competing_list,
                    "resolved_value": winning_comp["value"],
                    "resolution_reason": reason
                })

                # Mark resolved spec
                winning_spec["evidence"] += f" [CONFLICT RESOLVED: Prioritized {w_source_type} over alternative distributor/third-party values]"
                final_specs.append(winning_spec)

        return final_specs, conflicts
