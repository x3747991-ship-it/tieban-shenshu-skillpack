#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
铁板神数 · 演算法式引擎（据《张椿来·铁版神数》第三部分「演算法式」逐条复原）

这是铁板神数的**起数主链路**：八字配数 → 化卦（年月先天 / 日时后天）→ 变卦、互卦
→ 八卦加则取数（「乾卦六为头、遇十不须用」）→ 合成四位条文号 → 查 12000 条条文库。

本模块补的是旧版 `tieban.py` 缺失的一环：旧版以「本命密钥（8 字太玄数连缀）+ 分类
偏移取模」定位条文，属自造确定性算法；本书正统是以「化卦 + 八卦加则」直接化出条文号，
且已与条文库逐号核对一致（3788 / 2664 / 9516 / 10416 / 6181 / 3926 / 8221 …）。

实现五种演算（与 references/演算法式.md 一一对应）：

  1. 太玄数演算法 —— 全景可证。年+月÷8 化先天卦、日+时去十化后天卦，
     互卦 / 变卦（先天变后天＝上下互置+元堂变爻）→ 八卦加则取数 → 八式条文号。
  2. 皇极易数演算法（元会运世）—— 元会（顺，考六亲）、运世（逆，推运程）；
     考六亲加「年干太玄×1000」（元·千位）、初刻即中再加「月干太玄×100」（会·百位）。
  3. 河洛理数演算法 —— 天干河洛数（§5 天干→卦的后天卦数）+ 地支河洛数（§6 生数·成数），
     奇数和为天数、偶数和为地数；天数−25、地数−30 化后天卦（上/下卦）→ 先天卦/后天卦。
  4. 日柱配卦演算法 —— 48 干支纳数（纳甲干+太玄支、遇十不用），上卦总和·下卦总和
     合成条文号；「日柱→化卦」为金钥匙口诀，原书未逐字转录，化卦可显式给出。
  5. 大运数演算法 —— §5「月日时年起数序 + 大运数序」共得数＝条文号（8648/10649/7645
     等书版命例硬证）；§27 流年取数（破解钥匙「流年干支代替年干支、加流年支生数」）。

