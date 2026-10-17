#!/usr/bin/env python3
"""Wild Matchups kanal kimliği: banner, profil, açıklama.  python brand.py --make | --apply"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import wild as Wd

A = Path('assets'); A.mkdir(exist_ok=True)
DESCRIPTION = """Lion vs tiger? Gorilla vs grizzly? Every matchup here is decided on paper, by real numbers: top speed, weight and bite force.

Tale-of-the-tape duels, brackets, tier lists, quizzes and full tournaments. No real fights, no gore, just the stats, and you pick a side in the comments.

New Shorts every day, plus longer tournaments.

Stats are typical adult figures and commonly cited estimates; sources are noted in every description. Silhouettes: PhyloPic (public domain)."""
KEYWORDS = ['animal vs animal', 'who would win', 'lion vs tiger', 'animal comparison', 'animal facts', 'wildlife', 'bite force',
            'fastest animals', 'animal tournament', 'tier list', 'animal stats']


def banner():
    W, H = 2560, 1440; img = Wd.background(W, H); d = ImageDraw.Draw(img); cy = H // 2
    d.rounded_rectangle([W // 2 - 760, cy - 260, W // 2 - 60, cy + 260], radius=24, fill=Wd.PANEL, outline=Wd.RED, width=8)
    d.rounded_rectangle([W // 2 + 60, cy - 260, W // 2 + 760, cy + 260], radius=24, fill=Wd.PANEL, outline=Wd.BLUE, width=8)
    a = Wd.sil('lion', 560, 380); img.paste(a, (W // 2 - 410 - a.width // 2, cy - a.height // 2), a)
    b = Wd.sil('grizzly', 560, 380, flip=True); img.paste(b, (W // 2 + 410 - b.width // 2, cy - b.height // 2), b)
    d.ellipse([W // 2 - 90, cy - 90, W // 2 + 90, cy + 90], fill=Wd.GOLD); d.text((W // 2, cy), 'VS', font=Wd.font(Wd.TEKO, 120), fill=Wd.BG, anchor='mm')
    d.text((W // 2, cy - 360), 'WILD MATCHUPS', font=Wd.font(Wd.TEKO, 200), fill=Wd.WHITE, anchor='mm')
    d.text((W // 2, cy + 340), 'REAL STATS  ·  YOU PICK THE WINNER', font=Wd.font(Wd.RAJ, 54), fill=Wd.GOLD, anchor='mm')
    img.save(A / 'banner_2560x1440.png')


def profile():
    img = Wd.background(800, 800); d = ImageDraw.Draw(img)
    d.pieslice([40, 40, 760, 760], 90, 270, fill=Wd.RED); d.pieslice([40, 40, 760, 760], 270, 90, fill=Wd.BLUE)
    s = Wd.sil('lion', 520, 380); img.paste(s, (400 - s.width // 2, 400 - s.height // 2 - 30), s)
    d.text((400, 650), 'VS', font=Wd.font(Wd.TEKO, 150), fill=Wd.GOLD, anchor='mm')
    img.save(A / 'profile_800x800.png')


def apply():
    from googleapiclient.http import MediaFileUpload
    api = Wd.yt(); ch = api.channels().list(part='snippet,brandingSettings', mine=True).execute()['items'][0]
    print('kanal:', ch['snippet']['title'])
    url = api.channelBanners().insert(media_body=MediaFileUpload(str(A / 'banner_2560x1440.png'), mimetype='image/png')).execute()['url']
    b = ch.get('brandingSettings', {}); b.setdefault('channel', {})
    b['channel'].update(description=DESCRIPTION, keywords=' '.join(f'"{k}"' if ' ' in k else k for k in KEYWORDS), defaultLanguage='en', country='US')
    b.setdefault('image', {})['bannerExternalUrl'] = url; b.pop('hints', None)
    api.channels().update(part='brandingSettings', body={'id': ch['id'], 'brandingSettings': b}).execute()
    api.channels().update(part='status', body={'id': ch['id'], 'status': {'selfDeclaredMadeForKids': False}}).execute()
    print('✓ banner + açıklama + çocuklara özel değil')


if __name__ == '__main__':
    banner(); profile(); print('✓ görseller')
    if '--apply' in sys.argv: apply()
