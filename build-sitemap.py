#!/usr/bin/env python3
"""สร้าง sitemap.xml จากหน้าเว็บจริง พร้อม lastmod จากประวัติ git

ทำไมต้องเป็นสคริปต์: sitemap เดิมเขียนมือ 51 URL พอเพิ่ม/ลบหน้าทีไรต้องไล่แก้เอง
และไม่มี lastmod เลย ทำให้ Google ไม่รู้ว่าหน้าไหนเพิ่งอัปเดตควรกลับมาเก็บใหม่

ใช้:  python3 build-sitemap.py
"""
import glob, subprocess, os

SITE = 'https://www.penguinx.co'
LANGS = [('en', ''), ('th', 'th/'), ('zh-Hans', 'zh/'), ('ja', 'ja/')]
# บางหน้ายังไม่ได้แปลครบทุกภาษา ต้องเช็คว่าไฟล์มีอยู่จริงก่อนใส่ลง sitemap
# ไม่งั้น Google จะไล่เก็บแล้วเจอ 404 ซึ่งเสียคะแนนมากกว่าไม่ประกาศไปเลย

def pages():
    out = []
    for f in glob.glob('**/*.html', recursive=True):
        if f.startswith(('th/', 'zh/', 'ja/')) or 'preview-' in f or '_template' in f:
            continue
        out.append(f)
    return sorted(out)

def lastmod(paths):
    """วันที่ commit ล่าสุดที่แตะไฟล์นี้ — ถ้าไฟล์ยังไม่เคย commit ใช้เวลาบนดิสก์"""
    for p in paths:
        d = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', p],
                           capture_output=True, text=True).stdout.strip()
        if d:
            return d
    return None

def url_of(page, prefix):
    rel = '' if page == 'index.html' else page
    return f'{SITE}/{prefix}{rel}'

def exists(page, prefix):
    return os.path.exists(page if prefix == '' else prefix + page)

rows = []
for page in pages():
    live = [(code, pre) for code, pre in LANGS if exists(page, pre)]
    mod = lastmod([page] + [pre + page for _, pre in live if pre])
    alts = '\n'.join(
        f'    <xhtml:link rel="alternate" hreflang="{code}" href="{url_of(page, pre)}"/>'
        for code, pre in live)
    alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{url_of(page, "")}"/>'
    for _, pre in live:
        loc = url_of(page, pre)
        mod_tag = f'\n    <lastmod>{mod}</lastmod>' if mod else ''
        rows.append(f'  <url>\n    <loc>{loc}</loc>{mod_tag}\n{alts}\n  </url>')

xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
       '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
       + '\n'.join(rows) + '\n</urlset>\n')
open('sitemap.xml', 'w', encoding='utf-8').write(xml)
print(f'sitemap.xml: {len(pages())} หน้า × {len(LANGS)} ภาษา = {len(rows)} URL')
