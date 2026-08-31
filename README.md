# 铁板神数（邵子神数）条文断命技能包

以「河洛理数」配数、以「12000 条铁板神数条文」（编号 1001–13000，分十二集）为断语库的**确定性、可复现**条文断命系统。

相传「铁板神数」为北宋邵雍（邵康节）所传。本技能包输入四柱八字 + 性别，按书传演算法式起数，经两轮「考刻」锁定真刻真分，输出命书（八大分类 + 考刻定分闭环 + 皇极值卦），并可依用户意愿续出 1–100 岁「十四表流年」。

## 交互流程

```
确认四柱 + 性别 + 出生年份
        ↓
起数（太玄配数 → 化卦 → 八卦加则 → 条文号，可逐号核对）
        ↓
两轮考刻（六亲硬锚点 + 性情事业等软锚点）
        ↓
出命书（八大分类 + 考刻定分闭环 + 皇极值卦）
        ↓
（可选）十四表流年：1–100 岁逐岁条文
```

## 目录结构

```
tieban-shenshu/
├── SKILL.md                  # 技能定义、交互流程与输出规范
├── scripts/
│   ├── tieban.py             # 条文断命引擎（起数 + 命书渲染主脚本）
│   ├── kaoke.py              # 考刻定分秘数表（考刻闭环引擎）
│   ├── liunian_14biao.py     # 十四表流年起数链
│   ├── tiaowen_grid.py       # 六亲条文网格（坤集密码 / 宫甲流度表）
│   ├── tieban_key.py         # 大运 / 流年起数（乾集原书）
│   ├── yansuan.py            # 演算法式引擎
│   └── yiji_gua.py           # 皇极值卦（值运 / 值年 / 值月 / 值日）
├── data/
│   ├── tiaowen.json          # 12000 条条文库（1001–13000，十二集）
│   ├── cases/                # 命例卡（考刻事实锚点）
│   └── liunian_14biao/       # 十四表流年数据
├── references/               # 算法依据古籍与校订说明
├── appreciation.jpg          # 赞赏码
└── wechat_qr.jpg             # 盘叔微信
```

## 安装

将 `tieban-shenshu` 整个文件夹放入技能目录（如 `~/.trae-cn/skills/`）即可，脚本仅依赖 Python 标准库。

## 命令示例

```bash
# 起数（不依赖任何人生事实，完全确定性）
python scripts/tieban.py --year 甲子 --month 乙亥 --day 庚戌 --hour 癸未 --gender 男

# 考刻问题生成器（两轮提问清单）
python scripts/kaoke.py
```

## 定位说明

正宗铁板神数依赖师传「考刻定分」「秘数表」。本技能包复原了其中可确证的考刻定分闭环（天干合化起数 → 1327 供数推八刻 → 八刻定父母弟兄表 → 十五分定妻子表），作为一条确定性、可复现的算法链；八字主起数采用书传演算法式，条文号可与 12000 条文库逐号核对。条文文本为古籍原文，未经改写。本命书仅作学习与娱乐参考。

## 赞赏与联系

| 赞赏码 | 盘叔微信 |
|:---:|:---:|
| ![赞赏码](https://raw.githubusercontent.com/x3747991-ship-it/tieban-shenshu-skillpack/main/appreciation.jpg) | ![盘叔微信](https://raw.githubusercontent.com/x3747991-ship-it/tieban-shenshu-skillpack/main/wechat_qr.jpg) |

公众号：【野生你盘叔】 出品 ｜ 苍盘命书体验官招募：https://mp.weixin.qq.com/s/9NFaItizyhEpjDzmTyEcPQ