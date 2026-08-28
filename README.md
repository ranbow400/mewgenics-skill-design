# Mewgenics 无色系技能 → 抹大拉卡牌设计表（协作版）

在线页面：https://ranbow400.github.io/mewgenics-skill-design/

把 Mewgenics 的无色系主动技能转成《杀戮尖塔2》抹大拉 mod 卡牌的设计协作表。

## 数据

- `designs.json`：协作数据源（唯一真源）。页面在线加载它，加载失败时回退到 `skill_design.html` 内嵌数据。
- 每个技能行的 `versions[]` 记录其他人提交的设计版本：`{author, date, design:{cost,type,rarity,effPre,effUpg,done}}`。
- `skill_design_v3_original.html`：v3 原始版备份。
- `scripts/build_skill_design.py`：重建页面（改版后跑它再提交）。
- `scripts/merge_issue.py`：维护者合并工具。

## 协作流程（提交者）

1. 打开在线页面，编辑某个技能行（费用/类型/稀有度/升级前后效果/已做）。
2. 点该行「提交此版」→ 填名字 → 自动打开 GitHub Issue 预填页，直接提交。
3. 等维护者合并进 `designs.json` 后，页面上该技能会出现新版本，所有人点「版本 N」都能看到。

## 协作流程（离线）

1. 页面「导出 JSON」→ 把文件发给别人。
2. 对方改完「导入 JSON」（填作者名，导入内容记为版本）→ 再导出。
3. 把最终 JSON 发回维护者，或在 GitHub 开 issue 贴内容。

## 维护者合并

```
python scripts/merge_issue.py submit.json
```

版本号自动 +1，推送 main 后 Pages 自动更新。
