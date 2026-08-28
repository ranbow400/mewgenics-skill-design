# -*- coding: utf-8 -*-
"""
重建 skill_design.html: 协作版 v4
- 数据外置 designs.json(在线加载, 失败回退内嵌 DATA)
- 每技能多版本记录(他人设计), 版本查看/采用
- 导出 JSON(含版本) / 导入 JSON(追加版本) / TSV
- 每行"提交此版本" -> GitHub Issue 预填链接
用法: python scripts/build_skill_design.py
"""
import json, re, io, os, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'skill_design_v3_original.html')
OUT = os.path.join(ROOT, 'skill_design.html')
DESIGNS = os.path.join(ROOT, 'designs.json')

html = io.open(SRC, encoding='utf-8').read()

# 提取原 DATA
m = re.search(r'const DATA = (\[.*?\]);', html, re.S)
if not m:
    raise SystemExit('DATA not found')
data = json.loads(m.group(1))
print('skills:', len(data))

# ---------- designs.json ----------
designs = {
    "version": 4,
    "updated": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
    "repo": "ranbow400/mewgenics-skill-design",
    "note": "本文件为协作数据源。每行 skills[] 的 versions[] 记录其他人提交的设计版本(author/date/design字段)。合并 issue 提交: python scripts/merge_issue.py <json>",
    "skills": data,
}
io.open(DESIGNS, 'w', encoding='utf-8').write(json.dumps(designs, ensure_ascii=False, indent=1))
print('wrote designs.json')

