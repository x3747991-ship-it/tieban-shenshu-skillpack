#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
铁板神数 · 六亲条文网格（坤集密码 / 宫甲流度表 的结构化实现）

依据《铁板神数正宗破解钥匙》第十章「坤集」与「宫甲流度表」的规则：
六亲条文在条文库中呈规整的「生肖 / 干支 → 条文号」网格。本模块**数据驱动**，
从 12000 条文库中按确定性规则抽取查表，而非硬编码条文号，保证与条文库永不错位。

已复原的网格（对应《铁版神数》坤集「宫甲流度表」，与张椿来版交叉验证；
数据驱动自条文库，引擎以正则在条文库取真实条文号、不做硬编码公式）：

  乾宫·父生肖   base=9003  支步+50   父命X年生方合   12/12（兔位9163、书刊作9153）
  坤宫·母生肖   base=9605  支步+50   母命X年生方合   12/12（猪位10175、书刊作10155）
  木宫·妻干支   base=9767  支步+50 干步+10   妻命[干支]生   60/60（6键标签纠错）
  金宫·夫干支   base=10363 支步+50 干步+10   夫命[干支]生   60/60（5键标签纠错）
  女宫·女生肖   base=12243 支步+10   （纯等差）  女属X   12/12
  子宫·子生肖   base=12123 支步+10   （虎位12113偏移） 子属X   12/12
  组合父母      父X母Y 专属条   父羊母兔 = 9904 等

  坤集扩展表（多婚次 / 父母同属 / 夫妻同庚 / 师父；据「坤集密数总表·校正版」）：
  再娶(木宫甲乙度)     60干支 base=9818  +50支+10干  60/60   再娶[干支]
  四娶(庚木甲流度)     60干支 base=12002 +50支+10干  60/60   四娶[干支]
  夫妻同庚(金木甲流度) 60干支 base=11003 +50支+10干  60/60   夫妻同[干支]
  再嫁(金甲乙流度)     60干支 base=12396 +50支+10干  59/60   再嫁[干支]（甲子无条，丙子12406起）
  三嫁(戊金甲流度)     60干支 base=11126 +50支+10干  60/60   三嫁[干支]
  师父(师徒爻密数)     60干支 base=11045 +50支+10干  59/60   师命[干支]（甲子无条，丙子11055起）
  三妻(戊木甲流度)     12生肖 base=10622 +10        12/12   三妻[生肖]命
  父母同属(乾坤甲流度) 12生肖 base=9024  +120       12/12   父母同/全/俱属[生肖]

  干支式公式：条文号 = 基础号 + 50×地支序 + 10×干位
  （阳支配阳干甲丙戊庚壬、阴支配阴干乙丁己辛癸，各取干位 0..4）
  详见 references/宫甲流度表.md 与 references/坤集密数总表.md
