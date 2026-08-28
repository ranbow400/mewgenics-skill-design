# -*- coding: utf-8 -*-
"""
合并设计提交到 designs.json（维护者用）
用法:
  python scripts/merge_issue.py submit.json [--author 名字] [--dry-run]
submit.json 结构(从 GitHub issue 的 ```json 块复制):
  {"code": "BarfBall", "en": "Barf Ball", "zh": "呕吐球", "author": "xxx", "date": "2026-08-28",
   "design": {"cost": "2", "type": "Attack", "rarity": "Common", "effPre": "...", "effUpg": "...", "done": true}}
或含多个提交的数组。
会把 design 作为新版本追加到对应技能的 versions[], 版本号 +1, 更新 updated。
"""
import json, io, sys, os, datetime, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DESIGNS = os.path.join(ROOT, 'designs.json')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file', help='提交 JSON 文件')
    ap.add_argument('--author', default=None, help='覆盖作者名')
    ap.add_argument('--dry-run', action='store_true', help='只预览不写文件')
    args = ap.parse_args()

    submits = json.load(io.open(args.file, encoding='utf-8'))
    if isinstance(submits, dict):
        submits = [submits]

    designs = json.load(io.open(DESIGNS, encoding='utf-8'))
    by_code = {c['code']: c for c in designs['skills']}

    n = 0
    for s in submits:
        c = by_code.get(s.get('code'))
        if not c:
            print('!! 未找到技能:', s.get('code'))
            continue
        design = s.get('design') or {k: v for k, v in s.items() if k in ('cost', 'type', 'rarity', 'effPre', 'effUpg', 'done')}
        if not design:
            print('!! 空设计:', s.get('code'))
            continue
        c.setdefault('versions', []).append({
            'author': args.author or s.get('author') or '匿名',
            'date': s.get('date') or datetime.date.today().isoformat(),
            'design': design,
        })
        n += 1
        print('+ 已记录 %s (%s) by %s' % (c.get('zh'), c['code'], args.author or s.get('author') or '匿名'))

    if n == 0:
        print('没有可合并的提交')
        sys.exit(1)

    designs['version'] = int(designs.get('version', 0)) + 1
    designs['updated'] = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    if args.dry_run:
        print('--dry-run: 版本号将变为 v%d, 共 %d 条提交' % (designs['version'], n))
        return
    io.open(DESIGNS, 'w', encoding='utf-8').write(json.dumps(designs, ensure_ascii=False, indent=1))
    print('已写入 designs.json v%d (skills=%d)' % (designs['version'], len(designs['skills'])))

if __name__ == '__main__':
    main()
