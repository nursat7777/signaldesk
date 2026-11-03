"""Deploy only the verified commit. Never log authorization or response secrets."""
import json
import os
import time
import urllib.request

service = os.environ['RENDER_SERVICE_ID']
key = os.environ['RENDER_API_KEY']
commit = os.environ['DEPLOY_COMMIT']
base = os.environ['LIVE_URL'].rstrip('/')
if not base.startswith('https://'):
    raise ValueError('LIVE_URL must use HTTPS')

def request(path, body=None):
    req = urllib.request.Request('https://api.render.com/v1'+path,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

deploy = request(f'/services/{service}/deploys',{'commitId':commit,'clearCache':'do_not_clear'})
for _ in range(100):
    result = request(f'/services/{service}/deploys/{deploy["id"]}')
    if result['status'] == 'live':
        break
    if result['status'] in ('build_failed','update_failed','canceled','deactivated'):
        raise RuntimeError('Render deployment did not become live: '+result['status'])
    time.sleep(10)
else:
    raise TimeoutError('Render deployment timeout')
with urllib.request.urlopen(base+'/api/health',timeout=20) as response:
    health = json.load(response)
    assert health == {'status':'ok','storage':'postgresql'},health
with urllib.request.urlopen(base,timeout=20) as response:
    assert b'id="root"' in response.read()
print('Verified commit deployed; HTTPS frontend and PostgreSQL health passed')
