#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
皇极值卦（值运 / 值年 / 值月 / 值日卦）推演模块
元堂取法（§11 含纯乾/纯坤分节气）、纳甲、世应、先天变后天依《张椿来·铁版神数》乾集原书；
值运/值年/值月/值日卦法（§30）原书缺高清图，以《图解易经象数学·铁版神数》（唐颐 著）§19 精校：
  §3  伏羲先天八卦数（乾一兑二离三震四巽五坎六艮七坤八）
  §11 元堂取法（阳时阴时 + 卦内阴阳爻多寡；纯乾/纯坤分男女节气）
  §13 爻纳干支（纳甲 / 纳支）
  §15 安世应（八宫世应）
  §16 先天卦变后天卦（上下互置 + 元堂变爻）
  §19 值运、年、月、日卦法（乾用九坤用六，阳爻九年阴爻六年；
       值年取应爻逐年；值月以值年卦元堂前一位起正月；值日一爻管一日六日一卦）

用途：以铁板神数正宗的皇极值卦体系，取代子平式「十神喜忌大运方向」，
输出「先天本命卦 → 元堂 → 值运卦（阳九阴六分段）→ 值年卦 → 值月卦 → 值日卦」
的运程框架。推演全程确定性、可复现。
"""
import os
import sys
from datetime import date

# 本模块与 tieban.py 同目录；供 tieban.py `from yiji_gua import ...` 时自包含，
# 亦可在无 tieban 上下文时单独以标准库运行。

TIANGAN = '甲乙丙丁戊己庚辛壬癸'
DIZHI = '子丑寅卯辰巳午未申酉戌亥'

# 阳时（子至巳）、阴时（午至亥）——元堂取法用（§11，非奇偶地支阴阳）
YANG_SHI = '子丑寅卯辰巳'
YIN_SHI = '午未申酉戌亥'

# 阳支（流年阴阳判断用，§30 值年卦）
YANG_ZHI = set('子寅辰午申戌')

# 八卦自然象（后天卦象 → 五行自然物）
XIANG = {'坎': '水', '坤': '地', '震': '雷', '巽': '风',
         '乾': '天', '兑': '泽', '艮': '山', '离': '火'}

# 爻位名
_YAO_NAME = {1: '初', 2: '二', 3: '三', 4: '四', 5: '五', 6: '上'}

# 八纯卦三爻：自初爻至上爻，1=阳、0=阴
BAGUA_3 = {
    '乾': [1, 1, 1],
    '兑': [1, 1, 0],
    '离': [1, 0, 1],
    '震': [1, 0, 0],
    '巽': [0, 1, 1],
    '坎': [0, 1, 0],
    '艮': [0, 0, 1],
    '坤': [0, 0, 0],
}
BAGUA_3_REV = {tuple(v): k for k, v in BAGUA_3.items()}

# 六十四卦名：key = (上卦, 下卦)，与 tieban.py 中 GUA64 完全一致
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

# 卦名 → (上卦, 下卦)
NAME2UP = {name: (up, low) for (up, low), name in GUA64.items()}

# 京房八宫（每宫八卦，次序：本宫/一世/二世/三世/四世/五世/游魂/归魂）
BAGUAN_8GONG = {
    '乾': ['乾为天', '天风姤', '天山遁', '天地否', '风地观', '山地剥', '火地晋', '火天大有'],
    '坎': ['坎为水', '水泽节', '水雷屯', '水火既济', '泽火革', '雷火丰', '地火明夷', '地水师'],
    '艮': ['艮为山', '山火贲', '山天大畜', '山泽损', '火泽睽', '天泽履', '风泽中孚', '风山渐'],
    '震': ['震为雷', '雷地豫', '雷水解', '雷风恒', '地风升', '水风井', '泽风大过', '泽雷随'],
    '巽': ['巽为风', '风天小畜', '风火家人', '风雷益', '天雷无妄', '火雷噬嗑', '山雷颐', '山风蛊'],
    '离': ['离为火', '火山旅', '火风鼎', '火水未济', '山水蒙', '风水涣', '天水讼', '天火同人'],
    '坤': ['坤为地', '地雷复', '地泽临', '地天泰', '雷天大壮', '泽天夬', '水天需', '水地比'],
    '兑': ['兑为泽', '泽水困', '泽地萃', '泽山咸', '水山蹇', '地山谦', '雷山小过', '雷泽归妹'],
}

# 世应位置：idx 0..7 → (世爻, 应爻)，爻位 1=初 .. 6=上
SHIYING = {0: (6, 3), 1: (1, 4), 2: (2, 5), 3: (3, 6),
           4: (4, 1), 5: (5, 2), 6: (4, 1), 7: (3, 6)}
SHIYING_NAME = {0: '本宫（八纯）', 1: '一世', 2: '二世', 3: '三世',
                4: '四世', 5: '五世', 6: '游魂', 7: '归魂'}

# 纳甲爻辰（八纯卦，自初爻至上爻六纳支，含天干）
NAJIA = {
    '乾': ['甲子', '甲寅', '甲辰', '壬午', '壬申', '壬戌'],
    '坤': ['乙未', '乙巳', '乙卯', '癸丑', '癸亥', '癸酉'],
    '震': ['庚子', '庚寅', '庚辰', '庚午', '庚申', '庚戌'],
    '巽': ['辛丑', '辛亥', '辛酉', '辛未', '辛巳', '辛卯'],
    '坎': ['戊寅', '戊辰', '戊午', '戊申', '戊戌', '戊子'],
    '离': ['己卯', '己丑', '己亥', '己酉', '己未', '己巳'],
    '艮': ['丙辰', '丙午', '丙申', '丙戌', '丙子', '丙寅'],
    '兑': ['丁巳', '丁卯', '丁丑', '丁亥', '丁酉', '丁未'],
}


# ----------------------------------------------------------------------
# 基础卦象工具
# ----------------------------------------------------------------------

def gua_yao(name):
    """返回某卦六爻 [初..上]，1=阳、0=阴。"""
    up, low = NAME2UP[name]
    return BAGUA_3[low] + BAGUA_3[up]


def gua_from_yao(yao):
    """由六爻 [初..上] 反查卦名。"""
    low = BAGUA_3_REV[tuple(yao[0:3])]
    up = BAGUA_3_REV[tuple(yao[3:6])]
    return GUA64[(up, low)]


def shiying_of(name):
    """返回 {gong, type_idx, type_name, shi, ying}。"""
    for gong, names in BAGUAN_8GONG.items():
        if name in names:
            idx = names.index(name)
            shi, ying = SHIYING[idx]
            return {'gong': gong, 'type_idx': idx,
                    'type_name': SHIYING_NAME[idx], 'shi': shi, 'ying': ying}
    raise ValueError('未知卦名：%s' % name)


def najia_of(name):
    """返回某卦六纳甲爻辰 [初..上]（内卦纳内干、外卦纳外干）。"""
    up, low = NAME2UP[name]
    return NAJIA[low][0:3] + NAJIA[up][3:6]


def xiang_of(name):
    """返回 '上象下象' 自然象描述。"""
    up, low = NAME2UP[name]
    return '上%s下%s' % (XIANG[up], XIANG[low])


def flip_yao(name, pos):
    """翻转某卦第 pos 爻（1=初 .. 6=上）阴阳，返回新卦名。"""
    yao = gua_yao(name)
    yao[pos - 1] ^= 1
    return gua_from_yao(yao)


def ying_yao_pos(pos):
    """六爻应爻位（隔三位）：初应四、二应五、三应上，反之亦然。"""
    return ((pos - 1) + 3) % 6 + 1


# ----------------------------------------------------------------------
# 元堂取法（§11）
# ----------------------------------------------------------------------

def solar_term_period(month_zhi):
    """由月柱地支推定「冬至→夏至」还是「夏至→冬至」区间（纯乾女/纯坤男分节气用）。
    冬至≈子月中（约12/22）、夏至≈午月中（约6/21）。
    丑寅卯辰巳 → 冬至至夏至；未申酉戌亥 → 夏至至冬至；
    子、午两月横跨冬至/夏至中点，无精确日期则存疑。返回 (period, 说明)。"""
    if month_zhi in '丑寅卯辰巳':
        return 'dongzhi', '冬至至夏至之间'
    if month_zhi in '未申酉戌亥':
        return 'xiazhi', '夏至至冬至之间'
    if month_zhi == '子':
        return None, '子月跨冬至，非精确出生日期不可细分'
    if month_zhi == '午':
        return None, '午月跨夏至，非精确出生日期不可细分'
    return None, ''


def _pure_gua_yuantang(name, hour_zhi, gender, month_zhi=None, jieqi=None):
    """纯乾/纯坤卦元堂取法（张椿来原书·乾集例九至十四）。

    纯乾卦（六阳爻）：男命不分节气（例九）；女命分节气（例十、例十一）。
    纯坤卦（六阴爻）：女命不分节气（例十二）；男命分节气（例十三、例十四）。
    「往复重数三爻」= 12 时辰在相应三爻上自下而上（或自上而下）循环落位。
    返回 (pos, detail, pattern)。
    """
    is_qian = (name == '乾为天')
    male = (gender == 'm')
    is_yang_shi = hour_zhi in YANG_SHI
    shi_idx = DIZHI.index(hour_zhi)

    period = jieqi
    period_lbl = ''
    if (is_qian and not male) or ((not is_qian) and male):
        if period is None:
            period, period_lbl = solar_term_period(month_zhi)

    # A：阳时下卦自下而上、阴时上卦自下而上往复
    A_yang = {0: 1, 1: 2, 2: 3, 3: 1, 4: 2, 5: 3}
    A_yin = {6: 4, 7: 5, 8: 6, 9: 4, 10: 5, 11: 6}
    # B：阳时上卦自上而下、阴时下卦自上而下往复
    B_yang = {0: 6, 1: 5, 2: 4, 3: 6, 4: 5, 5: 4}
    B_yin = {6: 3, 7: 2, 8: 1, 9: 3, 10: 2, 11: 1}

    pattern = 'A'
    lbl = ('（' + period_lbl + '）') if period_lbl else ''
    if is_qian:
        if male:
            detail = '男命不分节气：阳时下卦自下而上、阴时上卦自下而上往复重数三阳爻'
        elif period == 'dongzhi':
            pattern = 'B'
            detail = '女命·冬至至夏至：阳时上卦自上而下、阴时下卦自上而下往复重数三阳爻'
        else:
            detail = '女命·夏至至冬至%s：阳时下卦自下而上、阴时上卦自下而上往复重数三阳爻' % lbl
    else:
        if not male:
            detail = '女命不分节气：阳时下卦自下而上、阴时上卦自下而上往复重数三阴爻'
        elif period == 'xiazhi':
            pattern = 'B'
            detail = '男命·夏至至冬至：阳时上卦自上而下、阴时下卦自上而下往复重数三阴爻'
        else:
            detail = '男命·冬至至夏至%s：阳时下卦自下而上、阴时上卦自下而上往复重数三阴爻' % lbl

    table = A_yang if is_yang_shi else A_yin
    if pattern == 'B':
        table = B_yang if is_yang_shi else B_yin
    pos = table[shi_idx]
    return pos, detail, pattern


def yuantang(name, hour_zhi, gender, month_zhi=None, jieqi=None):
    """依本命卦阴阳爻多寡与出生时支，定元堂（变爻）位置 1..6。

    歌诀：阴爻阳爻一二重而寄，三位虽重没寄宫；四五无重应有寄，纯爻男女不相同。
    - 阳时（子至巳）取阳爻、阴时（午至亥）取阴爻；
    - 卦内阳爻为 1 或 2 个时「重而寄」（少数爻占满前几时后，余时寄到对宫）；
    - 爻数恰 3 时「不寄」（阳时阳爻、阴时阴爻，各轮两遍）；
    - 4/5 个时「无重有寄」；纯卦男女异取。
    纯乾/纯坤卦依张椿来原书分男女节气取法（例九至十四；month_zhi/jieqi 供分节气定向）。
    注：原书详细「12 时 → 爻位」映射表见原例九至十四，未转录；
    本实现按歌诀骨架复原，个别时辰的寄宫次序为可复现近似，非书传逐时原文。
    """
    yao = gua_yao(name)                       # [初..上]
    yang_idx = [i + 1 for i, v in enumerate(yao) if v == 1]
    yin_idx = [i + 1 for i, v in enumerate(yao) if v == 0]
    n_yang = len(yang_idx)
    shi_idx = DIZHI.index(hour_zhi)           # 0=子 .. 11=亥
    is_yang_shi = hour_zhi in YANG_SHI
    parity = '阳时' if is_yang_shi else '阴时'
    male = (gender == 'm')

    if n_yang == 1:
        case = '一阳爻卦（五阴一阳）'
        if shi_idx in (0, 1):                 # 子、丑同在阳爻
            pos = yang_idx[0]
            detail = '子丑二时元堂同寄唯一阳爻'
        else:
            seq = (shi_idx - 2) % 12           # 寅=0 .. 亥=9
            pos = yin_idx[seq % len(yin_idx)]
            detail = '寅时起寄阴爻、由下往上，五阴各两回'
    elif n_yang == 5:
        case = '一阴爻卦（五阳一阴）'
        if shi_idx in (6, 7):                 # 午、未同在阴爻
            pos = yin_idx[0]
            detail = '午未二时元堂同寄唯一阴爻'
        else:
            seq = (shi_idx - 8) % 12           # 申=0 .. 巳=9
            pos = yang_idx[seq % len(yang_idx)]
            detail = '申时起寄阳爻、由下往上，五阳各两回'
    elif n_yang == 2:
        case = '二阳爻卦（二阳四阴）'
        if shi_idx == 0:
            pos = yang_idx[0]
        elif shi_idx == 1:
            pos = yang_idx[1]
        elif shi_idx == 2:
            pos = yang_idx[1]
        elif shi_idx == 3:
            pos = yang_idx[0]
        else:
            seq = (shi_idx - 4) % 12           # 辰=0 .. 亥=7
            pos = yin_idx[seq % len(yin_idx)]
        detail = '二阳重数两时两次往复，辰时起寄阴爻'
    elif n_yang == 4:
        case = '二阴爻卦（四阳二阴）'
        if shi_idx == 6:
            pos = yin_idx[0]
        elif shi_idx == 7:
            pos = yin_idx[1]
        elif shi_idx == 8:
            pos = yin_idx[1]
        elif shi_idx == 9:
            pos = yin_idx[0]
        else:
            seq = (shi_idx - 10) % 12          # 戌=0 .. 巳=7
            pos = yang_idx[seq % len(yang_idx)]
        detail = '二阴重数两时两次往复，戌时起寄阳爻'
    elif n_yang == 3:
        case = '三阳/三阴爻卦（三位不寄宫）'
        if is_yang_shi:
            pos = yang_idx[shi_idx % len(yang_idx)]
        else:
            pos = yin_idx[(shi_idx - 6) % len(yin_idx)]
        detail = '三位虽重没寄宫——阳时取阳爻、阴时取阴爻，各轮两遍'
    elif n_yang == 0:
        case = '纯坤卦'
        pos, detail, _p = _pure_gua_yuantang(name, hour_zhi, gender, month_zhi, jieqi)
    else:  # n_yang == 6
        case = '纯乾卦'
        pos, detail, _p = _pure_gua_yuantang(name, hour_zhi, gender, month_zhi, jieqi)

    return {'position': pos, 'case': case, 'detail': detail,
            'hour_zhi': hour_zhi, 'parity': parity,
            'yang_idx': yang_idx, 'yin_idx': yin_idx,
            'yao': yao}


# ----------------------------------------------------------------------
# 先天卦变后天卦（§16）
# ----------------------------------------------------------------------

def houtian_gua(name, pos):
    """先天卦上卦下卦互置 + 元堂（pos）爻翻转，得后天卦。

    元堂爻随上下互置镜像：上卦之爻（位4/5/6）互置后落到下卦（位1/2/3）的对应位，
    故翻转位应为 pos 隔三位之应位（1↔4、2↔5、3↔6），而非原 pos。
    命例硬证（河洛理数·原书第42页）：先天风天小畜（巽上乾下，元堂位4）→ 上下互置
    天风姤 → 翻应位(位1) → 乾为天，与原书后天卦「乾为天」一致。
    """
    up, low = NAME2UP[name]
    swapped = GUA64.get((low, up), low + up)
    yao = gua_yao(swapped)
    yao[ying_yao_pos(pos) - 1] ^= 1
    return gua_from_yao(yao)


# ----------------------------------------------------------------------
# 值运卦（§30-1 / 图解版 §19 值运卦）
# ----------------------------------------------------------------------

def value_motion(name, hour_zhi, gender, qiyun=3, month_zhi=None, jieqi=None):
    """值运卦：先天卦自元堂起、由下而上顺行六爻，再行后天卦六爻；
    阳爻管九年、阴爻管六年。返回逐爻运段（含起止岁）。"""
    yt = yuantang(name, hour_zhi, gender, month_zhi, jieqi)
    pos = yt['position']
    houtian = houtian_gua(name, pos)
    sy = shiying_of(name)

    # 由元堂起、爻位向上环形顺行的六爻次序（1=初 .. 6=上）
    seq = [(pos + k - 1) % 6 + 1 for k in range(6)]

    segments = []
    age = qiyun
    for phase, gua in (('先天', name), ('后天', houtian)):
        yao = gua_yao(gua)
        nj = najia_of(gua)
        for yw in seq:
            yang = (yao[yw - 1] == 1)
            years = 9 if yang else 6
            segments.append({
                'phase': phase, 'gua': gua, 'xiang': xiang_of(gua),
                'yao': yw, 'yang': yang, 'najia': nj[yw - 1], 'years': years,
                'from_age': age, 'to_age': age + years - 1,
            })
            age += years

    return {
        'yuantang': yt, 'shiying': sy, 'najia': najia_of(name),
        'houtian_gua': houtian, 'houtian_xiang': xiang_of(houtian),
        'seq': seq, 'segments': segments, 'qiyun': qiyun,
    }


# ----------------------------------------------------------------------
# 值年卦（§30-2 / 图解版 §19 值年卦）
# ----------------------------------------------------------------------

def ganzhi_of_year(year):
    """公历年 → 干支（以 1984=甲子 为基准；立春前按上一年，此处按公历年近似）。"""
    g = (year - 4) % 10
    z = (year - 4) % 12
    return TIANGAN[g] + DIZHI[z]


def value_year_seq(seg, birth_year):
    """值年卦：以一个值运爻段（seg）为体，一年一变。

    段内逐年变爻序列（爻位 1=初..6=上）：
      段首年：值运爻本身，视「值运爻阴阳 vs 该年流年地支阴阳」相合决定变否（相左则变）；
      次年：值运爻之应爻（隔三位）；
      其后：值运爻 → 值运爻+1 → +2 …（向上顺行环绕），一律变爻。
    每年在上一年的卦上累计变爻。返回 [{xusui, year, gz, gua, xiang, yao, yao_name, yang, note}]。
    """
    p = seg['yao']
    n = seg['years']
    seg_yang = bool(seg['yang'])
    cur = gua_yao(seg['gua'])
    out = []
    for k in range(n):
        xusui = seg['from_age'] + k
        year = birth_year + xusui - 1
        gz = ganzhi_of_year(year)
        year_yang = gz[1] in YANG_ZHI
        if k == 0:
            ypos = p
            flip = (seg_yang != year_yang)
            note = '段首·值运%s爻遇%s%s年→%s' % (
                '阳' if seg_yang else '阴', gz[1],
                '阳' if year_yang else '阴', '变' if flip else '不变')
        elif k == 1:
            ypos = ying_yao_pos(p)
            flip = True
            note = '次岁·变应爻（值运爻隔三位→%s爻）' % _YAO_NAME[ypos]
        else:
            ypos = ((p - 1) + (k - 2)) % 6 + 1
            flip = True
            note = '第%d岁·向上顺行变%s爻' % (k + 1, _YAO_NAME[ypos])
        if flip:
            cur[ypos - 1] ^= 1
        g = gua_from_yao(cur)
        out.append({
            'xusui': xusui, 'year': year, 'gz': gz,
            'gua': g, 'xiang': xiang_of(g),
            'yao': ypos, 'yao_name': _YAO_NAME[ypos],
            'yang': bool(gua_yao(g)[ypos - 1]),
            'note': note,
        })
    return out


def value_years_all(vm, birth_year):
    """按值运段依次生成全部值年卦（自起运岁至十二段毕）。"""
    all_years = []
    for seg in vm['segments']:
        all_years.extend(value_year_seq(seg, birth_year))
    return all_years


# ----------------------------------------------------------------------
# 值月卦（§30-3 / 图解版 §19 值月卦）
# ----------------------------------------------------------------------

def value_month_gua(year_gua, zhinian_yao_pos):
    """值月卦：以值年卦为体、以值年卦「值年爻」（zhinian_yao_pos）为元堂。

    正月：元堂「前一位」（向上顺行 +1 环绕）变爻，得正月卦；
    单月（正、三、五、七、九、十一月）自正月起向上顺行累计变一爻
    （单月 k 变爻位 = 元堂向上第 k 位，k=1..6）；
    双月（二、四、六、八、十、十二月）取前一单月卦「值月爻」的应爻（隔三位）变。
    返回 [{month, gua, xiang, yao_pos, rule}]。yao_pos 即该月值月爻之位（供值日卦用）。
    """
    odd = []                       # 单月卦（自 year_gua 累计变爻）
    g = year_gua
    for k in range(1, 7):
        yv = ((zhinian_yao_pos - 1) + k) % 6 + 1   # 元堂向上第 k 位
        g = flip_yao(g, yv)
        odd.append((g, yv))
    months = []
    for m in range(1, 13):
        if m % 2 == 1:
            g, yv = odd[(m - 1) // 2]
            rule = '单月·元堂向上第%d位（%s爻）变' % ((m + 1) // 2, _YAO_NAME[yv])
        else:
            prev, pv = odd[(m - 2) // 2]
            yv = ying_yao_pos(pv)
            g = flip_yao(prev, yv)
            rule = '双月·取%d月值月爻应爻（%s爻）变' % (m - 1, _YAO_NAME[yv])
        months.append({'month': m, 'gua': g, 'xiang': xiang_of(g),
                       'yao_pos': yv, 'rule': rule})
    return months


# ----------------------------------------------------------------------
# 节候表（§30-4「月令的计算是以节候为起点的」——十二「节」定节气月起点）
# ----------------------------------------------------------------------

# 二十四节气分「节」与「中气」；此十二「节」各启一个节气月（1=寅/正月 … 12=丑/腊月）。
# 公历交节日为近似值（±1 天，精确须交节时刻）。
JIE_TERMS = [
    # (month, day, 节气月序号, 节名)
    (1, 6, 12, '小寒'), (2, 4, 1, '立春'), (3, 6, 2, '惊蛰'), (4, 5, 3, '清明'),
    (5, 6, 4, '立夏'), (6, 6, 5, '芒种'), (7, 7, 6, '小暑'), (8, 8, 7, '立秋'),
    (9, 8, 8, '白露'), (10, 8, 9, '寒露'), (11, 7, 10, '立冬'), (12, 7, 11, '大雪'),
]


def jie_month_of(d):
    """由公历日期求「节气月序号(1=寅/正月…12=丑/腊月)」+「节候月内第几日(节当日=1)」。

    值月/值日卦均以十二「节」为起点（张椿来 §30「月令的计算是以节候为起点的」）。
    交节日取近似（±1 天）；1/1–1/5 属前一年大雪起的子月。返回 (jie_no, day_no, 节名)。
    """
    md = (d.month, d.day)
    if md < (1, 6):
        start = date(d.year - 1, 12, 7)
        return 11, (d.toordinal() - start.toordinal() + 1), '大雪'
    prev = JIE_TERMS[0]
    for m, day, no, name in JIE_TERMS:
        if (m, day) <= md:
            prev = (m, day, no, name)
    start = date(d.year, prev[0], prev[1])
    return prev[2], (d.toordinal() - start.toordinal() + 1), prev[3]


# ----------------------------------------------------------------------
# 值日卦（§30-4 / 图解版 §19 值日卦）
# ----------------------------------------------------------------------

def value_month_days(month_gua, yue_yao_pos, days=30, start=1):
    """值日卦：以值月卦为体（值月爻 = yue_yao_pos）。

    第 k 个六日组（k=0,1,2…）变「值月爻 +1+k」位（环绕），得该组日卦体；
    日卦体六爻一爻管一日、由下向上（初爻=组内第1日 … 上爻=第6日）。
    返回 [{day, yao_pos, yao_name, gua, xiang, base_flip, base_flip_name}]。
    注：day 1 即「节候第一日」（节当日，§30 月令以节候为起点），由调用方经 jie_month_of 定位
    节气月与节候日后取今日；30 日为节候月约数，超出者按 §30 定时刻「每年日差增刻」校正。
    """
    out = []
    for d in range(start, start + days):
        k = (d - start) // 6                 # 第几个六日组
        yp = (d - start) % 6 + 1             # 组内第几日（即爻位，由下向上）
        base_flip = ((yue_yao_pos - 1) + 1 + k) % 6 + 1   # 值月爻+1+k 环绕
        g = flip_yao(month_gua, base_flip)
        out.append({'day': d, 'yao_pos': yp, 'yao_name': _YAO_NAME[yp],
                    'gua': g, 'xiang': xiang_of(g),
                    'base_flip': base_flip, 'base_flip_name': _YAO_NAME[base_flip]})
    return out


def _segment_for_age(segments, xusui):
    for seg in segments:
        if seg['from_age'] <= xusui <= seg['to_age']:
            return seg
    return segments[-1] if segments else None


# ----------------------------------------------------------------------
# 总装
# ----------------------------------------------------------------------

def build_yiji(pillars, gender, benming_gua, qiyun=3,
               birth_year=None, now_year=None, now_month=None, now_day=None, future_n=10, jieqi=None):
    """皇极值卦总装入口。pillars=[年,月,日,时] 每柱两字；返回 dict 供渲染。

    birth_year 公历出生年（流年定位）；now_year/now_month/now_day 可覆盖当前年月日保证可复现
    （值月/值日卦按「节候」定位，须 now_day 方可精确到当日，缺省取系统日期）；
    jieqi 可强制指定纯乾女/纯坤男的节气区间（'dongzhi'/'xiazhi'），缺省由月柱地支推定。
    """
    hour_zhi = pillars[3][1]
    month_zhi = pillars[1][1]
    vm = value_motion(benming_gua, hour_zhi, gender, qiyun=qiyun,
                      month_zhi=month_zhi, jieqi=jieqi)
    up, low = NAME2UP[benming_gua]
    pos = vm['yuantang']['position']

    value_years = []
    month_guas = []
    day_month = None
    jie_day = None
    jie_name = None
    today_days = []
    day_yao_pos = None
    if birth_year:
        now_year = now_year or date.today().year
        all_years = value_years_all(vm, birth_year)
        by_xusui = {vy['xusui']: vy for vy in all_years}
        seg_last = vm['segments'][-1]
        for y in range(now_year, now_year + future_n + 1):
            xusui = y - birth_year + 1
            vy = by_xusui.get(xusui)
            if vy is None:
                value_years.append({
                    'year': y, 'ganzhi': ganzhi_of_year(y), 'xusui': xusui,
                    'gua': seg_last['gua'], 'xiang': xiang_of(seg_last['gua']),
                    'yao': seg_last['yao'], 'yao_name': _YAO_NAME[seg_last['yao']],
                    'yang': bool(seg_last['yang']),
                    'note': '超出值运段覆盖（暂以末段卦示之）',
                })
            else:
                value_years.append({
                    'year': y, 'ganzhi': vy['gz'], 'xusui': xusui,
                    'gua': vy['gua'], 'xiang': vy['xiang'],
                    'yao': vy['yao'], 'yao_name': vy['yao_name'],
                    'yang': vy['yang'], 'note': vy['note'],
                })

        # 值月卦：以「当前年」值年卦 + 该年值年爻（值月卦之元堂）推十二月（§30-3）
        cur_vy = value_years[0] if value_years else None
        cur_gua = cur_vy['gua'] if cur_vy else benming_gua
        cur_yao = cur_vy['yao'] if cur_vy else pos
        month_guas = value_month_gua(cur_gua, cur_yao)

        # 值月/值日卦：月令以节候为起点（§30-4）——以「当前日期」定节气月与节候日
        if now_month is None:
            _now = date.today()
        else:
            _now = date(now_year, now_month, now_day if now_day else 1)
        day_month, jie_day, jie_name = jie_month_of(_now)
        day_month = day_month if 1 <= day_month <= 12 else 1
        jie_day = jie_day if 1 <= jie_day <= 30 else 30
        cur_month = month_guas[day_month - 1]
        cur_month_gua = cur_month['gua']
        day_yao_pos = cur_month['yao_pos']
        today_days = value_month_days(cur_month_gua, day_yao_pos, days=30, start=1)

    return {
        'benming_gua': benming_gua,
        'upper': up, 'lower': low, 'xiang': xiang_of(benming_gua),
        'yuantang': vm['yuantang'],
        'shiying': vm['shiying'],
        'najia': vm['najia'],
        'houtian_gua': vm['houtian_gua'],
        'houtian_xiang': vm['houtian_xiang'],
        'seq': vm['seq'],
        'segments': vm['segments'],
        'value_years': value_years,
        'month_guas': month_guas,
        'day_month': day_month,
        'day_yao_pos': day_yao_pos,
        'jie_day': jie_day,
        'jie_name': jie_name,
        'today_days': today_days,
        'qiyun': qiyun,
    }


if __name__ == '__main__':
    # 节候表回归断言（§30 月令以节候为起点；公历交节日近似 ±1 天）
    _c = [
        (date(1984, 2, 4), 1, 1),    # 立春当日 → 寅/正月·第1候日
        (date(1984, 2, 15), 1, 12),  # 正月十二
        (date(1984, 1, 6), 12, 1),   # 小寒当日 → 丑/腊月·第1候日
        (date(1984, 1, 5), 11, 30),  # 1/5 属前一年大雪起的子月第30候日
        (date(1984, 3, 6), 2, 1),    # 惊蛰当日 → 卯/二月
        (date(1984, 12, 7), 11, 1),  # 大雪当日 → 子/十一月
        (date(1984, 6, 21), 5, 16),  # 夏至在芒种节候月内第16日
    ]
    for _d, _no, _day in _c:
        _no2, _day2, _nm = jie_month_of(_d)
        assert (_no2, _day2) == (_no, _day), (_d, _no2, _day2, _nm)
    print('jie_month_of 节候表自检通过（%d 组）' % len(_c))