# ---------- 页面脚本 ----------
script = r'''
const tbody = document.querySelector('#tbody, tbody');
const count = document.getElementById('count');
const state = { online: false, dataVersion: null, dataUpdated: null, author: '' };

/* 在线加载 designs.json, 5 秒超时; 页面已先用内置数据渲染, 加载成功才切换 */
async function loadOnline() {
  const ctl = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timer = setTimeout(() => { if (ctl) ctl.abort(); }, 5000);
  try {
    const r = await fetch('designs.json', { cache: 'no-cache', signal: ctl ? ctl.signal : undefined });
    if (!r.ok) throw new Error(r.status);
    const d = await r.json();
    if (Array.isArray(d.skills) && d.skills.length) {
      DATA = d.skills;
      state.online = true;
      state.dataVersion = d.version || null;
      state.dataUpdated = d.updated || null;
    }
  } catch (e) { /* 超时/离线, 保持内置数据 */ }
  clearTimeout(timer);
  refreshSourceBadge();
  render(getFiltered());
}

function refreshSourceBadge() {
  const el = document.getElementById('srcBadge');
  const ver = document.getElementById('dataVer');
  if (state.online) {
    el.textContent = '在线数据';
    el.style.background = '#e8f0e8';
    el.style.borderColor = '#b7ccb7';
    ver.textContent = 'designs.json v' + state.dataVersion + (state.dataUpdated ? ' · ' + state.dataUpdated.slice(0, 10) : '');
  } else {
    el.textContent = '内置数据';
    el.style.background = '#e7e9ec';
    el.style.borderColor = '#c9cdd3';
    ver.textContent = '';
  }
}

function rowHtml(c, i) {
  const noIcon = ['ABILITY_Metronome.svg','ABILITY_Look_at_me!.svg','ABILITY_Over_There!.svg','ABILITY_Reach.svg'].indexOf(c.icon) >= 0;
  const iconSrc = noIcon
    ? (c.icon === 'ABILITY_Metronome.svg' ? 'cards/ABILITY_Copycat.png' : '')
    : 'cards/' + c.icon.replace('.svg', '.png');
  const iconCell = iconSrc
    ? `<img src="${iconSrc}" onerror="this.style.visibility='hidden'">`
    : `<div style="width:84px;height:64px;display:flex;align-items:center;justify-content:center;background:#333a48;border-radius:4px;color:#78909c;font-size:11px">无图标</div>`;
  const nv = (c.versions || []).length;
  return `<tr data-i="${i}" class="${noIcon ? 'missing' : ''}">
    <td class="noicon ref" data-label="卡面">${iconCell}</td>
    <td class="ref" data-label="技能"><div class="zhname">${c.zh || '—'}</div><div class="enname">${c.en}${c.code ? ' · ' + c.code : ''}</div></td>
    <td class="desc ref" data-label="效果参考">${c.zhDesc || c.descEn}</td>
    <td class="mp ref" data-label="蓝耗">${c.mp}${c.upgMana ? ' → ' + c.upgMana : ''}</td>
    <td class="desc ref ref-last" data-label="升级后参考">${c.upgZh}</td>
    <td class="diy diy-first" data-label="费用"><input class="num" data-f="cost" value="${c.cost}" placeholder="几费"></td>
    <td class="diy" data-label="类型"><select data-f="type">
      ${['Attack','Skill','Power'].map(t => `<option ${t === c.type ? 'selected' : ''}>${t}</option>`).join('')}
    </select></td>
    <td class="diy" data-label="稀有度"><select data-f="rarity">
      ${['Common','Uncommon','Rare'].map(t => `<option ${t === c.rarity ? 'selected' : ''}>${t}</option>`).join('')}
    </select></td>
    <td class="diy" data-label="升级前效果"><textarea data-f="effPre">${c.effPre || ''}</textarea></td>
    <td class="diy" data-label="升级后效果"><textarea data-f="effUpg">${c.effUpg || ''}</textarea></td>
    <td class="diy" data-label="已做" style="text-align:center"><input type="checkbox" data-f="done" ${c.done ? 'checked' : ''} style="width:auto"></td>
    <td class="diy" data-label="版本/提交" style="text-align:center;white-space:nowrap">
      <button class="vbtn" data-act="view" title="查看该技能的所有设计版本">${nv ? '版本 ' + nv : '版本'}</button><br>
      <button class="vbtn alt" data-act="submit" title="把当前编辑作为新版本提交(生成 GitHub Issue 链接)">提交此版</button>
    </td>
  </tr>`;
}
function getFiltered() {
  const q = document.getElementById('filter').value.trim().toLowerCase();
  const hideDone = document.getElementById('hideDone').checked;
  let list = DATA;
  if (q) list = list.filter(c => (c.zh + c.en + c.code).toLowerCase().includes(q));
  if (hideDone) list = list.filter(c => !c.done);
  return list;
}
function render(list) {
  tbody.innerHTML = list.map(rowHtml).join('');
  count.textContent = list.length + ' / ' + DATA.length + ' 个技能';
}
function collect() {
  const out = [];
  document.querySelectorAll('#tbl tbody tr').forEach(tr => {
    const c = DATA[+tr.dataset.i];
    const item = Object.assign({}, c);
    delete item.versions;
    tr.querySelectorAll('[data-f]').forEach(el => {
      item[el.dataset.f] = el.type === 'checkbox' ? el.checked : el.value;
    });
    if (c.versions && c.versions.length) item.versions = c.versions;
    out.push(item);
  });
  return out;
}
function exportJson() {
  const payload = { version: state.dataVersion || 4, updated: new Date().toISOString(), skills: collect() };
  const blob = new Blob([JSON.stringify(payload, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'skill_design_export.json';
  a.click();
}
function exportTsv() {
  const rows = [['名称(英)','code','中文名','蓝耗','图标','类型','稀有度','费用','升级前效果','升级后效果','已制作','版本数']];
  collect().forEach(c => rows.push([c.en, c.code, c.zh, c.mp, c.icon, c.type, c.rarity, c.cost, c.effPre, c.effUpg, c.done ? '是' : '', (c.versions || []).length]));
  const blob = new Blob(['\ufeff' + rows.map(r => r.join('\t')).join('\n')], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'skill_design_export.tsv';
  a.click();
}

/* ---------- 版本弹窗 ---------- */
const modal = document.getElementById('modal');
const modalBody = document.getElementById('modalBody');
function esc(s) { return String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function closeModal() { modal.style.display = 'none'; }
function openModal(title, bodyHtml) {
  document.getElementById('modalTitle').textContent = title;
  modalBody.innerHTML = bodyHtml;
  modal.style.display = 'flex';
}
function versionHtml(v) {
  const d = v.design || v;
  const rows = [
    ['费用', d.cost], ['类型', d.type], ['稀有度', d.rarity],
    ['升级前效果', d.effPre], ['升级后效果', d.effUpg], ['已做', d.done ? '是' : '否']
  ].filter(r => r[1] !== undefined && r[1] !== null && r[1] !== '');
  return `<div class="vcard">
    <div class="vhead"><b>${esc(v.author || '匿名')}</b> · ${esc((v.date || '').slice(0, 10))}</div>
    ${rows.map(r => `<div class="vrow"><span class="vkey">${r[0]}</span><span class="vval">${esc(r[1])}</span></div>`).join('')}
    <button class="vbtn adopt" data-author="${esc(v.author || '')}" data-date="${esc(v.date || '')}" data-json="${esc(JSON.stringify(d))}">采用此版本</button>
  </div>`;
}
function showVersions(i) {
  const c = DATA[i];
  const vers = c.versions || [];
  if (!vers.length) { openModal(c.zh + ' · 版本', '<div style="padding:12px;color:#90a4ae">还没有其他人提交的版本。编辑本行后点"提交此版"。</div>'); return; }
  openModal(c.zh + ' · 全部版本 (' + vers.length + ')', vers.map(versionHtml).join(''));
}
function adoptVersion(i, json, author, date) {
  const c = DATA[i];
  const d = JSON.parse(json);
  ['cost','type','rarity','effPre','effUpg','done'].forEach(k => { if (d[k] !== undefined) c[k] = d[k]; });
  render(getFiltered());
  closeModal();
  alert('已把 ' + (author || '该') + ' 的设计应用到当前行。导出发送或直接提交新版本即可同步线上。');
}

/* ---------- 提交此版本 -> 网页内直接提交(建 GitHub Issue) ---------- */
function submitVersion(i) {
  const c = DATA[i];
  document.getElementById('modal').dataset.i = i;
  const savedAuthor = localStorage.getItem('gh_author') || '';
  const savedToken = localStorage.getItem('gh_token') || '';
  openModal('提交设计: ' + (c.zh || c.en), `
    <div class="vcard">
      <div class="vrow"><span class="vkey">技能</span><span class="vval">${esc(c.zh || c.en)} (${esc(c.code)})</span></div>
      <div class="vrow"><span class="vkey">作者</span><input id="subAuthor" value="${esc(savedAuthor)}" placeholder="你的名字 / GitHub 用户名" style="flex:1;min-width:0"></div>
      <div class="vrow"><span class="vkey">Token</span><input id="subToken" type="password" value="${esc(savedToken)}" placeholder="GitHub Personal Access Token" style="flex:1;min-width:0"></div>
      <div style="font-size:11px;color:#888;margin:6px 0 10px;line-height:1.6">
        Token 只在你的浏览器本地调用 GitHub API 创建 issue，不会发往其他服务器，会保存在浏览器本地以便下次使用。
        获取：GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens →
        仓库选 mewgenics-skill-design → 权限 Issues 选 Read and write → 生成后粘贴到这里。
      </div>
      <button class="vbtn" id="subGo" style="font-size:13px;padding:8px 18px">提交</button>
      <span id="subResult" style="font-size:12px;margin-left:10px"></span>
    </div>`);
  document.getElementById('subGo').addEventListener('click', () => doSubmit(c));
}

async function doSubmit(c) {
  const author = document.getElementById('subAuthor').value.trim();
  const token = document.getElementById('subToken').value.trim();
  const res = document.getElementById('subResult');
  if (!author) { res.textContent = '请填作者名'; res.style.color = '#c62828'; return; }
  if (!token) { res.textContent = '请填 Token'; res.style.color = '#c62828'; return; }
  localStorage.setItem('gh_author', author);
  localStorage.setItem('gh_token', token);
  const tr = document.querySelector('#tbl tbody tr[data-i="' + document.getElementById('modal').dataset.i + '"]');
  const payload = {
    code: c.code, en: c.en, zh: c.zh, author: author,
    date: new Date().toISOString().slice(0, 10),
    design: { cost: tr.querySelector('[data-f="cost"]').value,
              type: tr.querySelector('[data-f="type"]').value,
              rarity: tr.querySelector('[data-f="rarity"]').value,
              effPre: tr.querySelector('[data-f="effPre"]').value,
              effUpg: tr.querySelector('[data-f="effUpg"]').value,
              done: tr.querySelector('[data-f="done"]').checked }
  };
  const body = '提交者: ' + author + '\n技能: ' + (c.zh || c.en) + ' (' + c.code + ')\n\n```json\n' + JSON.stringify(payload) + '\n```';
  res.textContent = '提交中…';
  res.style.color = '#888';
  try {
    const r = await fetch('https://api.github.com/repos/ranbow400/mewgenics-skill-design/issues', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '设计提交: ' + (c.zh || c.en) + ' (' + c.code + ')', body: body })
    });
    if (r.ok) {
      const d = await r.json();
      res.textContent = '已提交 issue #' + d.number + '，等待维护者合并后所有人可见';
      res.style.color = '#2e7d32';
    } else if (r.status === 401) {
      res.textContent = 'Token 无效，请检查';
      res.style.color = '#c62828';
    } else if (r.status === 403) {
      res.textContent = '权限不足，需要该仓库 Issues 写权限';
      res.style.color = '#c62828';
    } else {
      res.textContent = '提交失败: HTTP ' + r.status;
      res.style.color = '#c62828';
    }
  } catch (e) {
    res.textContent = '网络错误: ' + e.message;
    res.style.color = '#c62828';
  }
}

/* ---------- 导入本地 JSON(追加为版本) ---------- */
function importJson() {
  const author = prompt('导入的设计作者名(用于版本记录):', state.author || '');
  if (!author) return;
  const f = document.getElementById('fileInput');
  if (!f.files.length) { alert('先选择 JSON 文件'); return; }
  const rd = new FileReader();
  rd.onload = e => {
    try {
      const d = JSON.parse(e.target.result);
      const list = Array.isArray(d) ? d : (d.skills || []);
      let n = 0;
      const byCode = {};
      DATA.forEach((c, i) => byCode[c.code] = i);
      list.forEach(item => {
        if (!item.code || !(item.code in byCode)) return;
        const c = DATA[byCode[item.code]];
        const design = {};
        ['cost','type','rarity','effPre','effUpg','done'].forEach(k => { if (item[k] !== undefined) design[k] = item[k]; });
        c.versions = c.versions || [];
        c.versions.push({ author: author, date: new Date().toISOString().slice(0, 10), design: design });
        n++;
      });
      render(getFiltered());
      alert('已导入 ' + n + ' 个技能的版本。可点各行"版本"查看，或导出 JSON 提交给维护者合并。');
    } catch (err) { alert('JSON 解析失败: ' + err.message); }
  };
  rd.readAsText(f.files[0]);
}

/* ---------- 事件绑定 ---------- */
document.getElementById('filter').addEventListener('input', e => render(getFiltered()));
document.getElementById('hideDone').addEventListener('change', e => render(getFiltered()));
/* 导出/导入按钮走 onclick 属性, 不重复绑定 */
document.getElementById('fileInput').addEventListener('change', importJson);
document.getElementById('modalClose').addEventListener('click', closeModal);
document.getElementById('modal').addEventListener('click', e => { if (e.target === document.getElementById('modal')) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
tbody.addEventListener('click', e => {
  const btn = e.target.closest('button[data-act]');
  if (!btn) return;
  const tr = btn.closest('tr');
  const i = +tr.dataset.i;
  if (btn.dataset.act === 'view') showVersions(i);
  else if (btn.dataset.act === 'submit') submitVersion(i);
});
modalBody.addEventListener('click', e => {
  const btn = e.target.closest('button.adopt');
  if (!btn) return;
  const mi = +document.getElementById('modal').dataset.i;
  adoptVersion(mi, btn.dataset.json, btn.dataset.author, btn.dataset.date);
});
function showVersions(i) {
  document.getElementById('modal').dataset.i = i;
  const c = DATA[i];
  const vers = c.versions || [];
  if (!vers.length) { openModal(c.zh + ' · 版本', '<div style="padding:12px;color:#90a4ae">还没有其他人提交的版本。编辑本行后点"提交此版"。</div>'); return; }
  openModal(c.zh + ' · 全部版本 (' + vers.length + ')', vers.map(versionHtml).join(''));
}
// 表头 sticky 偏移
function syncSticky() {
  const hh = document.querySelector('header').offsetHeight;
  document.querySelectorAll('#tbl thead th').forEach(th => th.style.top = hh + 'px');
}
window.addEventListener('load', syncSticky);
window.addEventListener('resize', syncSticky);

// 列宽拖拽
(function() {
  const cols = document.querySelectorAll('#tbl col');
  const ths = document.querySelectorAll('#tbl thead th');
  let drag = null;
  ths.forEach((th, i) => {
    const h = document.createElement('span');
    h.className = 'rz';
    h.title = '拖拽调整列宽';
    h.addEventListener('mousedown', e => {
      e.preventDefault();
      drag = { i, x: e.clientX, w: cols[i].style.width ? parseInt(cols[i].style.width) : cols[i].offsetWidth };
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });
    th.appendChild(h);
  });
  document.addEventListener('mousemove', e => {
    if (!drag) return;
    const nw = Math.max(40, drag.w + (e.clientX - drag.x));
    cols[drag.i].style.width = nw + 'px';
  });
  document.addEventListener('mouseup', () => {
    drag = null;
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  });
})();

/* 内嵌数据(兜底, 会在线加载成功后覆盖) */
let DATA = __DATA__;
render(DATA);  /* 先用内置数据立即渲染, 不等网络 */
loadOnline();  /* 在线数据后台加载, 成功自动切换 */
'''

