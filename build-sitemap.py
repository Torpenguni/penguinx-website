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
        # ไฟล์ร่าง/ทดลองที่ไม่ใช่หน้าจริง: ชื่อขึ้นต้น _ (เช่น _news-section.disabled.html),
        # มี __ (index__f, index__x) หรือ .disabled ถ้าใส่ลง sitemap Google จะเก็บเป็นหน้าซ้ำกับหน้าแรก
        name = os.path.basename(f)
        if name.startswith('_') or '__' in name or '.disabled' in name:
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
    # index.html ในโฟลเดอร์ใช้ URL แบบ /โฟลเดอร์/ ให้ตรงกับ canonical ของหน้า
    rel = page[:-len('index.html')] if page.endswith('index.html') else page
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

# ส่วนที่มีแค่บางภาษา ไม่มีต้นฉบับอังกฤษ (Insights เขียนให้ผู้อ่านไทยก่อน)
# ไม่ใส่ hreflang ข้ามภาษา เพราะไม่มีหน้าคู่ที่เป็นเนื้อหาเดียวกันจริง
LANG_ONLY = ['th/insights/']
for folder in LANG_ONLY:
    for f in sorted(glob.glob(folder + '**/*.html', recursive=True)):
        if os.path.basename(f).startswith('_'):
            continue
        loc = f'{SITE}/' + (f[:-len('index.html')] if f.endswith('index.html') else f)
        mod = lastmod([f])
        mod_tag = f'\n    <lastmod>{mod}</lastmod>' if mod else ''
        rows.append(f'  <url>\n    <loc>{loc}</loc>{mod_tag}\n  </url>')

xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
       '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
       + '\n'.join(rows) + '\n</urlset>\n')
open('sitemap.xml', 'w', encoding='utf-8').write(xml)
print(f'sitemap.xml: {len(pages())} หน้า × {len(LANGS)} ภาษา = {len(rows)} URL')
