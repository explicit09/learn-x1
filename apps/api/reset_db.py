import psycopg2
from urllib.parse import urlparse

# Parse the DATABASE_URL from .env
with open('../../.env', 'r') as f:
    for line in f:
        if line.startswith('DATABASE_URL='):
            url = line.split('=')[1].strip().strip('"')
            break

# Parse the URL
parsed = urlparse(url)
dbname = parsed.path.strip('/')
username = parsed.username
password = parsed.password
hostname = parsed.hostname

# Connect to the database
conn = psycopg2.connect(
    dbname=dbname,
    user=username,
    password=password,
    host=hostname,
    sslmode='require'
)
conn.autocommit = True

try:
    with conn.cursor() as cur:
        # Drop all tables in public schema with CASCADE
        cur.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        print("All tables dropped successfully")
except psycopg2.Error as e:
    print(f"Error resetting database: {e}")
finally:
    conn.close()
