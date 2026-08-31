# -*- coding: utf-8 -*-
"""
liunian_14biao.py —— 十四表流年起数链（复刻 xaminxan/tiebanshenshu 主链路）

复用「本库 data/tiaowen.json」做断语查表；十四表表头结构见 data/liunian_14biao/14-*.csv。

起数主链路（与参考实现 tieban_main.py 一致）：
  先天命数 → 五音命数 → 日命数/时运数 → 考刻(初/正刻) → 本命数 → 十二辟卦
  → 后天命数 → 流年(每岁：四声/标记/字母/校正数 → 基数+加数=条文号 → 本库断语)

诚实边界（阶段6再收敛入 SKILL.md）：
  - 日命数/时运数依「求测时柱」，非出生时柱；缺求测时柱时回退出生时柱（近似标注 query_source）。
  - 本命条文分支(14-10)在参考实现即未生效，此处不实现，沿用本库八大分类条文。

阶段2结论（条文号域）：十四表产出的条文号(基数+加数)与「本库 data/tiaowen.json」
  同域同号（1001–13000），无需偏移重映射，直接以本库断语为准。仅 3 个 base=0 的空洞行
  （字母 西/萨/省，岁数 78–80，产出 177/345/513）在本库与参考库均无对应，按「缺条目」返回空。
"""
import os
import csv
import json
import io

HERE = os.path.dirname(os.path.abspath(__file__))
DATA14 = os.path.join(HERE, '..', 'data', 'liunian_14biao')
TIAOWEN_JSON = os.path.join(HERE, '..', 'data', 'tiaowen.json')

# 六十甲子纳音五行（与参考实现 NAYIN_WUXING 一致）
NAYIN_WUXING = {
    "甲子": "金", "乙丑": "金", "丙寅": "火", "丁卯": "火", "戊辰": "木", "己巳": "木",
    "庚午": "土", "辛未": "土", "壬申": "金", "癸酉": "金", "甲戌": "火", "乙亥": "火",
    "丙子": "水", "丁丑": "水", "戊寅": "土", "己卯": "土", "庚辰": "金", "辛巳": "金",
    "壬午": "木", "癸未": "木", "甲申": "水", "乙酉": "水", "丙戌": "土", "丁亥": "土",
    "戊子": "火", "己丑": "火", "庚寅": "木", "辛卯": "木", "壬辰": "水", "癸巳": "水",
    "甲午": "金", "乙未": "金", "丙申": "火", "丁酉": "火", "戊戌": "木", "己亥": "木",
    "庚子": "土", "辛丑": "土", "壬寅": "金", "癸卯": "金", "甲辰": "火", "乙巳": "火",
    "丙午": "水", "丁未": "水", "戊申": "土", "己酉": "土", "庚戌": "金", "辛亥": "金",
    "壬子": "木", "癸丑": "木", "甲寅": "水", "乙卯": "水", "丙辰": "土", "丁巳": "土",
    "戊午": "火", "己未": "火", "庚申": "木", "辛酉": "木", "壬戌": "水", "癸亥": "水",
}

TIANGAN = list("甲乙丙丁戊己庚辛壬癸")
DIZHI = list("子丑寅卯辰巳午未申酉戌亥")


