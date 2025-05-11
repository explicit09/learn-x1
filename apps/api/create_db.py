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

# Connect to the default postgres database
conn = psycopg2.connect(
    dbname='postgres',
    user=username,
    password=password,
    host=hostname,
    sslmode='require'
)
conn.autocommit = True

try:
    # Create the database
    with conn.cursor() as cur:
        cur.execute(f'CREATE DATABASE {dbname}')
    print(f"Database {dbname} created successfully")
except psycopg2.Error as e:
    print(f"Error creating database: {e}")
finally:
    conn.close()
