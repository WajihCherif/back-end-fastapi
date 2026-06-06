from urllib import request
import json
with open('tokens.json','r') as f:
    tokens=json.load(f)
admin=tokens['admin']['access_token']
req=request.Request('http://127.0.0.1:8000/users/13', headers={'Authorization':f'Bearer {admin}'})
try:
    r=request.urlopen(req); print(r.status); print(r.read().decode())
except Exception as e:
    try:
        print(e.code, e.read().decode())
    except Exception:
        print('error', e)
