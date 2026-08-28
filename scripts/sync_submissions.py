# -*- coding: utf-8 -*-
"""
从 jsonbin 提交箱拉取待合并提交 -> 合入 designs.json -> 推送到 GitHub -> 清空提交箱
维护者用。用法:
  python scripts/sync_submissions.py            # 拉取+合并+推送+清空(需要 git push 代理)
  python scripts/sync_submissions.py --dry-run  # 只预览不推送不清空
提交箱 bin/key 从 designs.json 的 submit 字段读取。
"""
import json, io, sys, os, datetime, subprocess, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DESIGNS = os.path.join(ROOT, 'designs.json')

def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    return urllib.request.urlopen(req, timeout=30)

def main():
    dry = '--dry-run' in sys.argv
    designs = json.load(io.open(DESIGNS, encoding='utf-8'))
    sub = designs.get('submit') or {}
    bin_id, key = sub.get('bin', ''), sub.get('key', '')
    if not bin_id or not key:
        print('designs.json 未配置 submit.bin/key，无法同步')
        sys.exit(1)

    r = http_get('https://api.jsonbin.io/v3/b/%s/latest' % bin_id, {'X-Master-Key': key})
    d = json.loads(r.read())
    items = (d.get('record') or {}).get('items') or []
    if not items:
        print('提交箱为空，没有待合并提交')
        return
    print('待合并提交 %d 条' % len(items))

    by_code = {c['code']: c for c in designs['skills']}
    n = 0
    for it in items:
        c = by_code.get(it.get('code'))
        if not c:
            print('!! 未找到技能:', it.get('code'), '| 作者:', it.get('author'))
            continue
        design = it.get('design') or {}
        if not design:
            print('!! 空设计:', it.get('code'))
            continue
        c.setdefault('versions', []).append({
            'author': it.get('author') or '匿名',
            'date': it.get('date') or datetime.date.today().isoformat(),
            'design': design,
        })
        n += 1
        print('+ %s (%s) by %s' % (c.get('zh'), c['code'], it.get('author')))

    if n == 0:
        print('没有可合并的提交')
        return

    designs['version'] = int(designs.get('version', 0)) + 1
    designs['updated'] = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    io.open(DESIGNS, 'w', encoding='utf-8').write(json.dumps(designs, ensure_ascii=False, indent=1))
    print('已写入 designs.json v%d' % designs['version'])

    if dry:
        print('--dry-run: 不推送不清空')
        return

    # 推送 GitHub
    os.chdir(ROOT)
    subprocess.run(['git', 'add', 'designs.json'], check=True)
    subprocess.run(['git', 'commit', '-m', '合并提交箱 %d 条设计 (sync_submissions)' % n], check=True)
    subprocess.run(['git', '-c', 'http.proxy=http://127.0.0.1:7890', 'push'], check=True)
    print('已推送到 GitHub')

    # 清空提交箱
    req = urllib.request.Request('https://api.jsonbin.io/v3/b/%s' % bin_id, method='PUT')
    req.add_header('X-Master-Key', key)
    req.add_header('Content-Type', 'application/json')
    urllib.request.urlopen(req, json.dumps({'items': []}).encode(), timeout=30)
    print('提交箱已清空')

if __name__ == '__main__':
    main()
