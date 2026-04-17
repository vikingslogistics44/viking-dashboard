import argparse
import csv
import os
import re
import sys

import pdfplumber
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_DIR = os.path.dirname(SCRIPT_DIR)
URL = "https://safer.fmcsa.dot.gov/CompanySnapshot.aspx"
MC_REGEX = r"\bMC[-\s]?(\d{5,8})\b"
MC_TIMEOUT_SECONDS = 10

DEFAULT_CSV_FILE = os.path.join(PIPELINE_DIR, "FMCSA_RESULTS.csv")

CSV_FIELDS = [
    "Company",
    "Phone",
    "City",
    "State",
    "Power Units",
    "Status",
    "Tag",
    "Call_Attempts",
    "Last_Called",
]


def log(message: str) -> None:
    print(message, flush=True)


def extract_mc_numbers(pdf_path: str) -> list[str]:
    mc_numbers = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                mc_numbers.extend(re.findall(MC_REGEX, text, re.IGNORECASE))
    unique_mcs = sorted(set(mc_numbers))
    log(f"Found {len(unique_mcs)} MC numbers")
    return unique_mcs


def setup_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(MC_TIMEOUT_SECONDS)
    return driver


def clean_value(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def normalize_authority_status(authority_raw: str) -> str:
    authority_clean = authority_raw.upper()
    if "AUTHORIZED" in authority_clean and "NOT" not in authority_clean:
        return "AUTHORIZED"
    if "NOT AUTHORIZED" in authority_clean:
        return "NOT AUTHORIZED"
    if "OUT-OF-SERVICE" in authority_clean or "OUT OF SERVICE" in authority_clean:
        return "OUT OF SERVICE"
    return "UNKNOWN"


def determine_lead_type(status: str, authority_status: str, power_units: int) -> str:
    if authority_status == "AUTHORIZED" and power_units <= 2:
        return "ACTIVE SMALL FLEET"
    if authority_status == "NOT AUTHORIZED":
        return "FUNDING / RESTART"
    if "OUT" in status.upper():
        return "REVIVAL"
    return "OTHER"


def is_broker(entity_type: str, carrier_operation: str, authority_raw: str) -> bool:
    signals = (
        entity_type.upper(),
        carrier_operation.upper(),
        authority_raw.upper(),
    )
    return any("BROKER" in value for value in signals)


def extract_labeled_value(section_text: str, label: str, next_labels: list[str]) -> str:
    escaped_label = re.escape(label)
    next_label_pattern = "|".join(re.escape(next_label) for next_label in next_labels)
    pattern = rf"{escaped_label}\s*(.*?)\s*(?={next_label_pattern}|$)"
    match = re.search(pattern, section_text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_result_section(driver: webdriver.Chrome, wait: WebDriverWait) -> str:
    results_table = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//table[contains(., 'USDOT INFORMATION') and contains(., 'COMPANY INFORMATION')]")
        )
    )
    return results_table.text


def parse_power_units(power_units_raw: str) -> int:
    try:
        return int(re.search(r"\d+", power_units_raw).group(0)) if power_units_raw else 0
    except ValueError:
        return 0
    except AttributeError:
        return 0


def parse_mileage(mileage_raw: str) -> str:
    match = re.search(r"[\d,]+", mileage_raw)
    return match.group(0).replace(",", "") if match else "0"


def parse_city_from_address_core(address_core: str) -> str:
    street_suffixes = (
        "ALY|AVE|AVENUE|BLVD|BOULEVARD|CIR|CIRCLE|COURT|CT|CV|DR|DRIVE|EXPY|"
        "FWY|HIGHWAY|HWY|LANE|LN|LOOP|PKWY|PLACE|PL|PLAZA|PLZ|RD|ROAD|RUN|SQ|"
        "ST|STREET|TER|TERRACE|TRL|TRAIL|WAY"
    )
    route_pattern = r"(?:\s+\d+[A-Z]?)?"
    postdir_pattern = (
        r"(?:\s+(?:N|S|E|W|NE|NW|SE|SW|NORTH|SOUTH|EAST|WEST|"
        r"NORTHEAST|NORTHWEST|SOUTHEAST|SOUTHWEST))*"
    )
    unit_pattern = r"(?:\s+(?:APT|APT\.|BLDG|DEPT|LOT|RM|SPACE|SPC|STE|SUITE|TRLR|UNIT)\s+\S+)*"
    street_pattern = (
        rf"^\d+\S*(?:\s+\S+)*?\s+(?:{street_suffixes}){route_pattern}{postdir_pattern}{unit_pattern}\s+(.+)$"
    )
    street_match = re.match(street_pattern, address_core, re.IGNORECASE)
    if street_match:
        return street_match.group(1).strip()
    return address_core


