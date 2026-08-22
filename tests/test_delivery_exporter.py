import csv
import io

from app.services.delivery_exporter import DELIVERY_COLUMNS, delivery_csv


def test_delivery_csv_preserves_header_order_and_unknown_blanks():
    result = {
        "identity": {"brand": "Acme", "mpn": "A-100", "normalized_mpn": "A100"},
        "classification": {"category_path": []},
        "commerce": {},
        "applications": [],
        "specifications": [],
        "sources": [],
    }

    reader = csv.DictReader(io.StringIO(delivery_csv([result])))
    rows = list(reader)

    assert len(DELIVERY_COLUMNS) == 252
    assert reader.fieldnames == DELIVERY_COLUMNS
    assert rows[0]["Mfg_Part_Num"] == "A-100"
    assert rows[0]["Part_Desc"] == ""
    assert rows[0]["ATTRIBUTE_VALUE 1"] == ""


def test_delivery_csv_emits_one_row_per_successful_result():
    base = {
        "classification": {"category_path": []}, "commerce": {}, "applications": [],
        "specifications": [], "sources": [],
    }
    first = {**base, "identity": {"brand": "Acme", "mpn": "A-100"}}
    second = {**base, "identity": {"brand": "Acme", "mpn": "A-200"}}

    rows = list(csv.DictReader(io.StringIO(delivery_csv([first, second]))))

    assert [row["Mfg_Part_Num"] for row in rows] == ["A-100", "A-200"]
