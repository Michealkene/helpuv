#!/bin/bash
# Upload ALL major CSV files from scraper directory
# Updated script to include all company data CSVs

LOG_DIR="/tmp/csv_uploads"
SCRAPER_DIR="$HOME/micky/scraper"
UPLOAD_SCRIPT="/var/www/helpuvio/upload_csv_data.py"

mkdir -p "$LOG_DIR"

echo "=========================================="
echo "UPLOADING ALL CSV FILES FROM SCRAPER"
echo "Time: $(date)"
echo "=========================================="

# Function to upload a CSV file
upload_csv() {
    local csv_file="$1"
    local filename=$(basename "$csv_file")
    local log_file="$LOG_DIR/${filename%.csv}_$(date +%s).log"

    echo ""
    echo "📁 Uploading: $filename"
    echo "   Size: $(du -h "$csv_file" | cut -f1)"
    echo "   Log: $log_file"

    python3 "$UPLOAD_SCRIPT" "$csv_file" --batch-size 500 > "$log_file" 2>&1

    if [ $? -eq 0 ]; then
        echo "   ✓ Completed successfully"
    else
        echo "   ✗ Completed with errors (check log)"
    fi

    # Show summary
    grep -E "Summary:|Total rows:|Inserted:|Skipped:" "$log_file" | sed 's/^/   /'

    # Current DB count
    current_count=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ')
    echo "   📊 Total in DB now: $current_count companies"
}

# Wait for any existing uploads
echo "Checking for running uploads..."
while ps aux | grep -v grep | grep "upload_csv_data.py" > /dev/null; do
    current_count=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ')
    echo "  ⏳ Upload in progress... Current: $current_count companies"
    sleep 15
done

BEFORE_COUNT=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ')
echo "Companies in database before new uploads: $BEFORE_COUNT"

echo ""
echo "=========================================="
echo "UPLOADING MAJOR CSV FILES"
echo "=========================================="

# Priority 1: Main data folder CSVs (already queued)
echo ""
echo "=== DATA FOLDER ==="
[ -f "$SCRAPER_DIR/data/companies_enriched.csv" ] && upload_csv "$SCRAPER_DIR/data/companies_enriched.csv"
[ -f "$SCRAPER_DIR/data/companies.csv" ] && upload_csv "$SCRAPER_DIR/data/companies.csv"
[ -f "$SCRAPER_DIR/data/companies1.csv" ] && upload_csv "$SCRAPER_DIR/data/companies1.csv"
[ -f "$SCRAPER_DIR/data/companiesusa.csv" ] && upload_csv "$SCRAPER_DIR/data/companiesusa.csv"

# Priority 2: Health industry (LARGE - 150MB!)
echo ""
echo "=== HEALTH INDUSTRY DATA ==="
[ -f "$SCRAPER_DIR/scripts/scraper/Health/companies1_enriched.csv" ] && upload_csv "$SCRAPER_DIR/scripts/scraper/Health/companies1_enriched.csv"
[ -f "$SCRAPER_DIR/scripts/scraper/Health/companies1.csv" ] && upload_csv "$SCRAPER_DIR/scripts/scraper/Health/companies1.csv"
[ -f "$SCRAPER_DIR/scripts/scraper/Health/ready.csv" ] && upload_csv "$SCRAPER_DIR/scripts/scraper/Health/ready.csv"

