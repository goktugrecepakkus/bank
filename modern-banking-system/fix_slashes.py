import os, glob

files = glob.glob('public/*.html')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Fastapi on Vercel strictly rejects /api/customers/ with 308 redirecting to /api/customers
    content = content.replace("fetch('/api/customers/'", "fetch('/api/customers'")
    content = content.replace("fetch('/api/accounts/'", "fetch('/api/accounts'")
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

with open('vercel.json', 'r', encoding='utf-8') as file:
    content = file.read()
if '"cleanUrls": true' not in content:
    content = content.replace('"routes": [', '"cleanUrls": true,\n    "routes": [')
    with open('vercel.json', 'w', encoding='utf-8') as file:
        file.write(content)
print('Fixed trailing slashes')
