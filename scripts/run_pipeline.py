"""
End-to-End Test Case Generation Pipeline
---------------------------------------
Orchestrates:
1. Input extraction
2. Requirement normalization
3. Coverage expansion
4. LLM-based test case generation
5. Validation & de-duplication
6. Export to JSON and Excel
"""

import os
import json
import datetime
import pandas as pd

from normalization.normalize_requirements import normalize_requirements
from coverage.expand_coverage import expand_coverage
from generation.generate_testcases import generate_testcases
from validation.deduplicate import deduplicate
from validation.quality_checks import validate_testcases


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_DIR = os.path.join(BASE_DIR, "inputs")
EXTRACTED_DIR = os.path.join(BASE_DIR, "extracted", "raw_text")
REQ_DIR = os.path.join(BASE_DIR, "requirements")
OUTPUT_JSON = os.path.join(BASE_DIR, "output", "json")
OUTPUT_EXCEL = os.path.join(BASE_DIR, "output", "excel")
AUDIT_DIR = os.path.join(BASE_DIR, "output", "audit")


def ensure_dirs():
    for d in [EXTRACTED_DIR, REQ_DIR, OUTPUT_JSON, OUTPUT_EXCEL, AUDIT_DIR]:
        os.makedirs(d, exist_ok=True)


def load_raw_text():
    """
    Loads the latest RAW_TEXT file from extracted/raw_text
    """
    files = sorted(
        [f for f in os.listdir(EXTRACTED_DIR) if f.startswith("RAW_TEXT_")]
    )
    if not files:
        raise FileNotFoundError("No RAW_TEXT file found. Run extraction first.")
    latest = files[-1]
    with open(os.path.join(EXTRACTED_DIR, latest), "r", encoding="utf-8") as f:
        return f.read(), latest


def save_audit_log(message):
    log_file = os.path.join(
        AUDIT_DIR,
        f"generation_trace_{datetime.date.today().isoformat()}.log"
    )
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def main():
    ensure_dirs()
    save_audit_log("Pipeline started")

    # Step 1: Load Raw Text
    raw_text, raw_file = load_raw_text()
    save_audit_log(f"Loaded raw input: {raw_file}")

    # Step 2: Normalize Requirements
    requirements = normalize_requirements(raw_text)
    if not requirements:
        raise ValueError("No testable requirements found")

    req_file = os.path.join(
        REQ_DIR,
        "normalized_requirements.json"
    )
    with open(req_file, "w", encoding="utf-8") as f:
        json.dump(requirements, f, indent=2)

    save_audit_log(f"Normalized {len(requirements)} requirements")

    # Step 3: Expand Coverage
    coverage_items = expand_coverage(requirements)
    save_audit_log(f"Expanded to {len(coverage_items)} coverage intents")

    # Step 4: Generate Test Cases
    generated_testcases = generate_testcases(coverage_items)
    save_audit_log(f"Generated {len(generated_testcases)} raw test cases")

    # Step 5: Validate Test Cases
    valid_testcases, rejected = validate_testcases(generated_testcases)

    if rejected:
        reject_log = os.path.join(
            BASE_DIR, "validation", "reject_log.json"
        )
        with open(reject_log, "w", encoding="utf-8") as f:
            json.dump(rejected, f, indent=2)

        save_audit_log(f"Rejected {len(rejected)} invalid test cases")

    # Step 6: De-duplicate
    final_testcases = deduplicate(valid_testcases)
    save_audit_log(
        f"Final test case count after de-duplication: {len(final_testcases)}"
    )

    # Step 7: Export JSON
    json_out = os.path.join(
        OUTPUT_JSON,
        f"banking_test_cases_{datetime.date.today().isoformat()}.json"
    )
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(final_testcases, f, indent=2)

    save_audit_log(f"Exported JSON: {json_out}")

    # Step 8: Export Excel
    df = pd.DataFrame(final_testcases)
    excel_out = os.path.join(
        OUTPUT_EXCEL,
        f"banking_test_cases_{datetime.date.today().isoformat()}.xlsx"
    )
    df.to_excel(excel_out, index=False)

    save_audit_log(f"Exported Excel: {excel_out}")

    save_audit_log("Pipeline completed successfully")
    print("Test Case Generation Pipeline completed successfully")


if __name__ == "__main__":
    main()