# 替换 __DATA__ 为内嵌数组(紧凑)
script = script.replace('__DATA__', json.dumps(data, ensure_ascii=False))

# 组装新 html: head 取到 <style> 之前, 全新 style 块, body 尾加 modal + 新 script
head = html[:html.find('<style>')]
body_start = html.find('<body>')
old_header_end = html.find('</header>', body_start)
old_table = html[html.find('<colgroup>'):html.find('</thead>')]

new_header = '''<header>
  <h1>无色系主动技能 → 抹大拉卡牌设计表</h1>
  <input id="filter" placeholder="筛选（中文名/英文名/code）" style="width:220px">
  <label style="font-size:12px;color:#666"><input type="checkbox" id="hideDone"> 隐藏已做</label>
  <button onclick="exportJson()">导出 JSON</button>
  <button class="alt" onclick="exportTsv()">导出 TSV</button>
  <button class="alt" onclick="document.getElementById('fileInput').click()">导入 JSON</button>
  <input type="file" id="fileInput" accept=".json" style="display:none">
  <span id="srcBadge" style="font-size:11px;color:#333;padding:3px 8px;border-radius:10px;background:#e7e9ec;border:1px solid #c9cdd3">内置数据</span>
  <span id="dataVer" style="font-size:11px;color:#888"></span>
  <button class="alt" onclick="document.getElementById('help').style.display = document.getElementById('help').style.display === 'none' ? 'block' : 'none'">协作说明</button>
  <span id="count" style="color:#888"></span>
</header>
<div id="help" style="display:none;background:#fff;border-bottom:1px solid #d5d8dc;padding:10px 16px;font-size:12px;color:#555;line-height:1.8">
  <b style="color:#8a6d1d">协作流程</b><br>
  1. 页面数据来自仓库 <code>designs.json</code>（在线加载，加载失败或超时用内置数据）。<br>
  2. 编辑某行（费用/类型/稀有度/效果）→ 点行内<b>「提交此版」</b> → 网页内填作者名和 GitHub Token 直接提交（不跳转）。首次需按提示创建 Fine-grained Token（Issues 写权限）。维护者合并后，其他人的页面自动出现该版本。<br>
  3. 想看某技能别人设计过什么版本：点行内<b>「版本 N」</b>，可逐版查看并「采用此版本」。<br>
  4. 离线协作：<b>导出 JSON</b> 发给别人 → 对方改完 <b>导入 JSON</b>（会作为新版本记录）→ 再导出发回或直接提交。<br>
  5. 仓库：<a href="https://github.com/ranbow400/mewgenics-skill-design" target="_blank" style="color:#1a6f9c">ranbow400/mewgenics-skill-design</a>
</div>'''

