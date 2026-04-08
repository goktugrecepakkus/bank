import urllib.request
import urllib.parse
import json

BASE_URL = 'http://127.0.0.1:8000'

def request(url, method='GET', data=None, token=None, is_form=False):
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    if data:
        if is_form:
            import urllib.parse
            data = urllib.parse.urlencode(data).encode('utf-8')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            data = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode('utf-8')
            return response.status, json.loads(res_data) if res_data else None
    except urllib.error.HTTPError as e:
        res_data = e.read().decode('utf-8')
        return e.code, json.loads(res_data) if res_data else None

print('--- Testing Authentication ---')
login_url = f'{BASE_URL}/auth/login'
# The fastAPI OAuth2PasswordRequestForm expects username and password. We also added mothers_maiden_name.
form_data = {
    'username': 'johndoe',
    'password': 'pass1234',
    'mothers_maiden_name': 'Unknown'
}

status, data = request(login_url, method='POST', data=form_data, is_form=True)

print(f"Login Status: {status}")
if status == 200:
    token = data['access_token']
    user_id = data['user_id']
    print(f"User ID from login: {user_id}")
    
    # 1. Fetch current accounts
    print('--- Fetching Initial Accounts ---')
    accounts_url = f'{BASE_URL}/accounts/customer/{user_id}'
    status, accounts = request(accounts_url, token=token)
    
    if status == 200:
        print(f"Found {len(accounts)} active accounts in dashboard:")
        has_zero_btc = False
        has_zero_try = False
        has_zero_other = False
        
        for acc in accounts:
            print(f" - {acc['currency']}: {acc['balance']} (id: {acc['id']})")
            if float(acc['balance']) <= 0:
                if acc['currency'] == 'BTC':
                    has_zero_btc = True
                elif acc['currency'] == 'TRY':
                    has_zero_try = True
                else:
                    has_zero_other = True
                    
        print(f"\nAnalysis:")
        if has_zero_other:
            print("❌ FAILED: Found zero-balance accounts that are not TRY or BTC!")
        else:
            print("✅ SUCCESS: No hidden zero-balance accounts visible.")
            if has_zero_try or has_zero_btc:
                 print("✅ SUCCESS: Zero-balance TRY/BTC accounts are correctly visible.")
    else:
         print(f"Failed to fetch accounts: {accounts}")
else:
    print(f"Login failed: {data}")

