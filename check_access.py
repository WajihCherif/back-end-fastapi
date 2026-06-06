import json
from urllib import request

with open('tokens.json','r',encoding='utf-8') as f:
    tokens = json.load(f)

def call(path, token):
    url = f'http://127.0.0.1:8000{path}'
    req = request.Request(url, headers={'Authorization': f'Bearer {token}'})
    try:
        resp = request.urlopen(req)
        return resp.getcode(), resp.read().decode('utf-8')
    except Exception as e:
        body = None
        try:
            body = e.read().decode('utf-8')
        except Exception:
            body = None
        return getattr(e,'code',None), body or str(e)

admin_token = tokens['admin']['access_token']
resp_token = tokens['resp']['access_token']

routes = ['/users/','/stock/','/alerts/']

results = {'admin':{}, 'resp':{}}
for r in routes:
    results['admin'][r] = call(r, admin_token)
    results['resp'][r] = call(r, resp_token)

print(json.dumps(results, indent=2))
