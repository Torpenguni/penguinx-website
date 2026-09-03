#!/usr/bin/env python3
"""สร้างหน้าเว็บภาษาไทยและจีนจากต้นฉบับภาษาอังกฤษ

ทำไมต้องเป็นสคริปต์: 17 หน้า × 2 ภาษา = 34 ไฟล์ที่ต้องตรงกับต้นฉบับทุกจุด
ยกเว้นข้อความ ถ้าก๊อปแก้มือ พอต้นฉบับเปลี่ยนทีเดียว ทั้ง 34 ไฟล์จะเพี้ยน
ตัวนี้อ่านคำแปลจาก i18n/<ภาษา>.json แล้วประกอบใหม่ทุกครั้ง

ใช้:  python3 build-i18n.py            # สร้างทุกหน้า
      python3 build-i18n.py index.html # เฉพาะหน้าที่ระบุ
"""
import json, os, re, sys, glob

LANGS = {
    'th': {'code': 'th', 'htmlLang': 'th', 'ogLocale': 'th_TH', 'label': 'ไทย'},
    'zh': {'code': 'zh', 'htmlLang': 'zh-Hans', 'ogLocale': 'zh_CN', 'label': '中文'},
}
SITE = 'https://www.penguinx.co'
# ไฟล์ที่ไม่ใช่หน้าเว็บ — ลิงก์พวกนี้ห้ามเติม prefix ภาษา
ASSET = re.compile(r'\.(css|js|png|jpe?g|JPG|JPEG|svg|webp|ico|gif|mp4|pdf|txt|xml)$', re.I)

def pages():
    out = []
    for f in glob.glob('**/*.html', recursive=True):
        # _template.html is linked from the news page and serves 200 in
        # production, so it needs a translated twin or those links 404 in
        # Thai and Chinese. Only the design previews are genuinely excluded.
        if any(x in f for x in ('preview-', '/th/', '/zh/')) or f.startswith(('th/', 'zh/')):
            continue
        out.append(f)
    return sorted(out)

def switcher(rel_path, current):
    """rel_path = เส้นทางหน้าเทียบกับราก เช่น '' หรือ 'work/makro.html'"""
    def href(code):
        base = '/' if code == 'en' else f'/{code}/'
        return base + rel_path
    items = []
    for code, label in (('en', 'EN'), ('th', 'ไทย'), ('zh', '中文')):
        cur = ' aria-current="true"' if code == current else ''
        items.append(f'<a href="{href(code)}" hreflang="{code}"{cur}>{label}</a>')
    return '<div class="lang-switch">' + ''.join(items) + '</div>'

def hreflangs(rel_path):
    rows = [f'<link rel="alternate" hreflang="en" href="{SITE}/{rel_path}">']
    for code in LANGS:
        rows.append(f'<link rel="alternate" hreflang="{LANGS[code]["htmlLang"]}" href="{SITE}/{code}/{rel_path}">')
    rows.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}/{rel_path}">')
    return '\n'.join(rows)

def translate_blocks(html, blocks, keep):
    """เก็บผลลัพธ์ไว้เป็นรหัสแทน แล้วค่อยใส่กลับหลังแปลรายคำเสร็จ

    ถ้าปล่อยไว้เฉย ๆ ตัวแปลรายคำจะไล่แปลข้อความข้างในบล็อกซ้ำอีกรอบ
    ทำให้บล็อกที่ตั้งใจให้คงภาษาอังกฤษ (เช่นการ์ด ecosystem ในหน้าไทย)
    ถูกแปลทับ การแทนทั้งก้อนต้องถือเป็นที่สิ้นสุด"""
    """แทนทั้งก้อน HTML สำหรับหัวข้อที่คำถูกหั่นเป็นหลาย <span>

    ตัวแทนรายคำ (translate_text) ทำหัวข้อพวกนี้ไม่ได้ เพราะคำอย่าง "us"/"to"
    อยู่คนละ element กัน แปลทีละชิ้นแล้วเรียงกลับมาจะได้ประโยคที่ผิดไวยากรณ์
    จีน/ไทย ก้อนพวกนี้จึงต้องเขียนใหม่ทั้งอันพร้อมกำหนดจุดขึ้นบรรทัดเอง
    จับแบบยืดหยุ่นช่องว่าง เพราะต้นฉบับจัดย่อหน้าไว้หลายบรรทัด"""
    for i, (src, dst) in enumerate(blocks.items()):
        pattern = r'\s+'.join(re.escape(w) for w in src.split())
        token = f'\x00BLOCK{i}\x00'
        html, n = re.subn(pattern, lambda m, t=token: t, html, count=1)
        if n:
            keep[token] = dst
    return html

def js_config(cfg_js):
    """ส่งคำแปลให้สคริปต์ฝั่งเบราว์เซอร์ (การ์ดวิดีโอ render ด้วย JS)"""
    if not cfg_js:
        return ''
    return '<script>window.__PX_I18N__=' + json.dumps(cfg_js, ensure_ascii=False) + ';</script>'

def translate_text(html, tmap):
    """แทนข้อความที่มองเห็น + attribute ที่ผู้ใช้อ่าน โดยไม่แตะโครงสร้าง"""
    def node(m):
        raw = m.group(1)
        key = raw.strip()
        if key in tmap:
            return '>' + raw.replace(key, tmap[key]) + '<'
        return m.group(0)
    html = re.sub(r'>([^<>]+)<', node, html)

    def attr(m):
        name, val = m.group(1), m.group(2)
        return f'{name}="{tmap[val]}"' if val in tmap else m.group(0)
    html = re.sub(r'\b(content|alt|title|placeholder|aria-label)="([^"]+)"', attr, html)
    return html

