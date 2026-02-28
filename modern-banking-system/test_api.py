import urllib.request
import urllib.parse
import json

BASE_URL = 'http://localhost:8000'

def request(url, method='GET', data=None, headers=None, is_form=False):
    headers = headers or {}
    if data and is_form:
        data = urllib.parse.urlencode(data).encode('utf-8')
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    elif data:
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
        
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()) if e.read() else str(e)

def test_api():
    print('--- Testing Authentication ---')
    login_url = f'{BASE_URL}/auth/login'
    status, data = request(login_url, method='POST', data={'username': 'johndoe', 'password': 'pass1234'}, is_form=True)
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
    
    if len(accounts) < 2:
        create_url = f'{BASE_URL}/accounts/'
        status, acc = request(create_url, method='POST', data={'customer_id': customer_id, 'account_type': 'savings'}, headers=headers)
        assert status == 201, f'Create account failed: {acc}'
        print('SUCCESS: Created new account')
        accounts.append(acc)
        
    account1_id = accounts[0]['id']
    account2_id = accounts[1]['id']
    
    print('\n--- Testing Transactions ---')
    transfer_url = f'{BASE_URL}/ledger/transfer'
    transfer_data = {'from_account_id': account1_id, 'to_account_id': account2_id, 'amount': 100.0}
    status, res = request(transfer_url, method='POST', data=transfer_data, headers=headers)
    assert status == 200, f'Transfer failed: {res}'
    print('SUCCESS: Transfer successful')
    
    print('\n--- Testing Audit Logs (Admin) ---')
    status, admin_data = request(login_url, method='POST', data={'username': 'admin', 'password': 'admin123'}, is_form=True)
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
