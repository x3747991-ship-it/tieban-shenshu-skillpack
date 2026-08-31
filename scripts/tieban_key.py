#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
铁板神数 · 大运 / 流年起数（据《张椿来·铁版神数》乾集原书）

依据节次（乾集 §2/§6/§26/§27，演算法式 §5）：
- §2  排大运：大运十年一变，以月柱干支为起点，按年干阴阳 + 性别定顺/逆推。
- §6  地支取数诀（河洛）：亥子一六、寅卯三八、巳午二七、申酉四九、辰戌丑未五十。
- §5  大运数演算法：大运以月柱起，配河洛地支数（生数.成数），十年一步、起止岁。
- §26 大运取数诀：「甲己乙庚四，丙辛数为六；丁壬戊癸三，胜算九十六。」
        「月日时年，春夏秋冬；亥子一六，干支合数。」——大运取数以月柱为首。
- §27 流年取数诀：「须知流年数，还看年干支；流年大运同，一样甲己四。」

勘正（相对此前「破解钥匙·加96/48递推」脚本，该脚本已删除）：
1. 「九十六」出自 §18「八刻分命妙无穷，九十六局见天工」= 12 时辰 × 8 刻 = 96 局，
   指刻分体系，不是「每步 +96」的递推步长。
2. 「四十八」出自 §14「变知六八止」= 48 干支纳数，不是「每步 +48」的递推步长。
3. 早前实现把上述两数误作算术递推、并以「一步一条文号」硬索引条文库，属误读，已废弃。

未转录边界（诚实自陈）：
§5「以月日时年起数序 + 大运数序」合出条文号的算式，已由《破解钥匙》「千位=月柱天干数
+大运天干数、百位=日柱天干数、十位=时柱天干数、个位=年柱天干数+大运支数」补齐，并经
书版命例（庚寅 甲申 丙午 甲午·男·大运乙酉 → 8648；丙戌 → 10649；辛卯 → 10647 等）逐位
硬证，故此环节已可证。§27 流年取数「流年干支代替年干支、加流年支数」同法，但破解钥匙
未逐字说明流年千位是否仍叠加大运干数、且原书无流年命例，其「千位保持大运干」为据破解
钥匙文字的推断、如实标注。天干配数另有跨传承分歧：破解钥匙自成一表「五合五行数」（甲己
合土=1、乙庚合金=2、丙辛合水=5、丁壬合木=3、戊癸合火=4），与张椿来 §26「甲己乙庚四、
丙辛六、丁壬戊癸三」不同；本脚本采张椿来 §26 配数（经 8648 命例逐位硬证，破解钥匙甲己=1
则千位得 3、与 8648 不符；且其 §27 口诀「一样甲己四」已作甲己=四、自相矛盾），不采用破解
钥匙五合数，如实标注。条文号由 scripts/yansuan.py 的 dayun_shuxu / liunian_shuxu 统一
计算，本脚本不重复实现、不硬造条文号。
"""
import argparse
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)
import yansuan

GAN = '甲乙丙丁戊己庚辛壬癸'
ZHI = '子丑寅卯辰巳午未申酉戌亥'
YANG_GAN = set('甲丙戊庚壬')

# §26 天干合化配数：甲己乙庚四、丙辛六、丁壬戊癸三
GAN_HE = {
    '甲': 4, '己': 4, '乙': 4, '庚': 4,
    '丙': 6, '辛': 6,
    '丁': 3, '壬': 3, '戊': 3, '癸': 3,
}

# §6 河洛地支配数（生数.成数）
HELUO_ZHI = {
    '亥': (1, 6), '子': (1, 6),
    '寅': (3, 8), '卯': (3, 8),
    '巳': (2, 7), '午': (2, 7),
    '申': (4, 9), '酉': (4, 9),
    '辰': (5, 10), '戌': (5, 10), '丑': (5, 10), '未': (5, 10),
}


def parse_pillar(s, label):
    s = (s or '').strip()
    if len(s) != 2 or s[0] not in GAN or s[1] not in ZHI:
        raise ValueError(f'{label}柱「{s}」应为天干+地支两字')
    return s


def dayun(pillars, gender, n=8):
    """§2 排大运：自月柱顺/逆排 n 步大运干支（十年一步）。
    顺逆：阳年男 / 阴年女顺行，阴年男 / 阳年女逆行。
    起运岁数须按 §2「顺逆推天数之和 ÷ 3」另算（需精确出生日期与交节），本函数不推。"""
    forward = (pillars[0][0] in YANG_GAN) == (gender == '男')
    step = 1 if forward else -1
    gi = GAN.index(pillars[1][0])
    zi = ZHI.index(pillars[1][1])
    out = []
    for _ in range(n):
        gi = (gi + step) % 10
        zi = (zi + step) % 12
        out.append(GAN[gi] + ZHI[zi])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description='铁板神数·大运/流年起数（乾集原书）')
    ap.add_argument('--year', required=True)
    ap.add_argument('--month', required=True)
    ap.add_argument('--day', required=True)
    ap.add_argument('--hour', required=True)
    ap.add_argument('--gender', required=True, choices=['男', '女'])
    ap.add_argument('--n', type=int, default=8, help='大运步数')
    args = ap.parse_args(argv)

    pillars = [parse_pillar(args.year, '年'), parse_pillar(args.month, '月'),
               parse_pillar(args.day, '日'), parse_pillar(args.hour, '时')]
    labels = '年月日时'

    print('═' * 60)
    print('   铁板神数 · 大运 / 流年起数（据乾集 §2/§6/§26/§27）')
    print('═' * 60)
    print(f'【四柱】{" ".join(pillars)}（{args.gender}命）')

    print()
    print('【天干合化数 §26】甲己乙庚=4，丙辛=6，丁壬戊癸=3')
    for lb, p in zip(labels, pillars):
        print(f'   {lb}柱 {p}：{p[0]} = {GAN_HE[p[0]]}')

    print()
    print('【地支河洛数 §6】亥子一六、寅卯三八、巳午二七、申酉四九、辰戌丑未五十')
    for lb, p in zip(labels, pillars):
        a, b = HELUO_ZHI[p[1]]
        print(f'   {lb}柱 {p}：{p[1]} = {a}.{b}')

    print()
    print(f'【排大运 §2/§5】（自月柱{args.month}起，十年一步）')
    ver = '顺行' if (pillars[0][0] in YANG_GAN) == (args.gender == '男') else '逆行'
    print(f'   年干 {pillars[0][0]}（{"阳" if pillars[0][0] in YANG_GAN else "阴"}）'
          f' + {args.gender}命 → {ver}')
    for i, gz in enumerate(dayun(pillars, args.gender, args.n), 1):
        g, z = gz[0], gz[1]
        a, b = HELUO_ZHI[z]
        ds = yansuan.dayun_shuxu(pillars, gz)
        wide = '（千位和≥10·进位五位数）' if ds['wide'] else ''
        print(f'   第{i:>2}步  {gz}   天干合化[{g}]={GAN_HE[g]:>2}   '
              f'地支河洛[{z}]={a}.{b}   大运数序〔{ds["n"]}〕{wide}')

    print()
    print('【边界】大运数序算式已可证（破解钥匙 + 书版 8648/10649/10647 命例硬证）；')
    print('       流年取数（§27）同法、千位保持大运干属推断（原书无流年命例），如实标注。')


if __name__ == '__main__':
    try:
        main()
    except ValueError as e:
        print(f'[输入错误] {e}')
        raise SystemExit(1)