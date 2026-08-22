"""Maps intelligence results to the Unihack catalog delivery CSV format."""

import csv
import io
from typing import Any, Iterable


ATTRIBUTE_COLUMNS = [
    column
    for index in range(1, 51)
    for column in (f"ATTRIBUTE_LABEL {index}", f"ATTRIBUTE_VALUE {index}", f"ATTRIBUTE_UOM {index}")
]

DELIVERY_COLUMNS = [
    "MFR URL", "Ref URL 1", "Ref URL 2", "Ref URL 3", "Ref URL 4", "Ref URL 5",
    "PART_NUMBER", "Dept", "Class", "Fine", "SKU - MY_PART_NUMBER", "Mfg_Part_Num",
    "Part_Desc", "E1_Brand", "Unilog_Brand", "DIB_Brand", "Part_Manuf",
    "MANUFACTURER_NAME", "BRAND_NAME", "TRADE_NAME", "MANUFACTURER_PART_NUMBER",
    "ALTERNATE_PART_NUMBER", "Classpath", "MOBILE_DESC", "INVOICE_DESC", "SHORT_DESC",
    "LONG_DESC1", "RETAIL_DESC", "MARKETING_DESCRIPTION",
    *[f"ITEM_FEATURES_{index}" for index in range(1, 21)],
    "With", "Standard/Approvals", "Prop 65", "Application", "Includes", "Product Name",
    *ATTRIBUTE_COLUMNS,
    "UPC", "EAN", "GTIN", "UNSPSC", "Warranty", "List Price", "Selling Qty", "Selling UOM",
    "Standard Packaging Information", "LENGTH", "LENGTH_UOM", "HEIGHT", "HEIGHT_UOM",
    "WIDTH", "WIDTH_UOM", "WEIGHT", "WEIGHT_UOM", "VOLUME", "VOLUME_UOM",
    "Product Image", "Alternate Image 1", "Alternate Image 2", "Alternate Image 3",
    "Alternate Image 4", "SDS", "SDS_1", "Warranty Information", "Catalog",
    "Specification Sheet", "Instruction/Installation Manual", "Service Manual", "Owners/User Manual",
    "Line Drawing", "MTR", "RoHS", "Full Engineering Drawing", "Energy Star Guide",
    "Technical Bulletin", "Submittal", "Compatibility Chart", "Size Chart", "Product Label/Insert",
    "Video Link", "Video Link 1", "Country Of Origin", "Discontinued", "Actual Image (Yes/No)",
]


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _first_spec(specifications: list[dict[str, Any]], *terms: str) -> dict[str, Any] | None:
    return next(
        (spec for spec in specifications if any(term in spec.get("normalized_key", "") for term in terms)),
        None,
    )


def _spec_value(specification: dict[str, Any] | None) -> tuple[str, str]:
    if not specification:
        return "", ""
    return _text(specification.get("value")), _text(specification.get("unit"))


def _source_urls(sources: list[dict[str, Any]]) -> tuple[str, list[str]]:
    manufacturer = next((item for item in sources if item.get("source_type") == "MANUFACTURER"), None)
    manufacturer_url = _text(manufacturer.get("url")) if manufacturer else ""
    other_urls = [_text(item.get("url")) for item in sources if _text(item.get("url")) and item is not manufacturer]
    return manufacturer_url, other_urls[:5]


def _document_links(sources: list[dict[str, Any]]) -> dict[str, str]:
    links = {"Specification Sheet": "", "Instruction/Installation Manual": "", "Owners/User Manual": "", "Service Manual": "", "SDS": "", "Catalog": ""}
    for source in sources:
        title = f"{source.get('name', '')} {source.get('url', '')}".lower()
        url = _text(source.get("url"))
        if not url:
            continue
        if "spec" in title or "datasheet" in title:
            links["Specification Sheet"] = links["Specification Sheet"] or url
        elif "install" in title or "instruction" in title:
            links["Instruction/Installation Manual"] = links["Instruction/Installation Manual"] or url
        elif "owner" in title or "user manual" in title:
            links["Owners/User Manual"] = links["Owners/User Manual"] or url
        elif "service" in title:
            links["Service Manual"] = links["Service Manual"] or url
        elif "sds" in title or "safety data" in title:
            links["SDS"] = links["SDS"] or url
        elif "catalog" in title:
            links["Catalog"] = links["Catalog"] or url
    return links


