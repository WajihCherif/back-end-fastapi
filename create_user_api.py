import json
from urllib import request
import urllib.error

with open('tokens.json','r',encoding='utf-8') as f:
    tokens = json.load(f)
admin_token = tokens['admin']['access_token']

url = 'http://127.0.0.1:8000/users/'
new_user = {
    "username": "newmanager",
    "email": "new.manager@example.com",
    "full_name": "New Manager",
    "password": "ManagerPass123",
    "role": "responsible",
    "is_active": True
}
req = request.Request(url, data=json.dumps(new_user).encode('utf-8'), headers={
    'Content-Type':'application/json',
    'Authorization': f'Bearer {admin_token}'
}, method='POST')
try:
    resp = request.urlopen(req)
    print(resp.status)
    print(resp.read().decode())
except urllib.error.HTTPError as e:
    print(e.code)
    try:
        print(e.read().decode())
    except Exception:
        print('no body')
except Exception as e:
    print('err', e)
