#!/usr/bin/env python3
"""Wild Matchups — vahşi hayvanların gerçek istatistiklerle karşılaştırması ("on paper", kavga sahnesi YOK) (2026-10-17).

Neden: Paw Rivals'ın patlayan "iki taraf, izleyici taraf tutar" mekaniği; ama format kendine ait (istatistik turları,
turnuva braketi) — evcil hayvan tepkisi değil (Paw), nesne boyutu değil (Bigger). Görsel kimlik: spor yayını
(siyah zemin, kırmızı/mavi köşe, skor tabelası), Teko + Rajdhani, PhyloPic silüetleri (CC0/PDM; CC BY ise atıf),
ses en-US-RogerNeural. Şiddet/kan yok; sonuç "kağıt üstünde" (istatistik turları), gerçek dövüş iddiası yok.

Short kurguları (12): tape, bracket4, poll, top5, higherlower, truefalse, ratio, race, scale, bite, underdog, guessstat
Uzun (16:9): 16 hayvanlık turnuva (~6-8 dk).

  python wild.py --dry-run [--kurgu tape] [--long]
  python wild.py --auto          # günde N Short (+ haftada 3 uzun), publishAt ile ABD saatine
"""
import asyncio
import csv
import json
import math
import os
import random
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SIL = HERE / 'assets' / 'sil'
OUT = HERE / 'out'
LOG = HERE / 'records' / 'published.csv'
FPS = 30
BG, BG2, PANEL, INK, DIM, RED, BLUE, GOLD, WHITE = (12, 12, 16), (24, 24, 32), (34, 34, 44), (240, 240, 245), (150, 150, 165), (230, 50, 60), (40, 120, 255), (255, 200, 40), (255, 255, 255)
TEKO, RAJ, RAJM = str(HERE / 'fonts' / 'Teko-SemiBold.ttf'), str(HERE / 'fonts' / 'Rajdhani-Bold.ttf'), str(HERE / 'fonts' / 'Rajdhani-Medium.ttf')
VOICE = os.environ.get('WM_VOICE', 'en-US-RogerNeural')
DRY = '--dry-run' in sys.argv
CREDITS = json.loads((SIL / 'credits.json').read_text())

# id: (EKRAN, konuşma, ortam, ağırlık kg, hız km/sa, ısırma psi|None, vücut uzunluğu m (baş+gövde; insan için boy))  — tipik yetişkin erkek; yaygın kaynak değerleri (tahmin)
A = {
    'lion': ('LION', 'the lion', 'land', 190, 80, 650, 2.0), 'tiger': ('TIGER', 'the tiger', 'land', 220, 65, 1050, 2.5),
    'jaguar': ('JAGUAR', 'the jaguar', 'land', 100, 80, 1500, 1.7), 'leopard': ('LEOPARD', 'the leopard', 'land', 60, 58, 300, 1.5),
    'cheetah': ('CHEETAH', 'the cheetah', 'land', 54, 104, 475, 1.3), 'puma': ('COUGAR', 'the cougar', 'land', 60, 80, None, 1.4),
    'grizzly': ('GRIZZLY BEAR', 'the grizzly bear', 'land', 300, 56, 1160, 2.2), 'polarbear': ('POLAR BEAR', 'the polar bear', 'land', 450, 40, 1200, 2.4),
    'gorilla': ('GORILLA', 'the gorilla', 'land', 160, 40, 1300, 1.7), 'chimp': ('CHIMPANZEE', 'the chimpanzee', 'land', 60, 40, None, 0.9),
    'hippo': ('HIPPO', 'the hippo', 'land', 1500, 30, 1800, 3.5), 'elephant': ('ELEPHANT', 'the African elephant', 'land', 6000, 40, None, 6.0),
    'rhino': ('RHINO', 'the white rhino', 'land', 2300, 50, None, 3.8), 'giraffe': ('GIRAFFE', 'the giraffe', 'land', 1200, 60, None, 4.3),
    'zebra': ('ZEBRA', 'the zebra', 'land', 380, 65, None, 2.4), 'wolf': ('GRAY WOLF', 'the gray wolf', 'land', 45, 60, 400, 1.4),
    'hyena': ('HYENA', 'the spotted hyena', 'land', 60, 60, 1100, 1.4), 'wilddog': ('WILD DOG', 'the African wild dog', 'land', 25, 66, 317, 1.0),
    'saltie': ('SALTWATER CROC', 'the saltwater crocodile', 'land', 500, 18, 3700, 5.0), 'komodo': ('KOMODO DRAGON', 'the Komodo dragon', 'land', 80, 20, None, 2.6),
    'ostrich': ('OSTRICH', 'the ostrich', 'land', 115, 70, None, 2.0), 'moose': ('MOOSE', 'the moose', 'land', 550, 56, None, 2.8),
    'bison': ('BISON', 'the American bison', 'land', 900, 56, None, 3.0), 'buffalo': ('CAPE BUFFALO', 'the Cape buffalo', 'land', 750, 57, None, 3.0),
    'horse': ('HORSE', 'the horse', 'land', 500, 88, None, 2.4), 'human': ('HUMAN', 'a human', 'land', 75, 44.7, 162, 1.75),
    'wolverine': ('WOLVERINE', 'the wolverine', 'land', 15, 48, None, 0.9), 'honeybadger': ('HONEY BADGER', 'the honey badger', 'land', 10, 30, None, 0.8),
    'gwshark': ('GREAT WHITE', 'the great white shark', 'sea', 1100, 56, 4000, 4.5), 'orca': ('ORCA', 'the orca', 'sea', 5500, 56, None, 7.0),
    'bullshark': ('BULL SHARK', 'the bull shark', 'sea', 230, 40, None, 2.4),
}
A = {k: v for k, v in A.items() if (SIL / f'{k}.png').exists()}
STAT = {'speed': ('TOP SPEED', 4, 'km/h'), 'weight': ('WEIGHT', 3, 'kg'), 'bite': ('BITE FORCE', 5, 'psi'), 'length': ('BODY LENGTH', 6, 'm')}
SOURCE = ('Body length is typical head-and-body length (height for humans). Stats are typical adult figures and commonly cited estimates (National Geographic, Smithsonian, zoo fact sheets and published '
          'bite-force studies); real animals vary. "On paper" compares numbers only — no real fight is shown or claimed.')
KURGU = ['tape', 'bracket4', 'poll', 'top5', 'higherlower', 'truefalse', 'ratio', 'race', 'scale', 'bite', 'underdog', 'guessstat',
         'mystery', 'shadow', 'oddone', 'tierlist', 'threeway', 'kinghill', 'teamup', 'outrun', 'quickfire', 'weightclass', 'closest']


def log(m): print(m, flush=True)
def NM(k): return A[k][0]
def nm(k): return A[k][1]
def cap(s): return s[0].upper() + s[1:]
def sv(k, s): return A[k][STAT[s][1]]
def fmt(k, s):
    v = sv(k, s)
    return '—' if v is None else (f'{v:,.0f} KG' if s == 'weight' else f'{v:g} KM/H' if s == 'speed' else f'{v:g} M' if s == 'length' else f'{v:,} PSI')
def say_stat(k, s):
    v = sv(k, s)
    return {'weight': f'{v:,.0f} kilograms', 'speed': f'{v:g} kilometers per hour', 'bite': f'{v:,} PSI', 'length': f'{v:g} meters'}[s]
def TN(k): return ' '.join(w.capitalize() for w in NM(k).split())


IRREG = {'wolf': 'wolves', 'human': 'humans', 'moose': 'moose', 'bison': 'bison', 'buffalo': 'buffalo', 'ostrich': 'ostriches', 'great white': 'great whites'}
def PL(k):
    n = NM(k).lower()
    for a_, b_ in IRREG.items():
        if n.endswith(a_): return n[: -len(a_)] + b_
    return n + 's'


def same_env(*ks): return len({A[k][2] for k in ks}) == 1


def tape(a, b):
    """Turlar: her istatistik bir tur (ikisinde de varsa). Eşitlikte ağırlık bozar. Döner: [(stat, kazanan)], şampiyon."""
    rounds = []
    for s in ('speed', 'weight', 'bite', 'length'):
        va, vb = sv(a, s), sv(b, s)
        if va is None or vb is None or va == vb: continue
        rounds.append((s, a if va > vb else b))
    wa = sum(w == a for _, w in rounds); wb = sum(w == b for _, w in rounds)
    champ = a if wa > wb else b if wb > wa else (a if sv(a, 'weight') > sv(b, 'weight') else b)
    return rounds, champ