def to_delivery_row(result: dict[str, Any]) -> dict[str, str]:
    """Return one row using exactly the expected delivery column names and order."""
    row = {column: "" for column in DELIVERY_COLUMNS}
    identity = result.get("identity", {})
    classification = result.get("classification", {})
    commerce = result.get("commerce", {})
    applications = result.get("applications", [])
    specs = result.get("specifications", [])
    sources = result.get("sources", [])
    path = classification.get("category_path", [])
    mfr_url, ref_urls = _source_urls(sources)
    features = commerce.get("feature_bullets", [])[:20]
    manufacturer = identity.get("normalized_brand") or identity.get("brand", "")
    product_name = identity.get("product_name") or commerce.get("title", "")

    row.update({
        "MFR URL": mfr_url,
        "PART_NUMBER": _text(identity.get("normalized_mpn") or identity.get("mpn")),
        "Mfg_Part_Num": _text(identity.get("mpn")),
        "Part_Desc": _text(commerce.get("short_description")),
        "E1_Brand": _text(manufacturer),
        "Unilog_Brand": _text(manufacturer),
        "DIB_Brand": _text(manufacturer),
        "Part_Manuf": _text(manufacturer),
        "MANUFACTURER_NAME": _text(manufacturer),
        "BRAND_NAME": _text(manufacturer),
        "TRADE_NAME": _text(manufacturer),
        "MANUFACTURER_PART_NUMBER": _text(identity.get("normalized_mpn") or identity.get("mpn")),
        "Dept": _text(path[0]) if path else "",
        "Class": _text(path[1]) if len(path) > 1 else "",
        "Fine": _text(path[-1]) if path else "",
        "Classpath": ">".join(_text(item) for item in path),
        "MOBILE_DESC": _text(commerce.get("short_description")),
        "INVOICE_DESC": _text(commerce.get("title")),
        "SHORT_DESC": _text(commerce.get("short_description")),
        "LONG_DESC1": _text(commerce.get("short_description")),
        "RETAIL_DESC": _text(commerce.get("short_description")),
        "MARKETING_DESCRIPTION": _text(commerce.get("short_description")),
        "Application": _text(applications[0].get("use_case")) if applications else "",
        "Product Name": _text(product_name),
        "UNSPSC": _text(classification.get("unspsc_code")),
    })
    for index, url in enumerate(ref_urls, 1):
        row[f"Ref URL {index}"] = url
    for index, feature in enumerate(features, 1):
        row[f"ITEM_FEATURES_{index}"] = _text(feature)
    for index, spec in enumerate(specs[:50], 1):
        row[f"ATTRIBUTE_LABEL {index}"] = _text(spec.get("key"))
        row[f"ATTRIBUTE_VALUE {index}"] = _text(spec.get("value"))
        row[f"ATTRIBUTE_UOM {index}"] = _text(spec.get("unit"))

    gtin = _text(identity.get("upc_gtin"))
    row["GTIN"] = gtin
    length, length_uom = _spec_value(_first_spec(specs, "length"))
    height, height_uom = _spec_value(_first_spec(specs, "height"))
    width, width_uom = _spec_value(_first_spec(specs, "width"))
    weight, weight_uom = _spec_value(_first_spec(specs, "weight"))
    volume, volume_uom = _spec_value(_first_spec(specs, "volume"))
    country, _ = _spec_value(_first_spec(specs, "country_of_origin"))
    row.update({
        "LENGTH": length, "LENGTH_UOM": length_uom, "HEIGHT": height, "HEIGHT_UOM": height_uom,
        "WIDTH": width, "WIDTH_UOM": width_uom, "WEIGHT": weight, "WEIGHT_UOM": weight_uom,
        "VOLUME": volume, "VOLUME_UOM": volume_uom, "Country Of Origin": country,
    })
    row.update(_document_links(sources))
    return row


def delivery_csv(results: Iterable[dict[str, Any]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=DELIVERY_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(to_delivery_row(result) for result in results)
    return output.getvalue()
