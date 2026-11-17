"""Deploy only the verified commit. Never log authorization or response secrets."""
import json
import os
import re
import time
import urllib.request

service = os.environ['RENDER_SERVICE_ID']
key = os.environ['RENDER_API_KEY']
image = os.environ['DEPLOY_IMAGE']
if not re.fullmatch(r'ghcr.io/[a-z0-9_.-]+/[a-z0-9_.-]+@sha256:[a-f0-9]{64}', image):
    raise ValueError('Deployment requires immutable GHCR image digest')
if not re.fullmatch(r'srv-[A-Za-z0-9]+', service):
    raise ValueError('Invalid Render service ID')
base = os.environ['LIVE_URL'].rstrip('/')
from urllib.parse import urlparse
parsed = urlparse(base)
if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.query or parsed.fragment:
    raise ValueError('LIVE_URL must use HTTPS')

def request(path, body=None):
    req = urllib.request.Request('https://api.render.com/v1'+path,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

deploy = request(f'/services/{service}/deploys',{'imageUrl': image})
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
print('Verified immutable image deployed; HTTPS frontend and PostgreSQL health passed')