new_table_head = '''<colgroup>
  <col class="c-fix"><col class="c-fix"><col class="c-ref"><col class="c-fix"><col class="c-ref">
  <col class="c-fix"><col class="c-fix"><col class="c-fix"><col class="c-fill"><col class="c-fill"><col class="c-fix"><col class="c-fix">
</colgroup>
<thead><tr>
  <th class="ref">卡面</th><th class="ref">技能（中/英）</th><th class="ref">效果（中文参考）</th><th class="ref">蓝耗(升级后)</th><th class="ref ref-last">升级后（中文参考）</th>
  <th class="diy diy-first">费用</th><th class="diy">类型</th><th class="diy">稀有度</th><th class="diy">升级前效果（填）</th><th class="diy">升级后效果（填）</th><th class="diy">已做</th><th class="diy">版本/提交</th>
</tr></thead>'''

modal_html = '''<div id="modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:100;align-items:center;justify-content:center">
  <div style="background:#fff;border:1px solid #d5d8dc;border-radius:8px;max-width:640px;width:92%;max-height:82vh;overflow:auto;padding:16px;box-shadow:0 4px 20px rgba(0,0,0,.15)">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <b id="modalTitle" style="color:#8a6d1d"></b>
      <button id="modalClose" style="background:#e7e9ec;border:1px solid #c9cdd3;color:#333;border-radius:4px;padding:4px 10px;cursor:pointer">✕</button>
    </div>
    <div id="modalBody"></div>
  </div>
</div>'''

