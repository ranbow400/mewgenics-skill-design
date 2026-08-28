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
2. 点该行「提交此版」→ 网页内填名字直接提交，不需要任何账号，不跳转。
3. 提交进入顶部「待合并」列表；维护者确认后合入 `designs.json`，自动成为该技能的版本，所有人点「版本 N」都能看到。

## 维护者

提交箱（jsonbin）配置在 `designs.json` 的 `submit` 字段（bin/key）。页面在线提交的数据存在提交箱，维护者用脚本合并：

```
python scripts/sync_submissions.py            # 拉取+合并+推送+清空
python scripts/sync_submissions.py --dry-run  # 只预览
```

离线提交的文件用 `scripts/merge_issue.py` 合并。
