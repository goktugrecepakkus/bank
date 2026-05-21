from passlib.context import CryptContext
import subprocess

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
new_pwd = "Zaguney123!"
new_hash = pwd_context.hash(new_pwd)

# Update database via psql
sql = f"UPDATE customers SET password_hash = '{new_hash}' WHERE username = 'Zaguney';"
cmd = ["docker", "exec", "banking_db", "psql", "-U", "bankadmin", "-d", "banking_db", "-c", sql]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print(f"SUCCESS: {result.stdout}")
    print(f"New password for Zaguney: {new_pwd}")
except subprocess.CalledProcessError as e:
    print(f"FAILED: {e.stderr}")