new_css = '''
  .vbtn { background:#e7e9ec; border:1px solid #c9cdd3; color:#333; padding:4px 8px; border-radius:4px; cursor:pointer; font-size:11px; margin:2px 0; }
  .vbtn:hover { background:#d8dbe0; }
  .vbtn.alt { background:#fff; }
  .vbtn.adopt { background:#e8f0e8; border-color:#b7ccb7; margin-top:6px; }
  .vcard { border:1px solid #d5d8dc; border-radius:6px; padding:10px; margin-bottom:10px; background:#fafbfc; }
  .vhead { margin-bottom:6px; color:#333; }
  .vrow { display:flex; gap:8px; font-size:12px; margin:2px 0; }
  .vkey { color:#777; width:70px; flex:none; }
  .vval { color:#444; white-space:pre-wrap; word-break:break-all; }

/* 手机端: 表格转卡片布局 */
@media (max-width: 900px) {
  header { gap: 6px; padding: 8px 10px; }
  header h1 { font-size: 14px; }
  header button { padding: 5px 8px; font-size: 12px; }
  header input { padding: 5px 6px; font-size: 12px; width: 150px; }
  .wrap { padding: 8px; }
  table, tbody, tr, td { display: block; width: 100%; box-sizing: border-box; }
  thead { display: none; }
  #tbl tbody tr { margin-bottom: 12px; border: 1px solid #d5d8dc; border-radius: 8px; background: #fff; padding: 6px 8px; }
  #tbl tbody td { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; border: 0; border-bottom: 1px dashed #e3e6ea; padding: 5px 2px; }
  #tbl tbody td:last-child { border-bottom: 0; }
  #tbl tbody td::before { content: attr(data-label); flex: none; width: 76px; color: #888; font-size: 11px; padding-top: 3px; }
  #tbl tbody td.ref { background: transparent; }
  #tbl tbody td.diy-first, #tbl tbody td.ref-last { border-left: 0; border-right: 0; }
  #tbl tbody td img { width: 56px; height: 43px; }
  #tbl tbody td input, #tbl tbody td textarea, #tbl tbody td select { flex: 1; min-width: 0; font-size: 12px; }
  #tbl tbody td textarea { height: 52px; }
  #tbl tbody td input.num { width: 44px; flex: none; }
  #tbl tbody td .vbtn { font-size: 12px; padding: 6px 12px; }
  #tbl tbody td:has(.vbtn) { justify-content: flex-start; gap: 10px; }
  .zhname { font-size: 13px; }
}
'''