def _decode(path):
    """整文件读取并按 utf-8-sig / gb18030 顺序尝试解码（各表编码混杂）。"""
    raw = open(path, 'rb').read()
    for enc in ('utf-8-sig', 'gb18030'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace')


def _read_rows(name):
    """读取 14-*.csv 为 dict list。"""
    text = _decode(os.path.join(DATA14, name))
    return list(csv.DictReader(io.StringIO(text)))


def _read_raw(name):
    """按无表头读 14-9.csv（刻别,本命数,卦名）。"""
    text = _decode(os.path.join(DATA14, name))
    return list(csv.reader(io.StringIO(text)))


class Tables14:
    """十四表惰性加载 + 一次解析为查表结构。"""

    def __init__(self):
        self.loaded = False

    def load(self):
        if self.loaded:
            return
        # 14-1 农历月份 -> 数值
        self.month_val = {r['农历月份'].strip(): int(r['数值']) for r in _read_rows('14-1.csv')}
        # 14-2 时支 -> 数值
        self.time_val = {r['时支'].strip(): int(r['数值']) for r in _read_rows('14-2.csv')}
        # 14-3 先天命数 -> {年干组(甲己..戊癸): 五音}
        self.cong_to_tone = {}
        for r in _read_rows('14-3.csv'):
            d = {k: r[k].strip() for k in ('甲己', '乙庚', '丙辛', '丁壬', '戊癸')}
            for n in r['先天命数'].split('|'):
                self.cong_to_tone[int(n.strip())] = d
        # 14-4 五音 -> 数值
        self.tone_val = {r['五音'].strip(): int(r['数值']) for r in _read_rows('14-4.csv')}
        # 14-5 日柱纳音 -> {天干: 数值}
        self.daynayin_gan = {}
        for r in _read_rows('14-5.csv'):
            self.daynayin_gan[r['日柱纳音'].strip()] = {g: int(r[g]) for g in TIANGAN}
        # 14-6 时柱纳音 -> 数值
        self.timenayin_val = {r['时柱纳音'].strip(): int(r['数值']) for r in _read_rows('14-6.csv')}
        # 14-7 考刻规则表 [(组别, 和值条件, 刻别)]
        self.rule_14_7 = [
            (r['组别'].strip(), r['和值条件'].strip(), r['刻别'].strip())
            for r in _read_rows('14-7.csv')
        ]
        # 14-9 十二辟卦 {(刻别, 本命数): 卦名}（无表头）
        self.hexagram = {}
        for row in _read_raw('14-9.csv'):
            if len(row) >= 3 and row[1].strip().isdigit():
                self.hexagram[(row[0].strip(), int(row[1].strip()))] = row[2].strip()
        # 14-11-1 (年支组, 性别) -> 起始数
        self.liunian_start = {}
        for r in _read_rows('14-11-1.csv'):
            self.liunian_start[(r['年支组'].strip(), r['性别'].strip())] = int(r['起始数'])
        # 14-11-2 (先天命数, 天干) -> [12 个流年四声]
        self.liunian_seq = {}
        for r in _read_rows('14-11-2.csv'):
            n = int(r['先天命数'].strip())
            seq = [r[str(i)].strip() for i in range(1, 13)]
            self.liunian_seq[(n, r['天干'].strip())] = seq
        # 14-12 {(流年地支, 后天命数): 流年标记}
        self.marker = {}
        for r in _read_rows('14-12.csv'):
            self.marker[(r['流年地支'].strip(), int(r['后天命数']))] = r['流年标记'].strip()
        # 14-13 {(考刻, 奇偶, 四声, 标记): 字母}
        self.letter = {}
        for r in _read_rows('14-13.csv'):
            self.letter[(r['考刻'].strip(), r['日命数加时运数的奇偶性'].strip(),
                         r['流年天四声'].strip(), r['流年标记'].strip())] = r['流年字母'].strip()
        # 14-14 双索引：(字母,岁数)->(基数,加数,校正数) / (校正数,岁数)->(基数,加数)
        self.by_letter = {}
        self.by_correction = {}
        for r in _read_rows('14-14.csv'):
            let = r['流年字母'].strip()
            age = int(r['流年岁数'])
            base = int(r['基数'])
            add = int(r['加数'])
            corr = int(r['条文校正数'])
            self.by_letter[(let, age)] = (base, add, corr)
            self.by_correction[(corr, age)] = (base, add)
        self.loaded = True


_TABLES = Tables14()
_TIAOWEN = {}
_TIAOWEN_LOADED = False


def load_tiaowen():
    """加载本库 tiaowen.json → {条文号: 断语文本}。"""
    global _TIAOWEN, _TIAOWEN_LOADED
    if _TIAOWEN_LOADED:
        return
    with open(TIAOWEN_JSON, 'r', encoding='utf-8') as f:
        rows = json.load(f)
    _TIAOWEN = {int(r['n']): r['t'] for r in rows}
    _TIAOWEN_LOADED = True


def gan_group(gan):
    if gan not in TIANGAN:
        return '甲己'
    return ('甲己', '乙庚', '丙辛', '丁壬', '戊癸')[TIANGAN.index(gan) % 5]


def zhi_group(zhi):
    if zhi in '寅午戌':
        return '寅午戌'
    if zhi in '申子辰':
        return '申子辰'
    if zhi in '巳酉丑':
        return '巳酉丑'
    return '亥卯未'


def is_yang_year(year_gan):
    return year_gan in '甲丙戊庚壬'


def norm_gender(g):
    return '男' if g in ('男', 'm', 'M') else '女'


def calc_correction(corr, age):
    """校正数按年龄校正：1-10/81-108 岁 +2(>6则-6)，其余 +3(>20则-20)。"""
    if corr == 0:
        return 0
    if (1 <= age <= 10) or (81 <= age <= 108):
        new = corr + 2
        if new > 6:
            new -= 6
    else:
        new = corr + 3
        if new > 20:
            new -= 20
    return new


# ----------------------------------------------------------------------
# 跨维度一致性约束：十四表流年断语 vs 考刻六亲事实（阶段5）
# 考刻已锁的六亲事实为权威；流年条文若与之相左，标「与事实冲突」、不据此改判六亲结论。
# ----------------------------------------------------------------------
_SON_BIRTH_KW = ('生子', '得子', '弄璋', '添丁', '生男', '产子')
_DAUGHTER_BIRTH_KW = ('生女', '弄瓦', '产女')
_FU_SANG_KW = ('父死', '父亡', '丧父', '父丧', '父终', '父殁', '父故', '父不禄',
               '椿折', '椿摧', '椿枯', '严亲见背', '哭父', '泣血', '丁忧',
               '父母俱亡', '父母双亡', '父母同亡', '父母同年丧')
_MU_SANG_KW = ('母亡', '母死', '丧母', '母丧', '母终', '母殁', '母故', '萱花萎', '哭母')
_WIFE_LOSS_KW = ('妻亡', '妻死', '丧妻', '妻丧', '妻殁', '鼓盆', '断弦', '克妻', '刑妻')

_LIUQIN_CN = {
    'no_child': '无子女', 'no_son': '有女无子',
    'fu_alive': '父健在', 'mu_alive': '母健在', 'wife_alive': '妻健在',
}


def _locked_liuqin(kaoke_facts):
    """从结构化考刻事实提取「已锁六亲事实」，供流年断语冲突标注。"""
    if not kaoke_facts:
        return {}
    lk = {}
    if kaoke_facts.get('fu_sang') is False:
        lk['fu_alive'] = True
    if kaoke_facts.get('mu_sang') is False:
        lk['mu_alive'] = True
    if kaoke_facts.get('wife_alive') is True:
        lk['wife_alive'] = True
    cc = kaoke_facts.get('child_count')
    cs = kaoke_facts.get('child_sex')
    if cc == 0:
        lk['no_child'] = True
    elif cs == '女' and cc:
        lk['no_son'] = True
    return lk


def _flag_conflict(text, lk):
    """对一条流年断语打冲突标记；无冲突返回 ''。"""
    if not text or not lk:
        return ''
    if lk.get('no_child') and any(k in text for k in _SON_BIRTH_KW + _DAUGHTER_BIRTH_KW):
        return '与本盘事实冲突（已锁无子女）'
    if lk.get('no_son') and any(k in text for k in _SON_BIRTH_KW):
        return '与本盘事实冲突（已锁无子·有女）'
    if lk.get('fu_alive') and any(k in text for k in _FU_SANG_KW):
        return '与本盘事实冲突（已锁父健在）'
    if lk.get('mu_alive') and any(k in text for k in _MU_SANG_KW):
        return '与本盘事实冲突（已锁母健在）'
    if lk.get('wife_alive') and any(k in text for k in _WIFE_LOSS_KW):
        return '与本盘事实冲突（已锁妻健在）'
    return ''


def compute(pillars, gender, lunar_month, lunar_day, is_leap=False, query_time_pillar=None,
            kaoke_facts=None):
    """十四表起数链。

    pillars: [年柱, 月柱, 日柱, 时柱]，每柱 2 字干支，如 ['甲子','庚午','乙丑','甲申']
    gender: '男'/'女'（或 'm'/'f'）
    lunar_month: 农历月 1-12；lunar_day: 农历日 1-30；is_leap: 是否闰月
    query_time_pillar: 求测时柱 2 字干支（缺省回退出生时柱，query_source 标记近似）
    """
    _TABLES.load()
    load_tiaowen()
    g = norm_gender(gender)

    y_gz, m_gz, d_gz, h_gz = pillars[0], pillars[1], pillars[2], pillars[3]
    y_gan, y_zhi = y_gz[0], y_gz[1]
    t_zhi = h_gz[1]

    # 求测时柱（用于日命数/时运数）；缺省回退出生时柱并标记
    if query_time_pillar:
        q_gz = query_time_pillar
        query_source = '求测时柱'
    else:
        q_gz = h_gz
        query_source = '出生时柱(近似)'

    # Step 1 先天命数
    calc_month = str(lunar_month + (1 if is_leap else 0))
    if int(calc_month) > 12:
        calc_month = '1'
    month_val = _TABLES.month_val.get(calc_month, int(calc_month))
    time_val = _TABLES.time_val.get(t_zhi, 0)
    cong_num = month_val + 3 - time_val
    if cong_num <= 0:
        cong_num += 12

    # Step 2 五音命数
    gg = gan_group(y_gan)
    tone = _TABLES.cong_to_tone.get(cong_num, {}).get(gg, '宫')
    tone_num = _TABLES.tone_val.get(tone, 5)

    # Step 3 日命数 & 时运数（用求测时柱）
    day_n = NAYIN_WUXING.get(d_gz, '金')
    day_life = _TABLES.daynayin_gan.get(day_n, {}).get(q_gz[0], 0)
    time_n = NAYIN_WUXING.get(q_gz, '金')
    time_luck = _TABLES.timenayin_val.get(time_n, 0)

    # Step 4 考刻（初刻/正刻）
    sum_val = day_life + time_luck
    grp = '阳男阴女' if ((g == '男') == is_yang_year(y_gan)) else '阴男阳女'
    cond = '>6' if sum_val > 6 else '<=6'
    moment_cn = '正刻'
    for gg_, cc, kk in _TABLES.rule_14_7:
        if gg_ == grp and cc == cond:
            moment_cn = kk
            break
    moment = 'Initial' if moment_cn == '初刻' else 'Main'

    # Step 5 本命数
    base_val = tone_num * 5 + day_life + time_luck
    fact = (base_val - 1) if sum_val <= 6 else (base_val - 6)
    main_num = fact * 30 + lunar_day

    # Step 6 十二辟卦
    hex_name = _TABLES.hexagram.get((moment_cn, main_num), None)

    # Step 7 后天命数
    pn_sum = cong_num + main_num
    pn_num = pn_sum % 8
    if pn_num == 0:
        pn_num = 8

    # Step 8 流年（1-100 岁）
    start = _TABLES.liunian_start.get((zhi_group(y_zhi), g), 0)
    raw_seq = _TABLES.liunian_seq.get((cong_num, y_gan))
    final_seq = ['?'] * 12
    if start != 0 and raw_seq and len(raw_seq) >= 12:
        off = (13 - start) % 12
        final_seq = [raw_seq[(i + off) % 12] for i in range(12)]

    st_tg = TIANGAN.index(y_gan)
    st_dz = DIZHI.index(y_zhi)
    lk = _locked_liuqin(kaoke_facts)
    liunian = []
    for age in range(1, 101):
        cur_tg = TIANGAN[(st_tg + age - 1) % 10]
        cur_dz = DIZHI[(st_dz + age - 1) % 12]
        sound = final_seq[(age - 1) % 12] if final_seq[0] != '?' else '?'
        marker = _TABLES.marker.get((cur_dz, pn_num), '?')
        parity = '奇数' if age % 2 != 0 else '偶数'
        letter = _TABLES.letter.get((moment_cn, parity, sound, marker), '?')

        base = add = corr = 0
        orig_fortune = corr2 = ''
        new_fortune = ''
        formula = ''
        if letter != '?' and (letter, age) in _TABLES.by_letter:
            base, add, corr = _TABLES.by_letter[(letter, age)]
            formula = '%d+%d' % (base, add)
            orig_fortune = str(base + add)
            corr2 = calc_correction(corr, age)
            if corr2 > 0 and (corr2, age) in _TABLES.by_correction:
                nb, na = _TABLES.by_correction[(corr2, age)]
                new_fortune = str(nb + na)

        t0 = _TIAOWEN.get(int(orig_fortune), '') if orig_fortune.isdigit() else ''
        t1 = _TIAOWEN.get(int(new_fortune), '') if new_fortune.isdigit() else ''
        conflict = _flag_conflict(t1 or t0, lk)

        liunian.append({
            'age': age, 'gz': cur_tg + cur_dz, 'sound': sound, 'marker': marker,
            'letter': letter, 'corr': corr, 'corr2': corr2,
            'formula': formula, 'n0': orig_fortune, 'n1': new_fortune,
            'text0': t0, 'text1': t1, 'conflict': conflict,
        })

    return {
        'bazi': pillars, 'gender': g,
        'lunar_month': lunar_month, 'lunar_day': lunar_day, 'is_leap': is_leap,
        'query_time_pillar': q_gz, 'query_source': query_source,
        'kaoke_facts': kaoke_facts, 'locked_liuqin': lk,
        'locked_liuqin_cn': [_LIUQIN_CN[k] for k in sorted(lk)],
        'cong_num': cong_num, 'tone': tone, 'tone_num': tone_num,
        'day_life': day_life, 'time_luck': time_luck, 'sum_val': sum_val,
        'grp': grp, 'moment_cn': moment_cn,
        'main_num': main_num, 'hex_name': hex_name,
        'pn_sum': pn_sum, 'pn_num': pn_num,
        'start': start, 'liunian': liunian,
    }


def render(res):
    L = []
    L.append('【十四表起数】')
    L.append('四柱 %s　性别 %s　农历 %d月%s　%d日' % (
        ' '.join(res['bazi']), res['gender'], res['lunar_month'],
        '(闰)' if res['is_leap'] else '', res['lunar_day']))
    L.append('先天命数 = %d　五音命数 = %s(%d)　日命:%d　时运:%d' % (
        res['cong_num'], res['tone'], res['tone_num'], res['day_life'], res['time_luck']))
    L.append('考刻 = %s (%s)　本命数 = %d　十二辟卦 = %s' % (
        res['moment_cn'], res['grp'], res['main_num'], res['hex_name']))
    L.append('后天命数 = (%d+%d)%%8 = %d　[求测时柱 %s，来源:%s]' % (
        res['cong_num'], res['main_num'], res['pn_num'],
        res['query_time_pillar'], res['query_source']))
    L.append('流年(1-100岁)：')
    for it in res['liunian']:
        flag = ('『%s』' % it['conflict']) if it.get('conflict') else ''
        L.append('  %3d %s 四声%s 标记%s 字母%s 校正%s→%s %s 条文%s→%s %s' % (
            it['age'], it['gz'], it['sound'], it['marker'], it['letter'],
            it['corr'], it['corr2'], it['formula'], it['n0'], it['n1'], flag))
    return '\n'.join(L)


def _selfcheck():
    # 命例锚定：README 1924-06-15 16:00（男，甲子 庚午 乙丑 甲申，五月十四，求测时柱 己巳）
    res = compute(['甲子', '庚午', '乙丑', '甲申'], '男', 5, 14,
                  is_leap=False, query_time_pillar='己巳')
    assert res['cong_num'] == 11, res['cong_num']
    assert res['tone_num'] == 2, res['tone_num']
    assert res['day_life'] == 4, res['day_life']
    assert res['time_luck'] == 3, res['time_luck']
    assert res['moment_cn'] == '初刻', res['moment_cn']
    assert res['main_num'] == 344, res['main_num']
    assert res['hex_name'] == '泰', res['hex_name']
    assert res['pn_num'] == 3, res['pn_num']

    a1 = res['liunian'][0]
    assert a1['gz'] == '甲子', a1['gz']
    assert a1['sound'] == '五', a1['sound']
    assert a1['marker'] == '土', a1['marker']
    assert a1['letter'] == '召', a1['letter']
    assert a1['n0'] == '2408', a1['n0']
    assert a1['n1'] == '6539', a1['n1']
    assert '时行平稳' in a1['text1'], a1['text1']

    a2 = res['liunian'][1]
    assert a2['gz'] == '乙丑', a2['gz']
    assert a2['n1'] == '3274', a2['n1']
    assert '童年一二岁' in a2['text1'], a2['text1']

    # 缺求测时柱 → 回退出生时柱，链路不崩
    res2 = compute(['甲子', '庚午', '乙丑', '甲申'], '男', 5, 14, is_leap=False)
    assert res2['query_source'] == '出生时柱(近似)', res2['query_source']
    assert isinstance(res2['liunian'], list) and len(res2['liunian']) == 100

    # 跨维度一致性约束（阶段5）：锁「无子女」→ 流年现「生子/生女」标冲突；
    # 锁「有女无子」→ 仅「生子」标冲突、「生女」不标；锁「父健在」→ 流年「父亡」标冲突。
    assert _locked_liuqin({}) == {}
    lk0 = _locked_liuqin({'child_count': 0})
    assert lk0 == {'no_child': True}, lk0
    lk1 = _locked_liuqin({'child_sex': '女', 'child_count': 2})
    assert lk1 == {'no_son': True}, lk1
    lk2 = _locked_liuqin({'fu_sang': False})
    assert lk2 == {'fu_alive': True}, lk2
    assert _flag_conflict('三女戏彩', lk0) == ''
    assert _flag_conflict('生男弄璋', lk0).startswith('与本盘事实冲突'), _flag_conflict('生男弄璋', lk0)
    assert _flag_conflict('生女弄瓦', lk0).startswith('与本盘事实冲突')
    assert _flag_conflict('生男弄璋', lk1).startswith('与本盘事实冲突')
    assert _flag_conflict('生女弄瓦', lk1) == ''
    assert _flag_conflict('父死母存', lk2).startswith('与本盘事实冲突')
    assert _flag_conflict('父死母存', {}) == ''
    # 引擎内冲突标注通路：同盘锁无子女后，流年中「生子」条目应带 conflict 字段
    res3 = compute(['甲子', '庚午', '乙丑', '甲申'], '男', 5, 14,
                   is_leap=False, query_time_pillar='己巳',
                   kaoke_facts={'child_count': 0})
    flags = [it['conflict'] for it in res3['liunian'] if it['conflict']]
    assert flags, '锁无子女后应有流年条目命中冲突标注'

    print('liunian_14biao.py 自检通过：1924 命例锚定命中，回退链路正常，冲突标注通路正常。')


def main():
    _selfcheck()


if __name__ == '__main__':
    main()