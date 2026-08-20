"""Deterministic input cleanup for the product-intelligence pipeline.

This module does not identify products, research sources, or create product facts.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping


class InputNormalizer:
    """Normalize minimal product input while preserving the submitted values."""

    _FIELD_ALIASES: dict[str, tuple[str, ...]] = {
        "brand": ("brand", "manufacturer", "manufacturer_name"),
        "mpn": ("mpn", "manufacturer_part_number", "manufacturerPartNumber", "part_number"),
        "description": (
            "description",
            "product_description",
            "productDescription",
            "one_line_description",
        ),
    }
    _CONTROL_OR_ZERO_WIDTH = re.compile(r"[\x00-\x1f\x7f-\x9f\u200b-\u200d\ufeff]")
    _WHITESPACE = re.compile(r"\s+")
    _MPN_LABEL = re.compile(
        r"^\s*(?:mfr\.?\s*)?(?:part\s*(?:number|no\.?)|mpn)\s*[:#-]?\s*",
        re.IGNORECASE,
    )
    _NORMAL_MPN = re.compile(r"^[A-Z0-9./_+#-]+$")

    @classmethod
    def normalize(cls, brand: Any, mpn: Any, description: Any) -> dict[str, Any]:
        """Normalize three explicit product inputs.

        Values are returned in a JSON-serializable dictionary. Original values are
        retained exactly in ``raw_input``; normalized values are safe for matching.
        """
        return cls._build_result(brand, mpn, description, [])

    @classmethod
    def normalize_record(cls, input_data: Mapping[str, Any]) -> dict[str, Any]:
        """Normalize a request mapping and report conflicting field aliases.

        This helper supports FastAPI handlers that receive raw JSON with aliases
        such as ``manufacturer`` or ``manufacturer_part_number``.
        """
        if not isinstance(input_data, Mapping):
            return {
                "raw_input": {"brand": None, "mpn": None, "description": None},
                "normalized_input": {"brand": None, "mpn": None, "description": None},
                "search_keys": [],
                "search_query": None,
                "validation": {
                    "valid": False,
                    "errors": [{"code": "INVALID_INPUT", "message": "Expected an object containing brand, MPN, and description."}],
                },
                "warnings": [],
            }

        warnings: list[dict[str, Any]] = []
        values = {
            field: cls._read_field(input_data, field, warnings)
            for field in cls._FIELD_ALIASES
        }
        return cls._build_result(values["brand"], values["mpn"], values["description"], warnings)

    @classmethod
    def _clean_text(cls, value: Any) -> str | None:
        if value is None or isinstance(value, bool) or not isinstance(value, (str, int, float)):
            return None
        text = unicodedata.normalize("NFKC", str(value))
        text = cls._CONTROL_OR_ZERO_WIDTH.sub(" ", text)
        text = cls._WHITESPACE.sub(" ", text).strip()
        return text or None

    @classmethod
    def _read_field(cls, input_data: Mapping[str, Any], field: str, warnings: list[dict[str, Any]]) -> Any:
        candidates = [
            {"key": key, "value": cls._clean_text(input_data[key])}
            for key in cls._FIELD_ALIASES[field]
            if key in input_data and cls._clean_text(input_data[key]) is not None
        ]
        if len({candidate["value"] for candidate in candidates}) > 1:
            warnings.append(
                {
                    "code": "CONFLICTING_INPUT_ALIASES",
                    "field": field,
                    "message": f"Multiple values were supplied for {field}; the canonical field takes precedence.",
                    "values": candidates,
                }
            )
        return candidates[0]["value"] if candidates else None

    @classmethod
    def _normalize_mpn(cls, value: str | None, errors: list[dict[str, str]], warnings: list[dict[str, Any]]) -> str | None:
        if not value:
            return None
        normalized = cls._MPN_LABEL.sub("", value)
        normalized = cls._WHITESPACE.sub("", normalized).upper()
        if not normalized:
            return None
        if not re.search(r"[A-Z0-9]", normalized):
            errors.append({"code": "INVALID_MPN", "field": "mpn", "message": "MPN must include at least one letter or digit."})
        if not cls._NORMAL_MPN.fullmatch(normalized):
            warnings.append(
                {
                    "code": "UNUSUAL_MPN_CHARACTERS",
                    "field": "mpn",
                    "message": "MPN contains characters that may reduce matching accuracy; the value was preserved.",
                }
            )
        return normalized

    @classmethod
    def _build_result(cls, raw_brand: Any, raw_mpn: Any, raw_description: Any, warnings: list[dict[str, Any]]) -> dict[str, Any]:
        errors: list[dict[str, str]] = []
        brand = cls._clean_text(raw_brand)
        source_mpn = cls._clean_text(raw_mpn)
        description = cls._clean_text(raw_description)
        mpn = cls._normalize_mpn(source_mpn, errors, warnings)

        for field, value in (("brand", brand), ("mpn", mpn), ("description", description)):
            if value is None:
                errors.append({"code": "MISSING_REQUIRED_FIELD", "field": field, "message": f"{field} is required."})
        if description and len(description) > 500:
            warnings.append({"code": "LONG_DESCRIPTION", "field": "description", "message": "Description exceeds 500 characters; it was preserved."})

        search_keys = []
        if brand and mpn:
            search_keys.append(f'{brand} "{mpn}"')
        if brand and mpn and description:
            search_keys.append(f'{brand} "{mpn}" {description}')
        if mpn:
            search_keys.append(f'"{mpn}"')

        return {
            "raw_input": {"brand": raw_brand, "mpn": raw_mpn, "description": raw_description},
            "normalized_input": {"brand": brand, "mpn": mpn, "description": description},
            "normalized_brand": brand,  # <-- ADDED THIS
            "normalized_mpn": mpn,      # <-- ADDED THIS
            "search_keys": search_keys,
            "search_query": search_keys[0] if search_keys else None,
            "validation": {"valid": not errors, "errors": errors},
            "warnings": warnings,
        }