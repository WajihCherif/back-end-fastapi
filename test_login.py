import json
from urllib import request

url = 'http://127.0.0.1:8000/users/login'

for u,p in [('admin','AdminPass123'), ('resp_raw','RespRaw123')]:
    data = json.dumps({'username': u, 'password': p}).encode('utf-8')
    req = request.Request(url, data=data, headers={'Content-Type':'application/json'})
    try:
        resp = request.urlopen(req)
        print('LOGIN', u, 'status', resp.getcode())
        body = resp.read().decode('utf-8')
        print(body)
    except Exception as e:
        print('LOGIN', u, 'error', e)
