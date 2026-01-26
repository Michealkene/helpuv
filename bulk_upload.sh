#!/bin/bash
#
# Bulk CSV Upload Script
# Uploads all CSV files from a directory to Helpuvio database
#

SCRIPT_DIR="/var/www/helpuvio"
UPLOAD_SCRIPT="$SCRIPT_DIR/upload_csv_data.py"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if directory is provided
if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <csv_directory> [dataset_id]${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 /var/www/data"
    echo "  $0 /var/www/data 1"
    exit 1
fi

CSV_DIR="$1"
DATASET_ID="${2:-}"

# Check if directory exists
if [ ! -d "$CSV_DIR" ]; then
    echo -e "${RED}Error: Directory not found: $CSV_DIR${NC}"
    exit 1
fi

# Count CSV files
CSV_COUNT=$(find "$CSV_DIR" -maxdepth 1 -name "*.csv" -type f | wc -l)

if [ "$CSV_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}No CSV files found in: $CSV_DIR${NC}"
    exit 0
fi

echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}  Bulk CSV Upload${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "Directory: ${YELLOW}$CSV_DIR${NC}"
echo -e "CSV Files: ${YELLOW}$CSV_COUNT${NC}"
if [ -n "$DATASET_ID" ]; then
    echo -e "Dataset ID: ${YELLOW}$DATASET_ID${NC}"
fi
echo -e "${GREEN}=================================================${NC}"
echo ""

# Process each CSV file
SUCCESS_COUNT=0
FAIL_COUNT=0

for csv_file in "$CSV_DIR"/*.csv; do
    if [ -f "$csv_file" ]; then
        filename=$(basename "$csv_file")
        echo -e "${YELLOW}Processing: $filename${NC}"

        # Build command
        if [ -n "$DATASET_ID" ]; then
            python3 "$UPLOAD_SCRIPT" "$csv_file" --dataset-id "$DATASET_ID"
        else
            python3 "$UPLOAD_SCRIPT" "$csv_file"
        fi

        # Check result
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Success: $filename${NC}"
            ((SUCCESS_COUNT++))
        else
            echo -e "${RED}✗ Failed: $filename${NC}"
            ((FAIL_COUNT++))
        fi

        echo ""
    fi
done

# Summary
echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}  Upload Summary${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "Total files:    ${YELLOW}$CSV_COUNT${NC}"
echo -e "Successful:     ${GREEN}$SUCCESS_COUNT${NC}"
echo -e "Failed:         ${RED}$FAIL_COUNT${NC}"
echo -e "${GREEN}=================================================${NC}"

# Exit with appropriate code
if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi

exit 0
