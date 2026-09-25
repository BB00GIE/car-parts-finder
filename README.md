# Car Parts Finder

A lightweight Python application for checking whether a part number fits a vehicle based on year, make, and model. It supports OEM manufacturer part numbers and OES supplier part numbers.

## What it does

- Accepts a vehicle year, make, and model
- Receives a candidate part number
- Checks it against a catalog of OEM and OES numbers
- Returns whether the part fits and identifies the match source

## Project structure

- `car_parts_finder.py` – compatibility matching logic and dataset-backed catalog
- `app.py` – Flask web app and optional CLI entry point
- `templates/index.html` – browser form and result page
- `tests/test_compatibility.py` – verification for OEM and OES matches

## Example

Start the browser app:

```bash
python app.py
```

Then check a part in the browser form with values like:

- Year: `2018`
- Make: `Honda`
- Model: `Civic`
- Part: `06560TGGA01`

The CLI fallback still works:

```bash
python app.py --cli --year 2018 --make honda --model civic --part 06560TGGA01
```

Example output:

```text
The part number 06560TGGA01 matches an OES supplier part for the 2018 honda civic.
Match type: oes
Source: supplier
```

## How to run

1. Activate the virtual environment.
2. Start the web app with `python app.py`.
3. Open the local page in your browser.
4. Replace the default catalog in `car_parts_finder.py` with your own vehicle and part mappings.

## Notes

This is a starter project designed to be extended with:

- a real supplier catalog or database
- flexible lookup by common part families
- a richer vehicle filter set like engine, trim, and drivetrain
- a search layer across multiple OEM and aftermarket brands
