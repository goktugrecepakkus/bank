import urllib.request
import urllib.parse
import json

BASE_URL = 'http://localhost:8000/api'

def request(url: str, method: str = 'GET', data: dict = None, headers: dict = None, is_form: bool = False):
    req_headers = dict(headers) if headers else {}
    if data and is_form:
        req_data = urllib.parse.urlencode(data).encode('utf-8')
        req_headers['Content-Type'] = 'application/x-www-form-urlencoded'
    elif data:
        req_data = json.dumps(data).encode('utf-8')
        req_headers['Content-Type'] = 'application/json'
    else:
        req_data = None
        
    req = urllib.request.Request(url, data=req_data, method=method, headers=req_headers)
    with urllib.request.urlopen(req) as response:
        return response.status, json.loads(response.read().decode())

def test_external_transfer():
    print("Logging in...")
    login_url = f'{BASE_URL}/auth/login'
    status, data = request(login_url, method='POST', data={'username': 'johndoe', 'password': 'pass1234', 'mothers_maiden_name': 'Unknown'}, is_form=True)
    token = data['access_token']
    customer_id = data['user_id']
    headers = {'Authorization': f'Bearer {token}'}
    
    print("Getting accounts...")
    accounts_url = f'{BASE_URL}/accounts/customer/{customer_id}'
    status, accounts = request(accounts_url, headers=headers)
    
    if not accounts:
        # Create an account
        create_url = f'{BASE_URL}/accounts/'
        status, acc = request(create_url, method='POST', data={'customer_id': customer_id, 'account_type': 'SAVINGS'}, headers=headers)
        accounts.append(acc)

    account_id = accounts[0]['id']
    
    print("Depositing money...")
    deposit_url = f'{BASE_URL}/ledger/deposit?account_id={account_id}&amount=1000.0'
    request(deposit_url, method='POST', headers=headers)
    
    print("Sending external transfer...")
    external_url = f'{BASE_URL}/external/send'
    transfer_data = {
        'from_account_id': account_id,
        'to_iban': 'TR123456789012345678901234',
        'amount': 250.0
    }
    status, res = request(external_url, method='POST', data=transfer_data, headers=headers)
    print("External transfer response:", res)

if __name__ == '__main__':
    test_external_transfer()
