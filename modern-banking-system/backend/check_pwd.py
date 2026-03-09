from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_to_check = "$2b$12$LaPFTJMP3Qu1Rn.A9CwpmuzTAIoN3aNuqM9YXl8o96AYl7PqkupKa"

passwords_to_try = [
    "Zaguney",
    "Zaguney123",
    "Marika",
    "pass1234",
    "admin123",
    "Elden",
    "Zeynel123",
    "Güney123",
    "password",
    "Together we will devour the very gods!",
    "Together we will devour the very gods",
]

for pwd in passwords_to_try:
    if pwd_context.verify(pwd, hash_to_check):
        print(f"MATCH FOUND: {pwd}")
        break
else:
    print("No match found in the list.")