诚实边界：河洛「天数地数」配法由 §5 天干取数诀、§6 地支取数诀（口诀明确、覆盖全干全支）
+ 命例逐项硬证（1497/2666），整体可证；皇极「年干×1000 / 月干×100」加数仅一造命例硬证
（9516/10416），据「元=千位、会=百位」框架推广到全干支，属合理推断、非逐字规则；
日柱配卦「金钥匙口诀」为歌诀/师传，原书未逐字转录。大运数序（§26「月日时年」口诀 +
破解钥匙算式 + 书版 8648/10649/10647/7645/8649/8647/7649 命例）整体可证；流年取数（§27）
破解钥匙未逐字说明流年千位是否仍叠加大运干数、且原书无流年命例，其「千位保持大运干」
为据破解钥匙文字的推断、如实标注。天干配数另有跨传承分歧：破解钥匙自成一表「五合五行数」
（甲己合土=1、乙庚合金=2、丙辛合水=5、丁壬合木=3、戊癸合火=4），与本书 §26
「甲己乙庚四、丙辛六、丁壬戊癸三」不同；本引擎采张椿来 §26 配数（经 8648 命例逐位硬证：
甲己=4 方得千位 8，破解钥匙甲己=1 则千位得 3、与 8648 不符；且破解钥匙自身 §27 口诀
「一样甲己四」已作甲己=四、与其五合表自相矛盾），不采用破解钥匙五合数，如实标注。
本引擎只对**可证**部分给出确定性数值，不可证部分如实标注，不臆造公式。
"""
from __future__ import annotations

import os
import sys

# 与 tieban.py / yiji_gua.py 同目录；复用 yiji_gua 的卦六爻 / 卦名 / 元堂 / 变卦 / 纳甲工具。
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)
from yiji_gua import (GUA64, NAME2UP, BAGUA_3, BAGUA_3_REV, gua_yao, gua_from_yao,
                      houtian_gua, yuantang, najia_of, xiang_of, XIANG)

# ----------------------------------------------------------------------
# 一、配数常量
# ----------------------------------------------------------------------

# 太玄数：甲己子午九、乙庚丑未八、丙辛寅申七、丁壬卯酉六、戊癸辰戌五、巳亥四。
TAIXUAN = {
    '甲': 9, '乙': 8, '丙': 7, '丁': 6, '戊': 5,
    '己': 9, '庚': 8, '辛': 7, '壬': 6, '癸': 5,
    '子': 9, '丑': 8, '寅': 7, '卯': 6, '辰': 5, '巳': 4,
    '午': 9, '未': 8, '申': 7, '酉': 6, '戌': 5, '亥': 4,
}

TIANGAN = '甲乙丙丁戊己庚辛壬癸'
DIZHI = '子丑寅卯辰巳午未申酉戌亥'

# 先天八卦数：乾一兑二离三震四巽五坎六艮七坤八。
XIAN_NUM = {'乾': 1, '兑': 2, '离': 3, '震': 4, '巽': 5, '坎': 6, '艮': 7, '坤': 8}
XIAN_GUA = {v: k for k, v in XIAN_NUM.items()}

# 后天八卦数（洛书）：坎一坤二震三巽四中五乾六兑七艮八离九。
HOU_NUM = {'坎': 1, '坤': 2, '震': 3, '巽': 4, '中': 5, '乾': 6, '兑': 7, '艮': 8, '离': 9}
HOU_GUA = {1: '坎', 2: '坤', 3: '震', 4: '巽', 6: '乾', 7: '兑', 8: '艮', 9: '离'}

# 河洛天干取数诀（天干→卦）：壬甲乾、乙癸坤、丙艮、丁兑、戊坎、己离、庚震、辛巽。
GAN_GUA_HELUO = {
    '甲': '乾', '壬': '乾', '乙': '坤', '癸': '坤', '丙': '艮',
    '丁': '兑', '戊': '坎', '己': '离', '庚': '震', '辛': '巽',
}

# 日柱配卦 · 地支配卦（铁板神数「金钥匙」口诀，多本传承一致）：
#   亥子坎宫寅震木，巳午离门丑在坤；卯酉乾金辰是兑，未申艮宫戌巽真。
# 十二地支配八卦（上卦）：亥子→坎、丑→坤、寅→震、卯酉→乾、辰→兑、巳午→离、
# 未申→艮、戌→巽。命例硬证：日柱丁酉 → 天泽履（乾上兑下），即「上卦＝日支酉→乾、
# 下卦＝日干丁→兑（河洛天干配卦）」，与本表酉→乾、丁→兑完全吻合。
# 旧版误按「河洛地支成数化先天卦」复原（寅卯→坤、巳午→艮、申→乾、辰戌丑未→巽），
# 仅命中子亥酉三支；已据权威歌诀更正为下示全表。
# 参校《铁板神数正宗破解钥匙》「地支配卦」诀复作「寅卯震…申酉乾金…」，与权威版在
# 卯（乾/震）、申（艮/乾）两支有传抄分歧。已据第三来源陈鼎龙《铁板神数十九法秘解》
# 第八法/第九法「地支配卦数」（乾卯酉6、坤丑2、震寅3、巽戌4、坎子亥1、离巳午9、
# 艮未申8、兑辰7，12 支全覆盖）与第四来源金泉《铁版神数预测学》第十二章「日主配卦
# 也叫地支配卦」诀，三书独立坐实：卯→乾、申→艮，与权威版一致；破解钥匙系
# 「卯→震、申→乾」为少数异文，不采用。
DIZHI_PEIGUA = {
    '子': '坎', '亥': '坎',
    '丑': '坤',
    '寅': '震',
    '卯': '乾', '酉': '乾',
    '辰': '兑',
    '巳': '离', '午': '离',
    '未': '艮', '申': '艮',
    '戌': '巽',
}

# 大运天干合化配数（§26）：甲己乙庚四、丙辛六、丁壬戊癸三。
DAYUN_GAN_HE = {
    '甲': 4, '己': 4, '乙': 4, '庚': 4, '丙': 6, '辛': 6, '丁': 3, '壬': 3, '戊': 3, '癸': 3,
}

# 河洛地支配数（§6）：亥子一六、寅卯三八、巳午二七、申酉四九、辰戌丑未五十。
HELUO_ZHI = {
    '亥': (1, 6), '子': (1, 6), '寅': (3, 8), '卯': (3, 8),
    '巳': (2, 7), '午': (2, 7), '申': (4, 9), '酉': (4, 9),
    '辰': (5, 10), '戌': (5, 10), '丑': (5, 10), '未': (5, 10),
}

# 河洛天干数（§5 天干取数诀「壬甲从乾数、乙癸向坤求…」→ 天干→卦 → 后天八卦数）：
#   壬甲→乾=6、乙癸→坤=2、丙→艮=8、丁→兑=7、戊→坎=1、己→离=9、庚→震=3、辛→巽=4。
# 命例硬证（原书第 42 页河洛理数）：庚寅甲申丙午甲午，天干河洛数 庚=3(震)、甲=6(乾)、
# 丙=8(艮)、甲=6(乾)，配地支河洛数（寅3.8/申4.9/午2.7/午2.7），奇数和=天数29、
# 偶数和=地数36，与原书「天数(3+3+9+7+7)=29、地数(6+8+6+8+4+2+2)=36」逐项吻合。
GAN_HELUO_NUM = {
    '甲': 6, '壬': 6, '乙': 2, '癸': 2, '丙': 8,
    '丁': 7, '戊': 1, '己': 9, '庚': 3, '辛': 4,
}

YANG_GAN = set('甲丙戊庚壬')


# ----------------------------------------------------------------------
# 二、卦工具
# ----------------------------------------------------------------------

def _hz_taixuan(pillar):
    """一柱（干支两字）的太玄数之和。"""
    return TAIXUAN[pillar[0]] + TAIXUAN[pillar[1]]


def xian_gua_from_num(n):
    """先天数化卦：÷8 取余，余 0 作坤（8）。"""
    r = n % 8
    r = r or 8
    return XIAN_GUA[r]


def hou_gua_from_num(n, gender):
    """后天数化卦：去十余（取个位），0 / 5 无卦寄中宫（男寄艮、女寄坤）。"""
    r = n % 10
    if r in (0, 5):
        r = 8 if gender == 'm' else 2          # 中宫寄卦：男艮(8)、女坤(2)
    return HOU_GUA[r]


def hugua(name):
    """内外互卦：去初爻、上爻，二三四爻互作下卦、三四五爻互作上卦。"""
    yao = gua_yao(name)
    low = BAGUA_3_REV[tuple(yao[1:4])]
    high = BAGUA_3_REV[tuple(yao[2:5])]
    return GUA64[(high, low)]


def jiaze_qu_shu(name, num_map):
    """八卦加则取数：『乾卦六为头』——千位=(上卦数+6)去十、百位=上卦数、
    十位=互卦上卦数、个位=互卦下卦数。返回 (四位条文号, 互卦名)。

    num_map 为先天数 XIAN_NUM 或后天数 HOU_NUM（先天卦用先天数、后天卦用后天数）。
    """
    up, _low = NAME2UP[name]
    a = num_map[up]                            # 上卦数
    qian = (a + 6) % 10 or 1                   # 加六取千位：满十归于一（「遇十不须用」）
    bai = a
    hu = hugua(name)
    hu_up, hu_low = NAME2UP[hu]
    shi = num_map[hu_up]                       # 互卦上卦数
    ge = num_map[hu_low]                       # 互卦下卦数
    return 1000 * qian + 100 * bai + 10 * shi + ge, hu


# ----------------------------------------------------------------------
# 三、太玄数演算法（全景可证）
# ----------------------------------------------------------------------

def taixuan_suanfa(pillars, gender):
    """太玄数演算法。

    pillars = [年, 月, 日, 时]，每柱两字；gender 'm'/'f'。

    返回：四柱太玄配数、先天卦（年+月 ÷8）、后天卦（日+时 去十）、
    元堂（时支）、先/后天变卦、先/后天互卦、以及「八式」条文号（正卦/互卦/变卦/变互，
    各经八卦加则取数）；主条文号为先天正卦式与后天正卦式（3778→3788、2664）。"""
    names = ['年', '月', '日', '时']
    sums = [_hz_taixuan(p) for p in pillars]

    # 年月 → 先天卦（÷8）
    xian_up = xian_gua_from_num(sums[0])
    xian_low = xian_gua_from_num(sums[1])
    xian_gua = GUA64[(xian_up, xian_low)]

    # 日时 → 后天卦（去十余）
    hou_up = hou_gua_from_num(sums[2], gender)
    hou_low = hou_gua_from_num(sums[3], gender)
    hou_gua = GUA64[(hou_up, hou_low)]

    # 元堂（时支）→ 变卦（先天变后天＝上下互置 + 元堂变爻；后天变卦同法）
    hour_zhi = pillars[3][1]
    month_zhi = pillars[1][1]
    yt = yuantang(xian_gua, hour_zhi, gender, month_zhi=month_zhi)
    xian_bian = houtian_gua(xian_gua, yt['position'])
    hou_bian = houtian_gua(hou_gua, yt['position'])

    xian_hu = hugua(xian_gua)
    xian_bian_hu = hugua(xian_bian)
    hou_hu = hugua(hou_gua)
    hou_bian_hu = hugua(hou_bian)

    # 八式：每轴 正卦 / 互卦 / 变卦 / 变互 四式，各经八卦加则取数。
    def _four(gua, num_map):
        zheng, _hu = jiaze_qu_shu(gua, num_map)
        hu, _ = jiaze_qu_shu(hugua(gua), num_map)
        bian = houtian_gua(gua, yt['position'])
        bian_num, _ = jiaze_qu_shu(bian, num_map)
        bian_hu_num, _ = jiaze_qu_shu(hugua(bian), num_map)
        return [zheng, hu, bian_num, bian_hu_num]

    xian_shu = _four(xian_gua, XIAN_NUM)
    hou_shu = _four(hou_gua, HOU_NUM)

    return {
        'pillars': pillars, 'gender': gender,
        'names': names, 'sums': sums,
        'xian_gua': xian_gua, 'xian_xiang': xiang_of(xian_gua),
        'hou_gua': hou_gua, 'hou_xiang': xiang_of(hou_gua),
        'xian_up': xian_up, 'xian_low': xian_low,
        'hou_up': hou_up, 'hou_low': hou_low,
        'yuantang': yt,
        'xian_bian': xian_bian, 'hou_bian': hou_bian,
        'xian_hu': xian_hu, 'xian_bian_hu': xian_bian_hu,
        'hou_hu': hou_hu, 'hou_bian_hu': hou_bian_hu,
        'xian_shu': xian_shu, 'hou_shu': hou_shu,
        'anchor_xian': xian_shu[0], 'anchor_hou': hou_shu[0],
    }


# ----------------------------------------------------------------------
# 四、皇极易数演算法（元会运世）
# ----------------------------------------------------------------------

def huangji_suanfa(pillars):
    """皇极易数：元（年·千位）会（月·百位）运（日·十位）世（时·个位）。

    - 元会互合（顺，考六亲）：元数·会数 顺次连缀（元占千百、会占十个）。
    - 运世互合（逆，推运程）：运数、世数各自倒序后连缀（体用互合、运世为逆）。
    - 加数：考六亲加「年干太玄×1000」（元·千位）；初刻即中再「月干太玄×100」（会·百位）。
      原书第 43 页：「加上出生年天干（元）的 8000 为千位」「出生月（会）的 900（百位）」，
      即 8000=庚(8)×1000、900=甲(9)×100；据此推广为年干/月干太玄数，非逐字规则。
    """
    sums = [_hz_taixuan(p) for p in pillars]
    yuan, hui, yun, shi = sums

    yuan_hui = yuan * 100 + hui                  # 顺：元会 1516
    yun_shi = int(str(yun)[::-1]) * 100 + int(str(shi)[::-1])   # 逆：运世 6181

    # 书中命例：考六亲在元会基数上加年干×1000 → 9516；初刻即中再加月干×100 → 10416。
    jia_qian = TAIXUAN[pillars[0][0]] * 1000
    jia_bai = TAIXUAN[pillars[1][0]] * 100
    jia_8000 = yuan_hui + jia_qian
    jia_900 = yuan_hui + jia_qian + jia_bai

    return {
        'sums': sums, 'yuan': yuan, 'hui': hui, 'yun': yun, 'shi': shi,
        'yuan_hui': yuan_hui, 'yun_shi': yun_shi,
        'jia_qian': jia_qian, 'jia_bai': jia_bai,
        'jia_8000': jia_8000, 'jia_900': jia_900,
    }


# ----------------------------------------------------------------------
# 五、河洛理数演算法（天数地数，经命例硬证）
# ----------------------------------------------------------------------

def _he_qu_yu(n, base):
    """河洛「去十余取余」：超过基数 base 先减 base，再取个位；个位 0 取十位（10→1、20→2、30→3）。

    张椿来原书命例天数 29(减25)=4、地数 36(减30)=6，仅此一造、未逐字转录「取个位」细节；
    「减后去十余」由三书一致补充：陈鼎龙《铁板神数十九法秘解》、唐颐《图解易经象数学·铁版神数》
    （「當天數<25 余數取個位；=10 取1、=20 取2；=25 余5；>25 先減25 再取個位」）、
    金泉《铁板神数预测学》，三书与命例自洽。
    """
    if n > base:
        n -= base
    r = n % 10
    if r == 0:
        r = n // 10
    return r


def _zhonggong_jigong(gender, year_gan, birth_year=None):
    """余数=5（中宫无卦）寄宫。三元以甲子 1864/1924/1984 为界（每 60 年一元，
    (出生年−1864)//60%3 → 0上元/1中元/2下元）：
      上元：男寄艮(8)、女寄坤(2)
      中元：阳男阴女寄艮(8)、阴男阳女寄坤(2)
      下元：男寄离(9)、女寄兑(7)
    三书一致：陈鼎龙《十九法秘解》、唐颐《图解易经象数学》「當余數為5：上元男艮女坤、
    中元陽男陰女艮/陰男陽女坤、下元男離女兌」、金泉《铁版神数预测学》（上元 1846~1923，1846 疑
    1864 之 OCR 误读，仍以 1864 甲子为界）。缺 birth_year 回退上元（男艮女坤），epoch 标注缺年默认。
    返回 (卦名, 三元名)。"""
    gm = gender == 'm'
    if birth_year is None:
        return ('艮' if gm else '坤'), '上元(缺年默认)'
    idx = ((birth_year - 1864) // 60) % 3
    if idx == 0:
        return ('艮' if gm else '坤'), '上元'
    if idx == 1:
        yang_male_yin_female = ((year_gan in YANG_GAN) and gm) or ((year_gan not in YANG_GAN) and (not gm))
        return ('艮' if yang_male_yin_female else '坤'), '中元'
    return ('离' if gm else '兑'), '下元'


def _he_yu_gua(n, gender, year_gan, birth_year=None):
    """河洛取余数化卦：1-9 查 HOU_GUA；5（中宫）走三元寄宫。返回 (卦名|None, 寄宫三元名|None)。"""
    if n == 5:
        gua, epoch = _zhonggong_jigong(gender, year_gan, birth_year)
        return gua, epoch
    return HOU_GUA.get(n), None


def heluo_suanfa(pillars, gender, birth_year=None):
    """河洛理数：天干河洛数（§5 天干取数诀→后天卦数）+ 地支河洛数（§6 地支取数诀→
    生数·成数），奇数和为天数、偶数和为地数；天数 >25 减 25、地数 >30 减 30 后
    「去十余取个位」（个位 0 取十位）化后天卦；余 5（中宫）按三元寄宫；再按「阳男阴女
    天数在上、阴男阳女天数在下」合先天卦（考六亲）；「上下互置+元堂变爻」得后天卦（推运程）；
    经八卦加则取条文号。

    §5/§6 口诀覆盖全干全支（可证）；天数减25/地数减30 经原书命例硬证（29→4、36→6）；
    「去十余取个位 + 5 寄宫 + 阴阳合卦」为三书一致补充（陈鼎龙/唐颐/金泉），原书仅一造命例、
    未逐字转录，属第三方书坐实的可证补充、非规则推断。
    """
    gan_nums = [GAN_HELUO_NUM[p[0]] for p in pillars]
    zhi_nums = [n for p in pillars for n in HELUO_ZHI[p[1]]]
    all_nums = gan_nums + zhi_nums

    tian = sum(n for n in all_nums if n % 2 == 1)
    di = sum(n for n in all_nums if n % 2 == 0)
    # 「去」与「去十不用」同义：超过方减；减后去十余取个位，个位 0 取十位。
    year_gan = pillars[0][0]
    tian_yu = _he_qu_yu(tian, 25)
    di_yu = _he_qu_yu(di, 30)
    tian_gua, tian_jigong = _he_yu_gua(tian_yu, gender, year_gan, birth_year)
    di_gua, di_jigong = _he_yu_gua(di_yu, gender, year_gan, birth_year)

    # 阴阳合卦：阳男阴女天数在上、地数在下；阴男阳女反之（§25 男女异命 + 三书一致）
    tian_above = ((year_gan in YANG_GAN) and gender == 'm') or ((year_gan not in YANG_GAN) and gender == 'f')
    if tian_gua and di_gua:
        xiangua = GUA64[(tian_gua, di_gua)] if tian_above else GUA64[(di_gua, tian_gua)]
    else:
        xiangua = None

    # 后天卦：上下互置 + 元堂变爻（元堂随互置镜像，见 yiji_gua.houtian_gua）
    yt = None
    houtian = None
    if xiangua:
        yt = yuantang(xiangua, pillars[3][1], gender, month_zhi=pillars[1][1])
        houtian = houtian_gua(xiangua, yt['position'])

    # 八卦加则取数：河洛贯穿后天卦数（洛书数），先天卦亦用 HOU_NUM。
    xian_shu = jiaze_qu_shu(xiangua, HOU_NUM)[0] if xiangua else None
    hou_shu = jiaze_qu_shu(houtian, HOU_NUM)[0] if houtian else None

    return {
        'pillars': pillars, 'gender': gender, 'birth_year': birth_year,
        'gan_nums': gan_nums, 'zhi_nums': zhi_nums,
        'tian': tian, 'di': di, 'tian_yu': tian_yu, 'di_yu': di_yu,
        'tian_gua': tian_gua, 'di_gua': di_gua,
        'tian_jigong': tian_jigong, 'di_jigong': di_jigong,
        'tian_above': tian_above,
        'xiangua': xiangua, 'xiangua_xiang': xiang_of(xiangua) if xiangua else None,
        'houtian': houtian, 'houtian_xiang': xiang_of(houtian) if houtian else None,
        'yuantang': yt,
        'xian_shu': xian_shu, 'hou_shu': hou_shu,
    }


# ----------------------------------------------------------------------
# 六、日柱配卦演算法（48 干支纳数）
# ----------------------------------------------------------------------

def rizhu_peigua_suanfa(pillars, ri_gua=None):
    """日柱配卦：日柱化卦（天泽履等）→ 48 干支纳数取数。

    纳数 = 太玄(纳甲干) + 太玄(纳支)，「遇十不须用」（和=10 的爻弃之）；
    上卦三爻纳数和为千白位、下卦三爻纳数和为十个位，合为条文号（如 3926）。

    ri_gua：日柱化卦结果（可选）；「日柱→化卦」即铁板神数金钥匙口诀，其规则为
    「上卦＝日支配卦（乾集 §20 地支配卦诀 DIZHI_PEIGUA）、下卦＝日干河洛配卦（§5
    天干配卦诀 GAN_GUA_HELUO）」。二者均为书传口诀，且经命例丁酉→天泽履（酉→乾、
    丁→兑）硬证，故缺省时直接按此推导，非近似。
    """
    day = pillars[2]
    if ri_gua is None:
        up_gua = DIZHI_PEIGUA.get(day[1], '乾')
        low_gua = GAN_GUA_HELUO.get(day[0], '乾')
        ri_gua = GUA64[(up_gua, low_gua)]

    nj = najia_of(ri_gua)                       # 六纳甲爻辰 [初..上]
    low3 = nj[0:3]
    up3 = nj[3:6]

    def _sum3(three):
        total = 0
        detail = []
        for na in three:
            g, z = na[0], na[1]
            v = TAIXUAN[g] + TAIXUAN[z]
            if v == 10:
                detail.append('%s=%d(遇十不用)' % (na, v))
            else:
                total += v
                detail.append('%s=%d' % (na, v))
        return total, detail

    up_sum, up_det = _sum3(up3)
    low_sum, low_det = _sum3(low3)
    n = up_sum * 100 + low_sum

    return {
        'day': day, 'ri_gua': ri_gua, 'ri_xiang': xiang_of(ri_gua),
        'najia': nj, 'up3': up3, 'low3': low3,
        'up_sum': up_sum, 'low_sum': low_sum, 'up_det': up_det, 'low_det': low_det,
        'n': n,
    }


def rizhu_bian_gua_qu_shu(pillars):
    """变卦取数（年月柱）· 82xx 系列（日柱配卦 §4 下半段「以变卦取数」）。

    年月两柱太玄 ÷8 取先天卦（上=年、下=月）作本卦，再「上下互置」（乾集 §16）得变卦；
    八卦加则「乾卦六为头」以**变卦上卦数**定千位、百位（千=上卦数+6 取个位、百=上卦数），
    十位/个位取「八式」（上卦数在前、下卦数在后，乾集 §24）。

    书版命例 癸巳 甲子 丁酉 甲辰：年癸巳(5+4=9)÷8 余1 乾、月甲子(9+9=18)÷8 余2 兑 →
    本卦天泽履（乾上兑下）→ 变卦泽天夬（兑上乾下，原书径称「泽天大壮」）；
    千位=2+6=8、百位=2 → 前缀 82，与书版 8239/8226/8212/8253/8221 之「82」吻合。

    十位/个位书版列五式，逐式锁定如下（前四式经页44原文或乾集§3/§16/§17 硬证）：
      39 = 本卦上卦纳数（乾·外纳壬 11+13+15）
      26 = 本卦下卦纳数（兑·内纳丁 14+12，丁巳10遇十弃）
      12 = 本卦卦数（乾1兑2）
      53 = 本卦互卦卦数（风火家人：巽5离3）
      21 = 变卦卦数（泽天夬：兑2乾1）
    八式余三式（变卦上纳、变卦下纳、变卦互卦）书版未列，按 §24「取数四式，与正卦合为
    八数」可推：变卦上纳=26（与 8226 重合）、变卦下纳=48（→8248）、变卦互卦=11（→8211）；
    属规则推断、无书版硬证，本函数不输出，详见 references/演算法式.md §4。"""
    s0 = _hz_taixuan(pillars[0])
    s1 = _hz_taixuan(pillars[1])
    bu_up = xian_gua_from_num(s0)
    bu_low = xian_gua_from_num(s1)
    ben = GUA64[(bu_up, bu_low)]
    n_up, n_low = NAME2UP[ben]
    bian = GUA64[(n_low, n_up)]          # 上下互置（§16）
    bian_up, bian_low = n_low, n_up
    hu = hugua(ben)
    h_up, h_low = NAME2UP[hu]

    qian = (XIAN_NUM[bian_up] + 6) % 10 or 1
    bai = XIAN_NUM[bian_up]

    nj = najia_of(ben)

    def _sum3(three):
        total = 0
        for na in three:
            v = TAIXUAN[na[0]] + TAIXUAN[na[1]]
            if v != 10:
                total += v
        return total

    shang_na = _sum3(nj[3:6])
    xia_na = _sum3(nj[0:3])
    ben_shu = 10 * XIAN_NUM[bu_up] + XIAN_NUM[bu_low]
    hu_shu = 10 * XIAN_NUM[h_up] + XIAN_NUM[h_low]
    bian_shu = 10 * XIAN_NUM[bian_up] + XIAN_NUM[bian_low]

    shili = [
        ('shang_na', '本卦上卦纳数（%s外卦＝%s）' % (bu_up, '·'.join(nj[3:6])), shang_na, '外卦三爻纳甲太玄和'),
        ('xia_na', '本卦下卦纳数（%s内卦＝%s）' % (bu_low, '·'.join(nj[0:3])), xia_na, '内卦三爻纳甲太玄和'),
        ('ben_shu', '本卦卦数（%s%d·%s%d）' % (bu_up, XIAN_NUM[bu_up], bu_low, XIAN_NUM[bu_low]), ben_shu, '乾集§3先天数'),
        ('hu_shu', '本卦互卦卦数（%s：%s%d·%s%d）' % (hu, h_up, XIAN_NUM[h_up], h_low, XIAN_NUM[h_low]), hu_shu, '乾集§17互卦+§3'),
        ('bian_shu', '变卦卦数（%s：%s%d·%s%d）' % (bian, bian_up, XIAN_NUM[bian_up], bian_low, XIAN_NUM[bian_low]), bian_shu, '乾集§16上下互置+§3'),
    ]
    haos = [(key, lab, tv, 1000 * qian + 100 * bai + tv, why) for key, lab, tv, why in shili]

    return {
        'year_month': [pillars[0], pillars[1]],
        's0': s0, 's1': s1, 'bu_up': bu_up, 'bu_low': bu_low,
        'ben': ben, 'ben_xiang': xiang_of(ben),
        'bian': bian, 'bian_xiang': xiang_of(bian),
        'hu': hu, 'hu_xiang': xiang_of(hu),
        'qian': qian, 'bai': bai, 'prefix': 100 * qian + 10 * bai,
        'haos': haos,
    }


# ----------------------------------------------------------------------
# 七、大运数演算法（河洛数表）
# ----------------------------------------------------------------------

def dayun_suanfa(pillars, gender, n=8):
    """大运数：自月柱起十年一步顺/逆排，配河洛地支数（生数.成数）。
    阳年男/阴年女顺行、阴年男/阳年女逆行。起运岁须按交节另算。"""
    forward = (pillars[0][0] in YANG_GAN) == (gender == 'm')
    step = 1 if forward else -1
    gi = TIANGAN.index(pillars[1][0])
    zi = DIZHI.index(pillars[1][1])
    out = []
    for _ in range(n):
        gi = (gi + step) % 10
        zi = (zi + step) % 12
        gz = TIANGAN[gi] + DIZHI[zi]
        out.append((gz, DAYUN_GAN_HE[gz[0]], HELUO_ZHI[gz[1]]))
    return {'forward': forward, 'steps': out}


def dayun_shuxu(pillars, dayun_gz):
    """§5 大运数演算法：『以月日时年起数序 + 大运数序』共得数 = 条文号（书版命例硬证）。

    pillars = [年, 月, 日, 时]（各两字）；dayun_gz = 大运干支（两字）。
    位次（§26「月日时年」口诀 + 破解钥匙算式）：
      千位 = 月干合化数 + 大运干合化数（和可 ≥10，作高位自然进位）
      百位 = 日干合化数
      十位 = 时干合化数
      个位 = 年干合化数 + 大运支生数（§6 生数，即 HELUO_ZHI[支][0]）
    共得数为四位相加（标准十进制，千位和=10 时进位成五位数），非「去十余取个位」。
    书版命例（第 45 页，庚寅 甲申 丙午 甲午·男）：
      乙酉 → 8(甲4+乙4)　6(丙)　4(甲)　8(庚4+酉生数4) = 8648
      丙戌 → 10(甲4+丙6)　6(丙)　4(甲)　9(庚4+戌生数5) = 10649
      己丑 → 8649；庚寅 → 8647；辛卯 → 10647；壬辰 → 7649，本函数逐位复现一致。
    """
    _y, m, d, h = pillars
    dgan, dzhi = dayun_gz[0], dayun_gz[1]
    qian_sum = DAYUN_GAN_HE[m[0]] + DAYUN_GAN_HE[dgan]
    bai = DAYUN_GAN_HE[d[0]]
    shi = DAYUN_GAN_HE[h[0]]
    ge_sum = DAYUN_GAN_HE[pillars[0][0]] + HELUO_ZHI[dzhi][0]
    n = qian_sum * 1000 + bai * 100 + shi * 10 + ge_sum
    return {
        'dayun': dayun_gz, 'n': n,
        'qian_sum': qian_sum, 'bai': bai, 'shi': shi, 'ge_sum': ge_sum,
        'wide': qian_sum >= 10,   # 千位和进位成五位数（书版 10649/10647 硬证）
    }


def liunian_shuxu(pillars, dayun_gz, liunian_gz):
    """§27 流年取数：破解钥匙「流年干支代替原生年干支，依月日时年顺起数，再加流年地支数」。

    在 §5 大运数序基础上，个位的「年干」换成「流年干」、「大运支生数」换成「流年支生数」；
    千位（月干+大运干）、百位、十位与大运数序同，大运十年内不变。
    条号为标准十进制相加（千位和≥10 进位、个位和≥10 进位），与大运共得数规则一致。
    诚实边界：破解钥匙未逐字说明流年千位是否仍叠加大运干数，张椿来原书亦无流年命例，
    故「流年千位保持大运干」为据破解钥匙文字的推断、非命例硬证，已如实标注。
    """
    m, d, h = pillars[1], pillars[2], pillars[3]
    dgan = dayun_gz[0]
    lgan, lzhi = liunian_gz[0], liunian_gz[1]
    qian_sum = DAYUN_GAN_HE[m[0]] + DAYUN_GAN_HE[dgan]
    bai = DAYUN_GAN_HE[d[0]]
    shi = DAYUN_GAN_HE[h[0]]
    ge_sum = DAYUN_GAN_HE[lgan] + HELUO_ZHI[lzhi][0]
    n = qian_sum * 1000 + bai * 100 + shi * 10 + ge_sum
    return {
        'liunian': liunian_gz, 'dayun': dayun_gz, 'n': n,
        'qian_sum': qian_sum, 'bai': bai, 'shi': shi, 'ge_sum': ge_sum,
        'wide': qian_sum >= 10,   # 千位和进位成五位数
    }


def shuchuan_liunian(pillars, gender, qiyun=3, n_ages=100):
    """书传流年 · 逐岁条文链（§5 大运数序 + §27 流年取数）。

    逐年流年干支 = 出生年柱起、顺排六十甲子（一年一进）；每十年入一大运，
    大运自月柱顺/逆排（阳男阴女顺、阴男阳女逆），起运岁 qiyun 之前为「未交运」
    童限、以月柱代运；逐岁条文号 = liunian_shuxu（千=月干合化+大运干合化、百=日干、
    十=时干、个=流年干合化+流年支生数，标准十进制、千位和≥10 进位五位数）。

    诚实边界（与 liunian_shuxu 一致）：§27「流年干支代替年干支、加流年支生数」出自
    《破解钥匙》；破解钥匙未逐字说明流年千位是否仍叠加大运干数、张椿来原书亦无流年命例，
    故「流年千位保持大运干」为据破解钥匙文字的推断、非命例硬证。本表为书传流年，
    与「十四表流年」（跨传承）两套体系并存、互不混淆。
    """
    year_gan, year_zhi = pillars[0][0], pillars[0][1]
    gi0, zi0 = TIANGAN.index(year_gan), DIZHI.index(year_zhi)

    steps_needed = (n_ages - qiyun) // 10 + 2
    dy = dayun_suanfa(pillars, gender, n=max(steps_needed, 8))
    dayun_list = [s[0] for s in dy['steps']]

    items = []
    for age in range(1, n_ages + 1):
        lgi = (gi0 + (age - 1)) % 10
        lzi = (zi0 + (age - 1)) % 12
        ln_gz = TIANGAN[lgi] + DIZHI[lzi]
        if age < qiyun:
            dayun_gz = pillars[1]
            note = '未交运·以月柱%s代运' % pillars[1]
        else:
            di = (age - qiyun) // 10
            if di >= len(dayun_list):
                dayun_gz = dayun_list[-1]
                note = '超出已排大运·沿用末步%s' % dayun_list[-1]
            else:
                dayun_gz = dayun_list[di]
                note = ''
        ds = liunian_shuxu(pillars, dayun_gz, ln_gz)
        items.append({
            'age': age, 'liunian': ln_gz, 'dayun': dayun_gz,
            'n': ds['n'], 'qian': ds['qian_sum'], 'bai': ds['bai'],
            'shi': ds['shi'], 'ge': ds['ge_sum'], 'wide': ds['wide'],
            'note': note,
        })

    return {
        'pillars': pillars, 'gender': gender, 'qiyun': qiyun,
        'forward': dy['forward'], 'dayun_list': dayun_list, 'items': items,
    }


# ----------------------------------------------------------------------
# 八、渲染
# ----------------------------------------------------------------------

def render_yansuan(pillars, gender, ri_gua=None, dayun_n=8, birth_year=None):
    L = []
    L.append('── 演算法式 · 起数推演（据《张椿来·铁版神数》第三部分） ──')

    # 1. 太玄数
    t = taixuan_suanfa(pillars, gender)
    L.append('')
    L.append('【一 · 太玄数演算法】')
    L.append('  配太玄数（甲己子午九、乙庚丑未八、丙辛寅申七、丁壬卯酉六、戊癸辰戌五、巳亥四）：')
    L.append('    ' + '　'.join('%s%s=%d' % (n, p, s) for n, p, s in zip(t['names'], pillars, t['sums'])))
    L.append('  化卦：年%s（%d÷8余%d=%s·上）+ 月%s（%d÷8余%d=%s·下）→ 先天卦 %s（%s）' % (
        pillars[0], t['sums'][0], t['sums'][0] % 8 or 8, t['xian_up'],
        pillars[1], t['sums'][1], t['sums'][1] % 8 or 8, t['xian_low'],
        t['xian_gua'], t['xian_xiang']))
    L.append('        日%s（%d去十余%d=%s·上）+ 时%s（%d去十余%d=%s·下）→ 后天卦 %s（%s）' % (
        pillars[2], t['sums'][2], t['sums'][2] % 10 or (8 if gender == 'm' else 2), t['hou_up'],
        pillars[3], t['sums'][3], t['sums'][3] % 10 or (8 if gender == 'm' else 2), t['hou_low'],
        t['hou_gua'], t['hou_xiang']))
    yt = t['yuantang']
    L.append('  元堂：%s（%s）——%s爻为变爻' % (t['xian_gua'], yt['case'], {1: '初', 2: '二', 3: '三', 4: '四', 5: '五', 6: '上'}[yt['position']]))
    L.append('  互卦：先天 %s → 互 %s；后天 %s → 互 %s' % (
        t['xian_gua'], t['xian_hu'], t['hou_gua'], t['hou_hu']))
    L.append('  变卦（上下互置+元堂变爻）：先天 %s → %s；后天 %s → %s' % (
        t['xian_gua'], t['xian_bian'], t['hou_gua'], t['hou_bian']))
    L.append('  八卦加则取数（乾卦六为头：千=上卦数+6去十、百=上卦数、十个=互卦上下卦数）：')
    L.append('    先天八式：%s → 主条文号 〔%d〕' % (', '.join(str(x) for x in t['xian_shu']), t['anchor_xian']))
    L.append('    后天八式：%s → 主条文号 〔%d〕' % (', '.join(str(x) for x in t['hou_shu']), t['anchor_hou']))

    # 2. 皇极
    h = huangji_suanfa(pillars)
    L.append('')
    L.append('【二 · 皇极易数演算法（元会运世）】')
    L.append('  元(年)=%d 会(月)=%d 运(日)=%d 世(时)=%d' % (h['yuan'], h['hui'], h['yun'], h['shi']))
    L.append('  元会互合（顺·考六亲）=%d；运世互合（逆·推运程）=%d' % (h['yuan_hui'], h['yun_shi']))
    L.append('  考六亲加年干太玄×1000（%s=%d→+%d）→ %d；初刻即中再月干×100（%s=%d→+%d）→ %d' % (
        pillars[0][0], TAIXUAN[pillars[0][0]], h['jia_qian'], h['jia_8000'],
        pillars[1][0], TAIXUAN[pillars[1][0]], h['jia_bai'], h['jia_900']))

    # 3. 河洛
    hl = heluo_suanfa(pillars, gender, birth_year)
    L.append('')
    L.append('【三 · 河洛理数演算法（天数地数）】')
    L.append('  天干河洛数：%s；地支河洛数：%s' % (
        '　'.join('%s=%d' % (p[0], n) for p, n in zip(pillars, hl['gan_nums'])),
        ','.join('%s%s' % (p[1], HELUO_ZHI[p[1]]) for p in pillars)))
    L.append('  天数(奇数之和)=%d、地数(偶数之和)=%d（大衍之数55）' % (hl['tian'], hl['di']))
    _tj = '（%s寄宫）' % hl['tian_jigong'] if hl['tian_jigong'] else ''
    _dj = '（%s寄宫）' % hl['di_jigong'] if hl['di_jigong'] else ''
    L.append('  天数去25取余=%d→%s%s；地数去30取余=%d→%s%s' % (
        hl['tian_yu'], hl['tian_gua'], _tj, hl['di_yu'], hl['di_gua'], _dj))
    L.append('  阴阳合卦（%s）：先天卦 %s（%s）→ 后天卦 %s（%s）' % (
        '阳男阴女天数在上' if hl['tian_above'] else '阴男阳女天数在下',
        hl['xiangua'], hl['xiangua_xiang'], hl['houtian'], hl['houtian_xiang']))
    L.append('  八卦加则取数（洛书数）：先天〔%s〕、后天〔%s〕' % (hl['xian_shu'], hl['hou_shu']))

    # 4. 日柱配卦
    rz = rizhu_peigua_suanfa(pillars, ri_gua)
    L.append('')
    L.append('【四 · 日柱配卦演算法（48 干支纳数）】')
    L.append('  日柱 %s 化卦 %s（%s）——「日柱配卦」金钥匙：上卦=日支配卦、下卦=日干河洛配卦' % (
        rz['day'], rz['ri_gua'], rz['ri_xiang']))
    L.append('  纳甲：' + ' · '.join(rz['najia']))
    L.append('  上卦纳数 %s = %d；下卦纳数 %s = %d' % (
        ' + '.join(x.split('=')[0] for x in rz['up_det']), rz['up_sum'],
        ' + '.join(x.split('=')[0] for x in rz['low_det']), rz['low_sum']))
    L.append('  上下卦总和合为条文号 → 〔%d〕' % rz['n'])

    # 4b. 变卦取数（年月柱）→ 82xx 系列
    bv = rizhu_bian_gua_qu_shu(pillars)
    L.append('')
    L.append('  以变卦取数（年月两柱）：%s%s → 先天卦本卦 %s（%s）→ 变卦（上下互置）%s（%s）' % (
        pillars[0], pillars[1], bv['ben'], bv['ben_xiang'], bv['bian'], bv['bian_xiang']))
    L.append('      互卦 %s（%s）；「乾卦六为头」：千位=上卦%d+6=%d、百位=%d → 前缀 %02d' % (
        bv['hu'], bv['hu_xiang'], XIAN_NUM[NAME2UP[bv['bian']][0]], bv['qian'], bv['bai'], bv['prefix']))
    for _key, lab, tv, hao, why in bv['haos']:
        L.append('      %s = 十位个位 %02d → 条文号 〔%d〕（%s）' % (lab, tv, hao, why))
    L.append('      （书版列五式；余三式书版未列、属规则推断，本函数不输出，详见演算法式.md §4）')

    # 5. 大运 / 流年
    dy = dayun_suanfa(pillars, gender, dayun_n)
    L.append('')
    L.append('【五 · 大运数演算法（§5 月日时年起数序 + 大运数序 → 条文号）】')
    L.append('  自月柱%s 十年一步%s排：' % (pillars[1], '顺' if dy['forward'] else '逆'))
    for i, (gz, gh, hlz) in enumerate(dy['steps'], 1):
        ds = dayun_shuxu(pillars, gz)
        tag = '［千位和≥10·进位五位数］' if ds['wide'] else ''
        L.append('    %02d步 %s：千=%s+%s=%d　百=%d　十=%d　个=%s+%d=%d → 大运数序〔%d〕%s' % (
            i, gz, pillars[1][0], gz[0], ds['qian_sum'], ds['bai'], ds['shi'],
            pillars[0][0], hlz[0], ds['ge_sum'], ds['n'], tag))
    L.append('  （书版命例：庚寅 甲申 丙午 甲午·男·大运乙酉 → 8648，本引擎逐位复现一致）')
    L.append('  流年（§27）：流年干支代替年干支、加流年支生数（千位保持大运干），一年一变；')
    L.append('    例：大运%s 内流年 ↔ 个位 = 流年干合化 + 流年支生数（破解钥匙公式·推断，原书无流年命例）。'
             % dy['steps'][0][0])
    return '\n'.join(L)


# ----------------------------------------------------------------------
# 九、独立测试入口
# ----------------------------------------------------------------------

def _selfcheck():
    from yiji_gua import GUA64 as _G
    ok = True

    # 太玄数演算法：庚寅 甲申 丙午 甲午（男）→ 先天山地剥 / 后天天山遁，3788 / 2664
    t = taixuan_suanfa(['庚寅', '甲申', '丙午', '甲午'], 'm')
    assert t['xian_gua'] == '山地剥', t['xian_gua']
    assert t['hou_gua'] == '天山遁', t['hou_gua']
    assert t['anchor_xian'] == 3788, t['anchor_xian']
    assert t['anchor_hou'] == 2664, t['anchor_hou']

    # 皇极：元会 1516、运世 6181、9516、10416
    h = huangji_suanfa(['庚寅', '甲申', '丙午', '甲午'])
    assert h['yuan_hui'] == 1516, h['yuan_hui']
    assert h['yun_shi'] == 6181, h['yun_shi']
    assert h['jia_8000'] == 9516, h['jia_8000']
    assert h['jia_900'] == 10416, h['jia_900']
    assert h['jia_qian'] == 8000 and h['jia_bai'] == 900, (h['jia_qian'], h['jia_bai'])

    # 河洛：天数29→4巽、地数36→6乾；先天风天小畜→后天乾为天；1497 / 2666
    hl = heluo_suanfa(['庚寅', '甲申', '丙午', '甲午'], 'm')
    assert hl['gan_nums'] == [3, 6, 8, 6], hl['gan_nums']          # §5：庚震3/甲乾6/丙艮8
    assert hl['zhi_nums'] == [3, 8, 4, 9, 2, 7, 2, 7], hl['zhi_nums']  # §6：寅3.8/申4.9/午2.7
    assert hl['tian'] == 29, hl['tian']
    assert hl['di'] == 36, hl['di']
    assert hl['tian_yu'] == 4 and hl['tian_gua'] == '巽', (hl['tian_yu'], hl['tian_gua'])
    assert hl['di_yu'] == 6 and hl['di_gua'] == '乾', (hl['di_yu'], hl['di_gua'])
    assert hl['xiangua'] == '风天小畜', hl['xiangua']
    assert hl['houtian'] == '乾为天', hl['houtian']
    assert hl['xian_shu'] == 1497, hl['xian_shu']
    assert hl['hou_shu'] == 2666, hl['hou_shu']

    # 河洛「去十余取个位 + 5寄宫三元 + 阴阳合卦」边界（三书独立坐实：陈鼎龙/唐颐/金泉）：
    # 1984 例（甲子乙亥庚戌癸未·男·下元）：天数15→余5寄离、地数42→余2坤，先天火地晋（旧版余5返None）
    hl84 = heluo_suanfa(['甲子', '乙亥', '庚戌', '癸未'], 'm', birth_year=1984)
    assert hl84['tian'] == 15 and hl84['di'] == 42, (hl84['tian'], hl84['di'])
    assert hl84['tian_yu'] == 5 and hl84['tian_gua'] == '离' and hl84['tian_jigong'] == '下元', hl84['tian_jigong']
    assert hl84['di_yu'] == 2 and hl84['di_gua'] == '坤', (hl84['di_yu'], hl84['di_gua'])
    assert hl84['xiangua'] == '火地晋', hl84['xiangua']
    assert hl84['xian_shu'] == 5918 and hl84['hou_shu'] == 8237, (hl84['xian_shu'], hl84['hou_shu'])

    # 三元寄宫分支（余5）：上元男艮女坤、中元阳男阴女艮/阴男阳女坤、下元男离女兑
    assert (_zhonggong_jigong('m', '甲', 1900), _zhonggong_jigong('m', '甲', 1960),
            _zhonggong_jigong('m', '甲', 1984)) == (('艮', '上元'), ('艮', '中元'), ('离', '下元'))
    assert (_zhonggong_jigong('f', '甲', 1900), _zhonggong_jigong('f', '甲', 1960),
            _zhonggong_jigong('f', '甲', 1984)) == (('坤', '上元'), ('坤', '中元'), ('兑', '下元'))
    assert _zhonggong_jigong('m', '乙', 1960) == ('坤', '中元')   # 阴男中元寄坤
    assert _zhonggong_jigong('f', '乙', 1960) == ('艮', '中元')   # 阴女中元寄艮
    assert _zhonggong_jigong('m', '甲', None) == ('艮', '上元(缺年默认)')  # 缺年回退上元

    # 去十余取余边界（唐颐《图解易经象数学》天数28→28-25=3、地数30→余0取十位=3，
    # 地数恰等于30不减、个位0取十位的临界）；原造 29→4、36→6 已在上文验证。
    assert _he_qu_yu(28, 25) == 3, _he_qu_yu(28, 25)
    assert _he_qu_yu(30, 30) == 3, _he_qu_yu(30, 30)
    assert _he_qu_yu(29, 25) == 4 and _he_qu_yu(36, 30) == 6
    assert _he_qu_yu(25, 25) == 5 and _he_qu_yu(15, 25) == 5

    # 阴阳合卦：阳男天数在上（1984 例已证）；阳年女（甲年女）天数在下 → 地泽临
    hl84f = heluo_suanfa(['甲子', '乙亥', '庚戌', '癸未'], 'f', birth_year=1984)
    assert hl84f['tian_above'] is False and hl84f['xiangua'] == '地泽临', hl84f['xiangua']
    assert hl84f['tian_gua'] == '兑' and hl84f['tian_jigong'] == '下元', hl84f['tian_gua']

    # 口诀覆盖性：河洛天干 10、地支 12 全配（§5/§6），三套表与天干地支全集一致
    assert set(GAN_HELUO_NUM) == set(TIANGAN) == set(GAN_GUA_HELUO)
    assert set(HELUO_ZHI) == set(DIZHI) == set(DIZHI_PEIGUA)

    # §14 四十八干支纳数表（原书第22页）：纳甲48爻辰逐字核对，锁定「变知六八止」纳甲来源；
    # 每爻纳数 = 纳干太玄 + 纳支太玄（此规律经下方 3926 命例硬证）
    from yiji_gua import NAJIA as _NAJIA
    _NAJIA_48 = {
        '乾': ['甲子', '甲寅', '甲辰', '壬午', '壬申', '壬戌'],
        '坤': ['乙未', '乙巳', '乙卯', '癸丑', '癸亥', '癸酉'],
        '震': ['庚子', '庚寅', '庚辰', '庚午', '庚申', '庚戌'],
        '巽': ['辛丑', '辛亥', '辛酉', '辛未', '辛巳', '辛卯'],
        '坎': ['戊寅', '戊辰', '戊午', '戊申', '戊戌', '戊子'],
        '离': ['己卯', '己丑', '己亥', '己酉', '己未', '己巳'],
        '艮': ['丙辰', '丙午', '丙申', '丙戌', '丙子', '丙寅'],
        '兑': ['丁巳', '丁卯', '丁丑', '丁亥', '丁酉', '丁未'],
    }
    assert _NAJIA == _NAJIA_48, '纳甲48爻辰与《乾集》§14(页22)不符'
    # 纳数规律已由下方 3926 命例硬证：每爻纳数 = 纳干太玄 + 纳支太玄

    # 日柱配卦：丁酉化天泽履 → 3926（显式化卦）
    rz = rizhu_peigua_suanfa(['癸巳', '甲子', '丁酉', '甲辰'], ri_gua='天泽履')
    assert rz['up_sum'] == 39, rz['up_sum']
    assert rz['low_sum'] == 26, rz['low_sum']
    assert rz['n'] == 3926, rz['n']

    # 金钥匙缺省推导：日柱丁酉 → 上卦=日支酉→乾、下卦=日干丁→兑 → 天泽履 → 3926
    rz2 = rizhu_peigua_suanfa(['癸巳', '甲子', '丁酉', '甲辰'])
    assert rz2['ri_gua'] == '天泽履', rz2['ri_gua']
    assert rz2['n'] == 3926, rz2['n']

    # 日柱配卦 · 变卦取数（年月柱）：癸巳甲子丁酉甲辰 → 本卦天泽履→变卦泽天夬→互卦风火家人，
    # 前缀 82（千=2+6=8、百=2），书版五式 8239/8226/8212/8253/8221 逐位锁定。
    bv = rizhu_bian_gua_qu_shu(['癸巳', '甲子', '丁酉', '甲辰'])
    assert bv['ben'] == '天泽履', bv['ben']
    assert bv['bian'] == '泽天夬', bv['bian']
    assert bv['hu'] == '风火家人', bv['hu']
    assert (bv['qian'], bv['bai']) == (8, 2), (bv['qian'], bv['bai'])
    _expect = {
        'shang_na': 8239,
        'xia_na': 8226,
        'ben_shu': 8212,
        'hu_shu': 8253,
        'bian_shu': 8221,
    }
    _got = {key: hao for key, _lab, _tv, hao, _why in bv['haos']}
    assert _got == _expect, (_got, _expect)

    # §5 大运数演算法（书版第 45 页命例硬证）：庚寅 甲申 丙午 甲午（男）逐步复现。
    _p45 = ['庚寅', '甲申', '丙午', '甲午']
    ds = dayun_shuxu(_p45, '乙酉')
    assert (ds['qian_sum'], ds['bai'], ds['shi'], ds['ge_sum']) == (8, 6, 4, 8), ds
    assert ds['n'] == 8648 and ds['wide'] is False, ds
    # 千位和=10 进位成五位数（书版 10649/10647 硬证，非「去十余取0」）
    assert dayun_shuxu(_p45, '丙戌')['n'] == 10649, dayun_shuxu(_p45, '丙戌')
    assert dayun_shuxu(_p45, '辛卯')['n'] == 10647, dayun_shuxu(_p45, '辛卯')
    # 其余步大运数序（书版 7645/8649/8647/7649）
    assert [dayun_shuxu(_p45, g)['n'] for g in ['丁亥', '己丑', '庚寅', '壬辰']] == [7645, 8649, 8647, 7649]
    # 大运序列（§2 排大运：阳年男自月柱甲申顺排八步）与书版一致
    _dy = dayun_suanfa(_p45, 'm', n=8)
    assert [s[0] for s in _dy['steps']] == ['乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰'], \
        [s[0] for s in _dy['steps']]
    # 每步大运干合化数（§26 全表）：乙4 丙6 丁3 戊3 己4 庚4 辛6 壬3
    assert [s[1] for s in _dy['steps']] == [4, 6, 3, 3, 4, 4, 6, 3], [s[1] for s in _dy['steps']]
    # 每步大运支河洛数（§6 生数.成数）：酉4.9 戌5.10 亥1.6 子1.6 丑5.10 寅3.8 卯3.8 辰5.10
    assert [s[2] for s in _dy['steps']] == [(4, 9), (5, 10), (1, 6), (1, 6), (5, 10), (3, 8), (3, 8), (5, 10)], \
        [s[2] for s in _dy['steps']]
    # 流年（§27 破解钥匙公式，推断·原书无流年命例）：大运乙酉内流年丙戌 →
    #   千=甲4+乙4=8、百=丙6、十=甲4、个=丙6+戌生数5=11 → 标准十进制进位 = 8651。
    ln = liunian_shuxu(_p45, '乙酉', '丙戌')
    assert ln['n'] == 8651 and ln['ge_sum'] == 11, ln

    return ok


if __name__ == '__main__':
    if _selfcheck():
        print('[自检] 太玄/皇极/河洛/日柱配卦 四式书版命例全部通过：')
        print()
    print(render_yansuan(['庚寅', '甲申', '丙午', '甲午'], 'm'))
    print()
    print('-' * 70)
    print('书版「日柱配卦」命例（癸巳 甲子 丁酉 甲辰，日柱丁酉化天泽履）：')
    rz = rizhu_peigua_suanfa(['癸巳', '甲子', '丁酉', '甲辰'], ri_gua='天泽履')
    print('  上卦纳数 %s = %d；下卦纳数 %s = %d → 条文号〔%d〕' % (
        ' + '.join(x.split('=')[0] for x in rz['up_det']), rz['up_sum'],
        ' + '.join(x.split('=')[0] for x in rz['low_det']), rz['low_sum'], rz['n']))