from typing import List, Dict, Any

class CommerceSynthesizer:
    """
    Responsibilities 10 & 11:
    - Generate commerce-ready product information.
    - Preserve evidence supporting claims.
    - Clearly separate facts from marketing text and flag unverified claims.
    """

    TAXONOMY_MAP = {
        "drill": (["Tools & Home Improvement", "Power Tools", "Drills & Drivers", "Cordless Drills"], "27112703", "8467.21.00"),
        "laptop": (["Electronics", "Computers & Accessories", "Laptops & Notebooks"], "43211503", "8471.30.01"),
        "multimeter": (["Industrial & Scientific", "Test, Measure & Inspect", "Electrical Testing", "Multimeters"], "41113630", "9030.31.00"),
        "default": (["Industrial & Commercial Products", "General Equipment & Hardware"], "31160000", "8479.89.90")
    }

    def synthesize(
        self,
        norm_input: Dict[str, Any],
        specs: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        brand = norm_input["normalized_brand"]
        mpn = norm_input["mpn"]
        raw_desc = norm_input["clean_description"]

        # Identify key specs for title building
        spec_dict = {s["normalized_key"]: f"{s['value']} {s['unit'] or ''}".strip() for s in specs}

        # 1. Product Identity
        name_parts = [brand, mpn]
        if "voltage" in spec_dict:
            name_parts.append(spec_dict["voltage"])
        if "motor_type" in spec_dict:
            name_parts.append(spec_dict["motor_type"])
        elif "max_torque_hard" in spec_dict or "max_torque" in spec_dict:
            t_val = spec_dict.get("max_torque_hard") or spec_dict.get("max_torque")
            name_parts.append(f"({t_val})")
        
        canonical_name = f"{brand} {mpn} " + raw_desc.split('.')[0]
        commerce_title = " ".join(name_parts) + f" - {raw_desc}"

        # 2. Taxonomy & Classification
        category_path, unspsc, hs_code = self._determine_taxonomy(raw_desc, specs)
        
        classification = {
            "category_path": category_path,
            "unspsc_code": unspsc,
            "hs_code": hs_code,
            "target_market": "Professional / Heavy Duty" if "professional" in raw_desc.lower() or "heavy duty" in raw_desc.lower() else "Commercial & Industrial"
        }

        # 3. Bullet points derived strictly from verified specs
        feature_bullets = []
        unverified_claims = []

        for s in specs:
            if s.get("is_verified", False):
                feature_bullets.append(f"{s['key']}: {s['raw_value']} (Source Evidence: {s['evidence'].split('snippet:')[0].strip()})")

        # Flag any unverified marketing claims from original input description
        words = raw_desc.split()
        for word in words:
            if any(w in word.lower() for w in ["ultra", "best", "unbeatable", "patented", "revolutionary"]):
                unverified_claims.append(f"Unverified subjective marketing term in input description: '{word}'")

        if not feature_bullets:
            feature_bullets.append(f"Official model identifier: {mpn} by {brand}")

        # 4. Commerce Object
        commerce = {
            "title": commerce_title,
            "short_description": f"Official {brand} {mpn} specification package. {raw_desc}",
            "feature_bullets": feature_bullets,
            "seo_keywords": [
                brand.lower(),
                mpn.lower(),
                f"{brand.lower()} {mpn.lower()}",
                f"{mpn.lower()} specs",
                f"{brand.lower()} datasheet"
            ],
            "unverified_claims": unverified_claims
        }

        # 5. Applications & Use cases derived from product domain
        applications = self._generate_applications(raw_desc, specs)

        # 6. Identity Object
        identity = {
            "brand": norm_input["brand"],
            "normalized_brand": brand,
            "mpn": norm_input["mpn"],
            "normalized_mpn": norm_input["normalized_mpn"],
            "product_name": canonical_name,
            "model_series": f"{brand} Professional Series" if "professional" in raw_desc.lower() else None,
            "upc_gtin": None,
            "verification_status": "VERIFIED_MANUFACTURER" if any(s.get("is_verified") for s in specs) else "PARTIALLY_VERIFIED"
        }

        return {
            "identity": identity,
            "classification": classification,
            "commerce": commerce,
            "applications": applications
        }

    def _determine_taxonomy(self, desc: str, specs: List[Dict[str, Any]]) -> tuple:
        desc_lower = desc.lower()
        for kw, tax in self.TAXONOMY_MAP.items():
            if kw in desc_lower:
                return tax
        return self.TAXONOMY_MAP["default"]

    def _generate_applications(self, desc: str, specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        desc_lower = desc.lower()
        if "drill" in desc_lower or "driver" in desc_lower:
            return [
                {
                    "use_case": "Precision metal and timber drilling",
                    "recommended_environment": "Jobsite & Construction Workshop",
                    "suitability_rating": "High"
                },
                {
                    "use_case": "Heavy-duty screwdriving & fastening",
                    "recommended_environment": "Commercial Installation & Manufacturing",
                    "suitability_rating": "High"
                }
            ]
        elif "laptop" in desc_lower:
            return [
                {
                    "use_case": "Mobile Software Development & Data Analysis",
                    "recommended_environment": "Office & On-the-go",
                    "suitability_rating": "High"
                }
            ]
        return [
            {
                "use_case": "Industrial and commercial operations",
                "recommended_environment": "Facility Management & Field Service",
                "suitability_rating": "Medium"
            }
        ]
