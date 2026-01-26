#!/usr/bin/env python3
"""Initialize Supabase database"""

from sqlalchemy import create_engine, text
import sys

DATABASE_URL = "postgresql://postgres:Mickyboo%40081@db.ewrlsgvzdaydagxvhcbo.supabase.co:5432/postgres"

print("Connecting to Supabase...")

try:
    engine = create_engine(DATABASE_URL, echo=False)

    # Read SQL file
    with open('database/supabase_init.sql', 'r') as f:
        sql_content = f.read()

    # Split into statements (handle $$ blocks specially)
    with engine.connect() as conn:
        # Execute the whole file as one transaction
        # Split by semicolons but be careful with function bodies

        statements = []
        current = ""
        in_function = False

        for line in sql_content.split('\n'):
            # Track if we're in a function definition
            if '$$' in line:
                in_function = not in_function

            current += line + "\n"

            # If we hit a semicolon and we're not in a function, it's end of statement
            if ';' in line and not in_function:
                statements.append(current.strip())
                current = ""

        success = 0
        skipped = 0
        errors = 0

        for stmt in statements:
            if not stmt or stmt.startswith('--'):
                continue
            try:
                conn.execute(text(stmt))
                conn.commit()
                success += 1
            except Exception as e:
                err_str = str(e).lower()
                if 'already exists' in err_str or 'duplicate' in err_str:
                    skipped += 1
                else:
                    errors += 1
                    print(f"  Error: {str(e)[:100]}")

    print(f"\n✅ Database initialized!")
    print(f"   Statements executed: {success}")
    print(f"   Skipped (exists): {skipped}")
    print(f"   Errors: {errors}")

except Exception as e:
    print(f"❌ Connection error: {e}")
    sys.exit(1)
