# -*- coding: utf-8 -*-
import re, io, subprocess, os
os.chdir(r'C:\Users\28437\.openclaw\workspace\sts2mod_ref\mewgenics_wiki')
html = io.open('skill_design.html', encoding='utf-8').read()
m = re.search(r'<script>\n(.*)</script>', html, re.S)
io.open('_check.js', 'w', encoding='utf-8').write(m.group(1))
print('网页内提交:', 'doSubmit' in html)
print('无 window.open 跳转:', 'window.open' not in html)
print('token 本地存储:', "localStorage.setItem('gh_token'" in html)
print('issue API:', 'api.github.com/repos/ranbow400/mewgenics-skill-design/issues' in html)
print('协作说明更新:', '网页内填作者名和 GitHub Token' in html)
r = subprocess.run(['node', '--check', '_check.js'], capture_output=True, text=True)
print('JS syntax:', 'OK' if r.returncode == 0 else r.stderr[:300])
os.remove('_check.js')