# Priority 3: Health ready subfiles
echo ""
echo "=== HEALTH READY FILES ==="
for file in "$SCRAPER_DIR/scripts/scraper/Health/ready"/*.csv; do
    [ -f "$file" ] && upload_csv "$file"
done

# Priority 4: Financial industry
echo ""
echo "=== FINANCIAL INDUSTRY DATA ==="
[ -f "$SCRAPER_DIR/scripts/scraper/Financial/companiesusa_enriched.csv" ] && upload_csv "$SCRAPER_DIR/scripts/scraper/Financial/companiesusa_enriched.csv"
[ -f "$SCRAPER_DIR/scripts/scraper/Financial/companiesusa.csv" ] && upload_csv "$SCRAPER_DIR/scripts/scraper/Financial/companiesusa.csv"
[ -f "$SCRAPER_DIR/scripts/scraper/Financial/readyfin.csv" ] && upload_csv "$SCRAPER_DIR/scripts/scraper/Financial/readyfin.csv"

# Priority 5: Importer data
echo ""
echo "=== IMPORTER DATA ==="
[ -f "$SCRAPER_DIR/scripts/importer/auto_companies.csv" ] && upload_csv "$SCRAPER_DIR/scripts/importer/auto_companies.csv"
[ -f "$SCRAPER_DIR/scripts/importer/ready.csv" ] && upload_csv "$SCRAPER_DIR/scripts/importer/ready.csv"

# Priority 6: Crawler data
echo ""
echo "=== CRAWLER DATA ==="
[ -f "$SCRAPER_DIR/scripts/crawer/home.csv" ] && upload_csv "$SCRAPER_DIR/scripts/crawer/home.csv"
[ -f "$SCRAPER_DIR/scripts/crawer/home_companies.csv" ] && upload_csv "$SCRAPER_DIR/scripts/crawer/home_companies.csv"
[ -f "$SCRAPER_DIR/scripts/crawer/await.csv" ] && upload_csv "$SCRAPER_DIR/scripts/crawer/await.csv"
[ -f "$SCRAPER_DIR/scripts/crawer/await_enriched.csv" ] && upload_csv "$SCRAPER_DIR/scripts/crawer/await_enriched.csv"

# Priority 7: Send folder data
echo ""
echo "=== SEND FOLDER DATA ==="
[ -f "$SCRAPER_DIR/send/ready.csv" ] && upload_csv "$SCRAPER_DIR/send/ready.csv"
[ -f "$SCRAPER_DIR/send/companies_enriched.csv" ] && upload_csv "$SCRAPER_DIR/send/companies_enriched.csv"
[ -f "$SCRAPER_DIR/send/australia/data/companies_canada.csv" ] && upload_csv "$SCRAPER_DIR/send/australia/data/companies_canada.csv"

# Priority 8: API folder data
echo ""
echo "=== API FOLDER DATA ==="
[ -f "$SCRAPER_DIR/Api/new_enriched.csv" ] && upload_csv "$SCRAPER_DIR/Api/new_enriched.csv"
[ -f "$SCRAPER_DIR/Api/new.csv" ] && upload_csv "$SCRAPER_DIR/Api/new.csv"

# Priority 9: API csv_uploads folder
echo ""
echo "=== API READY FILES ==="
for file in "$SCRAPER_DIR/Api/csv_uploads"/ready*.csv; do
    [ -f "$file" ] && upload_csv "$file"
done

# Priority 10: Root ready files
echo ""
echo "=== ROOT READY FILES ==="
[ -f "$SCRAPER_DIR/ready2.csv" ] && upload_csv "$SCRAPER_DIR/ready2.csv"
[ -f "$SCRAPER_DIR/companies_enriched.csv" ] && upload_csv "$SCRAPER_DIR/companies_enriched.csv"

# Final summary
echo ""
echo "=========================================="
echo "ALL UPLOADS COMPLETED!"
echo "Time: $(date)"
echo "=========================================="

AFTER_COUNT=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ')
echo "Total companies in database: $AFTER_COUNT"
echo "New companies added: $((AFTER_COUNT - BEFORE_COUNT))"

echo ""
echo "📊 DATABASE STATISTICS:"
docker exec helpuvio_postgres psql -U postgres -d helpuvio -c "
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN has_email THEN 1 END) as with_email,
    COUNT(CASE WHEN has_phone THEN 1 END) as with_phone,
    COUNT(DISTINCT country) as countries,
    COUNT(DISTINCT state) as states,
    COUNT(DISTINCT city) as cities
FROM companies;
" 2>/dev/null

echo ""
echo "✓ All CSV files uploaded!"
echo "Logs saved to: $LOG_DIR"
