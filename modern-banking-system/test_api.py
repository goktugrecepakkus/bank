import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Any

BASE_URL = 'http://localhost:8000'

def request(url: str, method: str = 'GET', data: Any = None, headers: dict[str, str] | None = None, is_form: bool = False) -> tuple[int, Any]:
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
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body.decode()) if body else {"detail": str(e)}
        except json.JSONDecodeError:
            return e.code, {"detail": body.decode() if body else str(e)}

def test_api():
    print('--- Testing Authentication ---')
    login_url = f'{BASE_URL}/auth/login'
    status, data = request(login_url, method='POST', data={'username': 'johndoe', 'password': 'pass1234', 'mothers_maiden_name': 'Unknown'}, is_form=True)
    assert status == 200, f'Login failed: {data}'
    token = data['access_token']
    customer_id = data['user_id']
    headers = {'Authorization': f'Bearer {token}'}
    print('SUCCESS: Login successful')
    
    print('\n--- Testing Account Management ---')
    accounts_url = f'{BASE_URL}/accounts/customer/{customer_id}'
    status, accounts = request(accounts_url, headers=headers)
    assert status == 200, f'Fetch accounts failed: {accounts}'
    print(f'SUCCESS: Fetched {len(accounts)} accounts')
    
    while len(accounts) < 2:
        create_url = f'{BASE_URL}/accounts/'
        status, acc = request(create_url, method='POST', data={'customer_id': customer_id, 'account_type': 'SAVINGS'}, headers=headers)
        assert status == 201, f'Create account failed: {acc}'
        print('SUCCESS: Created new account')
        accounts.append(acc)
        
    account1_id = accounts[0]['id']
    account2_id = accounts[1]['id']
    
    print('\n--- Testing Transactions ---')
    # Deposit money first so we don't get Insufficient Funds
    deposit_url = f'{BASE_URL}/ledger/deposit?account_id={account1_id}&amount=500.0'
    status, res = request(deposit_url, method='POST', headers=headers)
    assert status == 200, f'Deposit failed: {res}'
    print('SUCCESS: Deposit successful')

    transfer_url = f'{BASE_URL}/ledger/transfer'
    transfer_data = {'from_account_id': account1_id, 'to_account_id': account2_id, 'amount': 100.0}
    status, res = request(transfer_url, method='POST', data=transfer_data, headers=headers)
    assert status == 200, f'Transfer failed: {res}'
    print('SUCCESS: Transfer successful')
    
    print('\n--- Testing Audit Logs (Admin) ---')
    status, admin_data = request(login_url, method='POST', data={'username': 'sysadmin', 'password': 'admin123', 'mothers_maiden_name': 'Unknown'}, is_form=True)
    assert status == 200, f'Admin login failed: {admin_data}'
    admin_token = admin_data['access_token']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    
    audit_url = f'{BASE_URL}/ledger/audit/all'
    status, audit_logs = request(audit_url, headers=admin_headers)
    assert status == 200, f'Audit log fetch failed: {audit_logs}'
    print(f'SUCCESS: Fetched {len(audit_logs)} audit logs')
    
    print('\nSUCCESS: All API Tests Passed!')

if __name__ == '__main__':
    try:
        test_api()
    except AssertionError as e:
        print(f'ERROR: TEST FAILED: {e}')
