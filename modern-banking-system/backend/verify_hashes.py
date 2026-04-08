from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hashes from DB
# Zaguney: $2b$12$LaPFTJMP3Qu1Rn.A9CwpmuzTAIoN3aNuqM9YXl8o96AYl7PqkupKa
# johndoe: $2b$12$Lk8k0.S4AMCs0Cc5Tl8jye2Cd/DX5WObzAlWgoBQ33gBsKU1OKIZ2
# admin:   $2b$12$2/jjbaG.NH2OBJNwg4Ky2.srpmWfJAohlPUx1EBk4E50vlh.jjPJe

hashes = {
    "Zaguney": "$2b$12$LaPFTJMP3Qu1Rn.A9CwpmuzTAIoN3aNuqM9YXl8o96AYl7PqkupKa",
    "johndoe": "$2b$12$Lk8k0.S4AMCs0Cc5Tl8jye2Cd/DX5WObzAlWgoBQ33gBsKU1OKIZ2",
    "admin": "$2b$12$2/jjbaG.NH2OBJNwg4Ky2.srpmWfJAohlPUx1EBk4E50vlh.jjPJe"
}

passwords = {
    "admin": "admin123",
    "johndoe": "pass1234"
}

for user, pwd in passwords.items():
    if pwd_context.verify(pwd, hashes[user]):
        print(f"VERIFIED: {user} password is indeed {pwd}")
    else:
        print(f"FAILED: {user} password is NOT {pwd}")

# Testing common guesses for Zaguney again just in case
zaguney_guesses = ["Zaguney1234", "Zaguney12", "Zaguney!", "Marika123"]
for guess in zaguney_guesses:
    if pwd_context.verify(guess, hashes["Zaguney"]):
        print(f"MATCH FOUND for Zaguney: {guess}")
