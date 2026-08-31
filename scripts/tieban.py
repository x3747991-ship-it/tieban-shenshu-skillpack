#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
铁板神数（邵子神数）条文断命引擎
输入：四柱八字（年/月/日/时干支）+ 性别，可选流年年龄
依据：12000 条铁板神数条文库（data/tiaowen.json）
起数：河洛太玄配数 → 天数/地数 → 先天本命卦 → 本命密钥 → 分类条文定位
"""
import argparse
import json
import os
import re
import sys
from itertools import combinations
from math import gcd
from datetime import date

# 方案C：六亲条文网格查表模块（与本引擎同目录）
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)
from tiaowen_grid import build_grid, lookup_liuqin, lookup_soft
import kaoke
import yansuan
from yiji_gua import build_yiji

# ----------------------------------------------------------------------
# 一、基础常量
# ----------------------------------------------------------------------

# 太玄配数诀（河洛理数 / 太玄数）：甲己子午九、乙庚丑未八、丙辛寅申七、
# 丁壬卯酉六、戊癸辰戌五、巳亥四。天干地支共用此表。
TAIXUAN = {
    '甲': 9, '乙': 8, '丙': 7, '丁': 6, '戊': 5,
    '己': 9, '庚': 8, '辛': 7, '壬': 6, '癸': 5,
    '子': 9, '丑': 8, '寅': 7, '卯': 6, '辰': 5, '巳': 4,
    '午': 9, '未': 8, '申': 7, '酉': 6, '戌': 5, '亥': 4,
}

TIANGAN = '甲乙丙丁戊己庚辛壬癸'
DIZHI = '子丑寅卯辰巳午未申酉戌亥'
YANG_GAN = set('甲丙戊庚壬')   # 阳干

# 后天八卦数（洛书数）→ 卦名；5 为中宫无卦
HOU_GUA = {1: '坎', 2: '坤', 3: '震', 4: '巽', 6: '乾', 7: '兑', 8: '艮', 9: '离'}
HOU_XIANG = {1: '水', 2: '地', 3: '雷', 4: '风', 6: '天', 7: '泽', 8: '山', 9: '火'}

# 六十四卦名：key = (上卦, 下卦)，卦用后天卦名
GUA64 = {
    ('乾', '乾'): '乾为天', ('乾', '兑'): '天泽履', ('乾', '离'): '天火同人', ('乾', '震'): '天雷无妄',
    ('乾', '巽'): '天风姤', ('乾', '坎'): '天水讼', ('乾', '艮'): '天山遁', ('乾', '坤'): '天地否',
    ('兑', '乾'): '泽天夬', ('兑', '兑'): '兑为泽', ('兑', '离'): '泽火革', ('兑', '震'): '泽雷随',
    ('兑', '巽'): '泽风大过', ('兑', '坎'): '泽水困', ('兑', '艮'): '泽山咸', ('兑', '坤'): '泽地萃',
    ('离', '乾'): '火天大有', ('离', '兑'): '火泽睽', ('离', '离'): '离为火', ('离', '震'): '火雷噬嗑',
    ('离', '巽'): '火风鼎', ('离', '坎'): '火水未济', ('离', '艮'): '火山旅', ('离', '坤'): '火地晋',
    ('震', '乾'): '雷天大壮', ('震', '兑'): '雷泽归妹', ('震', '离'): '雷火丰', ('震', '震'): '震为雷',
    ('震', '巽'): '雷风恒', ('震', '坎'): '雷水解', ('震', '艮'): '雷山小过', ('震', '坤'): '雷地豫',
    ('巽', '乾'): '风天小畜', ('巽', '兑'): '风泽中孚', ('巽', '离'): '风火家人', ('巽', '震'): '风雷益',
    ('巽', '巽'): '巽为风', ('巽', '坎'): '风水涣', ('巽', '艮'): '风山渐', ('巽', '坤'): '风地观',
    ('坎', '乾'): '水天需', ('坎', '兑'): '水泽节', ('坎', '离'): '水火既济', ('坎', '震'): '水雷屯',
    ('坎', '巽'): '水风井', ('坎', '坎'): '坎为水', ('坎', '艮'): '水山蹇', ('坎', '坤'): '水地比',
    ('艮', '乾'): '山天大畜', ('艮', '兑'): '山泽损', ('艮', '离'): '山火贲', ('艮', '震'): '山雷颐',
    ('艮', '巽'): '山风蛊', ('艮', '坎'): '山水蒙', ('艮', '艮'): '艮为山', ('艮', '坤'): '山地剥',
    ('坤', '乾'): '地天泰', ('坤', '兑'): '地泽临', ('坤', '离'): '地火明夷', ('坤', '震'): '地雷复',
    ('坤', '巽'): '地风升', ('坤', '坎'): '地水师', ('坤', '艮'): '地山谦', ('坤', '坤'): '坤为地',
}

# 条文集分类：类别码 → (章节名, 固定秘数偏移)
# 分类体系源自条文库「条文类别」字段；偏移为本技能包约定秘数（确定性、可复现）
CATEGORY = [
    (5,  '一、性情禀赋', 7),
    (1,  '二、父母祖业', 41),
    (2,  '三、兄弟排行', 27),
    (3,  '四、婚姻夫妻', 13),
    (4,  '五、子女后嗣', 59),
    (6,  '六、事业功名', 31),
    (9,  '七、财帛家业', 73),
    (10, '八、康宁寿元', 97),
]

GENDER_LABEL = {'m': '男命', 'f': '女命'}

# 命例卡「事实」中文键 → 类别码（六亲 + 软维度）
FACT_CAT = {
    '性情': 5, '父母': 1, '兄弟': 2, '婚姻': 3, '子女': 4,
    '事业': 6, '财帛': 9, '财运': 9, '康寿': 10, '健康': 10,
}


# ----------------------------------------------------------------------
# 二、数据加载
# ----------------------------------------------------------------------

def load_data():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, '..', 'data', 'tiaowen.json')
    with open(path, 'r', encoding='utf-8') as f:
        rows = json.load(f)
    rows.sort(key=lambda r: r['n'])
    return rows


# ----------------------------------------------------------------------
# 三、起数核心
# ----------------------------------------------------------------------

def jiu_yu(x):
    """取九余：正整数映射到 1..9（洛书九宫数域）。"""
    return (x - 1) % 9 + 1


def zhong_gong(gender):
    """中宫(5)无卦寄宫：男寄艮(8)、女寄坤(2)。"""
    return 8 if gender == 'm' else 2


def _parse_ages(text):
    """提取条文开头括号内的全部阿拉伯年龄数字。"""
    m = re.match(r'^[（(]\s*([^）)]*)\s*[)）]', text)
    if not m:
        return []
    return [int(x) for x in re.findall(r'\d+', m.group(1))]


# 流年条文主题关键词表：用于把某一岁的候选条文归类为「人生主题光谱」，
# 供后半生（未经历区）诚实呈现与「不符重算」时选锚。仅作参考标注，不作事实判断。
LIUNIAN_THEMES = [
    ('婚姻感情', ['夫妻', '婚姻', '鸳鸯', '并蒂', '双莲', '菱花', '白头', '琴瑟', '合卺',
                  '花烛', '绣户', '配偶', '结发', '佳偶', '鸾', '凤']),
    ('子女后嗣', ['生子', '生女', '一胎', '双胎', '添丁', '桂子', '弄璋', '弄瓦', '得子',
                  '产子', '麟', '儿孙', '子息', '玉燕']),
    ('父母六亲', ['父母', '萱草', '椿萱', '泣血', '丁忧', '丧父', '丧母', '严慈', '慈亲',
                  '萱堂', '椿庭', '双亲', '父', '母', '萱', '椿']),
    ('事业功名', ['升迁', '功名', '官职', '科第', '房考', '高魁', '封赠', '敕封', '仕宦',
                  '登科', '得官', '进爵', '委任', '升擢', '擢', '魁']),
    ('财帛家业', ['财帛', '钱财', '破财', '耗财', '金银', '田产', '家业', '土木', '丰盈',
                  '进益', '利润', '财', '钱', '粟', '帛', '富', '贫']),
    ('健康灾寿', ['血光', '大限', '晦滞', '疾厄', '三灾', '愆度', '难过', '病', '疾', '灾',
                  '祸', '伤', '死', '寿', '凶', '坎']),
    ('是非官非', ['是非', '口舌', '官非', '诉讼', '词讼', '牢狱', '纠纷', '干戈', '讼', '刑', '争']),
    ('出行变动', ['行迈', '驰驱', '出外', '远行', '蓬转', '走他乡', '跋涉', '行旅', '迁移',
                  '驿', '迁', '移']),
]

# 主题固定呈现顺序（综合岁运兜底排最后）
_THEME_ORDER = [nm for nm, _ in LIUNIAN_THEMES] + ['综合岁运']


def _classify(text):
    """把一条流年条文归入最贴合的主题；返回 (主题名, 命中关键词数)。无命中返回 (None, 0)。"""
    best_name = None
    best_n = 0
    for name, kws in LIUNIAN_THEMES:
        n = 0
        for k in kws:
            n += text.count(k)
        if n > best_n:
            best_n = n
            best_name = name
    return (best_name, best_n)


def liunian_pool(rows, gset):
    """流年条文候选池（类别 0，先按性别过滤，空则回退通用）。"""
    pool0 = [r for r in rows if r['c'] == 0 and r['g'] in gset]
    if not pool0:
        pool0 = [r for r in rows if r['c'] == 0 and r['g'] == 0]
    return pool0


def liunian_candidates(pool0, age):
    """某一年龄的候选条文（按年龄标签命中）。"""
    return [r for r in pool0 if age in _parse_ages(r['t'])]


# 父丧一致性约束：一旦锁定父丧年龄，其余岁需跳过父亡/父母双丧类占位，避免自相矛盾。
FU_SANG_KW = ('父死', '父亡', '丧父', '父丧', '父终', '父殁', '父不禄', '父故',
              '父曰云亡', '椿折', '椿摧', '椿枯', '椿树枯', '老椿', '椿庭',
              '吹折', '严亲见背', '思父', '泣血', '丁忧',
              '父母同年丧', '父母俱亡', '父母双亡', '父母同亡', '同年而亡', '同弃世')


def _is_fu_sang(text):
    return any(k in text for k in FU_SANG_KW)


# 在世亲属（母/妻/子女/泛亲）丧亡占位：已确认健在，前半生一律排除。
ALIVE_SANG_KW = (
    '母亡', '母死', '母故', '母日云亡', '丧母', '母丧', '母终', '母殁', '萱花',
    '妻亡', '妻死', '丧妻', '妻丧', '妻殁', '鼓盆', '鼓盘', '断弦', '弦断',
    '鸾胶', '续弦', '刑其妻', '克妻', '镜破', '破镜', '分镜',
    '子夭', '子亡', '子死', '女夭', '女亡', '女死', '丧子', '丧女', '丧明', '卜商',
    '丧骨肉',
    '孝服', '服丧', '披孝', '披麻', '丁艰', '守制', '举哀',
    '赴瑶池', '归瑶池', '驾鹤', '西归', '作古',
)


def _is_alive_sang(text):
    return any(k in text for k in ALIVE_SANG_KW)


def summarize_age(pool0, age, exclude=None):
    """把某一年龄的候选条目按主题归类，每主题抽一条代表条文（确定性）。

    exclude：可选过滤回调 exclude(text)->bool，命中则从候选剔除（如父丧一致性）。"""
    cand = liunian_candidates(pool0, age)
    if exclude:
        cand = [r for r in cand if not exclude(r['t'])]
    buckets = {}
    for r in cand:
        name, n = _classify(r['t'])
        key = name or '综合岁运'
        buckets.setdefault(key, []).append((r, n))
    themes = []
    for th in _THEME_ORDER:
        if th not in buckets:
            continue
        lst = buckets[th]
        r, n = max(lst, key=lambda t: (t[1], -t[0]['n']))
        themes.append({'theme': th, 'count': len(lst), 'n': r['n'], 'text': r['t']})
    return {'age': age, 'candidate_count': len(cand), 'themes': themes}


def build_result(rows, pillars, gender, ages, offsets=None, facts=None, liunian_anchors=None, future_ages=None, kaoke_facts=None, qiyun=3, birth_year=None, now_year=None, now_month=None, now_day=None, future_n=10, jieqi=None):
    """主起数流程，返回完整结果 dict。

    facts：可选「事实锚点」映射 {类别码(int): 事实文本(str)}，
    六亲维度（1/2/3/4）走条文网格精确查表、软维度走语义检索，命中即覆盖偏移推索引。
    offsets：可选「考刻校准」映射 {类别码(int): 秘数偏移(int)}，
    在无事实锚点的维度作回退，覆盖 CATEGORY 的默认偏移。
    liunian_anchors：可选「流年考刻」映射 {年龄(int): 目标条文号(int)}。
    future_ages：可选「后半年纪序列」（未经历区）。
    kaoke_facts：可选「结构化六亲事实」dict，用于跑考刻定分闭环并附于结果 dict 的 kaoke 字段。
    """
    year, month, day, hour = pillars
    all_chars = [year[0], year[1], month[0], month[1], day[0], day[1], hour[0], hour[1]]
    nums = [TAIXUAN[ch] for ch in all_chars]

    # 天数 / 地数（河洛理数：奇数之和为天数，偶数之和为地数）
    tian = sum(n for n in nums if n % 2 == 1)
    di = sum(n for n in nums if n % 2 == 0)

    # 本命密钥：8 位太玄数连缀
    key_str = ''.join(str(n) for n in nums)
    key = int(key_str)

    # 先天本命卦：天数取九余、地数取九余配卦，阳男/阴女天数在上、否则在下
    yang = year[0] in YANG_GAN
    yang_flag = (yang and gender == 'm') or ((not yang) and gender == 'f')
    tian_yu = jiu_yu(tian)
    di_yu = jiu_yu(di)
    if tian_yu == 5:
        tian_yu = zhong_gong(gender)
    if di_yu == 5:
        di_yu = zhong_gong(gender)
    tian_gua = HOU_GUA[tian_yu]
    di_gua = HOU_GUA[di_yu]
    if yang_flag:
        upper, lower = tian_gua, di_gua
    else:
        lower, upper = tian_gua, di_gua
    benming = GUA64.get((upper, lower), f'{upper}{lower}')

    # 各分类条文定位：优先「事实→条文」网格/语义查表，其次「考刻偏移」推索引
    gset = ({0, 1} if gender == 'm' else {0, 2})
    grid = build_grid(rows)
    sections = []
    facts = facts or {}
    for cat, name, off in CATEGORY:
        fact = facts.get(cat)
        hit = None
        if fact:
            if cat in (1, 2, 3, 4):
                hit = lookup_liuqin(rows, grid, cat, fact)
            else:
                hit = lookup_soft(rows, grid, cat, fact, gset)
        if hit:
            n, text = hit
            row = next((x for x in rows if x['n'] == n), None)
            sections.append({
                'cat': cat, 'name': name, 'n': n, 'text': text,
                'age': row['age'] if row else None,
                'gender_code': row['g'] if row else None,
                'source': 'grid',
            })
            continue
        if offsets and cat in offsets:
            off = offsets[cat]
        pool = [r for r in rows if r['c'] == cat and r['g'] in gset]
        if not pool:
            pool = [r for r in rows if r['c'] == cat and r['g'] == 0]
        if not pool:
            continue
        r = pool[(key + off) % len(pool)]
        sections.append({
            'cat': cat, 'name': name, 'n': r['n'], 'text': r['t'],
            'age': r['age'], 'gender_code': r['g'],
            'source': 'offset',
        })

    # 流年条文（前半生逐岁单条，可用流年考刻锚点精确命中；后半生逐岁候选主题光谱）
    liunian = []
    future = []
    ln_anchors = {int(k): int(v) for k, v in (liunian_anchors or {}).items()}
    # 父丧一致性：检测锚点中锁定了哪些岁是「父亡」。
    n2t = {r['n']: r['t'] for r in rows} if ln_anchors else None
    fu_sang_ages = {a for a, tn in ln_anchors.items() if n2t and _is_fu_sang(n2t.get(tn, ''))}
    fu_exclude = _is_fu_sang if fu_sang_ages else None
    pool0 = None
    if ages or future_ages:
        pool0 = liunian_pool(rows, gset)
    if ages:
        for a in ages:
            cand = liunian_candidates(pool0, a)
            if not cand:
                continue
            # 前半生一致性：母/妻/子女等已确认健在，其丧亡占位一律排除；
            # 父丧仅保留在锁定岁，其余岁不再出现父亡/父母双丧占位。
            filtered = [r for r in cand
                        if not _is_alive_sang(r['t'])
                        and not (_is_fu_sang(r['t']) and a not in fu_sang_ages)]
            if filtered:
                cand = filtered
            idx = (key + a * 31) % len(cand)
            target = ln_anchors.get(a)
            rr = next((r for r in cand if r['n'] == target), None) if target is not None else None
            if rr is not None:
                source = 'anchor'
            elif target is not None:
                source = 'anchor-miss'
            else:
                source = 'offset'
            rr = rr or cand[idx]
            liunian.append({'age': a, 'n': rr['n'], 'text': rr['t'], 'source': source})
    if future_ages:
        for a in future_ages:
            s = summarize_age(pool0, a, exclude=fu_exclude)
            if s['candidate_count']:
                future.append(s)

    # 考刻定分闭环：有结构化六亲事实则跑，并把条文号附上库对应断语供渲染
    kaoke_result = None
    if kaoke_facts:
        kaoke_result = kaoke.run_kaoke(pillars, gender, kaoke_facts)
        n2t = {r['n']: r['t'] for r in rows}
        for k in kaoke_result['ke_articles']:
            k['text'] = n2t.get(k['n'], '（库无此号）')
            kaoke_result['n2t_used'] = True

    # 皇极值卦（值运/值年卦体系，铁板神数正宗流年推演，取代子平大运方向）
    yiji = build_yiji(pillars, gender, benming, qiyun=qiyun,
                      birth_year=birth_year, now_year=now_year,
                      now_month=now_month, now_day=now_day, future_n=future_n,
                      jieqi=jieqi)

    # 演算法式（书传起数：化卦 → 八卦加则 → 条文号）
    ys = build_yansuan(rows, pillars, gender, birth_year)

    return {
        'bazi': [year, month, day, hour],
        'gender': gender,
        'chars': all_chars,
        'nums': nums,
        'key_str': key_str,
        'key': key,
        'tian': tian,
        'di': di,
        'tian_yu': tian_yu,
        'di_yu': di_yu,
        'tian_gua': tian_gua,
        'di_gua': di_gua,
        'benming_xiang': f'{HOU_XIANG[tian_yu]}{HOU_XIANG[di_yu]}',
        'benming_gua': benming,
        'upper': upper,
        'lower': lower,
        'sections': sections,
        'liunian': liunian,
        'future': future,
        'offsets_used': offsets,
        'kaoke': kaoke_result,
        'yiji': yiji,
        'yansuan': ys,
    }


# ----------------------------------------------------------------------
# 三之补充、考刻可解性自检（单一交代数 δ 模型）
# ----------------------------------------------------------------------

# 条文号上界：交代数 δ 落在此范围内即视为「唯一」（lcm 超过它就在全书刻度内唯一）
TIAOWEN_MAX_N = 13000


def _lcm(a, b):
    return a // gcd(a, b) * b


def selfcheck(rows, key, gender, anchors, cap=TIAOWEN_MAX_N):
    """考刻可解性自检。

    anchors：[(类别码, 目标条文号), ...]，目标条文号即「与该维事实最吻合」的那条。
    模型：若用单一交代数 δ 统一驱动各维，每维须满足 δ ≡ (目标索引 − key) mod 池长。
    检验这些同余方程是否两两相容，并求最大相容团（能同时被同一个 δ 命中的最多锚点）。

    返回 dict：items / compatible_pairs / conflicts / clique / solvable / clique_lcm / unique。
    """
    gset = ({0, 1} if gender == 'm' else {0, 2})
    cat_name = {c: n for c, n, _ in CATEGORY}

    items = []
    for cat, tn in anchors:
        name = cat_name.get(cat, '类%d' % cat)
        pool = [r for r in rows if r['c'] == cat and r['g'] in gset]
        if not pool:
            pool = [r for r in rows if r['c'] == cat and r['g'] == 0]
        L = len(pool)
        idx = next((i for i, r in enumerate(pool) if r['n'] == tn), None)
        if not pool or idx is None:
            items.append({'cat': cat, 'name': name, 'L': L, 'target': tn,
                          'idx': idx, 'r': None, 'note': '目标条文不在此类性别池内'})
            continue
        r = (idx - key) % L
        items.append({'cat': cat, 'name': name, 'L': L, 'target': tn,
                      'idx': idx, 'r': r, 'note': ''})

    valid = [it for it in items if it['r'] is not None]
    n = len(valid)

    compat_pairs = []
    conflicts = []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = valid[i], valid[j]
            g = gcd(a['L'], b['L'])
            ok = (a['r'] - b['r']) % g == 0
            if ok:
                compat_pairs.append((a['cat'], b['cat']))
            else:
                conflicts.append({
                    'a': a['cat'], 'b': b['cat'], 'gcd': g,
                    'ra': a['r'], 'rb': b['r'],
                    'a_name': a['name'], 'b_name': b['name'],
                })

    # 最大相容团：n 较小时全子集穷举，超过 15 维退化为贪心
    clique = []
    if n <= 15:
        compat_mask = [[False] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                a, b = valid[i], valid[j]
                if (a['r'] - b['r']) % gcd(a['L'], b['L']) == 0:
                    compat_mask[i][j] = compat_mask[j][i] = True
        best = 0
        for mask in range(1 << n):
            size = bin(mask).count('1')
            if size <= best:
                continue
            members = [i for i in range(n) if (mask >> i) & 1]
            if all(compat_mask[members[i]][members[j]]
                   for i in range(len(members)) for j in range(i + 1, len(members))):
                best = size
                clique = [valid[i]['cat'] for i in members]
    else:
        valid_by_cat = {it['cat']: it for it in valid}
        clique = []
        for it in valid:
            if all((it['r'] - valid_by_cat[c]['r']) % gcd(it['L'], valid_by_cat[c]['L']) == 0
                   for c in clique):
                clique.append(it['cat'])

    clique_items = [it for it in valid if it['cat'] in clique]
    clique_lcm = 1
    for it in clique_items:
        clique_lcm = _lcm(clique_lcm, it['L'])
    unique = clique_lcm >= cap

    solvable = (n > 0) and (len(clique) == n)

    return {
        'key': key,
        'gender': gender,
        'items': items,
        'valid_count': n,
        'total_pairs': n * (n - 1) // 2,
        'conflict_count': len(conflicts),
        'compatible_pairs': compat_pairs,
        'conflicts': conflicts,
        'clique': clique,
        'clique_names': [cat_name.get(c, '类%d' % c) for c in clique],
        'clique_lcm': clique_lcm,
        'unique': unique,
        'solvable': solvable,
    }


# ----------------------------------------------------------------------
# 四、输入解析
# ----------------------------------------------------------------------

def parse_gender(s):
    s = (s or '').strip().lower()
    if s in ('男', 'male', 'm', '1'):
        return 'm'
    if s in ('女', 'female', 'f', '2'):
        return 'f'
    raise ValueError(f'无法识别的性别：{s}（应为 男/女）')


def parse_pillar(s, label):
    s = (s or '').strip()
    if len(s) != 2:
        raise ValueError(f'{label}柱「{s}」长度应为 2（天干+地支），如「戊辰」')
    g, z = s[0], s[1]
    if g not in TIANGAN:
        raise ValueError(f'{label}柱天干「{g}」非法')
    if z not in DIZHI:
        raise ValueError(f'{label}柱地支「{z}」非法')
    return s


# ----------------------------------------------------------------------
# 五、输出
# ----------------------------------------------------------------------

# 父母态 → 白话释义
_PAR_PLAIN = {
    '父母寿': '父母均健在',
    '父母丧': '父母均已故',
    '父丧母寿': '父已丧、母健在',
    '母丧父寿': '母已丧、父健在',
    '父丧': '父已丧',
    '母丧': '母已丧',
}

# 子态 → 白话释义（十五分妻子表之「子」指男丁）
_ZI_PLAIN = {
    '无子': '无男丁',
    '一子': '一男丁',
    '二子': '二男丁',
    '三子': '三男丁',
    '四子': '四男丁',
    '五子': '五男丁',
    '少子': '男丁少',
    '多子': '男丁多',
    '二女': '二女',
    '多女': '多女',
}


def render_kaoke_section(k):
    """把考刻定分结论渲染为命书中的一个段落。k 为 build_result 附带的 kaoke dict。"""
    L = []
    L.append('── 附 · 考刻定分闭环（八刻父母弟兄表 · 十五分妻子表） ──')
    L.append('起数基数（天干合化：月千日百时十个）= %d；时支 %s' % (k['base'], k['hour_zhi']))
    L.append('八刻候选（供数号 = 基数 + 1327×2(k-1)，1327 为《破解钥匙》考刻秘数、非张椿来原书）：')
    locked = [x['ke'] for x in k['locked_ke']]
    for x in k['ke_articles']:
        mark = ' ←锁刻' if x['ke'] in locked else ''
        L.append('  %d刻〔%d〕%s·手足%s·%s%s' % (x['ke'], x['n'], x['par'], x['bro'], x['yao'], mark))
    L.append('  锁刻结论：' + ('多刻并列，需再问 ' if k['ke_tie'] else '') + '、'.join(
        '%d刻(%s·手足%s)' % (x['ke'], x['par'], x['bro']) for x in k['locked_ke']))
    L.append('  锁分结论：' + ('多分并列，需再问 ' if k['fen_tie'] else '') + '、'.join(
        '%d分(妻=%s·子=%s)' % (x['fen'], x['qi'], x['zi']) for x in k['locked_fen']))
    par_states = sorted({x['par'] for x in k['locked_ke']})
    zi_states = sorted({x['zi'] for x in k['locked_fen']})
    par_short = '、'.join(par_states) if par_states else '父母态'
    par_plain = '、'.join(_PAR_PLAIN.get(p, p) for p in par_states) if par_states else '未锁定'
    zi_short = '、'.join(zi_states) if zi_states else '子态'
    zi_plain = '、'.join(_ZI_PLAIN.get(z, z) for z in zi_states) if zi_states else '未锁定'
    L.append('  衔接：以上锁刻/锁分已与命主所提交六亲事实相合——「%s」即%s；「%s」即%s。' % (
        par_short, par_plain, zi_short, zi_plain))
    L.append('   刻分并列即传统「再问」，如需唯一锁定可再补一两个六亲细节收窄。')
    if k['ke_tie'] or k['fen_tie']:
        _dis = kaoke.disambiguate(k['hour_zhi'], k['locked_ke'], k['locked_fen'])
        if _dis:
            for q in _dis:
                L.append('   再问：%s （%s）' % (q['text'],
                       ' / '.join(q['options']) if q['options'] else '自由作答'))
        else:
            L.append('   再问说明：并列项在可问维度上格局相同（如夫态对男命不计分），如实保留并列。')
    return L


def render_yiji_section(y):
    YAO = {1: '初', 2: '二', 3: '三', 4: '四', 5: '五', 6: '上'}
    L = []
    L.append('── 九、皇极值卦 · 值运年卦（铁板神数正宗推演） ──────────────')
    L.append('〔先天本命卦〕%s（上%s下%s · %s）' % (y['benming_gua'], y['upper'], y['lower'], y['xiang']))
    yt = y['yuantang']
    L.append('〔六爻〕%s（初爻→上爻）' % ''.join('阳' if v else '阴' for v in yt['yao']))
    L.append('〔元堂〕%s爻为变爻 —— %s；时支%s为%s，%s。' % (
        YAO[yt['position']], yt['case'], yt['hour_zhi'], yt['parity'], yt['detail']))
    sy = y['shiying']
    L.append('〔世应〕%s：世居%s爻、应居%s爻。' % (sy['type_name'], YAO[sy['shi']], YAO[sy['ying']]))
    L.append('〔纳甲〕' + ' · '.join('%s%s' % (YAO[i + 1], y['najia'][i]) for i in range(6)))
    L.append('〔后天卦〕%s（%s）= 先天上下互置 + 元堂变爻' % (y['houtian_gua'], y['houtian_xiang']))
    L.append('')
    L.append('【值运卦】自先天卦元堂爻起、由下而上顺行（乾用九、坤用六：阳爻九年、阴爻六年），')
    L.append('先天六爻行毕再行后天六爻，共十二运段：')
    L.append('    顺行爻序：' + '→'.join(YAO[p] for p in y['seq']))
    current_xusui = y['value_years'][0]['xusui'] if y.get('value_years') else None
    for seg in y['segments']:
        mark = ''
        if current_xusui is not None and seg['from_age'] <= current_xusui <= seg['to_age']:
            mark = '  〔当前〕'
        L.append('  %s·%s %s爻（%s爻·纳%s·%d年）约%d~%d岁%s' % (
            seg['phase'], seg['gua'], YAO[seg['yao']], '阳' if seg['yang'] else '阴',
            seg['najia'], seg['years'], seg['from_age'], seg['to_age'], mark))
    L.append('')
    if y.get('value_years'):
        L.append('【值年卦】一年一变——段首看值运爻与流年阴阳、其后取应爻再向上顺行累计：')
        for vy in y['value_years']:
            L.append('  %d年%s 虚岁%d → %s（%s）· 值年爻%s爻（%s）· %s' % (
                vy['year'], vy['ganzhi'], vy['xusui'], vy['gua'], vy['xiang'],
                vy['yao_name'], '阳' if vy['yang'] else '阴', vy['note']))
    if y.get('month_guas'):
        L.append('')
        L.append('【值月卦】以值年卦值年爻「前一位」变起正月，单月向上顺行累计、双月取前单月值月爻应爻（§30-3）：')
        for mg in y['month_guas']:
            L.append('  %2d月 → %s（%s）· 值月爻%s爻 · %s' % (
                mg['month'], mg['gua'], mg['xiang'], YAO[mg['yao_pos']], mg['rule']))
    if y.get('today_days'):
        L.append('')
        _jie = '｜今日＝%s节起第%d候日' % (y['jie_name'], y['jie_day']) if y.get('jie_name') else ''
        L.append('【值日卦】以%d月值月卦「%s」（值月爻%s爻）为体，一爻管一日、六爻管六日（§30-4，月令以节候为起点%s）：' % (
            y['day_month'], y['today_days'][0]['gua'], YAO.get(y.get('day_yao_pos'), '?'), _jie))
        groups = [d for d in y['today_days'] if (d['day'] - 1) % 6 == 0]
        for gd in groups:
            L.append('  第%02d–%02d日〔变值月爻+%d=%s爻〕→ %s（%s）' % (
                gd['day'], gd['day'] + 5, ((gd['day'] - 1) // 6) + 1,
                gd['base_flip_name'], gd['gua'], gd['xiang']))
    L.append('')
    L.append('〔性质〕元堂、世应、纳甲、值运/值年/值月/值日卦均依《乾集》§11/§13/§15/§30 推演，')
    L.append('值运/值年/值月/值日卦取法以《图解易经象数学·铁版神数》§19 精校，确定性可复现。')
    L.append('注：纯乾女/纯坤男元堂取法分冬至/夏至，缺出生日期时由月柱地支推定，子、午月存疑（可用 --jieqi 强制指定出生节气区间）；')
    L.append('值月/值日卦已按 §30「月令以节候为起点」配十二节表定位（公历交节日近似 ±1 天，精确须交节时刻）。')
    return L


def build_yansuan(rows, pillars, gender, birth_year=None):
    """书传演算法式起数：四柱 → 化卦 → 八卦加则取数 → 条文号，并对库查条文。

    与旧「本命密钥 + 偏移取模」定位法不同，此链路依《张椿来·铁版神数》第三部分
    逐条复原，条文号可与 12000 条文库逐号核对（3788 / 2664 / 9516 / 10416 / 3926 …）。
    """
    n2t = {r['n']: r['t'] for r in rows}
    g = 'm' if gender == 'm' else 'f'
    t = yansuan.taixuan_suanfa(pillars, g)
    h = yansuan.huangji_suanfa(pillars)
    rz = yansuan.rizhu_peigua_suanfa(pillars)

    def _lookup(items):
        out = []
        for it in items:
            n = it['n']
            txt = n2t.get(n)
            out.append({'式': it['式'], 'n': n, 'text': txt, 'hit': txt is not None})
        return out

    return {
        'chain': yansuan.render_yansuan(pillars, g, birth_year=birth_year),
        'taixuan': t,
        'huangji': h,
        'rizhu': rz,
        'xian_shi': _lookup([
            {'式': '先天·正卦', 'n': t['xian_shu'][0]},
            {'式': '先天·互卦', 'n': t['xian_shu'][1]},
            {'式': '先天·变卦', 'n': t['xian_shu'][2]},
            {'式': '先天·变互', 'n': t['xian_shu'][3]},
        ]),
        'hou_shi': _lookup([
            {'式': '后天·正卦', 'n': t['hou_shu'][0]},
            {'式': '后天·互卦', 'n': t['hou_shu'][1]},
            {'式': '后天·变卦', 'n': t['hou_shu'][2]},
            {'式': '后天·变互', 'n': t['hou_shu'][3]},
        ]),
        'huangji_rows': _lookup([
            {'式': '皇极·考六亲（+8000）', 'n': h['jia_8000']},
            {'式': '皇极·初刻即中（+900）', 'n': h['jia_900']},
        ]),
        'rizhu_row': _lookup([{'式': '日柱配卦', 'n': rz['n']}])[0],
    }


def render_yansuan_section(ys):
    L = []
    L.append(ys['chain'])
    L.append('')
    L.append('【书传条文号 对 12000 条文库核对】')
    for it in ys['xian_shi']:
        L.append('  〔%d〕%s → %s' % (it['n'], it['式'], it['text'] or '（库无此号）'))
    for it in ys['hou_shi']:
        L.append('  〔%d〕%s → %s' % (it['n'], it['式'], it['text'] or '（库无此号）'))
    for it in ys['huangji_rows']:
        L.append('  〔%d〕%s → %s' % (it['n'], it['式'], it['text'] or '（库无此号）'))
    r = ys['rizhu_row']
    L.append('  〔%d〕日柱配卦 → %s' % (r['n'], r['text'] or '（库无此号）'))
    L.append('')
    L.append('〔性质〕此为铁板神数「化卦 → 八卦加则取数 → 查条文」正起数法，')
    L.append('与下述八大分类「本命密钥 + 偏移」的定位法互为表里：演算法式出总纲条文号，')
    L.append('八大分类与考刻出六亲人事断语。')
    return L


def render_text(r):
    L = []
    L.append('════════════════════════════════════')
    L.append('        铁板神数 · 命书')
    L.append('════════════════════════════════════')
    L.append('')
    L.append('【四柱】年柱 %s　月柱 %s　日柱 %s　时柱 %s' % tuple(r['bazi']))
    L.append('【性别】%s' % GENDER_LABEL[r['gender']])
    L.append('')
    L.append('【太玄配数】' + ' '.join('%s=%d' % (c, n) for c, n in zip(r['chars'], r['nums'])))
    L.append('【天数】%d（奇数之和）　【地数】%d（偶数之和）' % (r['tian'], r['di']))
    L.append('【先天本命卦】%s（上%s下%s）' % (r['benming_gua'], r['upper'], r['lower']))
    L.append('【本命密钥】%s' % r['key_str'])
    L.append('')
    if r.get('yansuan'):
        L.extend(render_yansuan_section(r['yansuan']))
        L.append('')
    for s in r['sections']:
        L.append('── %s ─────────────────' % s['name'])
        L.append('〔条文 %d〕%s' % (s['n'], s['text']))
        L.append('')
    if r.get('kaoke'):
        L.extend(render_kaoke_section(r['kaoke']))
        L.append('')
    if r.get('yiji'):
        L.extend(render_yiji_section(r['yiji']))
        L.append('')
    L.append('── 附 · 能力边界自陈 ──')
    L.append('本技能当前可靠范围：演算法式起数（化卦→八卦加则→条文号，书传可复现）+')
    L.append('八大分类条文（有事实锚点者）+ 考刻定分 + 皇极值卦（值运/值年）。')
    L.append('演算法式中「皇极 +8000/+900」加数为「唯一命例 + 元会运世框架」的合理推断、')
    L.append('原书未逐字转录，已如实标注为非逐字规则，不臆造公式；河洛天数地数（§5/§6 口诀')
    L.append('+ 命例逐项硬证）与「日柱配卦金钥匙」地支配卦均已复原并经书版命例硬证，属可证环节。')
    L.append('流年（逐年时序条文）层尚未完善：逐岁取条为确定性占位，与真实人生未必相符，')
    L.append('为避免与已提交事实自相矛盾（如「三女」却现「侧室生子」），故已停用，')
    L.append('不再逐岁/逐年展开条文；待逐岁事实标注库与跨维度一致性约束完备后再行升级。')
    L.append('值月/值日卦已按 §30「月令以节候为起点」配十二节表定位（公历交节日近似 ±1 天）；')
    L.append('纯卦分节气（冬至/夏至）缺精确出生日期时由月柱地支推定、子午月存疑（可用 --jieqi 指定），作文化参考、不作精确择日断。')
    L.append('')
    L.append('──────── 免责声明 ────────')
    L.append('本命书为传统命理文化研究工具，条文仅供文化参考，')
    L.append('不构成医疗、投资、婚姻、法律等现实决策依据。')
    return '\n'.join(L)


def render_summarize(pillars, gender, s):
    """单一年龄的流年候选主题要览（用于「不符重算」时选锚）。"""
    L = []
    L.append('════════════════════════════════════')
    L.append('  铁板神数 · 流年候选主题要览')
    L.append('════════════════════════════════════')
    L.append('')
    L.append('【四柱】年柱 %s　月柱 %s　日柱 %s　时柱 %s' % tuple(pillars))
    L.append('【性别】%s' % GENDER_LABEL[gender])
    L.append('【年龄】%d 岁 · 候选 %d 条 · %d 主题' % (s['age'], s['candidate_count'], len(s['themes'])))
    L.append('')
    for th in s['themes']:
        L.append('  · %s(%d)　〔条文 %d〕%s' % (th['theme'], th['count'], th['n'], th['text']))
    L.append('')
    L.append('选定主题后，将其代表条文号设为流年锚点锁定：--liunian \'{"%d":条文号}\'' % s['age'])
    return '\n'.join(L)


def render_selfcheck(pillars, gender, sc):
    L = []
    L.append('════════════════════════════════════')
    L.append('      铁板神数 · 考刻可解性自检')
    L.append('════════════════════════════════════')
    L.append('')
    L.append('【四柱】年柱 %s　月柱 %s　日柱 %s　时柱 %s' % tuple(pillars))
    L.append('【性别】%s' % GENDER_LABEL[gender])
    L.append('【本命密钥】%d' % sc['key'])
    L.append('【模型】单一交代数 δ：每维须 δ ≡ (目标条文索引 − 密钥) mod 池长')
    L.append('')
    L.append('── 锚点明细 ─────────────────')
    L.append('%-4s %-8s %-6s %-9s %s' % ('类别', '章节', '池长', '目标条文', '余数 r'))
    for it in sc['items']:
        if it['r'] is None:
            L.append('%-4d %-8s %-6d %-9d %s' % (it['cat'], it['name'], it['L'], it['target'], '（%s）' % it['note']))
        else:
            L.append('%-4d %-8s %-6d %-9d δ≡%d (mod %d)' % (it['cat'], it['name'], it['L'], it['target'], it['r'], it['L']))
    L.append('')
    L.append('── 相容性 ─────────────────')
    L.append('共 %d 个有效锚点，%d 对中 %d 对矛盾。' % (sc['valid_count'], sc['total_pairs'], sc['conflict_count']))
    if sc['conflicts']:
        L.append('矛盾对：')
        for c in sc['conflicts']:
            L.append('  %s(δ≡%d) vs %s(δ≡%d)  gcd=%d，%d%%%d=%d ≠ %d%%%d=%d' % (
                c['a_name'], c['ra'], c['b_name'], c['rb'], c['gcd'],
                c['ra'], c['gcd'], c['ra'] % c['gcd'], c['rb'], c['gcd'], c['rb'] % c['gcd']))
    L.append('')
    L.append('── 结论 ─────────────────')
    L.append('全量锚点能否被单一交代数同时命中？　%s' % ('能' if sc['solvable'] else '否'))
    if sc['clique']:
        L.append('最大相容团：%d 维 —— %s' % (len(sc['clique']), '、'.join(sc['clique_names'])))
        L.append('该团 lcm = %d，在 [0, %d] 内交代数%s唯一' % (
            sc['clique_lcm'], TIAOWEN_MAX_N, '已' if sc['unique'] else '未'))
        L.append('建议：仅取上述相容团同考；其余锚点与全团不相容，强行并入将无解。')
    else:
        L.append('无任何两个锚点相容；单一交代数模型下这组锚点无法同考。')
    L.append('')
    L.append('──────── 说明 ────────')
    L.append('本自检仅针对「单一交代数 δ」模型；当前引擎默认「逐维独立偏移」，')
    L.append('不受此限制，各维可各自命中其事实条文。')
    return '\n'.join(L)


def render_kaoke(result, rows):
    """渲染考刻定分闭环结果。"""
    n2t = {r['n']: r['t'] for r in rows}
    locked_ke_n = [x['ke'] for x in result['locked_ke']]
    locked_fen_n = [x['fen'] for x in result['locked_fen']]
    L = []
    L.append('════════════════════════════════════')
    L.append('     铁板神数 · 考刻定分闭环')
    L.append('════════════════════════════════════')
    L.append('')
    L.append('【四柱】%s · %s · %s · %s' % tuple(result['bazi']))
    L.append('【性别】%s' % GENDER_LABEL[result['gender']])
    L.append('【时支】%s（考刻考分以时支定表）' % result['hour_zhi'])
    L.append('')
    L.append('── 一、起数基数 ──')
    L.append('天干合化配数（月千·日百·时十·年个）→ 基数 = %d' % result['base'])
    L.append('')
    L.append('── 二、八刻考父母弟兄 ──')
    L.append('供数号 = 基数 + 1327×2(k-1)（1327 出《破解钥匙》、非张椿来原书），回卷 [1001,13000]')
    for k in result['ke_articles']:
        mark = ' ← 锁刻' if k['ke'] in locked_ke_n else ''
        txt = n2t.get(k['n'], '（库无此号）')
        L.append('  %d刻 〔%d〕 父母=%s · 手足=%s · 得爻=%s%s' % (
            k['ke'], k['n'], k['par'], k['bro'], k['yao'], mark))
        if k['detail']:
            L.append('          命中：%s' % '、'.join(k['detail']))
        L.append('          库对应条：%s' % txt)
    if result['locked_ke']:
        L.append('')
        L.append('  〔锁刻结论〕' + ('多刻并列：' if result['ke_tie'] else ''))
        for x in result['locked_ke']:
            L.append('    %d刻 · 父母=%s · 手足=%s' % (x['ke'], x['par'], x['bro']))
        if result['uncertainty']:
            L.append('    （校订存疑：%s）' % result['uncertainty'])
    L.append('')
    L.append('── 三、每刻十五分考妻子 ──')
    for f in result['fen_rows']:
        mark = ' ← 锁分' if f['fen'] in locked_fen_n else ''
        L.append('  %2d分 妻=%s · 子=%s · 夫=%s%s' % (f['fen'], f['qi'], f['zi'], f['fu'], mark))
        if f['detail']:
            L.append('          命中：%s' % '、'.join(f['detail']))
    if result['locked_fen']:
        L.append('')
        L.append('  〔锁分结论〕' + ('多分并列：' if result['fen_tie'] else ''))
        for x in result['locked_fen']:
            L.append('    %d分 · 妻=%s · 子=%s%s' % (x['fen'], x['qi'], x['zi'],
                   ('（夫态 %s，仅女命参考）' % x['fu']) if x['fu'] else ''))
    L.append('')
    if result['ke_tie'] or result['fen_tie']:
        _dis = kaoke.disambiguate(result['hour_zhi'], result['locked_ke'], result['locked_fen'])
        if _dis:
            L.append('── 四、破并列再问（确定性问题生成器） ──')
            for q in _dis:
                L.append('  · [%s/%d] %s' % (q['dim'], q['cat'], q['text']))
                L.append('        备选：%s' % (' / '.join(q['options']) if q['options'] else '自由作答'))
            L.append('')
        else:
            L.append('〔再问说明〕并列项在可问维度（父母/手足/妻/子）上格局相同，')
            L.append('如「夫态」对男命不计分，无法以细节追问区分，如实保留并列、不强行取唯一。')
    L.append('──────── 说明 ────────')
    L.append('「供数号」出自《铁板神数正宗破解钥匙》考刻秘数 1327，非张椿来《铁版神数》原书，其库对应条仅作对照；')
    L.append('破解钥匙自有序文集，与本 12000 库次序未必一致，故以表中')
    L.append('「格局」（父母态/手足/妻/子）为考刻权威结论。')
    L.append('刻分并列即传统考刻的「再问」环节：命主再答一两个六亲事实，')
    L.append('即可由并列候选进一步锁定真刻真分。')
    return '\n'.join(L)


def parse_anchors(raw_list):
    """解析 --anchors 值：支持重复传参及逗号分隔，格式 类别:条文号（如 1:9904）。"""
    anchors = []
    for s in (raw_list or []):
        for part in s.split(','):
            part = part.strip()
            if not part:
                continue
            if ':' in part:
                cat, tn = part.split(':', 1)
            elif '：' in part:
                cat, tn = part.split('：', 1)
            else:
                raise ValueError('锚点格式应为 类别:条文号（如 1:9904），收到：%s' % part)
            anchors.append((int(cat), int(tn)))
    return anchors


def facts_from_case(case):
    """从命例卡提取「ground_truth」事实 → {类别码: 事实文本}。"""
    gt = case.get('ground_truth') or case.get('事实') or {}
    facts = {}
    for k, v in gt.items():
        cat = FACT_CAT.get(k)
        if cat is not None and v:
            facts[cat] = str(v)
    return facts


def render_liunian14(res):
    """十四表流年起数链 → 命书段落。res 为 liunian_14biao.compute 的返回。"""
    L = []
    L.append('── 附 · 十四表流年起数链（跨传承来源，出命书后询问启用） ──')
    L.append('【四柱】%s　【性别】%s　【农历】%d月%s %d日' % (
        ' '.join(res['bazi']), res['gender'], res['lunar_month'],
        '(闰)' if res['is_leap'] else '', res['lunar_day']))
    L.append('先天命数 = %d　五音命数 = %s(%d)　日命:%d　时运:%d' % (
        res['cong_num'], res['tone'], res['tone_num'], res['day_life'], res['time_luck']))
    L.append('考刻 = %s（%s）　本命数 = %d　十二辟卦 = %s' % (
        res['moment_cn'], res['grp'], res['main_num'], res['hex_name']))
    L.append('后天命数 = (%d + %d) %% 8 = %d' % (res['cong_num'], res['main_num'], res['pn_num']))
    L.append('流年起数所取时柱 = %s（来源：%s）' % (res['query_time_pillar'], res['query_source']))
    L.append('')
    L.append('流年条文（逐岁：四声/标记/字母 → 基数+加数=条文号 → 本库断语）')
    if res.get('locked_liuqin_cn'):
        L.append('　〔跨维度一致性〕已对下述已锁六亲事实做冲突标注，冲突条目仅作传承参考、不改判考刻结论：%s'
                 % '、'.join(res['locked_liuqin_cn']))
    for it in res['liunian']:
        conf = it.get('conflict') or ''
        if it['text1']:
            line = '  %3d岁 %s 四声%s 标记%s 字母%s 校正%s→%s 条文%s·%s' % (
                it['age'], it['gz'], it['sound'], it['marker'], it['letter'],
                it['corr'], it['corr2'], it['n1'], it['text1'])
        elif it['text0']:
            line = '  %3d岁 %s 四声%s 标记%s 字母%s 条文%s·%s（校正后缺条目，回退原始条文）' % (
                it['age'], it['gz'], it['sound'], it['marker'], it['letter'],
                it['n0'], it['text0'])
        else:
            line = '  %3d岁 %s 四声%s 标记%s 字母%s 无条文（缺条目）' % (
                it['age'], it['gz'], it['sound'], it['marker'], it['letter'])
        if conf:
            line += '　《%s，仅作传承参考》' % conf
        L.append(line)
    return '\n'.join(L)


def render_shuchuan_liunian(sl, rows):
    """渲染书传流年 · 逐岁条文链（§5 大运数序 + §27 流年取数）。"""
    n2t = {r['n']: r['t'] for r in rows}
    L = []
    L.append('════════════════════════════════════')
    L.append('   铁板神数 · 书传流年（§5 + §27 逐岁条文）')
    L.append('════════════════════════════════════')
    L.append('')
    L.append('【四柱】%s　【性别】%s　【起运】%d 岁' % (
        ' '.join(sl['pillars']), GENDER_LABEL[sl['gender']], sl['qiyun']))
    L.append('【大运】自月柱%s %s排：%s' % (
        sl['pillars'][1], '顺' if sl['forward'] else '逆', '、'.join(sl['dayun_list'])))
    L.append('【取数】千=月干合化+大运干合化　百=日干合化　十=时干合化　个=流年干合化+流年支生数')
    L.append('')
    cur_dayun = None
    for it in sl['items']:
        if it['dayun'] != cur_dayun:
            cur_dayun = it['dayun']
            L.append('── 大运 %s（%d 岁起）─────────────────' % (cur_dayun, it['age']))
        txt = n2t.get(it['n'])
        show = txt if txt else '（库无此号）'
        wide = '〔千位和≥10·五位数〕' if it['wide'] else ''
        note = ('　/' + it['note']) if it['note'] else ''
        L.append('  %3d岁 %s  千%d·百%d·十%d·个%d → 条文 %d %s：%s%s' % (
            it['age'], it['liunian'], it['qian'], it['bai'], it['shi'], it['ge'],
            it['n'], wide, show, note))
    L.append('')
    L.append('──────── 诚实边界 ────────')
    L.append('§5 大运数序经书版命例（庚寅 甲申 丙午 甲午·男·乙酉→8648 等）逐位硬证、可证；')
    L.append('§27 流年取数（流年干支代替年干支、加流年支生数）出自《破解钥匙》，但破解钥匙')
    L.append('未逐字说明流年千位是否仍叠加大运干数、张椿来原书无流年命例，故「流年千位保持')
    L.append('大运干」为据破解钥匙文字之推断、非命例硬证，逐年条文号查本库、命中即原文，')
    L.append('「库无此号」如实标注。本表为书传流年，与「十四表流年」（跨传承）两套体系并存、互不混淆。')
    return '\n'.join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description='铁板神数条文断命')
    ap.add_argument('--year', required=True, help='年柱，如 戊辰')
    ap.add_argument('--month', required=True, help='月柱，如 己未')
    ap.add_argument('--day', required=True, help='日柱，如 丁卯')
    ap.add_argument('--hour', required=True, help='时柱，如 辛丑')
    ap.add_argument('--gender', required=True, help='性别：男/女')
    ap.add_argument('--age', default='', help='流年年龄，多个用逗号分隔，如 45 或 21,22。与 --birth-year 二选一；给了出生年则自动生成全序列')
    ap.add_argument('--birth-year', type=int, default=None, help='出生公历年份，据此自动生成前半生(虚岁1..当前)与后N年年龄序列')
    ap.add_argument('--future', type=int, default=10, help='预测未来年数（默认10，需配合 --birth-year）')
    ap.add_argument('--now-year', type=int, default=None, help='当前年份（默认取系统年份，可覆盖保证可复现）')
    ap.add_argument('--now-month', type=int, default=None, help='当前月份（默认取系统月份，可覆盖保证值月/值日卦可复现）')
    ap.add_argument('--now-day', type=int, default=None, help='当前日（默认取系统日，配合 --now-month 精确到节候日的值日卦）')
    ap.add_argument('--summarize-age', type=int, default=None, help='输出指定年龄的流年候选主题要览（用于“不符重算”选锚）')
    ap.add_argument('--offsets', default='', help='考刻校准偏移，JSON 对象，如 {\"5\":29,\"1\":68}')
    ap.add_argument('--facts', default='', help='事实锚点，JSON 对象映射类别码→事实文本，如 {\"1\":\"父羊母兔\",\"5\":\"温和\"}')
    ap.add_argument('--liunian', default='', help='流年考刻锚点，JSON 对象映射 年龄→条文号，如 {\"31\":8662}')
    ap.add_argument('--case', default='', help='命例卡 JSON 路径，读取其中的 offsets 与 ground_truth 字段')
    ap.add_argument('--anchors', action='append', default=None,
                    help='考刻锚点，格式 类别:条文号，可逗号分隔或重复传参，如 "1:9904,2:11274"')
    ap.add_argument('--selfcheck', action='store_true',
                    help='运行考刻可解性自检（配合 --anchors 使用）')
    ap.add_argument('--kaoke', action='store_true', help='运行考刻定分闭环（配合 --kaoke-facts）')
    ap.add_argument('--kaoke-circuit', action='store_true',
                    help='以考刻闭环状态机跑一步：给当前已答事实，输出下一轮该问（硬锚点剩余→破并列追问）与锁刻锁分状态；配合 --kaoke-facts（可为空 {}）')
    ap.add_argument('--kaoke-facts', default='',
                    help='考刻事实，JSON 对象，如 {"fu_sang":true,"mu_sang":false,"brothers_n":1,'
                         '"wife_alive":true,"child_sex":"女","child_count":3}')
    ap.add_argument('--qiyun', type=int, default=3, help='起运岁数（皇极值卦值运段起点，未经节气精算时按此默认）')
    ap.add_argument('--jieqi', choices=['dongzhi', 'xiazhi'], default=None,
                    help='纯乾女/纯坤男元堂取法分冬/夏至；缺精确出生日期时由月柱地支推定、子午月跨节气存疑。'
                         '此参数强制指定出生节气区间：dongzhi=冬至至夏至 / xiazhi=夏至至冬至')
    ap.add_argument('--liunian14', action='store_true',
                    help='十四表流年（跨传承来源，默认关）：需配合 --lunar-month/--lunar-day，可选 --query-hour')
    ap.add_argument('--lunar-month', type=int, default=None, help='农历出生月（1-12，配合 --liunian14）')
    ap.add_argument('--lunar-day', type=int, default=None, help='农历出生日（1-30，配合 --liunian14）')
    ap.add_argument('--lunar-leap', action='store_true', help='出生月为闰月（配合 --liunian14）')
    ap.add_argument('--query-hour', default='',
                    help='求测时柱（2字干支，如 己巳；缺省回退出生时柱，流年起数视为近似）')
    ap.add_argument('--shuchuan-liunian', action='store_true',
                    help='书传流年（§5 大运数序 + §27 流年取数，逐岁条文）：据书传公式铺逐年条文号并查库')
    ap.add_argument('--shuchuan-ages', type=int, default=100,
                    help='书传流年覆盖岁数（默认 100，配合 --shuchuan-liunian）')
    ap.add_argument('--json', action='store_true', help='输出 JSON（供程序消费）')
    args = ap.parse_args(argv)

    offsets = None
    facts = {}
    liunian_anchors = None
    kaoke_case_facts = None
    case_birth_year = None
    if args.case.strip():
        with open(args.case, 'r', encoding='utf-8-sig') as f:
            case = json.load(f)
        offsets = case.get('offsets') or case.get('校准偏移')
        facts = facts_from_case(case)
        liunian_anchors = case.get('liunian_anchors') or case.get('流年考刻')
        kaoke_case_facts = case.get('kaoke_facts') or case.get('考刻事实')
        case_birth_year = case.get('birth_year')
    if args.offsets.strip():
        offsets = json.loads(args.offsets)
    if offsets:
        offsets = {int(k): int(v) for k, v in offsets.items()}
    if args.facts.strip():
        raw = json.loads(args.facts)
        facts.update({int(k): str(v) for k, v in raw.items()})
    if args.liunian.strip():
        raw = json.loads(args.liunian)
        liunian_anchors = {int(k): int(v) for k, v in raw.items()}

    gender = parse_gender(args.gender)
    pillars = [
        parse_pillar(args.year, '年'),
        parse_pillar(args.month, '月'),
        parse_pillar(args.day, '日'),
        parse_pillar(args.hour, '时'),
    ]
    ages = []
    future_ages = []
    birth_year = args.birth_year or case_birth_year
    now_year = args.now_year
    if birth_year:
        now_year = now_year or date.today().year
        xusui = now_year - birth_year + 1
        ages = list(range(1, xusui + 1))
        future_ages = list(range(xusui + 1, xusui + 1 + args.future))
    elif args.age.strip():
        ages = [int(t) for t in args.age.split(',') if t.strip()]

    rows = load_data()

    if args.selfcheck:
        anchors = parse_anchors(args.anchors)
        if not anchors:
            raise ValueError('--selfcheck 需通过 --anchors 提供至少一个锚点（格式 类别:条文号）')
        chars = [pillars[i][j] for i in range(4) for j in range(2)]
        nums = [TAIXUAN[c] for c in chars]
        key = int(''.join(str(x) for x in nums))
        sc = selfcheck(rows, key, gender, anchors)
        if args.json:
            print(json.dumps({'bazi': pillars, 'gender': gender, 'selfcheck': sc},
                             ensure_ascii=False, indent=2))
        else:
            print(render_selfcheck(pillars, gender, sc))
        return

    if args.summarize_age is not None:
        gset = ({0, 1} if gender == 'm' else {0, 2})
        pool0 = liunian_pool(rows, gset)
        s = summarize_age(pool0, args.summarize_age)
        if args.json:
            print(json.dumps({'bazi': pillars, 'gender': gender, 'summarize_age': s},
                             ensure_ascii=False, indent=2))
        else:
            print(render_summarize(pillars, gender, s))
        return

    if args.kaoke:
        # 事实来源优先级：命例卡 kaoke_facts > --kaoke-facts（内联 JSON 或文件路径）
        kfacts = kaoke_case_facts
        if kfacts is None and args.kaoke_facts.strip():
            raw = args.kaoke_facts.strip()
            try:
                kfacts = json.loads(raw)
            except json.JSONDecodeError:
                with open(raw, 'r', encoding='utf-8-sig') as f:
                    kfacts = json.load(f)
        if kfacts is None:
            raise ValueError('--kaoke 需结构化六亲事实：命例卡 kaoke_facts 字段，'
                             '或 --kaoke-facts 传内联 JSON / JSON 文件路径')
        result = kaoke.run_kaoke(pillars, gender, kfacts)
        if args.json:
            print(json.dumps({'bazi': pillars, 'gender': gender, 'kaoke': result},
                             ensure_ascii=False, indent=2))
        else:
            print(render_kaoke(result, rows))
        return

    if args.kaoke_circuit:
        # 闭环状态机：与 --kaoke 同一事实来源，但允许空/部分事实——每次调用推进一步。
        kfacts = kaoke_case_facts
        if kfacts is None and args.kaoke_facts.strip():
            raw = args.kaoke_facts.strip()
            try:
                kfacts = json.loads(raw)
            except json.JSONDecodeError:
                with open(raw, 'r', encoding='utf-8-sig') as f:
                    kfacts = json.load(f)
        if kfacts is None:
            kfacts = {}
        st = kaoke.kaoke_circuit(pillars, gender, kfacts)
        if args.json:
            print(json.dumps({'bazi': pillars, 'gender': gender, 'circuit': st},
                             ensure_ascii=False, indent=2))
        else:
            print(kaoke.render_circuit(st))
        return

    if args.liunian14:
        # 十四表流年：跨传承来源，默认关。需农历月日；求测时柱缺省回退出生时柱（近似）。
        if args.lunar_month is None or args.lunar_day is None:
            raise ValueError('--liunian14 需 --lunar-month 与 --lunar-day（农历出生月/日）')
        if not (1 <= args.lunar_month <= 12) or not (1 <= args.lunar_day <= 30):
            raise ValueError('农历月应在 1-12、农历日应在 1-30 之间')
        # 考刻六亲事实（结构化）：可选，用于对冲突流年条目做一致性标注（不改判）。
        kfacts = kaoke_case_facts
        if kfacts is None and args.kaoke_facts.strip():
            raw = args.kaoke_facts.strip()
            try:
                kfacts = json.loads(raw)
            except json.JSONDecodeError:
                with open(raw, 'r', encoding='utf-8-sig') as f:
                    kfacts = json.load(f)
        import liunian_14biao as ln14
        res14 = ln14.compute(pillars, gender, args.lunar_month, args.lunar_day,
                             is_leap=args.lunar_leap,
                             query_time_pillar=(args.query_hour or None),
                             kaoke_facts=kfacts)
        if args.json:
            print(json.dumps({'bazi': pillars, 'gender': gender, 'liunian14': res14},
                             ensure_ascii=False, indent=2))
        else:
            print(render_liunian14(res14))
        return

    if args.shuchuan_liunian:
        # 书传流年：§5 大运数序 + §27 流年取数（逐岁条文），据书传公式铺逐年条文号并查库。
        sl = yansuan.shuchuan_liunian(pillars, gender, qiyun=args.qiyun, n_ages=args.shuchuan_ages)
        if args.json:
            print(json.dumps({'bazi': pillars, 'gender': gender, 'shuchuan_liunian': sl},
                             ensure_ascii=False, indent=2))
        else:
            print(render_shuchuan_liunian(sl, rows))
        return

    res = build_result(rows, pillars, gender, ages, offsets=offsets, facts=facts, liunian_anchors=liunian_anchors, future_ages=future_ages, kaoke_facts=kaoke_case_facts, qiyun=args.qiyun, birth_year=birth_year, now_year=now_year, now_month=args.now_month, now_day=args.now_day, future_n=args.future, jieqi=args.jieqi)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(render_text(res))


if __name__ == '__main__':
    try:
        main()
    except ValueError as e:
        print(f'[输入错误] {e}', file=sys.stderr)
        sys.exit(1)