"""
import json
import os
import re

TIANGAN = '甲乙丙丁戊己庚辛壬癸'
DIZHI = '子丑寅卯辰巳午未申酉戌亥'
# 库中「犬」为父母块正字，「狗」为子女块用字，二义归一为「犬」
SHENGXIAO = '鼠牛虎兔龙蛇马羊猴鸡犬猪'
SX_CLASS = '鼠牛虎兔龙蛇马羊猴鸡犬狗猪'   # 正则字符类（含犬狗两写）
DZ2SX = {DIZHI[i]: SHENGXIAO[i] for i in range(12)}
SX2DZ = {SHENGXIAO[i]: DIZHI[i] for i in range(12)}
SX_ALIAS = {'狗': '犬'}                    # 输入别名归一

# 条文库干支标签转录纠错：正确干支键 -> 正确条文号。
# 条文号本身是干净等差网格（base + 50支 + 10干），但源库少数条目的干支字被错写/误植，
# 导致正则按「妻命[干支]生」「夫命[干支]生」精确匹配时错配或缺失。此表只订正检索键，
# 不动 tiaowen.json 断语原文（受「原文不得修改」约束）。详见 references/宫甲流度表.md
WIFE_GZ_LABEL_FIX = {
    '癸酉': 10257, '壬午': 10107, '乙酉': 10217,
    '己亥': 10337, '己酉': 10237, '庚戌': 10297,
}
HUSBAND_GZ_LABEL_FIX = {
    '乙巳': 10613, '己巳': 10633, '癸酉': 10853,
    '乙亥': 10913, '癸亥': 10953,
}


def _norm_sx(text):
    """生肖别名归一（狗→犬），供事实解析前统一处理。"""
    if not text:
        return text
    for a, b in SX_ALIAS.items():
        text = text.replace(a, b)
    return text


# 六十甲子（甲子序 0..59）
GANZHI_60 = [TIANGAN[i % 10] + DIZHI[i % 12] for i in range(60)]

# 中文数字 → 阿拉伯数字
_CHINESE_NUM = {
    '零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
}


def _load_rows():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, '..', 'data', 'tiaowen.json')
    import json
    with open(path, 'r', encoding='utf-8') as f:
        rows = json.load(f)
    rows.sort(key=lambda r: r['n'])
    return rows


# 坤集扩展密数表（据「坤集密数总表·校正版」，与 12000 条文库逐条反查校正）。
# 分两类：60 干支式（键=干支，条文号 = base + 50×支序 + 10×干位）、12 生肖式（键=地支，等差 +step）。
# 条文号是干净等差网格，本模块以公式生成编号后自条文库反查正文，绕开源库干支标签的错字/错位。
_EXT_60_GRIDS = {
    'remarry_wife':    (9818,  set()),      # 再娶 木宫甲乙度
    'fourth_wife':     (12002, set()),      # 四娶 庚木甲流度
    'couple_same':     (11003, set()),      # 夫妻同庚 金木甲流度
    'teacher':         (11045, {'甲子'}),   # 师父 师徒爻密数（甲子无条）
    'third_husband':   (11126, set()),      # 三嫁 戊金甲流度（源库干支标签有错位）
    'remarry_husband': (12396, {'甲子'}),   # 再嫁 金甲乙流度（甲子无条，丙子12406起；标签系统性错位）
}
_EXT_12_GRIDS = {
    'third_wife':   (10622, 10),            # 三妻 戊木甲流度
    'parents_same': (9024, 120),            # 父母同属 乾坤甲流度
}

# 扩展表「显示纠错映射」：表 -> 正确干支键 -> {源库错字文本: 正确文本}。
# 条文号由公式生成、本身干净，但源库条文正文里的干支标签存在错字/顺位错格（如再嫁块整体
# 错后一位、「丙子」印作「同年生」、「壬申」印作「任申」等）。此表在反查出正文后做文本替换，
# 只按查询条件订正**显示**，不改 tiaowen.json 断语原文（受「原文不得修改」约束）。
# 按表分键：同一干支（如丙子/丁丑/壬戌）在不同表中的错字不同，平铺会互相覆盖。
_EXT_DISPLAY_FIX = {
    # 再娶（木宫甲乙度）
    'remarry_wife': {
        '辛巳': {'丁巳': '辛巳'},            # 10098 印作「再娶丁巳」、实为辛巳
    },
    # 四娶（庚木甲流度）
    'fourth_wife': {
        '丙子': {'甲子': '丙子'},
        '己丑': {'乙丑': '己丑'},
        '丙寅': {'壬寅': '丙寅'},
        '己卯': {'乙卯': '己卯'},
        '壬申': {'任申': '壬申'},            # 「任申」为「壬申」错字
        '乙酉': {'己酉': '乙酉'},
        '丙戌': {'丙午': '丙戌'},
    },
    # 夫妻同庚（金木甲流度）
    'couple_same': {
        '丙子': {'同年生': '同丙子'},        # 丙子位印作「夫妻同年生」
        '丁丑': {'丁卯': '丁丑'},
        '庚午': {'同年生': '同庚午'},
        '壬戌': {'戊戌': '壬戌'},
    },
    # 师父（师徒爻密数）
    'teacher': {
        '丁丑': {'丁卯': '丁丑'},
        '庚辰': {'庚寅': '庚辰'},
        '壬戌': {'壬辰': '壬戌'},
    },
    # 三嫁（戊金甲流度）
    'third_husband': {
        '甲寅': {'甲辰': '甲寅'}, '庚寅': {'庚辰': '庚寅'}, '壬寅': {'壬辰': '壬寅'},
        '戊辰': {'壬辰': '戊辰'}, '庚午': {'庚申': '庚午'}, '壬午': {'戊午': '壬午'},
        '丁未': {'乙未': '丁未'}, '戊申': {'戊戌': '戊申'}, '庚申': {'庚戌': '庚申'},
        '己酉': {'己丑': '己酉'}, '己亥': {'乙亥': '己亥'},
    },
    # 再嫁（金甲乙流度）——正文干支整体错后一位（丙子位起），按位顺次订正
    'remarry_husband': {
        '戊子': {'丙子': '戊子'}, '庚子': {'戊子': '庚子'}, '壬子': {'庚子': '壬子'},
        '乙丑': {'壬子': '乙丑'}, '丁丑': {'乙丑': '丁丑'}, '己丑': {'壬子': '己丑'},
        '辛丑': {'己丑': '辛丑'}, '癸丑': {'辛丑': '癸丑'}, '甲寅': {'癸丑': '甲寅'},
        '丙寅': {'甲寅': '丙寅'}, '戊寅': {'丙寅': '戊寅'}, '庚寅': {'戊寅': '庚寅'},
        '壬寅': {'庚寅': '壬寅'}, '乙卯': {'壬寅': '乙卯'}, '丁卯': {'乙卯': '丁卯'},
        '己卯': {'丁卯': '己卯'}, '辛卯': {'己卯': '辛卯'}, '癸卯': {'辛卯': '癸卯'},
        '甲辰': {'癸卯': '甲辰'}, '丙辰': {'甲辰': '丙辰'}, '戊辰': {'丙辰': '戊辰'},
        '庚辰': {'戊辰': '庚辰'}, '壬辰': {'庚辰': '壬辰'}, '乙巳': {'壬辰': '乙巳'},
        '丁巳': {'乙丑': '丁巳'}, '己巳': {'丁巳': '己巳'}, '辛巳': {'己巳': '辛巳'},
        '癸巳': {'辛巳': '癸巳'}, '甲午': {'癸巳': '甲午'}, '丙午': {'甲申': '丙午'},
        '戊午': {'丙午': '戊午'}, '庚午': {'戊午': '庚午'}, '壬午': {'庚午': '壬午'},
        '乙未': {'壬午': '乙未'}, '丁未': {'乙未': '丁未'}, '己未': {'丁未': '己未'},
        '辛未': {'己未': '辛未'}, '癸未': {'辛未': '癸未'}, '甲申': {'癸未': '甲申'},
        '丙申': {'甲申': '丙申'}, '戊申': {'丙申': '戊申'}, '庚申': {'戊申': '庚申'},
        '壬申': {'庚申': '壬申'}, '乙酉': {'壬申': '乙酉'}, '丁酉': {'乙酉': '丁酉'},
        '己酉': {'丁酉': '己酉'}, '辛酉': {'己酉': '辛酉'}, '癸酉': {'辛酉': '癸酉'},
        '甲戌': {'癸酉': '甲戌'}, '丙戌': {'甲戌': '丙戌'}, '戊戌': {'丙戌': '戊戌'},
        '庚戌': {'戊戌': '庚戌'}, '壬戌': {'庚戌': '壬戌'}, '乙亥': {'壬戌': '乙亥'},
        '丁亥': {'乙亥': '丁亥'}, '己亥': {'丁亥': '己亥'}, '辛亥': {'己亥': '辛亥'},
        '癸亥': {'辛亥': '癸亥'},
    },
}


def _gan_wei(gz):
    """干支式干位：阳支(子寅辰午申戌)配甲丙戊庚壬、阴支配乙丁己辛癸，各取 0..4。"""
    g, d = gz[0], gz[1]
    i = DIZHI.index(d)
    return ('甲丙戊庚壬'.index(g) if i % 2 == 0 else '乙丁己辛癸'.index(g))


def _ext_ganzhi60():
    """干支式 60 组合（阳支配阳干、阴支配阴干），用作 60 干支扩展网格的键。"""
    seq = []
    for i, d in enumerate(DIZHI):
        gans = '甲丙戊庚壬' if i % 2 == 0 else '乙丁己辛癸'
        seq.extend(g + d for g in gans)
    return seq


def _dz2lead_gz(dz):
    """地支 → 甲/乙首干干支（阳支甲、阴支乙），供生肖/地支回退定位到 60 干支网格。"""
    return ('甲' if DIZHI.index(dz) % 2 == 0 else '乙') + dz


def build_extended_grid(rows):
    """构建坤集扩展密数网格。60 干支式按公式生成编号、12 生肖式按等差生成编号，
    均自条文库（data/tiaowen.json）反查断语原文；「无条」干支（库无对应语义条文）跳过。"""
    n2t = {r['n']: r['t'] for r in rows}
    ext = {k: {} for k in list(_EXT_60_GRIDS) + list(_EXT_12_GRIDS)}
    for key, (base, skip) in _EXT_60_GRIDS.items():
        fixmap = _EXT_DISPLAY_FIX.get(key, {})
        for gz in _ext_ganzhi60():
            if gz in skip:
                continue
            n = base + 50 * DIZHI.index(gz[1]) + 10 * _gan_wei(gz)
            t = n2t.get(n)
            if t:
                for old, new in fixmap.get(gz, {}).items():
                    t = t.replace(old, new)
                ext[key][gz] = (n, t)
    for key, (base, step) in _EXT_12_GRIDS.items():
        for i, dz in enumerate(DIZHI):
            n = base + step * i
            t = n2t.get(n)
            if t:
                ext[key][dz] = (n, t)
    return ext


def _chinese2int(s):
    if not s:
        return None
    if s == '十':
        return 10
    if '十' in s:
        parts = s.split('十')
        tens = _CHINESE_NUM.get(parts[0], 1) if parts[0] else 1
        ones = _CHINESE_NUM.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
        return tens * 10 + ones
    return _CHINESE_NUM.get(s, 0) if len(s) == 1 and not s.isdigit() else None


def build_grid(rows):
    """从条文库抽取六亲网格。返回结构化 dict，全部为确定性查表。"""
    g = {
        'father': {},        # 生肖 -> (n, text)
        'mother': {},        # 生肖 -> (n, text)
        'parents_pair': {},  # (父生肖, 母生肖) -> (n, text)
        'wife_ganzhi': {},   # 干支 -> (n, text)
        'husband_ganzhi': {},# 干支 -> (n, text)
        'daughter': {},      # 生肖 -> (n, text)
        'son': {},           # 生肖 -> (n, text)
        'sibling': {},       # (关系, 生肖) -> (n, text)  关系∈兄/弟/姊/妹
        'brothers': {},      # 人数 -> (n, text) 兄弟N人
        'children_count': {},# 数量 -> (n, text) 花结X朵 / 花开X朵
    }

    def cat(c):
        return [r for r in rows if r['c'] == c]

    # 1) 父生肖：父命X年(生)方合 / 父年X年方合（排除 父X母Y 组合）
    fp = re.compile('父命?年?([%s])年?生?方合' % SX_CLASS)
    for r in cat(1):
        m = fp.search(r['t'])
        if m and '母' not in r['t']:
            g['father'].setdefault(_norm_sx(m.group(1)), (r['n'], r['t']))

    # 2) 母生肖：母命X年(生)方合（排除 父X母Y 组合）
    mp = re.compile('母命([%s])年?生?方合' % SX_CLASS)
    for r in cat(1):
        m = mp.search(r['t'])
        if m and '父' not in r['t']:
            g['mother'].setdefault(_norm_sx(m.group(1)), (r['n'], r['t']))

    # 3) 组合父母：父X母Y（双方生肖都在同一句）
    for r in cat(1):
        t = r['t']
        if '父' not in t or '母' not in t:
            continue
        sx = [_norm_sx(c) for c in t if c in SX_CLASS]
        if len(sx) >= 2:
            g['parents_pair'].setdefault((sx[0], sx[1]), (r['n'], r['t']))

    # 4) 妻 / 夫 干支：妻命[干支]生 / 妻命生于[干支] / 妻命[干支]方合 / 妻命[干支]，
    wp = re.compile('妻命(生于)?([%s][%s])' % (TIANGAN, DIZHI))
    hp = re.compile('夫命(生于)?([%s][%s])' % (TIANGAN, DIZHI))
    for r in cat(3):
        m = wp.search(r['t'])
        if m:
            g['wife_ganzhi'].setdefault(m.group(2), (r['n'], r['t']))
        m = hp.search(r['t'])
        if m:
            g['husband_ganzhi'].setdefault(m.group(2), (r['n'], r['t']))

    # 5) 子女生肖：女属X / 子属X（男命之子）
    dp = re.compile('女属([%s])' % SX_CLASS)
    sp = re.compile('子属([%s])' % SX_CLASS)
    for r in cat(4):
        m = dp.search(r['t'])
        if m:
            g['daughter'].setdefault(_norm_sx(m.group(1)), (r['n'], r['t']))
        m = sp.search(r['t'])
        if m:
            g['son'].setdefault(_norm_sx(m.group(1)), (r['n'], r['t']))

    # 6) 兄弟：兄/弟/姊(姐)/妹 属X —— 关系与生肖同时入键
    sibp = re.compile('(兄|弟|姊|姐|妹)属([%s])' % SX_CLASS)
    for r in cat(2):
        m = sibp.search(r['t'])
        if m:
            rel = '姊' if m.group(1) == '姐' else m.group(1)
            g['sibling'].setdefault((rel, _norm_sx(m.group(2))), (r['n'], r['t']))

    # 7) 兄弟人数：兄弟N人
    bp = re.compile('兄弟([一二两三四五六七八九十]+)人')
    for r in cat(2):
        m = bp.search(r['t'])
        if m:
            n = _chinese2int(m.group(1))
            if n is not None:
                g['brothers'].setdefault(n, (r['n'], r['t']))

    # 8) 子女数量：花结X朵 / 花开X朵
    cp = re.compile('花[结开]([一二两三四五六七八九十]+)朵')
    for r in cat(4):
        m = cp.search(r['t'])
        if m:
            n = _chinese2int(m.group(1))
            if n is not None:
                g['children_count'].setdefault(n, (r['n'], r['t']))

    # 9) 干支标签纠错：覆盖正则错配/缺失，只订正键、不改断语原文
    n2t = {r['n']: r['t'] for r in rows}
    for gz, n in WIFE_GZ_LABEL_FIX.items():
        g['wife_ganzhi'][gz] = (n, n2t[n])
    for gz, n in HUSBAND_GZ_LABEL_FIX.items():
        g['husband_ganzhi'][gz] = (n, n2t[n])

    # 10) 坤集扩展密数表（再娶/三妻/四娶/再嫁/三嫁/夫妻同/父母同属/师父；经校验校正）
    g.update(build_extended_grid(rows))

    return g


def _hit(pool, kws, exclude=(), exact=''):
    """在池中找含关键词的条文，按相关性取最优（确定性）。
    排序：命中关键词数 降序 → 事实原文字面命中（精确子串）降序 → 条文号 升序。
    exact 为事实原文；若其字面出现在条文中，则该条优先于仅命中同义关键词者。"""
    best = None
    best_key = None
    for r in pool:
        t = r['t']
        if any(e in t for e in exclude):
            continue
        n_hit = sum(1 for k in kws if k in t)
        if n_hit == 0:
            continue
        hit_exact = 1 if exact and exact in t else 0
        key = (n_hit, hit_exact, -r['n'])
        if best_key is None or key > best_key:
            best_key = key
            best = r
    if best is None:
        return None
    return (best['n'], best['t'])


# ----------------------------------------------------------------------
# 六亲事实 → 条文 定位
# ----------------------------------------------------------------------

# 婚姻维多婚次子路由：事实关键词 → 扩展网格键
_EXT_MARRIAGE = {
    '再娶': 'remarry_wife', '二娶': 'remarry_wife', '续弦': 'remarry_wife',
    '三娶': 'third_wife', '三妻': 'third_wife',
    '四娶': 'fourth_wife', '四妻': 'fourth_wife',
    '再嫁': 'remarry_husband', '二嫁': 'remarry_husband',
    '三嫁': 'third_husband',
}


def _fact_zhi(fact):
    """从事实文本提取目标地支：优先「干支」（取支字），其次「生肖」归一。"""
    m = re.search('[%s][%s]' % (TIANGAN, DIZHI), fact)
    if m:
        return m.group(0)[1]
    for sx in SHENGXIAO:
        if sx in fact:
            return SX2DZ[sx]
    return None


def _fact_ganzhi(fact):
    """从事实文本提取完整干支，否则 None。"""
    m = re.search('([%s][%s])' % (TIANGAN, DIZHI), fact)
    return m.group(1) if m else None


def _lookup_ext_marriage(grid, key, fact):
    """扩展婚姻网格查表：优先完整干支键（60 干支式），其次地支/生肖回退——
    60 干支式取甲/乙首干，12 生肖式直接取地支键。"""
    g = grid.get(key)
    if not g:
        return None
    gz = _fact_ganzhi(fact)
    if gz and gz in g:
        return g[gz]
    zhi = _fact_zhi(fact)
    if zhi:
        return g.get(_dz2lead_gz(zhi)) or g.get(zhi)
    return None


def _sx_after(text, ch):
    """取 ch（父/母）后出现的第一个生肖字（归一后）。"""
    i = text.find(ch)
    if i < 0:
        return None
    for c in text[i:]:
        if c in SX_CLASS:
            return _norm_sx(c)
    return None


def lookup_parents(grid, fact):
    """父母维：父母同属（同/全/俱属）优先，其次「父X母Y」组合条，再其次父/母单条。"""
    if '属' in fact and ('同' in fact or '全' in fact or '俱' in fact):
        zhi = _fact_zhi(fact)
        if zhi:
            r = grid['parents_same'].get(zhi)
            if r:
                return {'pair': r, 'father': None, 'mother': None}
    fsx = _sx_after(fact, '父')
    msx = _sx_after(fact, '母')
    pair = grid['parents_pair'].get((fsx, msx)) if fsx and msx else None
    return {'pair': pair, 'father': grid['father'].get(fsx) if fsx else None,
            'mother': grid['mother'].get(msx) if msx else None}


def lookup_wife(rows, grid, fact):
    """婚姻维：多婚次/夫妻同庚 子路由优先，其次妻/夫干支，再其次生肖（属X/配X）兜底。"""
    for kw, key in _EXT_MARRIAGE.items():
        if kw in fact:
            r = _lookup_ext_marriage(grid, key, fact)
            if r:
                return r
            break   # 已判定为多婚次：无命中即停，避免误落正妻兜底
    if '夫妻同' in fact:
        r = _lookup_ext_marriage(grid, 'couple_same', fact)
        if r:
            return r
    m = re.search('([%s][%s])' % (TIANGAN, DIZHI), fact)
    if m:
        gz = m.group(1)
        if '妻' in fact:
            r = grid['wife_ganzhi'].get(gz)
            if r:
                return r
        if '夫' in fact:
            r = grid['husband_ganzhi'].get(gz)
            if r:
                return r
    # 生肖兜底：妻/夫 属X / 配X（精确匹配，避开“羊刃”等含生肖字的术词）
    sx = next((c for c in '鼠牛虎兔龙蛇马羊猴鸡犬猪' if c in fact), None)
    if sx:
        pool = [r for r in rows if r['c'] == 3]
        cand = [r for r in pool
                if '妻' in r['t'] and ('属%s' % sx in r['t'] or '配%s' % sx in r['t'])]
        if cand:
            r = min(cand, key=lambda x: x['n'])
            return (r['n'], r['t'])
    return None


def lookup_children(grid, fact):
    """子女维：女属X / 子属X 生肖优先，其次数量 花结X朵。"""
    if '女' in fact:
        for sx in SHENGXIAO:
            if sx in fact:
                return grid['daughter'].get(sx)
    if '子' in fact and '女' not in fact:
        for sx in SHENGXIAO:
            if sx in fact:
                return grid['son'].get(sx)
    m = re.search('[一二两三四五六七八九十]+', fact)
    if m:
        n = _chinese2int(m.group(0))
        if n is not None:
            return grid['children_count'].get(n)
    return None


def lookup_brothers(grid, fact):
    """兄弟维：姊/姐/妹/兄/弟 属X 优先，其次 兄弟N人。"""
    m = re.search('(姊|姐|妹|兄|弟)属([%s])' % SX_CLASS, fact)
    if m:
        rel = '姊' if m.group(1) == '姐' else m.group(1)
        return grid['sibling'].get((rel, _norm_sx(m.group(2))))
    mm = re.search('[一二两三四五六七八九十]+', fact)
    if mm:
        n = _chinese2int(mm.group(0))
        if n is not None:
            return grid['brothers'].get(n)
    return None


def lookup_teacher(grid, fact):
    """师父维（扩展表，源库类别 8）：师命生年，60 干支式按干支/地支查「师徒爻密数」网格。"""
    return _lookup_ext_marriage(grid, 'teacher', fact)


def lookup_liuqin(rows, grid, cat, fact):
    """六亲类别（1父母/2兄弟/3婚姻/4子女）统一入口，返回 (n, text) 或 None。"""
    if not fact:
        return None
    fact = _norm_sx(fact)
    if cat == 1:
        r = lookup_parents(grid, fact)
        return r['pair'] or r['father'] or r['mother']
    if cat == 2:
        return lookup_brothers(grid, fact)
    if cat == 3:
        return lookup_wife(rows, grid, fact)
    if cat == 4:
        return lookup_children(grid, fact)
    return None


# ----------------------------------------------------------------------
# 软维度（性情/事业/财帛/康寿）语义检索
# ----------------------------------------------------------------------

_SOFT_KW = {
    5: {   # 性情
        '温和': ['温和', '温良', '温恭', '和气', '温柔', '和顺', '量大'],
        '刚强': ['刚强', '刚烈', '刚毅', '性刚'],
        '急躁': ['性急', '急躁', '急性'],
        '聪明': ['聪明', '颖悟', '智慧', '灵敏'],
        '仁厚': ['仁厚', '仁德', '宽厚', '仁慈'],
        '正直': ['正直', '刚直', '忠直'],
        '清高': ['清高', '孤高', '高洁'],
        '豪爽': ['豪爽', '豪迈', '慷慨', '洒脱'],
    },
    6: {   # 事业
        '经商': ['商贾', '经商', '贸易', '营生', '生意', '商'],
        '功名': ['功名', '科第', '科甲', '进士', '科举', '登科', '及第'],
        '武职': ['武', '兵', '军', '将', '帅', '韬略'],
        '文职': ['文', '儒', '仕', '官', '宦', '黄堂'],
        '技艺': ['技艺', '手艺', '工匠', '医', '画'],
        '出家': ['出家', '僧', '道', '茅山'],
    },
    9: {   # 财帛
        '小康': ['小康', '温饱', '衣食', '蚕食', '丰衣', '足食'],
        '富': ['富贵', '巨富', '家财', '金玉', '丰财', '千金'],
        '贫': ['贫', '寒', '困', '无本'],
    },
    10: {  # 康寿
        '无伤病': ['多福', '无灾', '无病', '康宁', '多寿', '长寿', '安康', '无疾', '享福'],
        '有伤病': ['伤', '病', '疾', '刑', '残', '危'],
    },
}


def _soft_group(cat, fact):
    """匹配事实对应的语义组，返回关键词列表（未匹配则 None）。"""
    groups = _SOFT_KW.get(cat, {})
    for name, kws in groups.items():
        if name in fact:
            return kws
    # 康寿特判：否定词 + 病/灾/伤/刑/疾 → 无伤病。
    # 须在子串匹配之前判定，否则「无明显伤病」会被「伤/病」误判为「有伤病」。
    if cat == 10:
        if any(k in fact for k in ('无', '不', '免', '没', '未')) and \
           any(k in fact for k in ('病', '伤', '灾', '刑', '疾')):
            return groups.get('无伤病')
    for name, kws in groups.items():
        if any(k in fact for k in kws):
            return kws
    return None


def lookup_soft(rows, grid, cat, fact, gset):
    """软维度（性情/事业/财帛/康寿）语义检索，返回 (n, text) 或 None。"""
    if not fact:
        return None
    kws = _soft_group(cat, fact)
    pool = [r for r in rows if r['c'] == cat and r['g'] in gset]
    if not pool:
        pool = [r for r in rows if r['c'] == cat and r['g'] == 0]
    if not kws:
        return None
    return _hit(pool, kws, exact=fact)


# ----------------------------------------------------------------------
# 独立测试入口
# ----------------------------------------------------------------------

if __name__ == '__main__':
    rows = _load_rows()
    grid = build_grid(rows)
    print('网格规模：父生肖 %d 母生肖 %d 组合父母 %d 妻干支 %d 夫干支 %d 女属 %d 子属 %d 兄弟关系 %d 兄弟人数 %d 子女数 %d' % (
        len(grid['father']), len(grid['mother']), len(grid['parents_pair']),
        len(grid['wife_ganzhi']), len(grid['husband_ganzhi']),
        len(grid['daughter']), len(grid['son']), len(grid['sibling']),
        len(grid['brothers']), len(grid['children_count'])))
    print('扩展网格：再娶 %d 三妻 %d 四娶 %d 再嫁 %d 三嫁 %d 父母同属 %d 夫妻同庚 %d 师父 %d' % (
        len(grid['remarry_wife']), len(grid['third_wife']), len(grid['fourth_wife']),
        len(grid['remarry_husband']), len(grid['third_husband']), len(grid['parents_same']),
        len(grid['couple_same']), len(grid['teacher'])))
    print()
    tests = [
        (1, '父羊母兔'), (1, '父羊'), (1, '母兔'), (1, '父母同属羊'), (1, '父母全属猪'),
        (2, '姐属猪'), (2, '兄弟三人'),
        (3, '妻甲戌'), (3, '妻属羊'),
        (3, '再娶甲子'), (3, '再娶丙子'), (3, '三妻鼠'), (3, '三妻兔'),
        (3, '四娶甲午'), (3, '四娶壬午'),
        (3, '再嫁丙子'), (3, '再嫁壬子'), (3, '三嫁甲子'), (3, '三嫁龙'),
        (3, '夫妻同庚甲子'), (3, '夫妻同庚庚子'),
        (4, '三个女儿'), (4, '女属猪'), (4, '子属猴'),
    ]
    for cat, fact in tests:
        r = lookup_liuqin(rows, grid, cat, fact)
        print('%d | %-10s -> %s' % (cat, fact, r if r else '（未命中）'))
    print()
    for fact in ['师命乙丑', '师命丙子', '师命甲寅', '师命甲子', '师命鼠']:
        r = lookup_teacher(grid, fact)
        print('8 | %-10s -> %s' % (fact, r if r else '（未命中）'))