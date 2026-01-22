import csv
import io
from typing import List, Dict

class CSVValidator:
    """Validate and sanitize CSV files"""
    
    REQUIRED_COLUMNS = [
        'company_name',
        'company_domain',
        'company_email'
    ]
    
    @staticmethod
    def sanitize_value(value: str) -> str:
        """Prevent CSV injection"""
        if value and value[0] in ('=', '+', '-', '@'):
            return "'" + value
        return value
    
    @staticmethod
    def validate_csv(content: bytes) -> Dict:
        """Validate CSV structure and content"""
        try:
            csv_text = content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_text))
            headers = csv_reader.fieldnames
            
            # Check required columns
            missing = set(CSVValidator.REQUIRED_COLUMNS) - set(headers)
            if missing:
                return {
                    "valid": False,
                    "error": f"Missing required columns: {', '.join(missing)}"
                }
            
            # Count rows
            rows = list(csv_reader)
            row_count = len(rows)
            
            if row_count == 0:
                return {
                    "valid": False,
                    "error": "CSV file is empty"
                }
            
            return {
                "valid": True,
                "row_count": row_count,
                "headers": headers
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Invalid CSV format: {str(e)}"
            }
    
    @staticmethod
    def parse_sample_rows(content: bytes, num_rows: int = 5) -> List[Dict]:
        """Parse first N rows with redaction"""
        csv_text = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        
        sample_rows = []
        for i, row in enumerate(csv_reader):
            if i >= num_rows:
                break
            
            redacted_row = {}
            for key, value in row.items():
                if 'email' in key.lower() and '@' in value:
                    parts = value.split('@')
                    redacted_row[key] = f"{parts[0][:2]}***@{parts[1]}"
                elif 'phone' in key.lower() and len(value) > 8:
                    redacted_row[key] = f"{value[:4]}***{value[-4:]}"
                else:
                    redacted_row[key] = value
            
            sample_rows.append(redacted_row)
        
        return sample_rows