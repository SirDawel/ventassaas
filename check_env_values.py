import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path('.')
load_dotenv(os.path.join(BASE_DIR, '.env'), encoding='utf-8')

db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

print(f"DB_NAME valor: [{db_name}]")
print(f"DB_NAME bytes: {db_name.encode('utf-8') if db_name else 'None'}")
print(f"DB_NAME hex: {db_name.encode('utf-8').hex() if db_name else 'None'}")
print(f"DB_NAME length: {len(db_name) if db_name else 0}")
print()
print(f"DB_USER: [{db_user}]")
print(f"DB_HOST: [{db_host}]")
print(f"DB_PORT: [{db_port}]")
