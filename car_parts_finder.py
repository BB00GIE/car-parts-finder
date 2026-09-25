from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_CATALOG: dict[str, Any] = {
    "2018": {
        "Honda": {
            "Civic": {
                "oem_part_numbers": ["06560-TGG-A01", "12345-HONDA-01"],
                "oes_part_numbers": ["06560TGGA01", "A1-06560-TGG-A01"],
            }
        },
        "Toyota": {
            "Corolla": {
                "oem_part_numbers": ["04465-02170", "89485-02020"],
                "oes_part_numbers": ["0446502170", "8948502020"],
            }
        },
    },
    "2020": {
        "Ford": {
            "Focus": {
                "oem_part_numbers": ["B7GZ-7A095-AA", "HL3Z-5A234-AA"],
                "oes_part_numbers": ["B7GZ7A095AA", "HL3Z5A234AA"],
            }
        }
    },
}


def normalize_part_number(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", str(value).upper())


def normalize_vehicle_label(value: str) -> str:
    return str(value).strip().title()


def _split_part_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = str(value).replace("\n", ";").replace("|", ";").split(";")

    cleaned: list[str] = []
    for item in values:
        part = str(item).strip()
        if part and part not in cleaned:
            cleaned.append(part)
    return cleaned


def _build_part_entries(
    values: Any,
    *,
    supplier_name: str = "",
    part_family: str = "",
    price: str = "",
    source_type: str = "",
    notes: str = "",
) -> list[Any]:
    items = _split_part_list(values)
    if not items:
        return []

    has_metadata = any([supplier_name, part_family, price, source_type, notes])
    if not has_metadata:
        return items

    entries: list[Any] = []
    for part in items:
        entry: dict[str, str] = {"part_number": part}
        if supplier_name:
            entry["supplier_name"] = supplier_name
        if part_family:
            entry["part_family"] = part_family
        if price:
            entry["price"] = price
        if source_type:
            entry["source_type"] = source_type
        if notes:
            entry["notes"] = notes
        entries.append(entry)
    return entries


def _merge_catalog_record(
    catalog: dict[str, Any],
    year: str | int,
    make: str,
    model: str,
    oem_parts: list[Any],
    oes_parts: list[Any],
) -> dict[str, Any]:
    year_key = str(year)
    make_key = normalize_vehicle_label(make)
    model_key = normalize_vehicle_label(model)

    year_bucket = catalog.setdefault(year_key, {})
    make_bucket = year_bucket.setdefault(make_key, {})
    model_bucket = make_bucket.setdefault(model_key, {"oem_part_numbers": [], "oes_part_numbers": []})

    model_bucket["oem_part_numbers"] = list(dict.fromkeys(model_bucket.get("oem_part_numbers", []) + oem_parts))
    model_bucket["oes_part_numbers"] = list(dict.fromkeys(model_bucket.get("oes_part_numbers", []) + oes_parts))
    return catalog


def load_catalog(source: str | Path | dict[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(source, dict):
        return source

    if source is None:
        source = Path(__file__).with_name("catalog.json")

    path = Path(source)
    if not path.exists():
        return DEFAULT_CATALOG

    if path.suffix.lower() == ".csv":
        catalog: dict[str, Any] = {}
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if not row:
                    continue
                year = (row.get("year") or row.get("Year") or "").strip()
                make = (row.get("make") or row.get("Make") or "").strip()
                model = (row.get("model") or row.get("Model") or "").strip()
                if not year or not make or not model:
                    continue
                supplier_name = (row.get("supplier_name") or row.get("supplier") or "").strip()
                part_family = (row.get("part_family") or row.get("family") or "").strip()
                price = (row.get("price") or "").strip()
                source_type = (row.get("source_type") or row.get("type") or "").strip()
                notes = (row.get("notes") or "").strip()
                oem = _build_part_entries(
                    row.get("oem_part_numbers") or row.get("OEM Part Numbers") or row.get("oem") or "",
                    supplier_name=supplier_name,
                    part_family=part_family,
                    price=price,
                    source_type=source_type,
                    notes=notes,
                )
                oes = _build_part_entries(
                    row.get("oes_part_numbers") or row.get("OES Part Numbers") or row.get("oes") or "",
                    supplier_name=supplier_name,
                    part_family=part_family,
                    price=price,
                    source_type=source_type,
                    notes=notes,
                )
                _merge_catalog_record(catalog, year, make, model, oem, oes)
        return catalog

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, dict):
        return data

    raise ValueError("The catalog file must contain a JSON object keyed by vehicle year, make, and model.")


def save_catalog(source: str | Path, catalog: dict[str, Any]) -> None:
    path = Path(source)
    path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


def add_catalog_entry(
    catalog: dict[str, Any],
    year: str | int,
    make: str,
    model: str,
    oem_part_numbers: Any = None,
    oes_part_numbers: Any = None,
    *,
    supplier_name: str = "",
    part_family: str = "",
    price: str = "",
    source_type: str = "",
    notes: str = "",
) -> dict[str, Any]:
    return _merge_catalog_record(
        catalog,
        year,
        make,
        model,
        _build_part_entries(
            oem_part_numbers,
            supplier_name=supplier_name,
            part_family=part_family,
            price=price,
            source_type=source_type,
            notes=notes,
        ),
        _build_part_entries(
            oes_part_numbers,
            supplier_name=supplier_name,
            part_family=part_family,
            price=price,
            source_type=source_type,
            notes=notes,
        ),
    )


class CompatibilityChecker:
    def __init__(self, catalog: dict[str, Any] | str | Path | None = None):
        self.catalog = load_catalog(catalog) if not isinstance(catalog, dict) or catalog is None else catalog

    def _vehicle_record(self, vehicle_year: int | str, vehicle_make: str, vehicle_model: str) -> dict[str, Any] | None:
        year_key = str(vehicle_year)
        make_key = normalize_vehicle_label(vehicle_make)
        model_key = normalize_vehicle_label(vehicle_model)

        return self.catalog.get(year_key, {}).get(make_key, {}).get(model_key)

    def check(
        self,
        *,
        vehicle_year: int | str,
        vehicle_make: str,
        vehicle_model: str,
        part_number: str,
    ) -> dict[str, Any]:
        record = self._vehicle_record(vehicle_year, vehicle_make, vehicle_model)

        if record is None:
            return {
                "fits": False,
                "match_type": None,
                "source": None,
                "message": (
                    f"The part number {part_number} is not compatible with the {vehicle_year} {vehicle_make} {vehicle_model}. "
                    "There is no matching vehicle information in the catalog."
                ),
            }

        candidate = str(part_number).strip()
        if candidate:
            normalized_input = normalize_part_number(candidate)

            for kind, label in [("oem", "manufacturer"), ("oes", "supplier")]:
                for raw_part in record.get(f"{kind}_part_numbers", []):
                    if isinstance(raw_part, dict):
                        part_value = str(raw_part.get("part_number") or raw_part.get("number") or raw_part.get("value") or "").strip()
                        metadata = raw_part
                    else:
                        part_value = str(raw_part).strip()
                        metadata = {}

                    if part_value and part_value.casefold() == candidate.casefold():
                        result = {
                            "fits": True,
                            "match_type": kind,
                            "source": label,
                            "message": (
                                f"The part number {part_number} matches an {kind.upper()} part for the {vehicle_year} "
                                f"{vehicle_make} {vehicle_model}."
                            ),
                            "supplier_name": metadata.get("supplier_name"),
                            "part_family": metadata.get("part_family"),
                            "price": metadata.get("price"),
                            "source_type": metadata.get("source_type") or label,
                            "notes": metadata.get("notes"),
                            "catalog_part_number": part_value,
                        }
                        if kind == "oes":
                            result["message"] = (
                                f"The part number {part_number} matches an OES supplier part for the {vehicle_year} "
                                f"{vehicle_make} {vehicle_model}."
                            )
                        return result

            for kind, label in [("oem", "manufacturer"), ("oes", "supplier")]:
                for raw_part in record.get(f"{kind}_part_numbers", []):
                    if isinstance(raw_part, dict):
                        part_value = str(raw_part.get("part_number") or raw_part.get("number") or raw_part.get("value") or "").strip()
                        metadata = raw_part
                    else:
                        part_value = str(raw_part).strip()
                        metadata = {}

                    if part_value and normalize_part_number(part_value) == normalized_input:
                        result = {
                            "fits": True,
                            "match_type": kind,
                            "source": label,
                            "message": (
                                f"The part number {part_number} matches an {kind.upper()} part for the {vehicle_year} "
                                f"{vehicle_make} {vehicle_model}."
                            ),
                            "supplier_name": metadata.get("supplier_name"),
                            "part_family": metadata.get("part_family"),
                            "price": metadata.get("price"),
                            "source_type": metadata.get("source_type") or label,
                            "notes": metadata.get("notes"),
                            "catalog_part_number": part_value,
                        }
                        if kind == "oes":
                            result["message"] = (
                                f"The part number {part_number} matches an OES supplier part for the {vehicle_year} "
                                f"{vehicle_make} {vehicle_model}."
                            )
                        return result

        return {
            "fits": False,
            "match_type": None,
            "source": None,
            "message": (
                f"The part number {part_number} is not compatible with the {vehicle_year} {vehicle_make} {vehicle_model}. "
                "It does not match any OEM or OES numbers in the catalog."
            ),
        }


def demo_check() -> dict[str, Any]:
    checker = CompatibilityChecker()
    return checker.check(
        vehicle_year=2018,
        vehicle_make="Honda",
        vehicle_model="Civic",
        part_number="A1-06560-TGG-A01",
    )
