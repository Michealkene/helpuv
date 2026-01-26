#!/bin/bash
# Check the status of CSV uploads

echo "=========================================="
echo "CSV Upload Status Check"
echo "Time: $(date)"
echo "=========================================="
echo ""

# Check if upload process is still running
if ps aux | grep -v grep | grep "upload_csv_data.py" > /dev/null; then
    echo "⏳ Upload process is STILL RUNNING"
    ps aux | grep -v grep | grep "upload_csv_data.py" | awk '{print "   PID: " $2 " | CPU: " $3 "% | File: " $NF}'
    echo ""
else
    echo "✓ All upload processes COMPLETED"
    echo ""
fi

# Database statistics
echo "📊 Database Statistics:"
echo "-------------------------------------------"

# Total companies
TOTAL=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ')
echo "Total Companies: $TOTAL"

# Companies with email
WITH_EMAIL=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies WHERE has_email = true;" 2>/dev/null | tr -d ' ')
echo "With Email: $WITH_EMAIL ($(echo "scale=2; $WITH_EMAIL * 100 / $TOTAL" | bc 2>/dev/null)%)"

# Companies with phone
WITH_PHONE=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies WHERE has_phone = true;" 2>/dev/null | tr -d ' ')
echo "With Phone: $WITH_PHONE ($(echo "scale=2; $WITH_PHONE * 100 / $TOTAL" | bc 2>/dev/null)%)"

# Companies with both
WITH_BOTH=$(docker exec helpuvio_postgres psql -U postgres -d helpuvio -t -c "SELECT COUNT(*) FROM companies WHERE has_email = true AND has_phone = true;" 2>/dev/null | tr -d ' ')
echo "With Both Email & Phone: $WITH_BOTH ($(echo "scale=2; $WITH_BOTH * 100 / $TOTAL" | bc 2>/dev/null)%)"

echo ""
echo "📧 Email Verification Status:"
echo "-------------------------------------------"
docker exec helpuvio_postgres psql -U postgres -d helpuvio -c "
    SELECT
        email_verification_status,
        COUNT(*) as count
    FROM companies
    WHERE has_email = true
    GROUP BY email_verification_status;
" 2>/dev/null | grep -v "^$"

echo ""
echo "📁 Upload Logs:"
echo "-------------------------------------------"
if [ -d /tmp/csv_uploads ]; then
    ls -lh /tmp/csv_uploads/*.log 2>/dev/null | awk '{print $9 " (" $5 ")"}'
    echo ""
    echo "View master log: cat /tmp/csv_uploads/master_upload.log"
    echo "View ready.csv log: tail -100 /tmp/csv_upload_ready.log"
else
    echo "No upload logs found"
fi

echo ""
echo "=========================================="