def parse_city_state(address_raw: str) -> tuple[str, str]:
    lines = [
        clean_value(line)
        for line in address_raw.replace("\xa0", " ").splitlines()
        if clean_value(line)
    ]
    if lines:
        city_state_line = lines[-1]
        match = re.search(r"(.+?),\s*([A-Z]{2})\s+\d{5}(?:-\d{4})?\b", city_state_line)
        if match:
            address_core = match.group(1).strip()
            return parse_city_from_address_core(address_core), match.group(2).strip()

    address = clean_value(address_raw)
    match = re.search(r"(.+?)\s+([A-Z]{2})\s+\d{5}(?:-\d{4})?\b", address)
    if match:
        address_core = match.group(1).strip()
        state = match.group(2).strip()
        return parse_city_from_address_core(address_core), state
    return "", ""


def scrape_mc(driver: webdriver.Chrome, mc: str):
    try:
        wait = WebDriverWait(driver, MC_TIMEOUT_SECONDS)
        driver.get(URL)

        wait.until(EC.element_to_be_clickable((By.ID, "2"))).click()

        box = wait.until(EC.presence_of_element_located((By.ID, "4")))
        box.clear()
        box.send_keys(mc)

        driver.execute_script("arguments[0].form.submit();", box)

        section_text = extract_result_section(driver, wait)

        if "No records matching" in section_text:
            return None, "No Record Found"

        label_order = [
            "Entity Type:",
            "USDOT Status:",
            "Out of Service Date:",
            "USDOT Number:",
            "State Carrier ID Number:",
            "MCS-150 Form Date:",
            "MCS-150 Mileage (Year):",
            "Operating Authority Status:",
            "MC/MX/FF Number(s):",
            "Legal Name:",
            "DBA Name:",
            "Physical Address:",
            "Phone:",
            "Mailing Address:",
            "DUNS Number:",
            "Power Units:",
            "Non-CMV Units:",
            "Drivers:",
            "Operation Classification:",
            "Carrier Operation:",
            "Cargo Carried:",
        ]

        raw_status = extract_labeled_value(section_text, "USDOT Status:", label_order[2:])
        raw_authority = extract_labeled_value(
            section_text, "Operating Authority Status:", label_order[8:]
        )
        raw_entity_type = extract_labeled_value(section_text, "Entity Type:", label_order[1:])
        raw_company = extract_labeled_value(section_text, "Legal Name:", label_order[10:])
        raw_physical_address = extract_labeled_value(
            section_text, "Physical Address:", label_order[12:]
        )
        raw_phone = extract_labeled_value(section_text, "Phone:", label_order[13:])
        raw_power_units = extract_labeled_value(section_text, "Power Units:", label_order[16:])
        raw_carrier_operation = extract_labeled_value(
            section_text, "Carrier Operation:", label_order[20:]
        )
        raw_mileage = extract_labeled_value(
            section_text, "MCS-150 Mileage (Year):", label_order[7:]
        )

        status = clean_value(raw_status)
        entity_type = clean_value(raw_entity_type)
        company = clean_value(raw_company)
        city, state = parse_city_state(raw_physical_address)
        phone = clean_value(raw_phone) or "N/A"
        power_units = parse_power_units(raw_power_units)
        mileage = parse_mileage(raw_mileage)
        carrier_operation = clean_value(raw_carrier_operation)

        authority_status = normalize_authority_status(raw_authority)

        if not company:
            return None, "Missing Company Name"
        if authority_status != "AUTHORIZED":
            return None, f"Authority Status: {authority_status}"
        if "OUT OF SERVICE" in status.upper() or "OUT-OF-SERVICE" in status.upper():
            return None, "Out Of Service"
        if is_broker(entity_type, carrier_operation, raw_authority):
            return None, "Broker"
        if power_units < 0 or power_units > 2:
            return None, f"Power Units: {power_units}"

        lead_type = determine_lead_type(status, authority_status, power_units)

        return {
            "Company": company,
            "Phone": phone,
            "City": city,
            "State": state,
            "Power Units": power_units,
            "Status": "",
            "Tag": lead_type,
            "Call_Attempts": 0,
            "Last_Called": "",
        }, None
    except TimeoutException:
        return None, "Timeout"
    except Exception as exc:
        return None, f"Error: {exc}"


