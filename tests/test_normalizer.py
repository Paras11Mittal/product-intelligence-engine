from input_normalizer import InputNormalizer


def test_normalizes_normal_input() -> None:
    result = InputNormalizer.normalize("Bosch", "GSR18V-55", "18V drill driver")
    assert result["validation"]["valid"] is True
    assert result["normalized_input"] == {
        "brand": "Bosch",
        "mpn": "GSR18V-55",
        "description": "18V drill driver",
    }
    assert result["search_query"] == 'Bosch "GSR18V-55"'


def test_trims_whitespace_and_preserves_raw_values() -> None:
    result = InputNormalizer.normalize("  Bosch ", " MPN: gsr 18v-55 ", "  Cordless\n drill  ")
    assert result["raw_input"]["mpn"] == " MPN: gsr 18v-55 "
    assert result["normalized_input"] == {
        "brand": "Bosch",
        "mpn": "GSR18V-55",
        "description": "Cordless drill",
    }


def test_normalizes_unicode_safely() -> None:
    result = InputNormalizer.normalize("Ｂｏｓｃｈ\u200b", "ＧＳＲ－18V－55", "18\u00a0V drill")
    assert result["normalized_input"] == {
        "brand": "Bosch",
        "mpn": "GSR-18V-55",
        "description": "18 V drill",
    }


def test_rejects_missing_fields() -> None:
    result = InputNormalizer.normalize("Bosch", None, "")
    assert result["validation"]["valid"] is False
    assert {error["field"] for error in result["validation"]["errors"]} == {"mpn", "description"}


def test_warns_about_unusual_mpn_characters() -> None:
    result = InputNormalizer.normalize("Bosch", "GSR@18V", "Drill")
    assert result["validation"]["valid"] is True
    assert result["warnings"][0]["code"] == "UNUSUAL_MPN_CHARACTERS"


def test_reports_conflicting_brand_aliases() -> None:
    result = InputNormalizer.normalize_record({
        "brand": "Bosch", "manufacturer": "Other Brand", "mpn": "GSR18V-55", "description": "Drill"
    })
    assert result["normalized_input"]["brand"] == "Bosch"
    assert result["warnings"][0]["code"] == "CONFLICTING_INPUT_ALIASES"
