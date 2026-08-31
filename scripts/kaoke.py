#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
铁板神数 · 考刻定分秘数表（考刻闭环引擎）

依据两本书交叉校订（原文胶片见 references/）：
  1. 《铁板神数正宗破解钥匙》：考刻秘数 1327、附表「八刻定父母弟兄表」(第17–19页)
  2. 张椿来《铁版神数》：「28 考刻论父母兄弟」「29 考分论夫妻子女」(第24–28页)

考刻定分闭环（书中可确认的确定性步骤）：
  起数 → 基数（天干合化：月千·日百·时十·年个）
       → 八刻条文号 = 基数 + 1327×{0,2,4,6,8,10,12,14}（超12000减12000）
       → 查「八刻定父母弟兄表」[时辰][刻] 得该刻六亲格局
       → 命主父母/弟兄实况与该刻格局比对 → 锁定真刻
       → 查「每刻十五分定妻子表」[时辰][分] 得该分妻/子格局
       → 命主婚姻/子女实况与该分格局比对 → 锁定真分

说明：OCR 噪声校订规律——「毒」通「母」、「封/奔/沃/海」通「寿」、「孟/歪」通「母」、
「弧兄/弩儿」通「弟兄」、「坪」通「坤」、「巾」通「中」等，均已在表中订正。
个别原片无法 100% 判读处（如辰时一刻弟兄「三四」、戌时二刻弟兄「四五」）保留并按
表内并列时辰/同刻规律取最稳值，并附 source 说明，供后续高清重扫后复核。
"""
from __future__ import annotations

# ----------------------------------------------------------------------
# 一、起数基数（天干合化配数）
# ----------------------------------------------------------------------

GAN_HE = {
    '甲': 4, '己': 4, '乙': 4, '庚': 4,
    '丙': 6, '辛': 6, '丁': 3, '壬': 3,
    '戊': 3, '癸': 3,
}

DIZHI = '子丑寅卯辰巳午未申酉戌亥'

# 考刻秘数（供数之数）：出自《铁板神数正宗破解钥匙》，非张椿来《铁版神数》原书，
# 仅作供数/条号对照；考刻权威结论以张椿来原书「八刻/十五分表」格局为准。
KAO_KE_SECRET = 1327
# 八刻倍数：一时辰八刻，第 k 刻(1..8) = 基数 + 1327 × 2(k-1)
KAO_KE_MULT = [0, 2, 4, 6, 8, 10, 12, 14]


def jifen_base(year, month, day, hour):
    """考刻定分基数：四柱天干合化数，月千·日百·时十·年个。"""
    digits = [
        GAN_HE[month[0]],  # 千位
        GAN_HE[day[0]],    # 百位
        GAN_HE[hour[0]],   # 十位
        GAN_HE[year[0]],   # 个位
    ]
    return digits[0] * 1000 + digits[1] * 100 + digits[2] * 10 + digits[3]


def normalize_n(v, lo=1001, hi=13000):
    """把供数回卷到条文库编号区间 [1001, 13000]（12000 条周期）。
    书版公式以 1–12000 编号，本库以 1001–13000 编号，故以 +1000 平移并周期回卷。"""
    span = hi - lo + 1  # 12000
    v = lo + ((v - lo) % span)
    return v


def ba_ke_articles(base, lo=1001, hi=13000):
    """八刻条文号 = 基数 + 1327×2(k-1)，回卷到库编号区间 [1001,13000]。
    返回 [(刻序1..8, 条文号), ...]。"""
    out = []
    for k, m in enumerate(KAO_KE_MULT, 1):
        v = normalize_n(base + KAO_KE_SECRET * m, lo, hi)
        out.append((k, v))
    return out


# ----------------------------------------------------------------------
# 二、八刻定父母弟兄表（12 时辰 × 8 刻）
# 每格 (父母态, 弟兄, 得爻)
#   父母态 ∈ {父母寿, 父母丧, 父丧母寿, 母丧父寿, 父丧, 母丧}
#   弟兄   ∈ {多, 少, 无, 二三, 三四, 四五}
#   得爻   ∈ {乾中, 乾上, 乾初, 坤初, 坤中, 坤上, 兑离巽, 艮坎震}
# ----------------------------------------------------------------------

KE_TABLE = {
    '子': [
        ('父母寿', '多', '乾中'), ('母丧', '少', '乾上'),
        ('父母丧', '四五', '乾初'), ('父丧母寿', '多', '坤初'),
        ('父母丧', '无', '坤中'), ('父母寿', '无', '兑离巽'),
        ('父丧母寿', '二三', '坤上'), ('父丧', '无', '艮坎震'),
    ],
    '丑': [
        ('母丧父寿', '四五', '乾中'), ('父母寿', '二三', '乾上'),
        ('父丧', '二三', '乾初'), ('母丧', '四五', '坤初'),
        ('母丧', '少', '坤中'), ('父母丧', '无', '兑离巽'),
        ('父母寿', '少', '坤上'), ('父丧母寿', '少', '艮坎震'),
    ],
    '寅': [
        ('母丧父寿', '四五', '乾中'), ('父母寿', '多', '乾上'),
        ('父母丧', '二三', '乾初'), ('母丧父寿', '二三', '坤初'),
        ('父丧', '多', '坤中'), ('母丧', '少', '兑离巽'),
        ('父母丧', '四五', '坤上'), ('父母寿', '少', '艮坎震'),
    ],
    '卯': [
        ('母丧父寿', '多', '乾中'), ('父丧母寿', '二三', '乾初'),
        ('父母寿', '四五', '乾初'), ('父母丧', '无', '坤初'),
        ('父丧', '多', '坤中'), ('母丧', '少', '兑离巽'),
        ('父母寿', '二三', '坤上'), ('父母丧', '二三', '艮坎震'),
    ],
    '辰': [
        ('母丧父寿', '三四', '乾中'), ('父母寿', '无', '乾上'),
        ('父母丧', '四五', '乾初'), ('父丧母寿', '四五', '坤初'),
        ('父母寿', '二三', '坤中'), ('父母丧', '少', '兑离巽'),
        ('父丧', '无', '坤上'), ('父丧', '无', '艮坎震'),
    ],
    '巳': [
        ('父母寿', '四五', '乾中'), ('母丧', '四五', '乾上'),
        ('父丧母寿', '二三', '乾初'), ('父母丧', '二三', '坤初'),
        ('父丧母寿', '无', '坤中'), ('父母寿', '少', '兑离巽'),
        ('母丧', '二三', '坤上'), ('父母丧', '少', '艮坎震'),
    ],
    '午': [
        ('父母丧', '四五', '乾中'), ('父丧', '四五', '乾上'),
        ('父母寿', '多', '乾初'), ('母丧', '无', '坤初'),
        ('父母寿', '二三', '坤中'), ('母丧父寿', '多', '兑离巽'),
        ('父母丧', '二三', '坤上'), ('父丧母寿', '二三', '艮坎震'),
    ],
    '未': [
        ('父丧母寿', '多', '乾中'), ('父母丧', '无', '乾上'),
        ('母丧', '二三', '乾初'), ('父母寿', '无', '坤初'),
        ('父丧母寿', '二三', '坤中'), ('母丧', '多', '兑离巽'),
        ('父母丧', '二三', '坤上'), ('父母丧', '二三', '艮坎震'),
    ],
    '申': [
        ('父丧母寿', '四五', '乾中'), ('母丧', '四五', '乾上'),
        ('父母寿', '四五', '乾初'), ('父母丧', '四五', '坤初'),
        ('母丧父寿', '无', '坤中'), ('父母丧', '少', '兑离巽'),
        ('父丧', '无', '坤上'), ('父母寿', '二三', '艮坎震'),
    ],
    '酉': [
        ('父母丧', '二三', '乾中'), ('母丧', '二三', '乾上'),
        ('父母寿', '无', '乾初'), ('父丧母寿', '二三', '坤初'),
        ('父丧', '无', '坤中'), ('母丧父寿', '少', '兑离巽'),
        ('父母丧', '少', '坤上'), ('父母寿', '多', '艮坎震'),
    ],
    '戌': [
        ('父母丧', '二三', '乾中'), ('父丧', '四五', '乾上'),
        ('父母寿', '四五', '乾初'), ('母丧父寿', '四五', '坤初'),
        ('父母丧', '二三', '坤中'), ('父丧母寿', '少', '兑离巽'),
        ('父母寿', '四五', '坤上'), ('母丧', '二三', '艮坎震'),
    ],
    '亥': [
        ('父母丧', '无', '乾中'), ('父丧母寿', '二三', '乾上'),
        ('母丧', '无', '乾初'), ('父母寿', '无', '坤初'),
        ('母丧父寿', '多', '坤中'), ('父丧', '四五', '兑离巽'),
        ('父母丧', '二三', '坤上'), ('父母寿', '二三', '艮坎震'),
    ],
}

# 校订存疑标注（其余 96 格依两书交叉一致）
KE_UNCERTAINTY = {
    ('辰', 1): '弟兄「三四」原片作「三阳」，依同刻并列规律取「三四」，待复核',
    ('戌', 2): '弟兄「四五」原片作「四二」，依「四」在前取「四五」，待复核',
    ('午', 1): '父母态「父母丧」原片作「父册丧」，依「册≈母」取「父母丧」，待复核',
    ('亥', 2): '父母态原片「父丧母寿」依「二井→二三」校订弟兄为「二三」',
}


# ----------------------------------------------------------------------
# 三、每刻十五分定妻子表（12 时辰 × 15 分）
# 每格 (妻态, 子态, 夫态)
#   妻态 ∈ {偷妻, 强妻, 贤妻, 佳妻, 和妻, 克妻, 丧妻, 续妻, 无妻, 有妻, 有妾, 丧妾, 健妻}
#   子态 ∈ {五子, 四子, 三子, 二子, 一子, 少子, 多子, 无子, 二女, 多女}
#   夫态 ∈ {夫强, 克夫, 夫丧, 和夫, 佳夫, 夫兴, 健夫, 偷夫, 再嫁, 有夫, 无夫, 又丧夫}
# 注：原片左右两时辰并列，妻态字大量扫描噪声（偷/借/贺/绩/缉/绰≈娶妻系，
#     姝/婶/姓/姣/姑/娅/妍/姜/姚/始/蛎/螨/垂≈妾，夷/夹/失/灰≈夫，孔/儿≈子），
#     本表按语义归并到有限枚举，仅用于考分校验、不逐字等同于原片断语。
# ----------------------------------------------------------------------

FEN_TABLE = {
    '子': [('偷妻', '五子', '夫强'), ('克妻', '少子', '克夫'), ('和妻', '四子', '佳夫'),
           ('丧妻', '多子', '丧夫'), ('有妾', '无子', '再嫁'), ('贤妻', '一子', '健夫'),
           ('无妻', '无子', '无夫'), ('丧妾', '多子', '夫丧'), ('克妻', '少子', '有夫'),
           ('佳妻', '二子', '和夫'), ('续妻', '少子', '再嫁'), ('强妻', '三子', '夫兴'),
           ('有妾', '多子', '再嫁'), ('续妻', '多子', '再嫁'), ('有妻', '无子', '又丧夫')],
    '丑': [('和妻', '四子', '佳夫'), ('克妻', '少子', '夫丧'), ('有妾', '多子', '再嫁'),
           ('贤妻', '二子', '和夫'), ('丧妻', '多子', '夫丧'), ('有妻', '无子', '有夫'),
           ('佳妻', '一子', '健夫'), ('续妻', '少子', '再嫁'), ('丧妻', '多子', '又丧夫'),
           ('强妻', '三子', '夫兴'), ('无妻', '无子', '无夫'), ('续妻', '多子', '再嫁'),
           ('偷妻', '五子', '夫强'), ('续妻', '无子', '再嫁'), ('无妻', '少子', '又丧夫')],
    '寅': [('偷妻', '二子', '和夫'), ('克妻', '少子', '克夫'), ('有妾', '多子', '再嫁'),
           ('佳妻', '一子', '偷夫'), ('丧妻', '多子', '丧夫'), ('续妻', '多子', '再嫁'),
           ('强妻', '三子', '夫兴'), ('续妻', '少子', '再嫁'), ('偷妻', '五子', '夫强'),
           ('健妻', '五子', '强夫'), ('无妻', '无子', '无夫'), ('丧妾', '多子', '又丧夫'),
           ('和妻', '四子', '佳夫'), ('有妾', '无子', '再嫁'), ('克妻', '少子', '又丧夫')],
    '卯': [('佳妻', '一子', '偷夫'), ('续妻', '少子', '再嫁'), ('丧妾', '多子', '又丧夫'),
           ('强妻', '三子', '夫兴'), ('无妻', '无子', '无夫'), ('贤妻', '二子', '有夫'),
           ('偷妻', '五子', '夫强'), ('克妻', '少子', '又丧夫'), ('偷妻', '五子', '夫强'),
           ('和妻', '四子', '佳夫'), ('克妻', '少子', '克夫'), ('有妾', '多子', '再嫁'),
           ('有妻', '无子', '和夫'), ('丧妻', '多子', '克夫'), ('续妻', '多子', '再嫁')],
    '辰': [('强妻', '三子', '夫兴'), ('有妻', '无子', '再嫁'), ('丧妾', '多子', '又丧夫'),
           ('偷妻', '五子', '强夫'), ('无妻', '无子', '无夫'), ('克妻', '无子', '又丧夫'),
           ('和妻', '四子', '佳夫'), ('克妻', '少子', '克夫'), ('有妻', '多子', '再嫁'),
           ('贤妻', '二子', '和夫'), ('续妻', '多子', '再嫁'), ('有妻', '无子', '有夫'),
           ('佳妻', '一子', '偷夫'), ('续妻', '少子', '再嫁'), ('丧妻', '多子', '丧夫')],
    '巳': [('和妻', '四子', '佳夫'), ('有妾', '无子', '再嫁'), ('克妻', '少子', '克夫'),
           ('健妻', '五子', '夫强'), ('克妻', '少子', '克夫'), ('有妾', '多子', '再嫁'),
           ('贤妻', '二子', '和夫'), ('丧妻', '多子', '克夫'), ('有妻', '多子', '有夫'),
           ('佳妻', '一子', '偷夫'), ('续妻', '少子', '再嫁'), ('丧妻', '多子', '又克夫'),
           ('强妻', '三子', '夫兴'), ('无妻', '无子', '无夫'), ('续妻', '多子', '再嫁')],
    '午': [('克妻', '少子', '克夫'), ('有妾', '多子', '再嫁'), ('和妻', '五子', '夫强'),
           ('丧妻', '多子', '克夫'), ('有妻', '无子', '有夫'), ('偷妻', '三子', '夫兴'),
           ('续妻', '少子', '再嫁'), ('丧妻', '多子', '又丧夫'), ('佳妻', '五子', '和夫'),
           ('无妻', '无子', '无夫'), ('续妻', '多子', '再嫁'), ('强妻', '一子', '夫兴'),
           ('有妻', '无子', '再嫁'), ('克妻', '少子', '又丧夫'), ('健妻', '四子', '佳夫')],
    '未': [('丧妻', '多子', '夫丧'), ('有妻', '无子', '有夫'), ('偷妻', '三子', '夫兴'),
           ('续妻', '少子', '再嫁'), ('丧妻', '多子', '又丧夫'), ('佳妻', '二子', '和夫'),
           ('无妻', '无子', '无夫'), ('续妻', '多子', '再嫁'), ('强妻', '一子', '偷夫'),
           ('有妻', '无子', '再嫁'), ('克妻', '少子', '又丧夫'), ('偷妻', '四子', '佳夫'),
           ('克妻', '少子', '克夫'), ('有妻', '多子', '再嫁'), ('和妻', '五子', '强夫')],
    '申': [('续妻', '少子', '再嫁'), ('丧妻', '多子', '又丧夫'), ('佳妻', '二子', '和夫'),
           ('无妻', '无子', '无夫'), ('续妻', '多女', '再嫁'), ('强妻', '一子', '偷夫'),
           ('有妾', '无子', '再嫁'), ('克妻', '少子', '夫丧'), ('偷妻', '四子', '佳夫'),
           ('克妻', '少子', '克夫'), ('有妾', '多子', '再嫁'), ('和妻', '五子', '夫强'),
           ('丧妻', '多子', '克夫'), ('有妻', '无子', '有夫'), ('贤妻', '三子', '夫兴')],
    '酉': [('无妻', '无子', '无夫'), ('丧妻', '多子', '又丧夫'), ('佳妻', '一子', '偷夫'),
           ('有妾', '无子', '再嫁'), ('克妻', '少子', '又丧夫'), ('偷妻', '四子', '佳夫'),
           ('克妻', '少子', '克夫'), ('有妾', '多子', '再嫁'), ('和妻', '五子', '强夫'),
           ('偷妻', '三子', '夫兴'), ('丧妻', '多子', '克夫'), ('有妻', '无子', '有夫'),
           ('续妻', '少子', '再嫁'), ('佳妻', '二子', '和夫'), ('续妻', '多女', '再嫁')],
    '戌': [('有妻', '无子', '再嫁'), ('克妻', '少子', '又丧夫'), ('偷妻', '四子', '佳夫'),
           ('克妻', '少子', '克夫'), ('有妾', '多子', '再嫁'), ('和妻', '五子', '夫强'),
           ('丧妻', '多子', '夫丧'), ('有妻', '无子', '有夫'), ('贤妻', '三子', '夫兴'),
           ('续妻', '少子', '再嫁'), ('丧妻', '多子', '又丧夫'), ('佳妻', '二女', '和夫'),
           ('无妻', '无子', '无夫'), ('续妻', '多子', '再嫁'), ('强妻', '一子', '夫兴')],
    '亥': [('有妾', '多子', '再嫁'), ('强妻', '无子', '和妻'), ('丧妻', '少子', '夫丧'),
           ('有妻', '少子', '有夫'), ('贤妻', '三子', '夫兴'), ('丧妻', '多子', '夫丧'),
           ('丧妻', '多子', '夫丧'), ('有妻', '二子', '有夫'), ('续妻', '少子', '夫兴'),
           ('丧妻', '少子', '夫丧'), ('强妻', '一子', '又丧夫'), ('佳妻', '无子', '和夫'),
           ('无妻', '多子', '无夫'), ('偷妻', '四子', '再嫁'), ('无妻', '无子', '无夫')],
}

# 十五分表整体为 OCR 重灾区，凡写入者皆按语义归并；不建议逐字引为断语原文。
FEN_TABLE_NOTE = ('「每刻十五分定妻子表」原片左右两时辰并列、妻态字扫面噪声极多，'
                  '本表按有限枚举语义归并，仅作考分校验；断语原文以条文库为准。')


# ----------------------------------------------------------------------
# 四、考刻匹配（事实 → 刻分）
# ----------------------------------------------------------------------

def _parents_state(fu_sang=None, mu_sang=None):
    """把父母寿丧事实归入六态。True=已丧 / False=健在 / None=未知。"""
    if fu_sang and mu_sang:
        return '父母丧'
    if fu_sang and mu_sang is False:
        return '父丧母寿'
    if fu_sang is False and mu_sang:
        return '母丧父寿'
    if fu_sang is False and mu_sang is False:
        return '父母寿'
    if fu_sang:
        return '父丧'
    if mu_sang:
        return '母丧'
    return None


def _brothers_state(n):
    """把「同胞手足总数（兄弟+姐妹，不分男女）」归入手足枚举。None=未知。"""
    if n is None:
        return None
    if n == 0:
        return '无'
    if 1 <= n <= 2:
        return '少'
    if 3 <= n <= 5:
        return '二三' if n <= 3 else '四五'
    return '多'


def match_ke(hour_zhi, fu_sang=None, mu_sang=None, brothers_n=None):
    """考刻：给定时辰与父母/弟兄实况，返回按匹配度降序的候选刻。"""
    want_par = _parents_state(fu_sang, mu_sang)
    want_bro = _brothers_state(brothers_n)
    rows = KE_TABLE.get(hour_zhi)
    if rows is None:
        raise ValueError('时辰地支非法：%s' % hour_zhi)
    cands = []
    for k0, (par, bro, yao) in enumerate(rows, 1):
        score = 0
        detail = []
        if want_par is not None:
            if par == want_par:
                score += 2
                detail.append('父母态命中(%s)' % par)
            elif (par, want_par) in (('父母丧', '父丧'), ('父母丧', '母丧')):
                score += 1
                detail.append('父母态部分命中(%s/%s)' % (par, want_par))
            elif want_par == '父丧' and par == '父丧母寿':
                score += 1
                detail.append('父母态近似(父丧母寿≈父丧)')
        if want_bro is not None:
            if bro == want_bro:
                score += 1
                detail.append('手足命中(%s)' % bro)
            elif want_bro == '少' and bro in ('二三',):
                score += 0
                detail.append('手足邻近(%s≈少)' % bro)
        cands.append({'ke': k0, 'par': par, 'bro': bro, 'yao': yao,
                      'score': score, 'detail': detail})
    cands.sort(key=lambda c: (-c['score'], c['ke']))
    return cands


def _norm_sons_daughters(child_sex_count, sons_n, daughters_n):
    """把「单性别 child_sex_count=(性别,数量)」或「双栏 sons_n/daughters_n」归一化为双栏。"""
    if sons_n is None and daughters_n is None and child_sex_count:
        sex, cnt = child_sex_count
        if sex == '子':
            sons_n = cnt
        elif sex == '女':
            daughters_n = cnt
    return sons_n, daughters_n


def match_fen(hour_zhi, wife_alive=None, child_sex_count=None, gender=None,
              sons_n=None, daughters_n=None):
    """考分：给定时辰与婚姻/子女实况，返回按匹配度降序的候选分。
    wife_alive: True=有妻且健在 / False=无妻或已丧 / None=未知。
    子女：优先用 sons_n/daughters_n（儿子数/女儿数），否则回退 child_sex_count=(性别,数量)。
    gender: 'm' 用妻态+子态；'f' 用夫态+子态（夫态仅女命参考，不作硬性计分）。"""
    sons_n, daughters_n = _norm_sons_daughters(child_sex_count, sons_n, daughters_n)
    rows = FEN_TABLE.get(hour_zhi)
    if rows is None:
        raise ValueError('时辰地支非法：%s' % hour_zhi)
    cands = []
    for f0, (qi, zi, fu) in enumerate(rows, 1):
        score = 0
        detail = []
        scored = (gender != 'f')  # 妻态对男命（或未知）计分；女命以夫态为主题，妻态不计
        if wife_alive is not None and scored:
            if wife_alive:
                good = ('偷妻', '强妻', '贤妻', '佳妻', '和妻', '健妻', '有妻')
                if qi in good:
                    score += 1
                    detail.append('妻健(%s)' % qi)
                elif qi == '有妾':
                    score += 0
                    detail.append('妻态中性(有妾)')
            else:
                if qi in ('无妻',):
                    score += 1
                    detail.append('无妻命中')
                elif qi in ('丧妻', '丧妾'):
                    score += 1
                    detail.append('丧偶(%s)' % qi)
        # 子女匹配：儿子优先；有女无男按「无子/二女/多女」计；无子女按「无子」计。
        if sons_n is not None or daughters_n is not None:
            sons = sons_n if sons_n is not None else 0
            daughters = daughters_n if daughters_n is not None else 0
            cmap = {1: '一', 2: '二', 3: '三', 4: '四', 5: '五'}
            if sons > 0:
                cnum = cmap.get(sons, '多')
                if zi == cnum + '子':
                    score += 1
                    detail.append('子数命中(%s)' % zi)
                elif sons >= 6 and zi == '多子':
                    score += 1
                    detail.append('子数命中(%s)' % zi)
            elif daughters == 0:
                if zi == '无子':
                    score += 1
                    detail.append('无子女命中')
            else:
                if zi == '无子':
                    score += 1
                    detail.append('有女无子(%s)' % zi)
                if daughters == 2 and zi == '二女':
                    score += 1
                    detail.append('女数命中(%s)' % zi)
                elif daughters >= 3 and zi == '多女':
                    score += 1
                    detail.append('女数命中(%s)' % zi)
        cands.append({'fen': f0, 'qi': qi, 'zi': zi, 'fu': fu,
                      'score': score, 'detail': detail})
    cands.sort(key=lambda c: (-c['score'], c['fen']))
    return cands


# ----------------------------------------------------------------------
# 五、考刻闭环编排
# ----------------------------------------------------------------------

def parse_kaoke_facts(facts):
    """从结构化事实 dict 归一化出考刻/考分所需参数。
    接受键：fu_sang / mu_sang（bool 或 None）、brothers_n（int 或 None）、
    wife_alive（bool 或 None）、child_sex（'子'/'女'）、child_count（int 或 None），
    sons_n / daughters_n（儿子数/女儿数，优先于 child_sex/count）。
    也接受中文别名：父丧/母丧/弟兄数/有妻/子女性别/子女数/儿子数/女儿数。"""
    def b(v):
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ('1', 'true', 'yes', '是', '有', '已丧', '丧')

    def _int_or_none(v):
        return int(v) if v not in (None, '') else None

    fu_sang = b(facts.get('fu_sang', facts.get('父丧')))
    mu_sang = b(facts.get('mu_sang', facts.get('母丧')))
    brothers_n = _int_or_none(facts.get('brothers_n', facts.get('弟兄数')))
    wife_alive = b(facts.get('wife_alive', facts.get('有妻')))
    child_sex = facts.get('child_sex', facts.get('子女性别'))
    child_count = _int_or_none(facts.get('child_count', facts.get('子女数')))
    child_sex_count = None
    if child_sex in ('子', '女') and child_count is not None:
        child_sex_count = (child_sex, child_count)
    elif child_sex in ('子', '女'):
        child_sex_count = (child_sex, None)
    sons_n = _int_or_none(facts.get('sons_n', facts.get('儿子数')))
    daughters_n = _int_or_none(facts.get('daughters_n', facts.get('女儿数')))
    # 双栏缺省时回退单性别 child_sex_count
    if sons_n is None and daughters_n is None and child_sex_count:
        cs, cc = child_sex_count
        if cs == '子':
            sons_n = cc
        else:
            daughters_n = cc
    return {
        'fu_sang': fu_sang, 'mu_sang': mu_sang, 'brothers_n': brothers_n,
        'wife_alive': wife_alive, 'child_sex_count': child_sex_count,
        'sons_n': sons_n, 'daughters_n': daughters_n,
    }


def run_kaoke(pillars, gender, facts):
    """考刻定分闭环编排。

    pillars：四柱 [年, 月, 日, 时]，各为「天干+地支」两字。
    gender：'m'/'f'（本模块的刻分表不分性别，仅透传）。
    facts：结构化事实（见 parse_kaoke_facts）。

    返回 dict：
      base / hour_zhi / ke_articles（8 刻候选，含格局与 score）/
      locked_ke（并列最高分刻的列表）/ ke_tie /
      fen_rows（15 分候选，含格局与 score）/
      locked_fen（并列最高分分列表）/ fen_tie
    """
    year, month, day, hour = pillars
    base = jifen_base(year, month, day, hour)
    hour_zhi = hour[1]

    f = parse_kaoke_facts(facts)

    ke_rows = match_ke(hour_zhi, fu_sang=f['fu_sang'],
                       mu_sang=f['mu_sang'], brothers_n=f['brothers_n'])
    articles = dict(ba_ke_articles(base))
    ke_articles = []
    for c in ke_rows:
        ke_articles.append({
            'ke': c['ke'], 'n': articles[c['ke']],
            'par': c['par'], 'bro': c['bro'], 'yao': c['yao'],
            'score': c['score'], 'detail': c['detail'],
        })
    top = ke_articles[0]['score'] if ke_articles else None
    locked_ke = [k for k in ke_articles if k['score'] == top] if top is not None else []
    ke_tie = len(locked_ke) > 1

    fen_rows = match_fen(hour_zhi, wife_alive=f['wife_alive'],
                         child_sex_count=f['child_sex_count'], gender=gender,
                         sons_n=f['sons_n'], daughters_n=f['daughters_n'])
    ftop = fen_rows[0]['score'] if fen_rows else None
    locked_fen = [x for x in fen_rows if x['score'] == ftop] if ftop is not None else []
    fen_tie = len(locked_fen) > 1

    return {
        'bazi': pillars, 'gender': gender,
        'base': base, 'hour_zhi': hour_zhi,
        'facts': f,
        'ke_articles': ke_articles,
        'locked_ke': locked_ke, 'ke_tie': ke_tie,
        'fen_rows': fen_rows,
        'locked_fen': locked_fen, 'fen_tie': fen_tie,
        'uncertainty': KE_UNCERTAINTY.get((hour_zhi, locked_ke[0]['ke'] if locked_ke and not ke_tie else None)) if locked_ke else None,
    }


# ----------------------------------------------------------------------
# 六、考刻问题生成器
# ----------------------------------------------------------------------

# 软锚点维度 → 类别码（与 tieban.py FACT_CAT 一致）
SOFT_DIM_CAT = {'性情': 5, '事业': 6, '财运': 9, '健康': 10}


def _q(round_, dim, cat, key, text, purpose, optional=False, options=None):
    """构造一条考刻问题。key 为事实键（硬锚点用结构化键、软锚点用中文维度词）。"""
    return {'round': round_, 'dim': dim, 'cat': cat, 'key': key,
            'text': text, 'purpose': purpose, 'optional': optional,
            'options': options or []}


def generate_questions(pillars, gender, facts=None):
    """考刻问题生成器：确定性生成两轮提问清单（硬锚点→软锚点）。

    pillars：四柱 [年, 月, 日, 时]，各为「天干+地支」两字。
    gender：'m'/'f'。
    facts：已答事实（见 parse_kaoke_facts），部分/空均可；已答维度自动跳过。

    返回 {'hour_zhi', 'gender', 'facts', 'rounds':[{'name','questions'}]}。
    每轮 ≤4 条；硬锚点问题严格映射到 run_kaoke 所需结构化事实键，
    软锚点 optional=True（答不上回退默认，不影响出命书）。
    """
    f = parse_kaoke_facts(facts or {})
    hour_zhi = pillars[3][1]

    hard = []
    # 父母 → 锁「八刻定父母弟兄表」父母态（六态）
    if f['fu_sang'] is None and f['mu_sang'] is None:
        hard.append(_q(1, '父母', 1, ('fu_sang', 'mu_sang'),
                       '父亲、母亲都健在吗？是否有父/母一方已过世？',
                       '锁「八刻定父母弟兄表」父母态（父母寿/丧/父丧母寿/母丧父寿等）',
                       options=['父母双全', '父已故·母健在', '母已故·父健在', '父母双亡']))
    else:
        if f['fu_sang'] is None:
            hard.append(_q(1, '父母', 1, 'fu_sang', '那父亲是否健在？',
                           '补全父母态六态之一', options=['健在', '已过世']))
        if f['mu_sang'] is None:
            hard.append(_q(1, '父母', 1, 'mu_sang', '母亲是否健在？',
                           '补全父母态六态之一', options=['健在', '已过世']))

    # 手足 → 锁「八刻定父母弟兄表」手足格
    if f['brothers_n'] is None:
        hard.append(_q(1, '手足', 2, 'brothers_n',
                       '同胞手足共几位（兄弟+姐妹，不含您自己）？排行第几？',
                       '锁「八刻定父母弟兄表」手足格（无/少/二三/三四/四五/多）',
                       options=['无（独子）', '少（1-2位）', '二三（3位）', '四五（4-5位）', '多（6位以上）']))

    # 婚姻 → 锁「每刻十五分定妻子表」妻态/夫态
    if f['wife_alive'] is None:
        if gender != 'f':
            text = '是否已成家？妻子是否健在（有无纳妾/续弦/丧偶）？'
            opt = ['未婚/无偶', '有妻健在', '妻子已故/丧偶', '续弦/纳妾']
        else:
            text = '是否已成家？丈夫是否健在？'
            opt = ['未婚/无偶', '有夫健在', '丈夫已故/丧夫', '再嫁/续弦']
        hard.append(_q(1, '婚姻', 3, 'wife_alive', text,
                       '锁「每刻十五分定妻子表」妻态/夫态', options=opt))

    # 子女 → 锁「每刻十五分定妻子表」子态
    child_answered = (f['child_sex_count'] is not None
                      or f['sons_n'] is not None or f['daughters_n'] is not None)
    if not child_answered:
        hard.append(_q(1, '子女', 4, ('child_sex', 'child_count'),
                       '有几个孩子？几男几女？',
                       '锁「每刻十五分定妻子表」子态（无子/一二三四五子/多子/二女/多女）',
                       options=['无子女', '有子', '有女无子', '有儿有女']))

    soft = [
        _q(2, '性情', 5, '性情', '性格偏温和，还是刚强/急躁？',
           '分类条文·性情禀赋', optional=True,
           options=['温和内向', '刚强急躁', '随和中庸']),
        _q(2, '事业', 6, '事业', '做什么行当？（经商/从政/文职/武职/技艺）',
           '分类条文·事业功名', optional=True,
           options=['经商', '从政', '文职', '武职', '技艺/专业']),
        _q(2, '财运', 9, '财运', '家境大致如何？（小康/富足/贫寒/早年积累）',
           '分类条文·财帛家业', optional=True,
           options=['小康', '富足', '贫寒', '早年积累']),
        _q(2, '健康', 10, '健康', '身体有无明显伤病？或既往大病史？',
           '分类条文·康宁寿元', optional=True,
           options=['无明显伤病', '有旧疾/慢性病', '曾有大病/手术']),
    ]

    return {
        'hour_zhi': hour_zhi, 'gender': gender, 'facts': f,
        'rounds': [
            {'name': '第一轮 · 硬锚点（六亲，锁刻锁分）', 'questions': hard},
            {'name': '第二轮 · 软锚点（语义，可回退默认）', 'questions': soft},
        ],
    }


def disambiguate(hour_zhi, locked_ke=None, locked_fen=None):
    """破并列追问：考刻/考分出现多刻/多分并列时，比较并列项格局差异，
    生成能进一步区分的细化问题（对应 SKILL.md「并列与再问」环节）。"""
    qs = []
    if locked_ke and len(locked_ke) > 1:
        pars = sorted({k['par'] for k in locked_ke})
        bros = sorted({k['bro'] for k in locked_ke})
        if len(pars) > 1:
            qs.append(_q(3, '父母', 1, ('fu_sang', 'mu_sang'),
                         '换个问法：父亲和母亲，具体是哪一位先过世？（或都健在）',
                         '破除父母态并列' + ' / '.join(pars), options=pars))
        if len(bros) > 1:
            qs.append(_q(3, '手足', 2, 'brothers_n',
                         '再确认：同胞手足到底几位（兄弟+姐妹）？',
                         '破除手足格并列' + ' / '.join(bros), options=bros))
    if locked_fen and len(locked_fen) > 1:
        qis = sorted({x['qi'] for x in locked_fen})
        zis = sorted({x['zi'] for x in locked_fen})
        if len(qis) > 1:
            qs.append(_q(3, '婚姻', 3, 'wife_alive',
                         '再确认：配偶是否有纳妾/续弦/丧偶等情况？',
                         '破除妻态并列' + ' / '.join(qis), options=qis))
        if len(zis) > 1:
            qs.append(_q(3, '子女', 4, ('child_sex', 'child_count'),
                         '再确认：儿子到底几个？有没有男丁？',
                         '破除子态并列' + ' / '.join(zis), options=zis))
    return qs


def render_questions(plan, extra_disamb=None):
    """把问题清单渲染成可读文本（供交互引用与调试）。"""
    lines = ['【考刻提问 · 时柱 ' + plan['hour_zhi'] + '】']
    for r in plan['rounds']:
        lines.append('')
        lines.append('== ' + r['name'] + ' ==')
        if not r['questions']:
            lines.append('  （本轮已无待问维度）')
        for q in r['questions']:
            tag = '〔可选·答不上可跳过〕' if q['optional'] else ''
            lines.append('  · [%s/%d] %s  %s' % (q['dim'], q['cat'], q['text'], tag))
            lines.append('        目的：' + q['purpose'])
            if q['options']:
                lines.append('        备选：' + ' / '.join(q['options']))
    if extra_disamb:
        lines.append('')
        lines.append('== 第三轮 · 破并列追问 ==')
        for q in extra_disamb:
            lines.append('  · [%s/%d] %s' % (q['dim'], q['cat'], q['text']))
            lines.append('        目的：' + q['purpose'])
            if q['options']:
                lines.append('        备选：' + ' / '.join(q['options']))
    return '\n'.join(lines)


# ----------------------------------------------------------------------
# 七、考刻闭环状态机
# ----------------------------------------------------------------------

def _facts_short(f):
    """把归一化事实渲染成短串（未答维度省略）。"""
    bits = []
    if f['fu_sang'] is not None or f['mu_sang'] is not None:
        fu = '丧' if f['fu_sang'] else ('寿' if f['fu_sang'] is False else '?')
        mu = '丧' if f['mu_sang'] else ('寿' if f['mu_sang'] is False else '?')
        bits.append('父%s·母%s' % (fu, mu))
    if f['brothers_n'] is not None:
        bits.append('同胞%s位' % f['brothers_n'])
    if f['wife_alive'] is not None:
        bits.append('有偶' if f['wife_alive'] else '无偶/丧偶')
    if f['sons_n'] is not None or f['daughters_n'] is not None:
        bits.append('%d子%d女' % (f['sons_n'] or 0, f['daughters_n'] or 0))
    return ' · '.join(bits) if bits else '（未提供）'


def _lock_summary(result, ke_tie, fen_tie):
    """收敛后的锁刻锁分结论文本。"""
    parts = []
    if result and result['locked_ke']:
        s = '多刻并列' if ke_tie else '锁刻'
        parts.append('%s：%s' % (s, '、'.join(
            '%d刻(%s·手足%s)' % (k['ke'], k['par'], k['bro']) for k in result['locked_ke'])))
    if result and result['locked_fen']:
        s = '多分并列' if fen_tie else '锁分'
        parts.append('%s：%s' % (s, '、'.join(
            '%d分(妻=%s·子=%s)' % (x['fen'], x['qi'], x['zi']) for x in result['locked_fen'])))
    return '；'.join(parts) if parts else '（事实不足，未能锁定刻分）'


def kaoke_circuit(pillars, gender, facts=None):
    """考刻交互闭环状态机：AI 每收一轮答案调用一次，得「当前该问 + 锁定 + 是否收敛」。

    返回 dict：
      hour_zhi / facts（归一化） /
      questions（当前该问：硬锚点剩余 → 破并列追问）/ soft（软锚点，可回退）/
      result（考刻结果，硬锚点齐全时） / ke_tie / fen_tie / locked_ke / locked_fen /
      done（是否收敛：硬锚点无剩余且无未决并列）/
      summary（done 时的锁刻锁分结论）
    """
    plan = generate_questions(pillars, gender, facts)
    f = parse_kaoke_facts(facts or {})
    hour_zhi = plan['hour_zhi']
    hard_qs = plan['rounds'][0]['questions']
    soft_qs = plan['rounds'][1]['questions']

    result = None
    locked_ke, locked_fen = [], []
    ke_tie = fen_tie = False
    done = False

    if hard_qs:
        questions = hard_qs  # 仍有硬锚点未答，继续问
    else:
        result = run_kaoke(pillars, gender, facts)
        ke_tie, fen_tie = result['ke_tie'], result['fen_tie']
        locked_ke, locked_fen = result['locked_ke'], result['locked_fen']
        if ke_tie or fen_tie:
            dis = disambiguate(hour_zhi, locked_ke, locked_fen)
            if dis:
                questions = dis
            else:
                questions = []
                done = True  # 并列但无可区分差异，如实保留
        else:
            questions = []
            done = True

    return {
        'hour_zhi': hour_zhi, 'gender': gender, 'facts': f,
        'questions': questions, 'soft': soft_qs,
        'result': result, 'ke_tie': ke_tie, 'fen_tie': fen_tie,
        'locked_ke': locked_ke, 'locked_fen': locked_fen,
        'done': done, 'summary': _lock_summary(result, ke_tie, fen_tie) if done else '',
    }


def render_circuit(st):
    """把 kaoke_circuit 状态渲染成可读文本（供交互引用）。"""
    lines = ['【考刻闭环 · 时柱 %s】' % st['hour_zhi']]
    lines.append('已答事实：%s' % _facts_short(st['facts']))
    if st['done']:
        lines.append('→ 已收敛：%s' % (st['summary'] or '（无可锁定结论）'))
        if st['soft']:
            lines.append('→ 软锚点（可选，答不全不影响）：')
            for q in st['soft']:
                lines.append('    · [%s/%d] %s' % (q['dim'], q['cat'], q['text']))
    else:
        lines.append('→ 本轮待问 %d 条：' % len(st['questions']))
        for q in st['questions']:
            lines.append('    · [%s/%d] %s' % (q['dim'], q['cat'], q['text']))
            if q['options']:
                lines.append('        备选：%s' % ' / '.join(q['options']))
    return '\n'.join(lines)


# ----------------------------------------------------------------------
# 八、独立测试入口
# ----------------------------------------------------------------------

if __name__ == '__main__':
    base = jifen_base('甲子', '乙亥', '庚戌', '癸未')
    print('基数 =', base)
    print('八刻条文号 =', [(k, n) for k, n in ba_ke_articles(base)])
    print()
    # 案例：时柱癸未 → 未时；父2014卒(父丧)、母健在(母寿)、一个姐姐(弟兄少)
    print('── 未时考刻（父丧母寿 · 弟兄少）──')
    for c in match_ke('未', fu_sang=True, mu_sang=False, brothers_n=1):
        print('  %d刻 %s/%s/%s score=%d %s' % (c['ke'], c['par'], c['bro'], c['yao'], c['score'], '、'.join(c['detail'])))
    print()
    print('── 未时考分（有妻 · 三女）──')
    for c in match_fen('未', wife_alive=True, child_sex_count=('女', 3)):
        print('  %d分 %s/%s/%s score=%d %s' % (c['fen'], c['qi'], c['zi'], c['fu'], c['score'], '、'.join(c['detail'])))

    print()
    print('=' * 60)
    print('考刻问题生成器演示')
    print('=' * 60)

    pillars = ['庚寅', '甲申', '丙午', '甲午']  # 时柱甲午 → 午时

    print('\n① 空事实（第一问，全量两轮）：')
    plan = generate_questions(pillars, 'm')
    print(render_questions(plan))

    print('\n② 已答【父丧母寿 · 弟兄1位】后再问（婚姻/子女未被答）：')
    plan2 = generate_questions(pillars, 'm', {'父丧': True, '母丧': False, 'brothers_n': 1})
    print(render_questions(plan2))

    print('\n③ 全事实考刻 + 破并列追问：')
    facts = {'fu_sang': True, 'mu_sang': False, 'brothers_n': 1,
             'wife_alive': True, 'child_sex': '女', 'child_count': 3}
    r = run_kaoke(pillars, 'm', facts)
    print('  锁定刻（并列?%s）：' % r['ke_tie'], [(k['ke'], k['par'], k['bro']) for k in r['locked_ke']])
    print('  锁定分（并列?%s）：' % r['fen_tie'], [(x['fen'], x['qi'], x['zi']) for x in r['locked_fen']])
    if r['ke_tie'] or r['fen_tie']:
        dis = disambiguate('午', r['locked_ke'], r['locked_fen'])
        if dis:
            print(render_questions({'hour_zhi': '午', 'gender': 'm', 'facts': r['facts'], 'rounds': []}, extra_disamb=dis))
        else:
            print('  → 存在并列，但并列项在可问维度（父母/弟兄/妻/子）上格局相同，')
            print('    无法再以细节追问区分（例：夫态对男命不计分）。如实保留并列、不强行取唯一。')
    else:
        print('  → 无并列，刻分已唯一锁定，无需再问。')