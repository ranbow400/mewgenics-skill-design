# -*- coding: utf-8 -*-
import urllib.request, json

BIN_ID = '6a918a1af5f4af5e294dd90a'
KEY = '$2a$10$tzavVcXGo.lD8JfVnXfoCOZNMXAmRCp1qmu06awsQqX33bzWCNs2q'

# 1. 读 bin
req = urllib.request.Request('https://api.jsonbin.io/v3/b/' + BIN_ID + '/latest', headers={'X-Master-Key': KEY})
try:
    r = urllib.request.urlopen(req, timeout=20)
    d = json.loads(r.read())
    print('读取:', r.status)
    print('CORS:', r.headers.get('Access-Control-Allow-Origin'))
    print('record:', json.dumps(d.get('record'), ensure_ascii=False)[:200])
    print('meta name:', d.get('metadata', {}).get('name'))
except urllib.error.HTTPError as e:
    print('读取失败:', e.code, e.read().decode()[:200])
    raise SystemExit(1)

# 2. 写测试: 写入 {"items":[]} 再读回
req2 = urllib.request.Request('https://api.jsonbin.io/v3/b/' + BIN_ID, method='PUT', headers={
    'X-Master-Key': KEY, 'Content-Type': 'application/json'})
try:
    r2 = urllib.request.urlopen(req2, json.dumps({'items': []}).encode(), timeout=20)
    print('写入:', r2.status)
except urllib.error.HTTPError as e:
    print('写入失败:', e.code, e.read().decode()[:200])
    raise SystemExit(1)
