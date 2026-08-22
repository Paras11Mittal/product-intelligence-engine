import re
from typing import List, Dict, Any
from app.utils.unit_converter import extract_numeric_and_unit, normalize_unit
from app.utils.logger import get_logger

logger = get_logger("SpecExtractor")

class SpecExtractor:
    """
    Responsibilities 5 & 6:
    - Extract relevant product specifications.
    - Normalize specifications into consistent names and units.
    - Attach exact source evidence.
    """

    KEY_CATEGORY_MAP = {
        "voltage": "Electrical",
        "power": "Electrical",
        "current": "Electrical",
        "battery": "Electrical",
        "motor": "Performance",
        "torque": "Performance",
        "speed": "Performance",
        "rpm": "Performance",
        "bpm": "Performance",
        "chuck": "Mechanical",
        "drilling_capacity": "Performance",
        "weight": "Physical",
        "dimensions": "Physical",
        "display": "Display",
        "processor": "Computing",
        "memory": "Computing",
        "storage": "Computing",
        "sound": "Acoustics",
        "temperature": "Environmental",
        "protection": "Environmental",
        "safety": "Safety"
    }
    _NON_PRODUCT_KEYS = {
        "phone", "telephone", "fax", "email", "address", "contact", "customer_service",
        "privacy", "cookie", "copyright", "hours", "sign_in", "log_in", "menu",
    }

    def extract_specs(self, raw_documents: List[Dict[str, Any]], sources_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        extracted = []

        for doc in raw_documents:
            src_id = doc["source_id"]
            src_info = sources_map.get(src_id, {})
            reliability = src_info.get("reliability_score", 0.5)
            snippet = doc.get("snippet", "")

            lines = snippet.split("\n")
            for line in lines:
                line_str = line.strip()
                if not line_str or ":" not in line_str:
                    continue
                
                parts = line_str.split(":", 1)
                raw_key = parts[0].strip()
                raw_val = parts[1].strip()

                # Ignore non-spec headers
                if raw_key.upper() in ["MANUFACTURER OFFICIAL DATASHEET", "DISTRIBUTOR CATALOG", "PRODUCT MODEL", "BRAND", "MPN"]:
                    continue

                normalized_key = self._normalize_key(raw_key)
                if normalized_key in self._NON_PRODUCT_KEYS or self._is_contact_value(raw_val):
                    continue
                norm_val, std_unit = extract_numeric_and_unit(raw_val)
                category = self._categorize_key(normalized_key)

                is_verified = src_info.get("source_type") == "MANUFACTURER" and reliability >= 0.90

                extracted.append({
                    "key": raw_key,
                    "normalized_key": normalized_key,
                    "value": norm_val,
                    "unit": std_unit,
                    "raw_value": raw_val,
                    "category": category,
                    "confidence": reliability,
                    "source_id": src_id,
                    "evidence": f"Found in '{doc.get('title')}' snippet: '{line_str}'",
                    "is_verified": is_verified
                })

        return extracted

    @staticmethod
    def _is_contact_value(value: str) -> bool:
        """Reject phone/email/URL values accidentally harvested from support pages."""
        compact = value.strip()
        phone_digits = re.sub(r"\D", "", compact)
        return "@" in compact or "http://" in compact.lower() or "https://" in compact.lower() or (len(phone_digits) >= 10 and len(compact) <= 24)

    def _normalize_key(self, raw_key: str) -> str:
        clean = raw_key.lower()
        clean = re.sub(r'[\(\)\/-]', ' ', clean)
        clean = re.sub(r'[^a-z0-9\s]', '', clean)
        clean = re.sub(r'\s+', '_', clean.strip())
        return clean

    def _categorize_key(self, norm_key: str) -> str:
        for keyword, cat in self.KEY_CATEGORY_MAP.items():
            if keyword in norm_key:
                return cat
        return "General"
