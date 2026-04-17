from pathlib import Path
import runpy


SCRIPT_PATH = (
    Path(__file__).resolve().parent
    / "CORTANA MC SCRAPER"
    / "run_fmcsa_pdf_scraper.py"
)

runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
