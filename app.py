from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path

from flask import Flask, render_template, request

from car_parts_finder import CompatibilityChecker, add_catalog_entry, load_catalog, save_catalog

app = Flask(__name__)
CATALOG_PATH = Path(__file__).with_name("catalog.json")


@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        vehicle_year = request.form.get("year", "").strip()
        vehicle_make = request.form.get("make", "").strip()
        vehicle_model = request.form.get("model", "").strip()
        part_number = request.form.get("part_number", "").strip()

        if all([vehicle_year, vehicle_make, vehicle_model, part_number]):
            catalog = load_catalog(CATALOG_PATH)
            result = CompatibilityChecker(catalog).check(
                vehicle_year=vehicle_year,
                vehicle_make=vehicle_make,
                vehicle_model=vehicle_model,
                part_number=part_number,
            )

    return render_template("index.html", result=result)


@app.route("/catalog", methods=["GET", "POST"])
def catalog_manager():
    message = None

    if request.method == "POST":
        if request.files.get("catalog_file"):
            uploaded_file = request.files["catalog_file"]
            if uploaded_file.filename:
                catalog = load_catalog(CATALOG_PATH)
                stream = io.StringIO(uploaded_file.read().decode("utf-8"))
                reader = csv.DictReader(stream)
                for row in reader:
                    if not row:
                        continue
                    add_catalog_entry(
                        catalog,
                        row.get("year", ""),
                        row.get("make", ""),
                        row.get("model", ""),
                        row.get("oem_part_numbers", ""),
                        row.get("oes_part_numbers", ""),
                    )
                save_catalog(CATALOG_PATH, catalog)
                message = f"Imported catalog entries from {uploaded_file.filename}."
        else:
            year = request.form.get("year", "").strip()
            make = request.form.get("make", "").strip()
            model = request.form.get("model", "").strip()
            oem_part_numbers = request.form.get("oem_part_numbers", "").strip()
            oes_part_numbers = request.form.get("oes_part_numbers", "").strip()

            supplier_name = request.form.get("supplier_name", "").strip()
            part_family = request.form.get("part_family", "").strip()
            price = request.form.get("price", "").strip()
            source_type = request.form.get("source_type", "supplier").strip() or "supplier"
            notes = request.form.get("notes", "").strip()

            if all([year, make, model]):
                catalog = load_catalog(CATALOG_PATH)
                add_catalog_entry(
                    catalog,
                    year,
                    make,
                    model,
                    oem_part_numbers,
                    oes_part_numbers,
                    supplier_name=supplier_name,
                    part_family=part_family,
                    price=price,
                    source_type=source_type,
                    notes=notes,
                )
                save_catalog(CATALOG_PATH, catalog)
                message = f"Saved part numbers for {year} {make} {model}."

    return render_template("catalog.html", message=message)


def run_cli(args: argparse.Namespace) -> None:
    if not all([args.year, args.make, args.model, args.part_number]):
        print("Enter vehicle information and a part number.")
        print("Example: python app.py --cli --year 2018 --make honda --model civic --part 06560TGGA01")
        return

    catalog = load_catalog(args.catalog)
    result = CompatibilityChecker(catalog).check(
        vehicle_year=args.year,
        vehicle_make=args.make,
        vehicle_model=args.model,
        part_number=args.part_number,
    )

    print(result["message"])
    if result["fits"]:
        print(f"Match type: {result['match_type']}")
        print(f"Source: {result['source']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check if a part number is compatible with a vehicle.")
    parser.add_argument("--cli", action="store_true", help="Use the terminal-based checker instead of the web UI")
    parser.add_argument("--catalog", default="catalog.json", help="Path to the JSON catalog file used for OEM/OES lookups")
    parser.add_argument("--year", type=int, help="Vehicle model year")
    parser.add_argument("--make", help="Vehicle make")
    parser.add_argument("--model", help="Vehicle model")
    parser.add_argument("--part", dest="part_number", help="OEM or OES part number to check")
    parser.add_argument("--host", default="127.0.0.1", help="Web app host")
    parser.add_argument("--port", type=int, default=5000, help="Web app port")
    args = parser.parse_args()

    if args.cli or any([args.year, args.make, args.model, args.part_number]):
        run_cli(args)
        return

    app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