def init_csv(csv_path: str) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()


def ensure_csv(csv_path: str) -> None:
    if not os.path.exists(csv_path):
        init_csv(csv_path)
        return

    with open(csv_path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        existing_fields = rows[0].keys() if rows else []

    if list(existing_fields) == CSV_FIELDS:
        return

    normalized_rows = []
    for row in rows:
        normalized_rows.append({field: row.get(field, "") for field in CSV_FIELDS})

    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(normalized_rows)


def load_existing_companies(csv_path: str) -> set[str]:
    existing_companies = set()
    if not os.path.exists(csv_path):
        return existing_companies

    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            company = (row.get("Company") or "").strip().upper()
            if company:
                existing_companies.add(company)
    return existing_companies


def append_result(csv_path: str, row: dict) -> None:
    with open(csv_path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writerow(row)


def print_row(mc: str, data: dict) -> None:
    log(
        f"✅ MC {mc} | {data['Company']} | Units: {data['Power Units']} | "
        f"{data['Phone']} | Tag: {data['Tag']}"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape FMCSA by MC numbers extracted from a PDF."
    )
    parser.add_argument("--pdf", required=True, help="Input PDF path")
    parser.add_argument(
        "--output",
        default=DEFAULT_CSV_FILE,
        help=f"Output CSV path. Defaults to {DEFAULT_CSV_FILE}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only process the first N MC numbers; 0 means all",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run Chrome with a visible window",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to an existing CSV and skip MCs already present in that file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output = DEFAULT_CSV_FILE

    try:
        mc_numbers = extract_mc_numbers(args.pdf)
    except Exception as exc:
        print(f"Failed to read PDF: {exc}", file=sys.stderr, flush=True)
        return 1

    if not mc_numbers:
        log("No MC numbers found")
        return 0

    if args.limit > 0:
        mc_numbers = mc_numbers[: args.limit]

    total = len(mc_numbers)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    ensure_csv(args.output)

    existing_companies = set()
    if args.append and os.path.exists(args.output):
        existing_companies = load_existing_companies(args.output)
        log(f"Appending to: {args.output}")
        log(f"Skipping {len(existing_companies)} companies already present in output")
    else:
        log(f"Saving to: {args.output}")

    try:
        driver = setup_driver(headless=not args.headed)
    except WebDriverException as exc:
        print(f"Failed to start Chrome WebDriver: {exc}", file=sys.stderr, flush=True)
        return 1

    saved_count = 0
    skipped_count = 0
    try:
        for index, mc in enumerate(mc_numbers, start=1):
            print(f"Processing {index}/{total} → MC {mc}", flush=True)
            data, reason = scrape_mc(driver, mc)
            if data:
                company_key = data["Company"].strip().upper()
                if company_key in existing_companies:
                    skipped_count += 1
                    print(f"❌ Skipped → MC {mc} (Company Already In Output)", flush=True)
                    log(
                        f"[Dashboard] {index}/{total} | Saved: {saved_count} | Skipped: {skipped_count}"
                    )
                    continue
                saved_count += 1
                append_result(args.output, data)
                existing_companies.add(company_key)
                print_row(mc, data)
            else:
                skipped_count += 1
                print(f"❌ Skipped → MC {mc} ({reason})", flush=True)
            log(
                f"[Dashboard] {index}/{total} | Saved: {saved_count} | Skipped: {skipped_count}"
            )
    finally:
        driver.quit()

    log(f"DONE → {saved_count} leads saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
