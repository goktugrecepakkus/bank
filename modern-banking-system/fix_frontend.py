import os, glob

files = glob.glob("public/*.html")
replacements = {
    "fetch('/customers/password'": "fetch('/api/customers/password'",
    "fetch('/accounts/'": "fetch('/api/accounts/'",
    "fetch(`/accounts/customer/${userId}`": "fetch(`/api/accounts/customer/${userId}`",
    "fetch(`/ledger/history/${primaryTryAccountId}`": "fetch(`/api/ledger/history/${primaryTryAccountId}`",
    "fetch(`/ledger/deposit?account_id=${primaryTryAccountId}&amount=${amount}`": "fetch(`/api/ledger/deposit?account_id=${primaryTryAccountId}&amount=${amount}`",
    "fetch(`/accounts/validate/${targetId}`)": "fetch(`/api/accounts/validate/${targetId}`)",
    "fetch(`/ledger/audit/all`": "fetch(`/api/ledger/audit/all`"
}

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print("Fixed frontend fetch paths")