def localise_assets(html, src_page):
    """path รูป/ไฟล์แบบสัมพัทธ์ต้องเปลี่ยนเป็นอ้างจากราก

    ต้นฉบับอยู่ที่รากเว็บ src="Community/x.png" จึงชี้ถูก แต่ฉบับแปลถูกย้าย
    ไปอยู่ /zh/ เบราว์เซอร์จะไปหาที่ /zh/Community/x.png ซึ่งไม่มีอยู่จริง
    ผลคือรูปทั้งหน้าไม่ขึ้น เปลี่ยนเป็น /Community/x.png ให้ชี้ที่เดียวกัน
    ทุกภาษาและทุกความลึกของโฟลเดอร์"""
    base = os.path.dirname(src_page)
    SKIP = ('http://', 'https://', '//', '/', '#', 'data:', 'mailto:', 'tel:', 'javascript:')

    def to_root(url):
        # '${...}' คือ template literal ในสคริปต์ ค่าจริงเกิดตอนรัน ห้ามแตะ
        if not url or '${' in url or url.startswith(SKIP):
            return None
        return '/' + os.path.normpath(os.path.join(base, url)).replace(os.sep, '/')

    def fix_attr(m):
        new = to_root(m.group(2))
        return f'{m.group(1)}="{new}"' if new else m.group(0)
    html = re.sub(r'\b(src|poster)="([^"]+)"', fix_attr, html)

    def fix_url(m):
        quote, new = m.group(1), to_root(m.group(2))
        return f'url({quote}{new}{quote})' if new else m.group(0)
    html = re.sub(r'url\((["\']?)([^"\')]+)\1\)', fix_url, html)
    return html

def localise_links(html, code):
    """ลิงก์ภายในให้อยู่ในภาษาเดียวกัน ส่วนไฟล์ภาพ/CSS ปล่อยชี้รากเหมือนเดิม"""
    def fix(m):
        pre, url = m.group(1), m.group(2)
        if url.startswith(('http', '#', 'mailto:', 'tel:', '//')) or ASSET.search(url):
            return m.group(0)
        if url == '/':
            return f'{pre}"/{code}/"'
        if url.startswith('/'):
            return f'{pre}"/{code}{url}"'
        return m.group(0)
    return re.sub(r'(href=)"([^"]+)"', fix, html)


def strip_injected(html):
    """เอาของที่สคริปต์เคยใส่ไว้ออกก่อนเสมอ
    ไม่งั้นรันซ้ำทีไร hreflang กับปุ่มสลับภาษาจะทบกันไปเรื่อย ๆ"""
    html = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*" href="[^"]*">', '', html)
    html = re.sub(r'\s*<div class="lang-switch">.*?</div>', '', html, flags=re.S)
    html = re.sub(r'\s*<script>window\.__PX_I18N__=.*?</script>', '', html, flags=re.S)
    return html

def build(src, code):
    cfg = LANGS[code]
    tmap = json.load(open(f'i18n/{code}.json', encoding='utf-8'))
    html = strip_injected(open(src, encoding='utf-8').read())
    rel = '' if src == 'index.html' else src

    blocks = tmap.pop('_html', {})
    cfg_js = tmap.pop('_js', {})

    html = localise_assets(html, src)
    html = localise_links(html, code)
    kept = {}
    html = translate_blocks(html, blocks, kept)
    html = translate_text(html, tmap)
    for token, dst in kept.items():
        html = html.replace(token, dst, 1)
    html = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + '\n' + js_config(cfg_js), html, count=1)
    html = re.sub(r'<html[^>]*>', f'<html lang="{cfg["htmlLang"]}">', html, count=1)
    html = html.replace('<meta property="og:locale" content="en_US">',
                        f'<meta property="og:locale" content="{cfg["ogLocale"]}">')
    html = re.sub(r'<link rel="canonical" href="[^"]*">',
                  f'<link rel="canonical" href="{SITE}/{code}/{rel}">', html, count=1)
    html = re.sub(r'<meta property="og:url" content="[^"]*">',
                  f'<meta property="og:url" content="{SITE}/{code}/{rel}">', html, count=1)
    html = html.replace('<link rel="canonical"', hreflangs(rel) + '\n<link rel="canonical"', 1)

    sw = switcher(rel, code)
    html = re.sub(r'(<ul class="nav-links">.*?</ul>)', r'\1\n  ' + sw, html, count=1, flags=re.S)

    dst = os.path.join(code, src)
    os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
    open(dst, 'w', encoding='utf-8').write(html)
    return dst

def add_switcher_to_english(src):
    html = strip_injected(open(src, encoding='utf-8').read())
    rel = '' if src == 'index.html' else src
    html = re.sub(r'(<ul class="nav-links">.*?</ul>)', r'\1\n  ' + switcher(rel, 'en'),
                  html, count=1, flags=re.S)
    html = html.replace('<link rel="canonical"', hreflangs(rel) + '\n<link rel="canonical"', 1)
    open(src, 'w', encoding='utf-8').write(html)

if __name__ == '__main__':
    targets = sys.argv[1:] or pages()
    for src in targets:
        add_switcher_to_english(src)
        for code in LANGS:
            print('  สร้าง', build(src, code))
    print(f'\nเสร็จ {len(targets)} หน้า × {len(LANGS)} ภาษา')