style_end = html.find('</style>')
base_css = '''<style>
body { font-family: "Microsoft YaHei", sans-serif; margin: 0; background: #f2f3f5; color: #333; }
header { position: sticky; top: 0; background: #fff; padding: 10px 16px; display: flex; gap: 10px; align-items: center; z-index: 10; border-bottom: 1px solid #d5d8dc; flex-wrap: wrap; }
header h1 { font-size: 16px; margin: 0; color: #222; }
header button { background: #e7e9ec; border: 1px solid #c9cdd3; color: #333; padding: 7px 14px; border-radius: 4px; cursor: pointer; font-size: 13px; }
header button:hover { background: #d8dbe0; }
header button.alt { background: #fff; }
header input { background: #fff; border: 1px solid #c9cdd3; color: #333; padding: 6px 8px; border-radius: 4px; }
.wrap { padding: 14px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; table-layout: fixed; background: #fff; }
col.c-ref { width: 120px; } col.c-fill { width: 160px; } col.c-fix { width: 60px; }
th, td { border: 1px solid #d5d8dc; padding: 4px 6px; vertical-align: top; overflow: hidden; }
th { background: #f7f8fa; position: sticky; top: 56px; color: #444; font-size: 12px; }
/* 参考区(前5列)浅灰底, DIY区(费用起)白底, 中间分隔线 */
th.ref, td.ref { background: #eef0f2; }
th.diy, td.diy { background: #fff; }
th.diy-first, td.diy-first { border-left: 2px solid #aab2bd; }
th.ref-last, td.ref-last { border-right: 2px solid #aab2bd; }
th .rz { position: absolute; right: 0; top: 0; width: 7px; height: 100%; cursor: col-resize; background: transparent; z-index: 5; }
th .rz:hover { background: #b9c2cc88; }
td img { width: 84px; height: 64px; object-fit: cover; border-radius: 4px; display: block; }
td input, td textarea, td select { background: #fff; border: 1px solid #c9cdd3; color: #333; border-radius: 4px; padding: 4px 6px; font-size: 12px; width: 100%; box-sizing: border-box; }
td textarea { height: 44px; resize: vertical; }
td input.num { width: 44px; }
.zhname { font-weight: bold; color: #8a6d1d; }
.enname { color: #777; font-size: 11px; }
.desc { color: #555; font-size: 12px; }
.mp { color: #1a6f9c; font-size: 12px; }
.missing { opacity: 1; }
.noicon img { background: #e9ebee; }
'''
style = base_css + new_css + '\n</style>'

out = head + '\n' + style + '\n</head>\n<body>\n' + new_header + '\n<div class="wrap">\n<table id="tbl">\n' + new_table_head + '\n<tbody></tbody>\n</table>\n</div>\n' + modal_html + '\n<script>\n' + script + '\n</script>\n</body>\n</html>\n'
io.open(OUT, 'w', encoding='utf-8').write(out)
print('wrote skill_design.html (%d bytes)' % len(out.encode('utf-8')))

# 同步为 index.html (GitHub Pages 首页) + 确保 .nojekyll
io.open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(out)
print('wrote index.html (copy)')
noj = os.path.join(ROOT, '.nojekyll')
if not os.path.exists(noj):
    io.open(noj, 'w', encoding='utf-8').write('')
    print('wrote .nojekyll')
