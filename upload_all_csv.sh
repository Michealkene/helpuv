#!/bin/bash
# Upload all CSV files from scraper data directory
# This script uploads CSV files sequentially and logs all results

LOG_DIR="/tmp/csv_uploads"
DATA_DIR="$HOME/micky/scraper/data"
UPLOAD_SCRIPT="/var/www/helpuvio/upload_csv_data.py"

mkdir -p "$LOG_DIR"

echo "=========================================="
echo "CSV Upload Process Started"
echo "Time: $(date)"
echo "=========================================="

# Function to upload a CSV file
upload_csv() {
    local csv_file="$1"
    local filename=$(basename "$csv_file")
    local log_file="$LOG_DIR/${filename%.csv}.log"

    echo ""
    echo "📁 Uploading: $filename"
    echo "   Log: $log_file"

    python3 "$UPLOAD_SCRIPT" "$csv_file" --batch-size 200 > "$log_file" 2>&1

    if [ $? -eq 0 ]; then
        echo "   ✓ Completed successfully"
    else
        echo "   ✗ Completed with errors (check log)"
    fi

    # Show summary from log
    grep -E "Summary:|Total rows:|Inserted:|Skipped:" "$log_file" | sed 's/^/   /'
}

# Wait for current upload to finish
echo "Checking for running uploads..."
while ps aux | grep -v grep | grep "upload_csv_data.py.*ready.csv" > /dev/null; do
    current_count=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ')
    echo "  Current progress: $current_count companies uploaded..."
    sleep 10
done

echo "✓ ready.csv upload completed"
echo ""

# Get current database count
BEFORE_COUNT=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ')
echo "Companies in database before additional uploads: $BEFORE_COUNT"

# Upload remaining CSV files
echo ""
echo "Uploading additional CSV files..."

# companies_enriched.csv (26MB)
if [ -f "$DATA_DIR/companies_enriched.csv" ]; then
    upload_csv "$DATA_DIR/companies_enriched.csv"
fi

# companies.csv (11MB)
if [ -f "$DATA_DIR/companies.csv" ]; then
    upload_csv "$DATA_DIR/companies.csv"
fi

# companies1.csv (1MB)
if [ -f "$DATA_DIR/companies1.csv" ]; then
    upload_csv "$DATA_DIR/companies1.csv"
fi

# companiesusa.csv (998KB)
if [ -f "$DATA_DIR/companiesusa.csv" ]; then
    upload_csv "$DATA_DIR/companiesusa.csv"
fi

# Final summary
echo ""
echo "=========================================="
echo "Upload Process Completed!"
echo "Time: $(date)"
echo "=========================================="

AFTER_COUNT=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ')
echo "Total companies in database: $AFTER_COUNT"
echo "New companies added: $((AFTER_COUNT - BEFORE_COUNT))"

# Email verification status
echo ""
echo "Email Verification Status:"
docker exec helpuvio_postgres psql -U postgres -d helpuvio -c "
    SELECT
        email_verification_status,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM companies), 2) as percentage
    FROM companies
    GROUP BY email_verification_status;
" 2>/dev/null

echo ""
echo "All uploads complete! Check individual logs in: $LOG_DIR"
