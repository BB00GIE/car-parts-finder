import json

import pytest

from car_parts_finder import CompatibilityChecker, load_catalog


@pytest.fixture
def checker():
    return CompatibilityChecker(
        {
            "2018": {
                "Honda": {
                    "Civic": {
                        "oem_part_numbers": ["06560-TGG-A01", "12345-HONDA-01"],
                        "oes_part_numbers": ["06560TGGA01", "A1-06560-TGG-A01"],
                    }
                }
            }
        }
    )


def test_exact_oem_part_number_matches_vehicle(checker):
    result = checker.check(vehicle_year=2018, vehicle_make="Honda", vehicle_model="Civic", part_number="06560-TGG-A01")

    assert result["fits"] is True
    assert result["match_type"] == "oem"
    assert result["source"] == "manufacturer"


def test_oes_part_number_matches_vehicle(checker):
    result = checker.check(vehicle_year=2018, vehicle_make="Honda", vehicle_model="Civic", part_number="06560TGGA01")

    assert result["fits"] is True
    assert result["match_type"] == "oes"
    assert result["source"] == "supplier"


def test_non_matching_vehicle_returns_no_fit(checker):
    result = checker.check(vehicle_year=2018, vehicle_make="Honda", vehicle_model="Accord", part_number="06560-TGG-A01")

    assert result["fits"] is False
    assert result["match_type"] is None
    assert "not compatible" in result["message"].lower()


def test_json_catalog_loader_loads_remote_style_catalog(tmp_path):
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "2018": {
                    "Honda": {
                        "Civic": {
                            "oem_part_numbers": ["11111-ABC-01"],
                            "oes_part_numbers": ["11111ABC01"],
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    catalog = load_catalog(catalog_path)
    checker = CompatibilityChecker(catalog)
    result = checker.check(vehicle_year=2018, vehicle_make="Honda", vehicle_model="Civic", part_number="11111ABC01")

    assert result["fits"] is True
    assert result["match_type"] == "oes"
    assert result["source"] == "supplier"


def test_csv_catalog_loader_loads_supplier_rows(tmp_path):
    catalog_path = tmp_path / "catalog.csv"
    catalog_path.write_text(
        "year,make,model,oem_part_numbers,oes_part_numbers\n"
        "2018,Honda,Civic,11111-ABC-01;22222-XYZ-02,11111ABC01;22222XYZ02\n",
        encoding="utf-8",
    )

    catalog = load_catalog(catalog_path)
    checker = CompatibilityChecker(catalog)
    result = checker.check(vehicle_year=2018, vehicle_make="Honda", vehicle_model="Civic", part_number="22222XYZ02")

    assert result["fits"] is True
    assert result["match_type"] == "oes"
    assert result["source"] == "supplier"


def test_catalog_metadata_is_returned_with_match():
    checker = CompatibilityChecker(
        {
            "2018": {
                "Honda": {
                    "Civic": {
                        "oem_part_numbers": [],
                        "oes_part_numbers": [
                            {
                                "part_number": "11111ABC01",
                                "supplier_name": "Apex Auto",
                                "part_family": "brake",
                                "price": "89.99",
                                "source_type": "supplier",
                                "notes": "Aftermarket equivalent",
                            }
                        ],
                    }
                }
            }
        }
    )

    result = checker.check(vehicle_year=2018, vehicle_make="Honda", vehicle_model="Civic", part_number="11111ABC01")

    assert result["fits"] is True
    assert result["supplier_name"] == "Apex Auto"
    assert result["part_family"] == "brake"
    assert result["source_type"] == "supplier"
    assert result["price"] == "89.99"
    assert result["notes"] == "Aftermarket equivalent"