# ---------------------------------------------------------------- konu
def done():
    if not LOG.exists(): return set(), []
    with LOG.open(encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    return {r['topic_id'] for r in rows}, rows


def tkey(t):
    return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', re.sub(r'#\w+', ' ', t.lower())).split())


def key_for(k, rnd):
    L = list(A)
    if k in ('tape', 'poll', 'higherlower', 'underdog'):
        a, b = sorted(rnd.sample(L, 2))
        if not same_env(a, b): return None
        if k == 'underdog':
            rounds, champ = tape(a, b); small = min((a, b), key=lambda x: sv(x, 'weight'))
            if not any(w == small for _, w in rounds) or sv(a, 'weight') == sv(b, 'weight'): return None
        if k == 'higherlower':
            s = rnd.choice(['speed', 'weight', 'bite', 'length'])
            return [k, a, b, s] if sv(a, s) and sv(b, s) and sv(a, s) != sv(b, s) else None
        if k == 'tape' and len(tape(a, b)[0]) < 2: return None
        return [k, a, b]
    if k == 'bracket4':
        env = rnd.choice(['land', 'land', 'land', 'sea'])
        pool = [x for x in L if A[x][2] == env]
        return [k] + sorted(rnd.sample(pool, 4)) if len(pool) >= 4 else None
    if k in ('top5', 'guessstat'):
        s = rnd.choice(['speed', 'weight', 'bite', 'length']); pool = [x for x in L if sv(x, s)]
        if k == 'top5':
            ids = sorted(rnd.sample(pool, min(len(pool), 7)), key=lambda x: sv(x, s))[-5:]
            return [k, s] + sorted(ids)
        return [k, s, rnd.choice(pool)]
    if k == 'truefalse':
        a, b = rnd.sample(L, 2); s = rnd.choice(['speed', 'weight', 'bite', 'length']); f = rnd.choice([2, 3, 5])
        return [k, a, b, s, f] if sv(a, s) and sv(b, s) and same_env(a, b) and sv(a, s) > sv(b, s) else None
    if k in ('ratio', 'scale'):
        a, b = rnd.sample(L, 2)
        return [k, a, b] if sv(a, 'weight') > 2 * sv(b, 'weight') else None
    if k == 'race':
        a, b = sorted(rnd.sample(L, 2))
        return [k, a, b] if same_env(a, b) and abs(sv(a, 'speed') - sv(b, 'speed')) >= 5 else None
    if k in ('mystery', 'shadow'):
        x = rnd.choice(L); return [k, x] if k == 'shadow' or sum(sv(x, st) is not None for st in STAT) >= 2 else None
    if k == 'oddone':
        st = rnd.choice(['speed', 'weight', 'bite', 'length']); env = rnd.choice(['land', 'land', 'sea'])
        pool = [x for x in L if sv(x, st) and A[x][2] == env]
        if len(pool) < 4: return None
        ids = rnd.sample(pool, 4)
        return [k, st] + sorted(ids) if len({sv(x, st) for x in ids}) == 4 else None
    if k == 'tierlist':
        return [k] + sorted(rnd.sample([x for x in L if A[x][2] == 'land'], 6))
    if k == 'threeway':
        ids = sorted(rnd.sample([x for x in L if A[x][2] == 'land'], 3)); return [k] + ids
    if k == 'kinghill':
        ids = rnd.sample([x for x in L if A[x][2] == 'land'], 4); return [k] + ids
    if k == 'teamup':
        a, b = rnd.sample([x for x in L if A[x][2] == 'land'], 2)
        return [k, a, b] if 1.3 < sv(b, 'weight') / sv(a, 'weight') < 6 else None
    if k == 'outrun':
        ref = rnd.choice(['jog', 'sprint']); ids = sorted(rnd.sample([x for x in L if A[x][2] == 'land' and x != 'human'], 6))
        lim = 24 if ref == 'jog' else 44.7
        return [k, ref] + ids if 1 <= sum(sv(x, 'speed') < lim for x in ids) <= 4 else None
    if k == 'quickfire':
        qs = []
        for _ in range(3):
            a, b = rnd.sample(L, 2); st = rnd.choice(['speed', 'weight', 'bite', 'length'])
            if not (sv(a, st) and sv(b, st)) or sv(a, st) == sv(b, st): return None
            qs += [a, b, st]
        return [k] + qs
    if k == 'weightclass':
        x = rnd.choice(L); near = [y for y in L if y != x and 0.75 <= sv(y, 'weight') / sv(x, 'weight') <= 1.33]
        return [k, x] if len(near) >= 2 else None
    if k == 'closest':
        x = rnd.choice(L); st = rnd.choice(['speed', 'weight', 'bite', 'length'])
        return [k, x, st] if sv(x, st) and sum(1 for y in L if y != x and sv(y, st)) >= 3 else None
    if k == 'bite':
        a, b = sorted(rnd.sample([x for x in L if sv(x, 'bite')], 2)); return [k, a, b]


def pick(rnd, kurgu=None):
    seen, rows = done(); last = [r['topic_id'].split(':')[1] for r in rows[-4:] if r['topic_id'].startswith('wm:')]
    for _ in range(4000):
        k = kurgu or rnd.choice([x for x in KURGU if x not in last] or KURGU)
        for _ in range(60):
            key = key_for(k, rnd)
            if key is None: continue
            tid = 'wm:' + ':'.join(str(x) for x in key)
            animals = {x for x in key[1:] if x in A}
            if len(animals) <= 3 and any(animals and animals <= set(r['topic_id'].split(':')) for r in rows[-30:]):
                continue                                  # aynı hayvan(lar) son 30 videoda zaten işlendi
            if tid not in seen: return key, tid
    raise RuntimeError('yeni konu kalmadı')


def C(rnd, *o): return rnd.choice(o)


def build(key, rnd):
    k = key[0]; B = []; used = []
    if k in ('tape', 'underdog', 'poll'):
        a, b = key[1], key[2]; rounds, champ = tape(a, b); used = [a, b]
        intro = {'tape': C(rnd, f'{cap(nm(a))} versus {nm(b)}. Who wins on paper?', f'Tale of the tape: {nm(a)} against {nm(b)}.'),
                 'underdog': f'{cap(nm(a))} versus {nm(b)}. The smaller one has a surprise.',
                 'poll': f'{cap(nm(a))} or {nm(b)}? Vote in the comments before the stats.'}[k]
        B = [(intro, dict(t='vs', a=a, b=b))]
        if k == 'poll': B.append(('Red corner or blue corner? Lock in your pick.', dict(t='vs', a=a, b=b, timer=True)))
        for i, (s, w) in enumerate(rounds):
            B.append((f'Round {i + 1}, {STAT[s][0].lower()}. {cap(nm(a))}: {say_stat(a, s)}. {cap(nm(b))}: {say_stat(b, s)}. Point to {nm(w)}.',
                      dict(t='round', a=a, b=b, s=s, w=w, n=i + 1, score=[sum(x == a for _, x in rounds[:i + 1]), sum(x == b for _, x in rounds[:i + 1])])))
        sa, sb = sum(w == a for _, w in rounds), sum(w == b for _, w in rounds)
        B.append((f'On paper, {nm(champ)} wins, {max(sa, sb)} to {min(sa, sb)}.' + (' Tie broken by weight.' if sa == sb else ''), dict(t='winner', a=a, b=b, w=champ, score=[sa, sb])))
        B.append((C(rnd, 'Do you agree? Comment who you picked.', 'Which matchup should I do next? Comment below.'), dict(t='winner', a=a, b=b, w=champ, score=[sa, sb], cta='WHO DID YOU PICK?')))
        title = {'tape': C(rnd, f'{TN(a)} vs {TN(b)}: Who Wins on Paper?', f'{TN(a)} vs {TN(b)} — Tale of the Tape'),
                 'underdog': f'Underdog Alert: {TN(a)} vs {TN(b)}',
                 'poll': f'{TN(a)} or {TN(b)}? Vote Before You See the Stats'}[k]
    elif k == 'bracket4':
        ids = list(key[1:]); rnd.shuffle(ids); used = ids
        s1 = (ids[0], ids[1]); s2 = (ids[2], ids[3]); w1 = tape(*s1)[1]; w2 = tape(*s2)[1]; wf = tape(w1, w2)[1]
        br = dict(t='bracket', ids=ids)
        B = [(f'Four animals, one bracket: ' + ', '.join(nm(x) for x in ids) + '.', dict(br, stage=0)),
             (f'Semifinal one: {nm(ids[0])} versus {nm(ids[1])}. {cap(nm(w1))} moves on.', dict(br, stage=1, w1=w1)),
             (f'Semifinal two: {nm(ids[2])} versus {nm(ids[3])}. {cap(nm(w2))} moves on.', dict(br, stage=2, w1=w1, w2=w2)),
             (f'The final: {nm(w1)} versus {nm(w2)}. On paper, the champion is {nm(wf)}.', dict(br, stage=3, w1=w1, w2=w2, wf=wf)),
             ('Who should be in the next bracket? Comment below.', dict(br, stage=3, w1=w1, w2=w2, wf=wf, cta='NEXT BRACKET?'))]
        title = f'4-Animal Bracket: ' + ', '.join(TN(x) for x in ids[:3]) + ' & More'
    elif k == 'top5':
        s = key[1]; ids = sorted(key[2:], key=lambda x: sv(x, s)); used = ids
        B = [(f'Top five by {STAT[s][0].lower()}. Counting down.', dict(t='list', s=s, ids=ids, n=0))]
        for i, x in enumerate(ids):
            B.append((f'Number {5 - i}: {nm(x)}, {say_stat(x, s)}.', dict(t='list', s=s, ids=ids, n=i + 1)))
        B.append(('Did your favorite make the list? Comment below.', dict(t='list', s=s, ids=ids, n=5, cta='YOUR FAVORITE?')))
        title = f'Top 5 Animals by {STAT[s][0].title()}: {TN(ids[-1])} Takes #1'
    elif k == 'higherlower':
        a, b, s = key[1], key[2], key[3]; w = a if sv(a, s) > sv(b, s) else b; used = [a, b]
        B = [(f'Higher or lower: whose {STAT[s][0].lower()} is bigger, {nm(a)} or {nm(b)}?', dict(t='vs', a=a, b=b, s=s, hide=True)),
             ('Pick one.', dict(t='vs', a=a, b=b, s=s, hide=True, timer=True)),
             (f'{cap(nm(a))}: {say_stat(a, s)}. {cap(nm(b))}: {say_stat(b, s)}.', dict(t='round', a=a, b=b, s=s, w=w, n=1, score=None)),
             (f'{cap(nm(w))} takes it by {max(sv(a, s), sv(b, s)) / min(sv(a, s), sv(b, s)):.1f} times.', dict(t='round', a=a, b=b, s=s, w=w, n=1, score=None)),
             ('Did you get it? Comment below.', dict(t='round', a=a, b=b, s=s, w=w, n=1, score=None, cta='DID YOU GET IT?'))]
        title = f'{TN(a)} vs {TN(b)}: Who Has the Bigger {STAT[s][0].title()}?'
    elif k == 'truefalse':
        _, a, b, s, f = key; r = sv(a, s) / sv(b, s); tr = r >= f; used = [a, b]
        claim = f'{cap(nm(a))} has at least {f} times the {STAT[s][0].lower()} of {nm(b)}.'
        B = [(f'True or false? {claim}', dict(t='tf', q=claim, a=a, b=b)), ('Think about it.', dict(t='tf', q=claim, a=a, b=b, timer=True)),
             (f'{"True" if tr else "False"}. {say_stat(a, s)} versus {say_stat(b, s)}: {r:.1f} times.', dict(t='tf', q=claim, a=a, b=b, r=0 if tr else 1)),
             ('Did you get it right? Comment true or false.', dict(t='tf', q=claim, a=a, b=b, r=0 if tr else 1, cta='TRUE OR FALSE?'))]
        title = f'True or False: {TN(a)} Has {f}x the {STAT[s][0].title()} of a {TN(b)}'
    elif k == 'scale':
        a, b = key[1], key[2]; n = sv(a, 'weight') / sv(b, 'weight'); used = [a, b]
        g = max(2, round(n * rnd.choice([0.7, 0.8, 1.25, 1.4]))); heavy = a if sv(a, 'weight') > g * sv(b, 'weight') else b
        B = [(f'Which side is heavier: one {NM(a).lower()}, or {g} {PL(b)}?', dict(t='scale', a=a, b=b, n=0, g=g)),
             ('Pick a side.', dict(t='scale', a=a, b=b, n=0, g=g, timer=True)),
             (f'One {NM(a).lower()}: about {say_stat(a, "weight")}. {g} {PL(b)}: about {g * sv(b, "weight"):,.0f} kilograms.', dict(t='scale', a=a, b=b, n=0, g=g, tip=1 if heavy == a else -1)),
             (f'The {"single " + NM(a).lower() if heavy == a else str(g) + " " + PL(b)} side wins. It takes about {n:,.0f} to balance it exactly.', dict(t='scale', a=a, b=b, n=n, g=g, tip=1 if heavy == a else -1)),
             ('Did you pick the right side? Comment below.', dict(t='scale', a=a, b=b, n=n, g=g, tip=1 if heavy == a else -1, cta='RIGHT SIDE?'))]
        title = f'1 {TN(a)} vs {g} {PL(b).title()}: Which Side Is Heavier?'
    elif k == 'ratio':
        a, b = key[1], key[2]; n = sv(a, 'weight') / sv(b, 'weight'); used = [a, b]
        B = [(f'How many {PL(b)} would it take to balance one {NM(a).lower()} on a scale?', dict(t='scale', a=a, b=b, n=0)),
             (f'{cap(nm(a))} weighs about {say_stat(a, "weight")}. {cap(nm(b))}, about {say_stat(b, "weight")}.', dict(t='scale', a=a, b=b, n=0)),
             (f'You would need about {n:,.0f}.', dict(t='scale', a=a, b=b, n=n, anim=True)),
             ('Close to your guess? Comment below.', dict(t='scale', a=a, b=b, n=n, cta='YOUR GUESS?'))]
        title = f'How Many {PL(b).title()} Weigh as Much as One {TN(a)}?'
    elif k == 'race':
        a, b = key[1], key[2]; w = a if sv(a, 'speed') > sv(b, 'speed') else b; used = [a, b]
        lose = b if w == a else a; gap = 100 * (1 - sv(lose, 'speed') / sv(w, 'speed'))
        B = [(f'A 100 meter sprint: {nm(a)} against {nm(b)}, at top speed.', dict(t='race', a=a, b=b, p=0)),
             ('Ready, set, go!', dict(t='race', a=a, b=b, p=1, anim=True)),
             (f'{cap(nm(w))} wins. When it crosses the line, {nm(lose)} is about {gap:.0f} meters behind.', dict(t='race', a=a, b=b, p=1)),
             (f'Top speeds: {say_stat(a, "speed")} versus {say_stat(b, "speed")}. Who should race next? Comment below.', dict(t='race', a=a, b=b, p=1, cta='WHO RACES NEXT?'))]
        title = f'100m Sprint: {TN(a)} vs {TN(b)} at Top Speed'
    elif k == 'bite':
        a, b = key[1], key[2]; w = a if sv(a, 'bite') > sv(b, 'bite') else b; used = [a, b]
        B = [(f'Bite force battle: {nm(a)} or {nm(b)}?', dict(t='vs', a=a, b=b, s='bite', hide=True)),
             ('Guess first.', dict(t='vs', a=a, b=b, s='bite', hide=True, timer=True)),
             (f'{cap(nm(a))}: about {say_stat(a, "bite")}. {cap(nm(b))}: about {say_stat(b, "bite")}.', dict(t='round', a=a, b=b, s='bite', w=w, n=1, score=None)),
             (f'For scale, a human bite is about 162 PSI. {cap(nm(w))} is {sv(w, "bite") / 162:.0f} times that.', dict(t='round', a=a, b=b, s='bite', w=w, n=1, score=None)),
             ('Which bite should I test next? Comment below.', dict(t='round', a=a, b=b, s='bite', w=w, n=1, score=None, cta='WHO IS NEXT?'))]
        title = f'Bite Force: {TN(a)} vs {TN(b)}'
    elif k in ('mystery', 'shadow'):
        x = key[1]; used = [x]
        others = rnd.sample([y for y in A if y != x and A[y][2] == A[x][2]], 2); o = [x] + others; rnd.shuffle(o); r = o.index(x)
        ops = [NM(y) for y in o]
        hint = ', '.join(f'{STAT[st][0].lower()} {say_stat(x, st)}' for st in STAT if sv(x, st))
        if k == 'mystery':
            B = [(f'Mystery animal. Its stats: {hint}. Which animal is it?', dict(t='card', x=x, o=ops, hide=True)),
                 ('A, B or C?', dict(t='card', x=x, o=ops, hide=True, timer=True)),
                 (f'It is {"ABC"[r]}: {nm(x)}.', dict(t='card', x=x, o=ops, r=r)),
                 ('Did you get it from the stats alone? Comment below.', dict(t='card', x=x, o=ops, r=r, cta='DID YOU GET IT?'))]
            title = f'Mystery Animal: {TN(o[0])}, {TN(o[1])} or {TN(o[2])}?'
        else:
            B = [('Guess the animal from its shadow.', dict(t='shadow', x=x, o=ops, hide=True)),
                 ('A, B or C?', dict(t='shadow', x=x, o=ops, hide=True, timer=True)),
                 (f'It is {"ABC"[r]}: {nm(x)}. ' + (f'Its {hint}.' if hint else ''), dict(t='shadow', x=x, o=ops, r=r)),
                 ('How fast did you get it? Comment below.', dict(t='shadow', x=x, o=ops, r=r, cta='HOW FAST?'))]
            title = f'Shadow Quiz: {TN(o[0])}, {TN(o[1])} or {TN(o[2])}?'
    elif k == 'oddone':
        st, ids = key[1], list(key[2:]); rnd.shuffle(ids); used = ids; best = max(ids, key=lambda x: sv(x, st))
        word = {'speed': 'fastest', 'weight': 'heaviest', 'bite': 'strongest bite', 'length': 'longest body'}[st]
        B = [(f'Which of these four has the {word}?', dict(t='grid', ids=ids, s=st, show=False)),
             ('Pick one.', dict(t='grid', ids=ids, s=st, show=False, timer=True)),
             (' '.join(f'{cap(nm(x))}: {say_stat(x, st)}.' for x in ids), dict(t='grid', ids=ids, s=st, show=True)),
             (f'The {word}: {nm(best)}.', dict(t='grid', ids=ids, s=st, show=True, mark=best)),
             ('Did you pick it? Comment below.', dict(t='grid', ids=ids, s=st, show=True, mark=best, cta='DID YOU PICK IT?'))]
        title = {'speed': 'Fastest', 'weight': 'Heaviest', 'bite': 'Strongest Bite', 'length': 'Longest'}[st] + ': ' + ', '.join(TN(x) for x in ids[:-1]) + f' or {TN(ids[-1])}?'
    elif k == 'tierlist':
        ids = list(key[1:]); used = ids
        def pct(x, st):
            vals = sorted(sv(y, st) for y in A if sv(y, st)); v = sv(x, st)
            return None if v is None else vals.index(v) / max(1, len(vals) - 1)
        sc_ = {x: sum(p_ for p_ in (pct(x, st) for st in STAT) if p_ is not None) / max(1, sum(pct(x, st) is not None for st in STAT)) for x in ids}
        tier = {x: 'S' if v >= 0.75 else 'A' if v >= 0.5 else 'B' if v >= 0.3 else 'C' for x, v in sc_.items()}
        order = sorted(ids, key=lambda x: -sc_[x])
        B = [('Ranking six animals into tiers, by their stats against every animal on this channel.', dict(t='tier', ids=[], tier=tier))]
        for i, x in enumerate(order):
            B.append((f'{cap(nm(x))}: {tier[x]} tier.', dict(t='tier', ids=order[:i + 1], tier=tier)))
        B.append(('Would you change any tier? Comment below.', dict(t='tier', ids=order, tier=tier, cta='CHANGE A TIER?')))
        title = 'Animal Tier List by Real Stats: ' + ', '.join(TN(x) for x in order[:3]) + ' & More'
    elif k == 'threeway':
        ids = list(key[1:]); used = ids; pts = {x: 0 for x in ids}; lines_ = []
        for st in STAT:
            have = [x for x in ids if sv(x, st)]
            if len(have) < 2: continue
            w = max(have, key=lambda x: sv(x, st)); pts[w] += 1; lines_.append((st, w))
        champ = max(ids, key=lambda x: (pts[x], sv(x, 'weight')))
        B = [(f'Triple threat: {nm(ids[0])}, {nm(ids[1])} and {nm(ids[2])}. One point per stat.', dict(t='grid', ids=ids, s=None, show=False, pts={x: 0 for x in ids}))]
        run = {x: 0 for x in ids}
        for st, w in lines_:
            run[w] += 1; B.append((f'{STAT[st][0].capitalize()}: point to {nm(w)}.', dict(t='grid', ids=ids, s=st, show=True, mark=w, pts=dict(run))))
        B.append((f'On paper, {nm(champ)} takes the triple threat.', dict(t='grid', ids=ids, s=None, show=False, mark=champ, pts=dict(run))))
        B.append(('Who should join the next one? Comment below.', dict(t='grid', ids=ids, s=None, show=False, mark=champ, pts=dict(run), cta='WHO IS NEXT?')))
        title = f'Triple Threat: {TN(ids[0])} vs {TN(ids[1])} vs {TN(ids[2])}'
    elif k == 'kinghill':
        champ, chs = key[1], list(key[2:]); used = [champ] + chs; king = champ
        B = [(f'King of the hill. {cap(nm(champ))} defends against three challengers.', dict(t='vs', a=champ, b=chs[0]))]
        for c_ in chs:
            rounds, w = tape(king, c_)
            B.append((f'{cap(nm(c_))} steps up. ' + ' '.join(f'{STAT[st][0].capitalize()}: {nm(x)}.' for st, x in rounds) + f' {cap(nm(w))} {"keeps the crown" if w == king else "takes the crown"}.',
                      dict(t='winner', a=king, b=c_, w=w, score=[sum(x == king for _, x in rounds), sum(x == c_ for _, x in rounds)])))
            king = w
        B.append((f'The last one standing: {nm(king)}. Who should challenge next? Comment below.', dict(t='winner', a=king, b=chs[-1] if king != chs[-1] else champ, w=king, score=None, cta='NEXT CHALLENGER?')))
        title = f'King of the Hill: Can the {TN(champ)} Hold the Crown?'
    elif k == 'teamup':
        a, b = key[1], key[2]; used = [a, b]
        n = 2; wa, wb = n * sv(a, 'weight'), sv(b, 'weight'); ba = (sv(a, 'bite') or 0) * n; bb = sv(b, 'bite') or 0
        heavier = a if wa > wb else b
        B = [(f'Two {PL(a)} against one {NM(b).lower()}. Combined stats, on paper.', dict(t='vs', a=a, b=b)),
             (f'Combined weight: {wa:,.0f} kilograms versus {wb:,.0f}. ' + (f'{"Two " + PL(a) if heavier == a else "The " + NM(b).lower()} are heavier.' if heavier == a else f'The {NM(b).lower()} is heavier.'), dict(t='vs', a=a, b=b)),
             (f'Top speed does not add up: {say_stat(a, "speed")} versus {say_stat(b, "speed")}.', dict(t='round', a=a, b=b, s='speed', w=a if sv(a, 'speed') > sv(b, 'speed') else b, n=1, score=None)),
             ('Teamwork or size? Comment who you would back.', dict(t='vs', a=a, b=b, cta='TEAM OR SIZE?'))]
        title = f'2 {PL(a).title()} vs 1 {TN(b)}: Combined Stats'
    elif k == 'outrun':
        ref, ids = key[1], list(key[2:]); used = ids; lim = 24 if ref == 'jog' else 44.7
        who = 'an average person sprinting at about 24 kilometers per hour' if ref == 'jog' else 'Usain Bolt at 44.7 kilometers per hour'
        slow = [x for x in ids if sv(x, 'speed') < lim]
        B = [(f'Could {who} outrun these six animals at top speed?', dict(t='grid', ids=ids, s='speed', show=False)),
             ('Guess how many.', dict(t='grid', ids=ids, s='speed', show=False, timer=True)),
             (f'Only {len(slow)}: ' + ', '.join(nm(x) for x in slow) + '.', dict(t='grid', ids=ids, s='speed', show=True, yes=slow)),
             ('Every other one is faster. How many did you guess? Comment below.', dict(t='grid', ids=ids, s='speed', show=True, yes=slow, cta='HOW MANY?'))]
        title = 'Could You Outrun These 6 Animals?' if ref == 'jog' else 'Could Usain Bolt Outrun These 6 Animals?'
    elif k == 'quickfire':
        qs = [key[i:i + 3] for i in (1, 4, 7)]; used = [x for q in qs for x in q[:2]]
        B = [('Quick fire. Three questions, three seconds each.', dict(t='vs', a=qs[0][0], b=qs[0][1]))]
        for i, (a, b, st) in enumerate(qs):
            w = a if sv(a, st) > sv(b, st) else b
            B.append((f'Question {i + 1}: bigger {STAT[st][0].lower()}, {nm(a)} or {nm(b)}?', dict(t='vs', a=a, b=b, s=st, hide=True, timer=True)))
            B.append((f'{cap(nm(w))}: {say_stat(w, st)}.', dict(t='round', a=a, b=b, s=st, w=w, n=1, score=None)))
        B.append(('What did you score out of three? Comment below.', dict(t='vs', a=qs[2][0], b=qs[2][1], cta='YOUR SCORE?')))
        title = 'Animal Stats Quick Fire: Can You Get 3 out of 3?'
    elif k == 'weightclass':
        x = key[1]; near = sorted([y for y in A if y != x and 0.75 <= sv(y, 'weight') / sv(x, 'weight') <= 1.33], key=lambda y: abs(sv(y, 'weight') - sv(x, 'weight')))[:3]
        used = [x] + near; ids = [x] + near
        B = [(f'Same weight class as {nm(x)}, at about {say_stat(x, "weight")}. Which animals fight in this division?', dict(t='grid', ids=[x], s='weight', show=True))]
        for i, y in enumerate(near):
            B.append((f'{cap(nm(y))}: {say_stat(y, "weight")}.', dict(t='grid', ids=ids[:i + 2], s='weight', show=True)))
        B.append(('Who wins this weight class? Comment below.', dict(t='grid', ids=ids, s='weight', show=True, cta='WHO WINS?')))
        title = f'The {TN(x)} Weight Class: Animals of the Same Size'
    elif k == 'closest':
        x, st = key[1], key[2]; others = sorted([y for y in A if y != x and sv(y, st)], key=lambda y: abs(sv(y, st) - sv(x, st)))
        right = others[0]; o = [right] + rnd.sample(others[3:], 2); rnd.shuffle(o); r = o.index(right); used = [x] + o
        B = [(f'Which animal has the {STAT[st][0].lower()} closest to {nm(x)}?', dict(t='card', x=x, o=[NM(y) for y in o], st=st)),
             ('A, B or C?', dict(t='card', x=x, o=[NM(y) for y in o], st=st, timer=True)),
             (f'It is {"ABC"[r]}: {nm(right)}, at {say_stat(right, st)}. {cap(nm(x))} is {say_stat(x, st)}.', dict(t='card', x=x, o=[NM(y) for y in o], st=st, r=r)),
             ('Did you get it? Comment below.', dict(t='card', x=x, o=[NM(y) for y in o], st=st, r=r, cta='DID YOU GET IT?'))]
        title = f'Which Animal Is Closest to the {TN(x)} in {STAT[st][0].title()}?'
    else:                                           # guessstat
        s, x = key[1], key[2]; v = sv(x, s); o = [v, v * rnd.choice([0.5, 0.6]), v * rnd.choice([1.6, 2])]; rnd.shuffle(o); r = o.index(v); used = [x]
        unit = STAT[s][2]; nf = (lambda z: f'{z:.1f}') if s == 'length' else (lambda z: f'{z:,.0f}'); ops = [f'{nf(z)} {unit.upper()}' for z in o]
        B = [(f'What is the {STAT[s][0].lower()} of {nm(x)}?', dict(t='opts', a=x, o=ops)),
             (f'A: {nf(o[0])}. B: {nf(o[1])}. C: {nf(o[2])} {"meters" if unit == "m" else unit.replace("km/h", "kilometers per hour").replace("kg", "kilograms").replace("psi", "PSI")}.', dict(t='opts', a=x, o=ops, timer=True)),
             (f'It is {"ABC"[r]}: {say_stat(x, s)}.', dict(t='opts', a=x, o=ops, r=r)),
             ('Did you get it? Comment below.', dict(t='opts', a=x, o=ops, r=r, cta='DID YOU GET IT?'))]
        title = f'Guess the {STAT[s][0].title()} of ' + ('an ' if TN(x)[0] in 'AEIOU' else 'a ') + TN(x)
    credit = [f"{TN(k_)} silhouette: {CREDITS[k_]['by'] or 'PhyloPic'} ({CREDITS[k_]['license']}, {CREDITS[k_]['url']})"
              for k_ in dict.fromkeys(used) if CREDITS.get(k_, {}).get('license', '').startswith('CC BY')]
    desc = (title + '\n\n' + '\n'.join(f'{TN(k_)}: weight {fmt(k_, "weight").lower()}, top speed {fmt(k_, "speed").lower()}, bite {fmt(k_, "bite").lower()}' for k_ in dict.fromkeys(used))
            + f'\n\n{SOURCE}\nSilhouettes: PhyloPic (public domain / CC0' + (')' if not credit else '; ' + '; '.join(credit) + ')')
            + '\n\n#animals #wildlife #animalvsanimal #whowouldwin #shorts')
    return dict(key=key, kurgu=k, beats=[b for b, _ in B], scenes=[s for _, s in B], title=title[:95], desc=desc,
                tags=['animal vs animal', 'who would win', 'animal comparison', 'wildlife', 'animal facts', 'shorts'])


# ---------------------------------------------------------------- çizim
_FC, _SC = {}, {}


def font(p, s):
    if (p, s) not in _FC:
        f = ImageFont.truetype(p, s)
        if p == TEKO:
            try: f.set_variation_by_axes([600])
            except Exception: pass
        _FC[(p, s)] = f
    return _FC[(p, s)]


def sil(k, w, h, col=WHITE, flip=False):
    key = (k, w, h, col, flip)
    if key not in _SC:
        im = Image.open(SIL / f'{k}.png').convert('RGBA'); bb = im.split()[3].getbbox()
        if bb: im = im.crop(bb)
        im.thumbnail((w, h), Image.LANCZOS)
        a = im.split()[3]
        if k == 'zebra':                                   # çizgili çizim: içini doldur
            from PIL import ImageFilter
            a = a.filter(ImageFilter.MaxFilter(9))
        solid = Image.new('RGBA', im.size, col + (255,)); solid.putalpha(a)
        _SC[key] = solid.transpose(Image.FLIP_LEFT_RIGHT) if flip else solid
    return _SC[key]


def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def background(w, h):
    img = Image.new('RGB', (w, h), BG); d = ImageDraw.Draw(img)
    for y in range(0, h, 4):
        c = int(12 + 10 * math.exp(-((y - h * 0.45) / (h * 0.35)) ** 2)); d.line([(0, y), (w, y)], fill=(c, c, c + 4))
    return img


def corner(img, d, k, x, y, w, h, col, label=None, flip=False, glow=False):
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=PANEL, outline=col, width=8 if glow else 4)
    d.rectangle([x, y, x + w, y + 70], fill=col)
    d.text((x + w // 2, y + 38), NM(k), font=font(TEKO, 62 if len(NM(k)) < 12 else 46), fill=WHITE, anchor='mm')
    s = sil(k, w - 60, h - 200, WHITE, flip); img.paste(s, (x + (w - s.width) // 2, y + 90 + (h - 200 - s.height) // 2), s)
    if label: d.text((x + w // 2, y + h - 50), label, font=font(TEKO, 64), fill=GOLD, anchor='mm')


def wrap(d, text, f, maxw):
    out, cur = [], ''
    for w_ in text.split():
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=f) > maxw and cur: out.append(cur); cur = w_
        else: cur = t
    return out + [cur] if cur else out


def statbars(d, a, b, s, y, k=1.0, w=None):
    va, vb = sv(a, s), sv(b, s); mx = max(va, vb)
    d.text((540, y), STAT[s][0], font=font(TEKO, 70), fill=INK, anchor='mm')
    for i, (x, v, col) in enumerate(((a, va, RED), (b, vb, BLUE))):
        yy = y + 60 + i * 110; bw = 560 * v / mx * k
        d.rounded_rectangle([160, yy, 160 + max(8, bw), yy + 80], radius=10, fill=col if (w is None or w == x) else (90, 90, 100))
        d.text((150, yy + 40), NM(x)[:10], font=font(RAJ, 30), fill=DIM, anchor='rm')
        d.text((170 + bw, yy + 40), fmt(x, s), font=font(TEKO, 58), fill=WHITE, anchor='lm')


def frame(base, v, bi, t, dur):
    W, H = 1080, 1920; img = base.copy(); d = ImageDraw.Draw(img); sc = v['scenes'][bi]; T = sc['t']
    prev = v['scenes'][bi - 1] if bi else {}
    a_ = 1.0 if (prev.get('t') == T and prev.get('s') == sc.get('s') and prev.get('w') == sc.get('w') and prev.get('n') == sc.get('n')) else ease(t / 0.9)
    d.text((W // 2, 110), 'WILD MATCHUPS', font=font(TEKO, 96), fill=WHITE, anchor='mm')
    d.rectangle([W // 2 - 200, 160, W // 2 - 4, 168], fill=RED); d.rectangle([W // 2 + 4, 160, W // 2 + 200, 168], fill=BLUE)
    if T in ('vs', 'round', 'winner', 'tf'):
        a, b = sc['a'], sc['b']; win = sc.get('w')
        corner(img, d, a, 50, 230, 470, 620, RED, glow=(T == 'winner' and win == a))
        corner(img, d, b, 560, 230, 470, 620, BLUE, flip=True, glow=(T == 'winner' and win == b))
        d.ellipse([480, 480, 600, 600], fill=GOLD); d.text((540, 540), 'VS', font=font(TEKO, 70), fill=BG, anchor='mm')
        if sc.get('score'): d.text((W // 2, 920), f"{sc['score'][0]}  —  {sc['score'][1]}", font=font(TEKO, 120), fill=WHITE, anchor='mm')
        if T == 'vs' and sc.get('s'): d.text((W // 2, 950), f"{STAT[sc['s']][0]}?", font=font(TEKO, 110), fill=GOLD, anchor='mm')
        if T == 'round': statbars(d, a, b, sc['s'], 1030, k=a_, w=win)
        if T == 'winner':
            d.text((W // 2, 1080), 'WINNER ON PAPER', font=font(RAJ, 50), fill=DIM, anchor='mm')
            d.text((W // 2, 1180), NM(win), font=font(TEKO, int(150 * (0.6 + 0.4 * a_))), fill=GOLD, anchor='mm')
        if T == 'tf':
            for j, l in enumerate(wrap(d, sc['q'], font(RAJ, 52), 920)[:4]):
                d.text((W // 2, 920 + j * 62), l, font=font(RAJ, 52), fill=WHITE, anchor='mm')
            for i, o in enumerate(['TRUE', 'FALSE']):
                x = 110 + i * 440; on = sc.get('r') == i
                d.rounded_rectangle([x, 1200, x + 420, 1340], radius=20, fill=GOLD if on else PANEL, outline=WHITE, width=4)
                d.text((x + 210, 1270), o, font=font(TEKO, 90), fill=BG if on else WHITE, anchor='mm')
    elif T == 'bracket':
        ids = sc['ids']; st = sc['stage']; ys = [300, 560, 860, 1120]
        for i, k_ in enumerate(ids):
            out = (st >= 1 and i < 2 and k_ != sc.get('w1')) or (st >= 2 and i >= 2 and k_ != sc.get('w2'))
            col = (80, 80, 90) if out else (RED if i % 2 == 0 else BLUE)
            d.rounded_rectangle([40, ys[i], 440, ys[i] + 200], radius=14, fill=PANEL, outline=col, width=4)
            s_ = sil(k_, 180, 150, (110, 110, 120) if out else WHITE); img.paste(s_, (60, ys[i] + 25), s_)
            d.text((260, ys[i] + 100), NM(k_)[:12], font=font(TEKO, 46), fill=DIM if out else WHITE, anchor='lm')
        for j, kk in enumerate((sc.get('w1'), sc.get('w2'))):
            if kk and st >= j + 1:
                y = 430 + j * 560; d.line([(440, ys[2 * j] + 100), (520, y + 100), (440, ys[2 * j + 1] + 100)], fill=GOLD, width=5)
                d.rounded_rectangle([520, y, 900, y + 200], radius=14, fill=PANEL, outline=GOLD, width=5)
                s_ = sil(kk, 160, 140); img.paste(s_, (540, y + 30), s_); d.text((720, y + 100), NM(kk)[:12], font=font(TEKO, 42), fill=WHITE, anchor='lm')
        if st >= 3:
            d.rounded_rectangle([200, 1380, 880, 1540], radius=20, fill=GOLD)
            d.text((540, 1460), f"CHAMPION: {NM(sc['wf'])}", font=font(TEKO, 76 if len(NM(sc['wf'])) < 12 else 58), fill=BG, anchor='mm')
    elif T == 'list':
        s = sc['s']; ids = sc['ids']; mx = max(sv(x, s) for x in ids)
        d.text((W // 2, 260), f'TOP 5 · {STAT[s][0]}', font=font(TEKO, 92), fill=GOLD, anchor='mm')
        for i, x in enumerate(ids[:sc['n']]):
            y = 1300 - i * 230; bw = 560 * sv(x, s) / mx * (a_ if i == sc['n'] - 1 and not sc.get('cta') else 1)
            d.text((80, y + 70), f'#{5 - i}', font=font(TEKO, 90), fill=GOLD, anchor='lm')
            s_ = sil(x, 200, 150); img.paste(s_, (190, y), s_)
            d.text((420, y + 30), NM(x), font=font(TEKO, 52), fill=WHITE, anchor='lm')
            d.rounded_rectangle([420, y + 80, 420 + max(8, bw), y + 130], radius=8, fill=RED)
            d.text((430 + bw, y + 105), fmt(x, s), font=font(TEKO, 46), fill=WHITE, anchor='lm')
    elif T == 'opts':
        corner(img, d, sc['a'], 240, 230, 600, 640, GOLD)
        for i, o in enumerate(sc['o']):
            y = 950 + i * 150; on = sc.get('r') == i
            d.rounded_rectangle([140, y, 940, y + 120], radius=20, fill=GOLD if on else PANEL, outline=WHITE, width=4)
            d.text((W // 2, y + 60), f'{"ABC"[i]}   {o}', font=font(TEKO, 70), fill=BG if on else WHITE, anchor='mm')
    elif T == 'scale':
        a, b, n = sc['a'], sc['b'], sc['n']; tilt = int(round(sc.get('tip', 1) * 14 * a_)) if (n or 'tip' in sc) else 0
        d.polygon([(540, 1150), (500, 1300), (580, 1300)], fill=DIM)
        lx, rx, yb = 160, 920, 1150 + 0
        d.line([(lx, yb - tilt * 6 * -1), (rx, yb - tilt * 6)], fill=WHITE, width=10)
        sa = sil(a, 380, 300); img.paste(sa, (lx - 40, yb - 320 + tilt * 6), sa); d.text((lx + 150, yb + 60), NM(a), font=font(TEKO, 54), fill=RED, anchor='mm')
        g = sc.get('g') or 1; bw_ = max(70, 220 // max(1, min(g, 4)))
        for gi in range(min(g, 8)):
            sb = sil(b, bw_, int(bw_ * 0.8)); img.paste(sb, (rx - 60 - (gi % 4 + 1) * (bw_ - 10), yb - int(bw_ * 0.8) - 20 - (gi // 4) * int(bw_ * 0.7) - int(tilt * 6)), sb)
        d.text((rx - 120, yb + 60), (f'{g} × ' if g > 1 else '') + NM(b), font=font(TEKO, 54), fill=BLUE, anchor='mm')
        if n and not sc.get('g'):
            d.text((W // 2, 600), f'{n * (a_ if sc.get("anim") else 1):,.0f}', font=font(TEKO, 260), fill=GOLD, anchor='mm')
            d.text((W // 2, 760), f'{PL(b).upper()} = 1 {NM(a)}', font=font(TEKO, 70), fill=WHITE, anchor='mm')
    elif T in ('card', 'shadow'):
        x = sc['x']; hide = sc.get('hide')
        d.rounded_rectangle([90, 230, 990, 900], radius=24, fill=PANEL, outline=GOLD, width=4)
        if T == 'shadow' or not hide:
            s_ = sil(x, 700, 380, (70, 70, 80) if hide else WHITE); img.paste(s_, (540 - s_.width // 2, 290 + (380 - s_.height) // 2), s_)
        if T == 'card':
            y0 = 700 if not hide else 330
            for j, st in enumerate([st for st in STAT if sv(x, st) and (not sc.get('st') or st == sc['st'])]):
                d.text((160, y0 + j * 70), STAT[st][0], font=font(RAJ, 46), fill=DIM, anchor='lm')
                d.text((920, y0 + j * 70), fmt(x, st), font=font(TEKO, 64), fill=GOLD, anchor='rm')
            if sc.get('st'): d.text((540, 830), NM(x), font=font(TEKO, 70), fill=WHITE, anchor='mm')
        for i, o in enumerate(sc['o']):
            y = 960 + i * 140; on = sc.get('r') == i
            d.rounded_rectangle([140, y, 940, y + 115], radius=20, fill=GOLD if on else PANEL, outline=WHITE, width=4)
            d.text((W // 2, y + 58), f'{"ABC"[i]}   {o}', font=font(TEKO, 66), fill=BG if on else WHITE, anchor='mm')
    elif T == 'grid':
        ids = sc['ids']; n = len(ids); cols = 2; cw, ch_ = 470, 380 if n > 4 else 520
        for i, x in enumerate(ids):
            cx = 50 + (i % cols) * 510; cy = 240 + (i // cols) * (ch_ + 20)
            mk = sc.get('mark') == x or x in (sc.get('yes') or [])
            d.rounded_rectangle([cx, cy, cx + cw, cy + ch_], radius=18, fill=PANEL, outline=GOLD if mk else (70, 70, 80), width=6 if mk else 3)
            s_ = sil(x, cw - 60, ch_ - 170); img.paste(s_, (cx + (cw - s_.width) // 2, cy + 20), s_)
            d.text((cx + cw // 2, cy + ch_ - 120), NM(x), font=font(TEKO, 50 if len(NM(x)) < 13 else 40), fill=WHITE, anchor='mm')
            if sc.get('s') and sc.get('show'): d.text((cx + cw // 2, cy + ch_ - 55), fmt(x, sc['s']), font=font(TEKO, 54), fill=GOLD, anchor='mm')
            if sc.get('pts') is not None: d.text((cx + cw - 30, cy + 40), str(sc['pts'].get(x, 0)), font=font(TEKO, 80), fill=GOLD, anchor='rm')
            if sc.get('yes') is not None and sc.get('show'):
                d.text((cx + 40, cy + 40), 'YES' if x in sc['yes'] else 'NO', font=font(TEKO, 60), fill=(60, 200, 110) if x in sc['yes'] else RED, anchor='lm')
    elif T == 'tier':
        cols_ = {'S': (230, 60, 70), 'A': (240, 150, 40), 'B': (230, 210, 60), 'C': (90, 170, 230)}
        for j, tname in enumerate('SABC'):
            y = 250 + j * 320; d.rectangle([40, y, 200, y + 300], fill=cols_[tname]); d.text((120, y + 150), tname, font=font(TEKO, 160), fill=BG, anchor='mm')
            d.rectangle([200, y, 1040, y + 300], fill=PANEL)
            inn = [x for x in sc['ids'] if sc['tier'][x] == tname]
            for i, x in enumerate(inn):
                s_ = sil(x, 250, 190); img.paste(s_, (220 + i * 270, y + 20), s_)
                d.text((345 + i * 270, y + 255), NM(x)[:12], font=font(TEKO, 38), fill=WHITE, anchor='mm')
    elif T == 'race':
        a, b = sc['a'], sc['b']; va, vb = sv(a, 'speed'), sv(b, 'speed'); vm = max(va, vb)
        p = sc['p'] * (ease(t / max(1.5, dur - 0.4)) if sc.get('anim') else 1)
        for i, (x, spd_, col) in enumerate(((a, va, RED), (b, vb, BLUE))):
            y = 520 + i * 420; d.rectangle([60, y + 300, 1020, y + 310], fill=DIM)
            d.line([(960, y), (960, y + 310)], fill=WHITE, width=6)
            px = 70 + 860 * p * spd_ / vm; s_ = sil(x, 260, 220, col); img.paste(s_, (int(px - s_.width + 40), y + 300 - s_.height), s_)
            d.text((70, y + 350), f'{NM(x)} · {fmt(x, "speed")}', font=font(TEKO, 56), fill=col, anchor='lm')
    if sc.get('timer'): d.text((W // 2, 1450), f'{max(0, 3 - int(t * 1.2))}', font=font(TEKO, 160), fill=GOLD, anchor='mm')
    if sc.get('cta'):
        d.rounded_rectangle([140, 1580, 940, 1720], radius=24, fill=RED)
        d.text((W // 2, 1650), sc['cta'], font=font(TEKO, 84), fill=WHITE, anchor='mm')
    else:
        f = font(RAJM, 48); ls = wrap(d, v['beats'][bi], f, 960)
        groups = [ls[i:i + 3] for i in range(0, len(ls), 3)] or [[]]
        for j, l in enumerate(groups[min(len(groups) - 1, int(t / max(dur, 0.1) * len(groups)))]):
            d.text((W // 2, 1590 + j * 58), l, font=f, fill=WHITE, anchor='mm')
    return img


# ---------------------------------------------------------------- ses + video
def ff(): return os.environ.get('FFMPEG') or 'ffmpeg'


def tts(text, path):
    import edge_tts

    async def go():
        await edge_tts.Communicate(text, VOICE, rate='+8%').save(str(path))
    for i in range(3):
        try:
            asyncio.run(go())
            if path.exists() and path.stat().st_size > 1000: return
        except Exception as e:
            log(f'  tts deneme {i + 1}: {e}')
    raise RuntimeError('edge-tts çalışmadı')


def voice(beats, tmp, pad=0.3, holds=(), minlen=None):
    durs, ws = [], []
    for i, b in enumerate(beats):
        a = tmp / f'a{i}.mp3'; tts(b, a); w = tmp / f'w{i}.wav'
        af = f'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur={pad}'
        if i in holds: af += ',apad=whole_dur=3.0'
        if minlen and minlen(i): af += f',apad=whole_dur={minlen(i)}'
        subprocess.run([ff(), '-y', '-loglevel', 'error', '-i', str(a), '-af', af, '-ar', '24000', '-ac', '1', '-c:a', 'pcm_s16le', str(w)], check=True)
        r = subprocess.run([ff(), '-i', str(w), '-f', 'null', '-'], capture_output=True, text=True)
        tm = r.stderr.split('time=')[-1].split()[0]; hh, mm, ss = tm.split(':'); durs.append(int(hh) * 3600 + int(mm) * 60 + float(ss)); ws.append(w)
    (tmp / 'a.txt').write_text(''.join(f"file '{w}'\n" for w in ws))
    subprocess.run([ff(), '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(tmp / 'a.txt'), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '44100', '-ac', '2', str(tmp / 'voice.wav')], check=True)
    return durs


def encode(fn, durs, wav, mp4, w, h):
    p = subprocess.Popen([ff(), '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-', '-i', str(wav),
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest',
                          '-movflags', '+faststart', str(mp4)], stdin=subprocess.PIPE)
    for i, dd in enumerate(durs):
        for k in range(int(dd * FPS)):
            p.stdin.write(fn(i, k / FPS, dd).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode: raise RuntimeError('ffmpeg hata')


def render(v, mp4):
    tmp = mp4.with_suffix(''); tmp.mkdir(parents=True, exist_ok=True)
    durs = voice(v['beats'], tmp, holds=[i for i, s in enumerate(v['scenes']) if s.get('timer')],
                 minlen=lambda i: 3.5 if (v['scenes'][i]['t'] == 'race' and v['scenes'][i].get('anim')) else None)
    base = background(1080, 1920)
    encode(lambda i, t, dd: frame(base, v, i, t, dd), durs, tmp / 'voice.wav', mp4, 1080, 1920)
    return mp4


# ---------------------------------------------------------------- uzun: 16'lı turnuva (16:9)
def pick_long(rnd):
    seen, _ = done(); land = [k for k in A if A[k][2] == 'land']
    for _ in range(300):
        ids = rnd.sample(land, 16); tid = 'wml:' + '-'.join(sorted(ids))
        if tid not in seen: return ids, tid
    raise RuntimeError('yeni uzun konu kalmadı')


def build_long(ids, rnd):
    B = [(C(rnd, f'Sixteen land animals. One bracket. Every match decided on paper by real stats: top speed, weight, bite force and body length.',
             'Welcome to the Wild Matchups tournament. Sixteen animals, four rounds, and the numbers decide everything.'), dict(r=0, alive=list(ids), m=None))]
    B.append(('Each match has up to four rounds. The animal that wins more rounds moves on. If it is tied, the heavier animal advances. No real fights, just the numbers.', dict(r=0, alive=list(ids), m=None)))
    cur = list(ids); names = ['Round of sixteen', 'Quarterfinals', 'Semifinals', 'The final']
    for ri in range(4):
        B.append((f'{names[ri]}.', dict(r=ri, alive=list(cur), m=None)))
        nxt = []
        for j in range(0, len(cur), 2):
            a, b = cur[j], cur[j + 1]; rounds, w = tape(a, b)
            detail = ' '.join(f'{STAT[s][0].capitalize()}: {nm(x)}.' for s, x in rounds)
            sa, sb = sum(x == a for _, x in rounds), sum(x == b for _, x in rounds)
            B.append((f'{cap(nm(a))} versus {nm(b)}. {detail} {cap(nm(w))} wins {max(sa, sb)} to {min(sa, sb)}.' + (' ' + rnd.choice(['Weight breaks the tie.', 'All square, so the heavier animal goes through.', 'A tie on rounds; size decides it.']) if sa == sb else ''),
                      dict(r=ri, alive=list(cur), m=(a, b, w))))
            nxt.append(w)
        cur = nxt
    B.append((f'Your champion on paper: {nm(cur[0])}. Who would you have picked? Tell me in the comments, and which animals should be in the next tournament.', dict(r=4, alive=cur, m=None, champ=cur[0])))
    three = ', '.join(TN(x) for x in rnd.sample(ids, 3))
    title = C(rnd, f'16 Animal Tournament: {three} & 13 More — Who Wins on Paper?', f'Animal Bracket of 16: {three} & More, Decided by Stats',
              f'{three} + 13 More Animals: Stat Tournament')
    desc = (title + '\n\nAnimals: ' + ', '.join(TN(x) for x in ids) + f'\n\n{SOURCE}\nSilhouettes: PhyloPic (public domain / CC0).\n\n#animals #wildlife #animalvsanimal #whowouldwin')
    return dict(ids=ids, beats=[b for b, _ in B], scenes=[s for _, s in B], title=title[:95], desc=desc,
                tags=['animal vs animal', 'animal tournament', 'who would win', 'wildlife', 'animal facts'])


def frame_long(base, v, bi, t, dur):
    W, H = 1920, 1080; img = base.copy(); d = ImageDraw.Draw(img); sc = v['scenes'][bi]
    d.text((60, 60), 'WILD MATCHUPS · TOURNAMENT', font=font(TEKO, 64), fill=WHITE, anchor='lm')
    if sc.get('m'):
        a, b, w = sc['m']
        corner(img, d, a, 140, 140, 640, 640, RED, glow=False); corner(img, d, b, 1140, 140, 640, 640, BLUE, flip=True)
        d.ellipse([900, 400, 1020, 520], fill=GOLD); d.text((960, 460), 'VS', font=font(TEKO, 70), fill=BG, anchor='mm')
        if t > dur * 0.7:
            d.rounded_rectangle([660, 800, 1260, 900], radius=20, fill=GOLD)
            d.text((960, 850), f'ADVANCES: {NM(w)}', font=font(TEKO, 64), fill=BG, anchor='mm')
    else:
        al = sc['alive']; n = len(al); cols = min(8, n); rows = (n + cols - 1) // cols
        for i, k_ in enumerate(al):
            x = 120 + (i % cols) * (1680 // cols); y = 200 + (i // cols) * 340
            s_ = sil(k_, 1680 // cols - 30, 200); img.paste(s_, (x, y), s_)
            d.text((x + (1680 // cols - 30) // 2, y + 240), NM(k_)[:13], font=font(TEKO, 40), fill=GOLD if sc.get('champ') == k_ else WHITE, anchor='mm')
    f = font(RAJM, 40); ls = wrap(d, v['beats'][bi], f, 1760)
    groups = [ls[i:i + 2] for i in range(0, len(ls), 2)] or [[]]
    d.rectangle([0, 960, W, H], fill=BG2)
    for j, l in enumerate(groups[min(len(groups) - 1, int(t / max(dur, 0.1) * len(groups)))]):
        d.text((W // 2, 995 + j * 48), l, font=f, fill=WHITE, anchor='mm')
    return img


def render_long(v, mp4):
    tmp = mp4.with_suffix(''); tmp.mkdir(parents=True, exist_ok=True)
    durs = voice(v['beats'], tmp, pad=0.6); base = background(1920, 1080); cache = {}
    def fn(i, t, dd):
        ck = (i, int(t / max(dd, 0.1) * 8), t > dd * 0.7)
        if ck not in cache: cache.clear(); cache[ck] = frame_long(base, v, i, t, dd)
        return cache[ck]
    encode(fn, durs, tmp / 'voice.wav', mp4, 1920, 1080)
    return mp4


# ---------------------------------------------------------------- akış
def yt():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build as gbuild
    creds = Credentials(None, refresh_token=os.environ['YT_REFRESH_TOKEN'], client_id=os.environ['YT_CLIENT_ID'],
                        client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
    return gbuild('youtube', 'v3', credentials=creds, cache_discovery=False)


def record(tid, vid, kind, title, pa):
    LOG.parent.mkdir(parents=True, exist_ok=True); new = not LOG.exists()
    with LOG.open('a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['topic_id', 'date_utc', 'video_id', 'kind', 'title', 'publish_at'])
        if new: w.writeheader()
        w.writerow(dict(topic_id=tid, date_utc=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'), video_id=vid, kind=kind, title=title, publish_at=pa))


def publish_at(kind, n):
    slots = {'short': ['15:00', '18:00', '21:00', '23:30'], 'long': ['19:30']}[kind]      # ABD öğleden sonra / akşam
    hh, mm = map(int, slots[min(n, len(slots) - 1)].split(':'))
    now = datetime.now(timezone.utc); t = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if t < now + timedelta(minutes=30): t = now + timedelta(minutes=40)
    return t.strftime('%Y-%m-%dT%H:%M:%SZ')


def main():
    a = sys.argv[1:]; kurgu = a[a.index('--kurgu') + 1] if '--kurgu' in a else None
    kind = 'long' if '--long' in a else 'short'; n_today = 0
    if '--auto' in a:
        _, rows = done(); today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        tr = [r for r in rows if r['date_utc'].startswith(today)]
        ns, nl = sum(r['kind'] == 'short' for r in tr), sum(r['kind'] == 'long' for r in tr)
        long_day = datetime.now(timezone.utc).strftime('%a').lower()[:3] in (os.environ.get('LONG_DAYS') or 'mon,wed,fri').split(',')
        if ns < int(os.environ.get('SHORTS_PER_DAY') or 3): kind, n_today = 'short', ns
        elif long_day and nl < int(os.environ.get('LONGS_PER_DAY') or 1): kind, n_today = 'long', nl
        else: log(f'bugün {ns} short + {nl} uzun, iş yok'); return
    rnd = random.Random(); OUT.mkdir(parents=True, exist_ok=True); stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M')
    if kind == 'long':
        seen = {tkey(r['title']) for r in done()[1]}
        for _ in range(25):
            ids, tid = pick_long(rnd); v = build_long(ids, rnd)
            if tkey(v['title']) not in seen: break
        else:
            raise SystemExit('25 denemede yeni başlık bulunamadı')
        log(f'[wild-long] {tid} → {v["title"]}'); mp4 = render_long(v, OUT / f'long_{stamp}.mp4')
    else:
        # 2026-10-25: aynı başlık iki kez yüklenmez (tekrar eden başlıkları YouTube dağıtmıyor)
        seen = {tkey(r['title']) for r in done()[1]}
        for _ in range(25):
            key, tid = pick(rnd, kurgu); v = build(key, rnd)
            if tkey(v['title']) not in seen: break
        else:
            raise SystemExit('25 denemede yeni başlık bulunamadı')
        log(f'[wild] {tid} → {v["title"]}'); mp4 = render(v, OUT / f'short_{stamp}.mp4')
    if DRY:
        log(f'  [dry-run] {mp4}\n{v["desc"]}'); return
    api = yt(); ch = api.channels().list(part='id,snippet', mine=True).execute()['items'][0]
    if os.environ.get('YT_CHANNEL_ID') and ch['id'] != os.environ['YT_CHANNEL_ID']: raise RuntimeError(f"yanlış kanal: {ch['snippet']['title']}")
    log(f"kanal: {ch['snippet']['title']}"); pa = publish_at(kind, n_today)
    from googleapiclient.http import MediaFileUpload
    body = {'snippet': {'title': (v['title'] + (' #shorts' if kind == 'short' else ''))[:100], 'description': v['desc'][:4900], 'tags': v['tags'],
                        'categoryId': '15', 'defaultLanguage': 'en', 'defaultAudioLanguage': 'en'},
            'status': {'privacyStatus': 'private', 'publishAt': pa, 'selfDeclaredMadeForKids': False}}
    vid = api.videos().insert(part='snippet,status', body=body, media_body=MediaFileUpload(str(mp4), resumable=True)).execute()['id']
    record(tid, vid, kind, v['title'], pa); log(f'  ✓ https://youtu.be/{vid} (yayın {pa})')
    if kind == 'short' and n_today == 0:                      # günün ilk Short'u → Telegram relay (Instagram/TikTok)
        import shutil
        soc = HERE / 'social'; soc.mkdir(exist_ok=True); shutil.copy(mp4, soc / 'video.mp4')
        tiktok = f"{v['title']}\nRed corner or blue corner? Comment 👇\n\n#animals #wildlife #animalvsanimal #whowouldwin #fyp"
        insta = (f"{v['title']}\n\nRed corner or blue corner? Comment your pick 👇\nFollow for daily Wild Matchups\n\n"
                 "#animals #wildlife #animalvsanimal #whowouldwin #animalfacts")      # Instagram: en fazla 5 etiket
        (soc / 'post.json').write_text(json.dumps({'channel': 'Wild Matchups', 'title': v['title'], 'url': f'https://youtube.com/shorts/{vid}',
                                                   'tiktok': tiktok, 'instagram': insta}, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
