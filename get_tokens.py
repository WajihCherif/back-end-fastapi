import json
from urllib import request

def login(username, password):
    url = 'http://127.0.0.1:8000/users/login'
    data = json.dumps({'username': username, 'password': password}).encode('utf-8')
    req = request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        resp = request.urlopen(req)
        return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {'error': str(e)}

out = {'admin': login('admin','AdminPass123'), 'resp': login('resp','RespPass123')}
with open('tokens.json','w',encoding='utf-8') as f:
    json.dump(out, f, indent=2)
print('Wrote tokens.json')
