#!/bin/bash
# Comprehensive CSV Upload Script
# Uploads all CSV files from scraper directory to local PostgreSQL

set -e

LOG_DIR="/tmp/csv_uploads"
SCRAPER_DIR="$HOME/micky/scraper"
UPLOAD_SCRIPT="/var/www/helpuvio/upload_csv_data.py"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MAIN_LOG="$LOG_DIR/upload_all_${TIMESTAMP}.log"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

mkdir -p "$LOG_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          CSV UPLOAD TO LOCAL POSTGRESQL DATABASE               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Started at: $(date)${NC}"
echo -e "${GREEN}Log directory: $LOG_DIR${NC}"
echo ""

# Function to upload a CSV file
upload_csv() {
    local csv_file="$1"
    local file_name=$(basename "$csv_file")
    local log_file="$LOG_DIR/${file_name%.csv}_${TIMESTAMP}.log"

    echo -e "${YELLOW}Uploading: $file_name${NC}"
    echo "  Size: $(du -h "$csv_file" | cut -f1)"
    echo "  Log: $log_file"

    if python3 "$UPLOAD_SCRIPT" "$csv_file" > "$log_file" 2>&1; then
        echo -e "${GREEN}✓ Success: $file_name${NC}"
        echo "---" >> "$MAIN_LOG"
        echo "SUCCESS: $file_name" >> "$MAIN_LOG"
        tail -5 "$log_file" >> "$MAIN_LOG"
    else
        echo -e "${RED}✗ Failed: $file_name${NC}"
        echo "  Check log: $log_file"
        echo "---" >> "$MAIN_LOG"
        echo "FAILED: $file_name" >> "$MAIN_LOG"
        tail -10 "$log_file" >> "$MAIN_LOG"
    fi
    echo ""
}

# Priority CSV files to upload
declare -a PRIORITY_FILES=(
    "$SCRAPER_DIR/data/companies.csv"
    "$SCRAPER_DIR/data/companies_enriched.csv"
    "$SCRAPER_DIR/data/companiesusa.csv"
    "$SCRAPER_DIR/data/ready.csv"
    "$SCRAPER_DIR/data/companies1.csv"
)

# Upload priority files
echo -e "${BLUE}=== PRIORITY FILES (Main Data Directory) ===${NC}"
echo ""
for csv_file in "${PRIORITY_FILES[@]}"; do
    if [ -f "$csv_file" ]; then
        upload_csv "$csv_file"
    else
        echo -e "${YELLOW}⊘ Skipped (not found): $(basename "$csv_file")${NC}"
        echo ""
    fi
done

# Upload ready files from __pycache__/csv_files
echo -e "${BLUE}=== READY FILES (Cache Directory) ===${NC}"
echo ""
if [ -d "$SCRAPER_DIR/__pycache__/csv_files" ]; then
    for csv_file in "$SCRAPER_DIR/__pycache__/csv_files"/ready*.csv; do
        if [ -f "$csv_file" ]; then
            upload_csv "$csv_file"
        fi
    done
fi

# Upload country-specific files
echo -e "${BLUE}=== COUNTRY-SPECIFIC FILES ===${NC}"
echo ""

# UK files
if [ -f "$SCRAPER_DIR/send/uk/data/companies_uk.csv" ]; then
    upload_csv "$SCRAPER_DIR/send/uk/data/companies_uk.csv"
fi

# Canada files
if [ -f "$SCRAPER_DIR/send/australia/data/companies_canada.csv" ]; then
    upload_csv "$SCRAPER_DIR/send/australia/data/companies_canada.csv"
fi

# Australia files
if [ -f "$SCRAPER_DIR/send/australia/data/scraped_businesses.csv" ]; then
    upload_csv "$SCRAPER_DIR/send/australia/data/scraped_businesses.csv"
fi

# Additional files
if [ -f "$SCRAPER_DIR/send/companies_enriched.csv" ]; then
    upload_csv "$SCRAPER_DIR/send/companies_enriched.csv"
fi

if [ -f "$SCRAPER_DIR/send/ready.csv" ]; then
    upload_csv "$SCRAPER_DIR/send/ready.csv"
fi

# Check final database count
echo -e "${BLUE}=== FINAL DATABASE STATUS ===${NC}"
echo ""
TOTAL_COMPANIES=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies;" | xargs)
echo -e "${GREEN}Total companies in database: $TOTAL_COMPANIES${NC}"
echo ""

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    UPLOAD COMPLETED                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Finished at: $(date)${NC}"
echo -e "${GREEN}Main log: $MAIN_LOG${NC}"
echo ""
echo "To check detailed logs for any file:"
echo "  ls -lh $LOG_DIR/"
echo ""
