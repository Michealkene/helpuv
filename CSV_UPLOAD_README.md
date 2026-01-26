# CSV Data Upload Tool

This tool uploads company data from CSV files to your Helpuvio PostgreSQL database.

## Features

- ✅ Extracts only required fields from CSV
- ✅ Maps CSV fields to database schema
- ✅ Handles email and phone arrays
- ✅ Batch processing for efficient uploads
- ✅ Skip duplicate entries
- ✅ Detailed progress reporting

## Required CSV Fields

The script expects CSV files with these fields:

### Primary Fields (Required):
- `company` or `website` - Company name
- `website` - Company website URL
- `email` / `emails` - Email addresses
- `phone` / `phones` - Phone numbers
- `street` - Street address
- `locality` - City name
- `country` - Country
- `category` - Business category

### Optional Fields:
- `state` - State/Province
- `zip` - Zip/Postal code
- `group` - Group name
- `linkedin_url`, `twitter_url`, `facebook_url`, `instagram_url` - Social media URLs
- `socials` - Raw social media data
- `ceo_name` - CEO name
- `description` - Company description
- `meta_title` - Meta title
- `avatar_url`, `favicon_url` - Image URLs
- `rating` - Company rating
- `reviews` - Number of reviews
- `employee_count` - Employee count
- `founded_year` - Year founded
- `performance_score` - Performance score
- `response_time_ms` - Response time
- `crawl_status`, `crawl_error` - Crawl metadata
- `sent` - Email sent status

## Field Mapping

CSV Field → Database Field:
```
company         → company_name
website         → website
email           → email (primary)
emails          → emails (array)
phone           → phone (primary)
phones          → phones (array)
street          → street
locality        → city, locality
country         → country
category        → category
state           → state
zip             → zip_code
```

## Installation

Install required Python packages:

```bash
cd /var/www/helpuvio
pip3 install psycopg2-binary python-dotenv
```

## Usage

### Basic Upload

```bash
python3 /var/www/helpuvio/upload_csv_data.py your_data.csv
```

### Upload with Dataset ID

```bash
python3 /var/www/helpuvio/upload_csv_data.py your_data.csv --dataset-id 1
```

### Custom Batch Size

```bash
python3 /var/www/helpuvio/upload_csv_data.py your_data.csv --batch-size 500
```

### Full Example

```bash
python3 /var/www/helpuvio/upload_csv_data.py \
  /path/to/companies.csv \
  --dataset-id 1 \
  --batch-size 200
```

## Examples

### Example 1: Upload single CSV file
```bash
python3 upload_csv_data.py companies_usa.csv
```

### Example 2: Upload multiple files in a loop
```bash
for file in *.csv; do
  python3 upload_csv_data.py "$file" --dataset-id 1
done
```

### Example 3: Upload from specific directory
```bash
python3 upload_csv_data.py /var/www/data/leads.csv --batch-size 1000
```

## Output

The script provides detailed progress:

```
✓ Connected to database

📁 Processing: companies.csv
============================================================
  ✓ Inserted batch: 100 companies (Total: 100)
  ✓ Inserted batch: 100 companies (Total: 200)
  ✓ Inserted final batch: 45 companies

============================================================
📊 Summary:
  Total rows:    245
  Inserted:      245
  Skipped:       0
============================================================

✓ Database connection closed
✓ Upload completed successfully!
```

## Data Validation

The script automatically:

1. **Skips invalid rows**: Rows without company name or website
2. **Handles arrays**: Splits comma-separated emails/phones into arrays
3. **Sets flags**: Automatically sets `has_email` and `has_phone` flags
4. **Default status**: Sets `email_verification_status` to 'pending'
5. **Displayable**: Sets `is_displayable` to False initially

## Database Connection

The script uses the `DATABASE_URL` from `/var/www/helpuvio/.env`:

```env
DATABASE_URL=postgresql://postgres:password@host:5432/database
```

## Troubleshooting

### Connection Error
```
✗ Database connection failed: could not connect to server
```
**Solution**: Check your DATABASE_URL in .env file

### File Not Found
```
✗ File not found: data.csv
```
**Solution**: Provide full path to CSV file

### Missing Fields
```
✗ Row 5 error: 'company'
```
**Solution**: Ensure CSV has required column headers

### Permission Denied
```
Permission denied: /var/www/helpuvio/data.csv
```
**Solution**: Check file permissions or run with sudo

## Notes

- Duplicate `id` values are skipped (ON CONFLICT DO NOTHING)
- Empty strings are converted to NULL in database
- Arrays (emails, phones) support comma-separated values
- Batch processing prevents memory issues with large files
- All timestamps are set automatically

## Support

For issues or questions, check:
- Database schema: `/var/www/helpuvio/backend/app/models/company.py`
- Environment config: `/var/www/helpuvio/.env`
