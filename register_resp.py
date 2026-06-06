import json
from urllib import request

url = 'http://127.0.0.1:8000/users/register'
creds = {'username':'resp_api','email':'resp_api@example.com','password':'RespApi123','full_name':'Resp API'}
req = request.Request(url, data=json.dumps(creds).encode('utf-8'), headers={'Content-Type':'application/json'})
try:
    resp = request.urlopen(req)
    print('REGISTER status', resp.getcode())
    print(resp.read().decode('utf-8'))
except Exception as e:
    print('REGISTER error', e)
