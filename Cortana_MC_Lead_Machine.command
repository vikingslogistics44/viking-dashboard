#!/bin/zsh

PDF_PATH=""
OUTPUT_CSV="/Users/kezrielandrew/Desktop/FMCSA_RUNS/MC CALL LIST FEB 25.csv"
SCRAPER="/Users/kezrielandrew/Desktop/fmcsa_scraper.py"

clear
echo "Cortana MC Lead Machine"
echo
echo "Paste the full PDF path, then press Enter."
echo "Example: /Users/kezrielandrew/Desktop/LI_CPL20250227.pdf"
echo
read "PDF_PATH?PDF PATH: "

if [[ -z "$PDF_PATH" ]]; then
  echo
  echo "No PDF path entered."
  read "noop?Press Enter to close..."
  exit 1
fi

if [[ ! -f "$PDF_PATH" ]]; then
  echo
  echo "File not found:"
  echo "$PDF_PATH"
  read "noop?Press Enter to close..."
  exit 1
fi

if [[ ! -f "$SCRAPER" ]]; then
  echo
  echo "Scraper not found:"
  echo "$SCRAPER"
  read "noop?Press Enter to close..."
  exit 1
fi

echo
echo "Running..."
echo "PDF: $PDF_PATH"
echo "CSV: $OUTPUT_CSV"
echo

python3 "$SCRAPER" --pdf "$PDF_PATH" --output "$OUTPUT_CSV" --append
STATUS=$?

echo
if [[ $STATUS -eq 0 ]]; then
  echo "Finished."
else
  echo "Run failed with exit code $STATUS."
fi

read "noop?Press Enter to close..."
