#!/usr/bin/env python3
"""สร้างหน้าเว็บภาษาไทยและจีนจากต้นฉบับภาษาอังกฤษ

ทำไมต้องเป็นสคริปต์: 17 หน้า × 2 ภาษา = 34 ไฟล์ที่ต้องตรงกับต้นฉบับทุกจุด
ยกเว้นข้อความ ถ้าก๊อปแก้มือ พอต้นฉบับเปลี่ยนทีเดียว ทั้ง 34 ไฟล์จะเพี้ยน
ตัวนี้อ่านคำแปลจาก i18n/<ภาษา>.json แล้วประกอบใหม่ทุกครั้ง

ใช้:  python3 build-i18n.py            # สร้างทุกหน้า
      python3 build-i18n.py index.html # เฉพาะหน้าที่ระบุ
"""
import json, os, re, sys, glob, urllib.parse
import html as html_lib

LANGS = {
    # keepEnglish: เมนูบนสุดและป้ายที่ติด data-keep-en คงเป็นภาษาอังกฤษในหน้าไทย
    # เจ้าของเว็บต้องการให้ชื่อเมนูและชื่อเสาหลัก (Media/Event/...) เป็นคำเดียวกันทุกภาษา
    'th': {'code': 'th', 'htmlLang': 'th', 'ogLocale': 'th_TH', 'label': 'ไทย',
           'keepEnglish': True},
    # หน้า Events ยังไม่แปลจีน เจ้าของเว็บขอรอเนื้อหานิ่งก่อน
    # ถ้าปล่อยให้สร้าง หน้าจีนจะมีเนื้อหาอังกฤษปนทั้งหน้า จึงกันไว้ทั้งชุด
    'zh': {'code': 'zh', 'htmlLang': 'zh-Hans', 'ogLocale': 'zh_CN', 'label': '中文',
           'alsoHreflang': 'zh-CN'},
    # ญี่ปุ่นเพิ่งเริ่ม ทำเฉพาะหน้าแรกก่อนให้เจ้าของภาษาตรวจ
    # 'only' คือรายชื่อหน้าที่ภาษานั้นมีจริง หน้าที่เหลือจะไม่ถูกสร้าง
    # ไม่ประกาศ hreflang และไม่ขึ้นในปุ่มสลับภาษา จนกว่าจะแปลเพิ่ม
    'ja': {'code': 'ja', 'htmlLang': 'ja', 'ogLocale': 'ja_JP', 'label': '日本語'},
    # เกาหลีเฟส 1: หน้าที่ลูกค้าเกาหลีใช้ตัดสินใจ (หน้าแรก ประวัติ Tor อีเวนต์ และ 4 เสาหลัก)
    # หน้า Work/News ยังไม่แปล ลิงก์จากหน้าเกาหลีจะชี้ฉบับอังกฤษแทน
    # ต้องใส่ทั้งชื่อไฟล์และ URL แบบโฟลเดอร์ (about/tor/) เพราะฟังก์ชันต่าง ๆ ส่งมาคนละแบบ
    'ko': {'code': 'ko', 'htmlLang': 'ko', 'ogLocale': 'ko_KR', 'label': '한국어',
           'only': ('index.html', 'about/tor/index.html', 'about/tor/', 'events.html',
                    'ecosystem/media.html', 'ecosystem/event.html',
                    'ecosystem/education.html', 'ecosystem/solution.html',
                    # 6 หน้าบริการเป็นชั้นตัวตนบริษัท ต้องมีครบทุกภาษา (พ.ย. 2026)
                    'services/exhibit-and-meet.html', 'services/co-host-seminars.html', 'services/brand-storytelling.html',
                    'services/market-testing.html', 'services/partner-matching.html', 'services/team-training.html')},
    # จีนตัวเต็มสำหรับไต้หวันและฮ่องกง (ทั้งสองที่ใช้ Google เป็นหลัก)
    # ไม่มีไฟล์แปลของตัวเอง: สร้างจากคำแปลจีนตัวย่อ (fromLang) แล้วแปลงตัวอักษร
    # ด้วย OpenCC แบบ s2twp (ตัวเต็มไต้หวัน + ปรับศัพท์ เช่น 视频→影片 软件→軟體)
    # ใช้ฉบับเดียวให้ทั้งไต้หวันและฮ่องกง จึงประกาศ hreflang zh-TW และ zh-HK ชี้ URL เดียวกัน
    # เฟส 1 เฉพาะชั้นตัวตนบริษัท: หน้าแรก ประวัติ Tor และ 4 เสาหลัก
    'zh-hant': {'code': 'zh-hant', 'htmlLang': 'zh-Hant', 'ogLocale': 'zh_TW', 'label': '繁體中文',
                'fromLang': 'zh', 'opencc': 's2twp', 'alsoHreflang': ('zh-TW', 'zh-HK'),
                'only': ('index.html', 'about/tor/index.html', 'about/tor/',
                         'ecosystem/media.html', 'ecosystem/event.html',
                         'ecosystem/education.html', 'ecosystem/solution.html',
                         'services/exhibit-and-meet.html', 'services/co-host-seminars.html', 'services/brand-storytelling.html',
                         'services/market-testing.html', 'services/partner-matching.html', 'services/team-training.html')},
}

# ศัพท์ธุรกิจแบบจีนแผ่นดินใหญ่ที่ OpenCC ไม่เปลี่ยน แต่คนไต้หวันใช้อีกคำ
# เรียงคำยาวก่อนคำสั้น (市場營銷 ก่อน 營銷) ไม่งั้นแทนซ้อนกันผิด
# ยังต้องให้คนไต้หวันตรวจรอบสุดท้าย รายการนี้แค่แก้คำที่เห็นชัด
TW_TERMS = (
    ('市場營銷', '行銷'), ('營銷', '行銷'),
    ('特許經營', '加盟'), ('門店', '門市'),
    ('企業培訓', '企業內訓'), ('關注', '追蹤'),
    ('出海泰國', '進軍泰國'), ('品牌出海', '品牌進軍海外'), ('出海', '進軍海外'),
    ('教育項目', '教育計畫'), ('項目', '專案'), ('質量', '品質'),
    # OpenCC แปลงคำสายไอทีผิดบริบท (连接→連線, 循环→迴圈, 发布→釋出, 脚本→指令碼 ฯลฯ)
    ('連線', '串連'), ('迴圈', '循環'), ('迴流', '回流'), ('迴歸', '回歸'),
    ('新品釋出', '新品發表'), ('釋出', '發布'), ('指令碼', '腳本'), ('匯入', '導入'),
    ('裝置', '設備'), ('籤租約', '簽租約'), ('微訊號', '微信 ID'),
    ('平臺', '平台'), ('舞臺', '舞台'), ('登臺', '登台'),
    ('媒體制作', '媒體製作'), ('自制', '自製'),
    # ศัพท์ธุรกิจจีนแผ่นดินใหญ่ → คำที่คนไต้หวันใช้
    ('創始團隊', '創辦團隊'), ('創始人', '創辦人'),
    ('首席行銷官', '行銷長'), ('首席財務官', '財務長'), ('註冊會計師', '會計師'), ('高管', '高階主管'),
    ('運營', '營運'), ('渠道', '通路'), ('全鏈路', '全漏斗'), ('獲客', '名單開發'),
    ('觸達', '觸及'), ('商戶', '店家'), ('外賣', '外送'), ('演講嘉賓', '講者'),
    ('撬動', '帶動'), ('高光時刻', '關鍵時刻'), ('單店盈利模型', '單店獲利模式'), ('單店模型', '單店獲利模式'),
    ('策劃', '企劃'), ('獲取', '取得'), ('反饋', '回饋'), ('對接', '媒合'), ('合作伙伴', '合作夥伴'),
    ('品牌建設', '品牌經營'), ('增長', '成長'), ('初創', '新創'), ('報道', '報導'),
    ('互助網路', '互助圈'), ('同業網路', '同業圈'), ('校友網路', '校友人脈'),
    # OpenCC แปลงผิด (类型→型別, 回复→回複) และคำที่ไต้หวันใช้ต่างไป
    ('型別', '類型'), ('回複', '回覆'), ('社交媒體', '社群媒體'),
    ('策略 PPT', '策略簡報'), ('郵箱', '電子郵件'), ('郵件應用', '郵件 App'),
    # 行業 → 產業 เฉพาะวลีที่เจอ (แทนทั้งคำไม่ได้ เพราะจะไปโดน 進行業務)
    ('餐飲行業', '餐飲產業'), ('行業經驗', '產業經驗'), ('打造行業', '打造產業'), ('行業活動', '產業活動'),
    ('跨行業', '跨產業'), ('行業資訊', '產業資訊'), ('行業研究', '產業研究'), ('這個行業', '這個產業'),
    ('行業洞見', '產業洞見'), ('行業積累', '產業積累'), ('整個行業', '整個產業'), ('行業人脈', '產業人脈'),
    # รอบ 3: อ่านแบบคนไต้หวัน
    ('教育專案', '教育計畫'), ('在讀', '就讀中'), ('房地產', '不動產'),
    ('我們輸出的是', '我們做的是'), ('級別', '等級'), ('演示', '展示'), ('即接入', '即加入'),
    ('策略簡報 帶', '策略簡報帶'), ('幹這一行', '做這一行'),   # 幹 ในไต้หวันเป็นคำหยาบ
    ('戰略合作', '策略合作'), ('戰略聯盟', '策略聯盟'),
    ('更習慣發郵件', '比較習慣寄 Email'),
    # ไต้หวันใช้เครื่องหมายคำพูด 「」 ไม่ใช่ “”
    ('“', '「'), ('”', '」'), ('‘', '『'), ('’', '』'),
)

_OPENCC = {}
def to_traditional(html, profile):
    """แปลงจีนตัวย่อเป็นตัวเต็มทั้งหน้า (ข้อความ, meta, JSON-LD)
    OpenCC แตะเฉพาะอักษรจีน URL และ markup ที่เป็น ASCII ไม่เปลี่ยน"""
    if profile not in _OPENCC:
        import opencc
        _OPENCC[profile] = opencc.OpenCC(profile)
    return _OPENCC[profile].convert(html)

# หน้าที่มีแค่ภาษาอังกฤษ ไม่สร้างฉบับแปล (เช่น เอกสารกฎหมาย ที่ต้องมีฉบับเดียวที่เป็นทางการ)
# ลิงก์จากหน้าภาษาอื่นจะชี้มาฉบับอังกฤษ และไม่ประกาศ hreflang ภาษาอื่น
EN_ONLY = ('privacy.html',)

def has_page(code, rel_path):
    """ภาษานี้มีหน้านี้จริงไหม — ใช้ตัดสินทั้งการสร้างไฟล์ hreflang และปุ่มสลับภาษา
    ถ้าไม่เช็ค จะได้ลิงก์ที่กดแล้ว 404 และ sitemap ที่ประกาศ URL ที่ไม่มีอยู่"""
    cfg = LANGS.get(code)
    if cfg is None:
        return True                       # 'en' คือต้นฉบับ มีทุกหน้าเสมอ
    src = rel_path or 'index.html'
    if src in EN_ONLY:
        return False
    if any(src.startswith(x) for x in cfg.get('skip', ())):
        return False
    only = cfg.get('only')
    return src in only if only else True

def withheld(code, rel_path):
    """หน้าที่ตั้งใจไม่ให้ภาษานี้เห็น (skip) ต่างจากหน้าที่แค่ยังแปลไม่ถึง (only)

    skip = เนื้อหายังไม่พร้อมในภาษานั้น เจ้าของสั่งซ่อน — ต้องลบเมนูทิ้ง
    only = ภาษาใหม่ที่เพิ่งทำหน้าแรก — เมนูยังต้องมี แต่ให้ชี้ฉบับอังกฤษ
           ผู้อ่านยังเดินต่อได้ ดีกว่าเมนูว่างเปล่าหรือกดแล้ว 404
    """
    cfg = LANGS.get(code)
    if cfg is None:
        return False
    src = rel_path or 'index.html'
    return any(src.startswith(x) for x in cfg.get('skip', ()))


def drop_withheld_links(html, code):
    """ตัดรายการเมนูที่ชี้ไปหน้าซึ่งภาษานี้สั่งซ่อนไว้"""
    cfg = LANGS.get(code)
    if not cfg or not cfg.get('skip'):
        return html

    def cut(m):
        url = m.group(1)
        if url.startswith(('http', '#', 'mailto:', 'tel:', '//')):
            return m.group(0)
        target = urllib.parse.unquote(url.lstrip('/').split('#')[0].split('?')[0])
        return '' if withheld(code, target) else m.group(0)

    return re.sub(r'<li>\s*<a href="([^"]+)"[^>]*>.*?</a>\s*</li>', cut, html, flags=re.S)
SITE = 'https://www.penguinx.co'
# ไฟล์ที่ไม่ใช่หน้าเว็บ — ลิงก์พวกนี้ห้ามเติม prefix ภาษา
ASSET = re.compile(r'\.(css|js|png|jpe?g|JPG|JPEG|svg|webp|ico|gif|mp4|pdf|txt|xml|webmanifest|json)$', re.I)

def page_url(src):
    """เส้นทาง URL ของหน้า เทียบกับราก: index.html ในโฟลเดอร์ใช้ URL แบบ /โฟลเดอร์/

    หน้าใหม่ที่อยู่ในโฟลเดอร์ของตัวเอง (เช่น about/tor/index.html) ควรมี
    canonical และ hreflang เป็น /about/tor/ ไม่ใช่ /about/tor/index.html
    ไม่งั้น Google จะเห็นสอง URL สำหรับหน้าเดียว"""
    return re.sub(r'(^|/)index\.html$', r'\1', src)

def pages():
    out = []
    for f in glob.glob('**/*.html', recursive=True):
        # _template.html is linked from the news page and serves 200 in
        # production, so it needs a translated twin or those links 404 in
        # Thai and Chinese. Only the design previews are genuinely excluded.
        # โฟลเดอร์ผลลัพธ์ของทุกภาษาต้องไม่ถูกนับเป็นต้นฉบับ อ่านจาก LANGS
        # ไม่ใช่เขียนชื่อไว้ตรงนี้ ไม่งั้นเพิ่มภาษาใหม่แล้วลืมมาแก้
        # ตัวสร้างจะกลับไปแปลไฟล์ที่ตัวเองเพิ่งเขียนออกมา
        outdirs = tuple(f'{c}/' for c in LANGS)
        if 'preview-' in f or f.startswith(outdirs) or any('/' + d in f for d in outdirs):
            continue
        out.append(f)
    return sorted(out)

LANG_LABELS = (('en', 'EN'), ('th', 'ไทย'), ('zh', '简体中文'), ('zh-hant', '繁體中文'), ('ja', '日本語'), ('ko', '한국어'))

# ป้ายของปุ่มเปิดเมนู เขียนไว้ตรงนี้เพราะ switcher ถูกแทรกหลัง translate_text
# ทำงานเสร็จแล้ว ตัวแปลรายคำจึงมองไม่เห็น aria-label ตัวนี้
SWITCH_ARIA = {'en': 'Change language', 'th': 'เปลี่ยนภาษา', 'zh': '切换语言', 'zh-hant': '切換語言',
               'ja': '言語を切り替える', 'ko': '언어 변경'}


def switcher(rel_path, current):
    """rel_path = เส้นทางหน้าเทียบกับราก เช่น '' หรือ 'work/makro.html'

    เป็น <details> ไม่ใช่เมนูที่สร้างด้วย JavaScript โดยตั้งใจ ลิงก์ทุกภาษา
    อยู่ใน HTML ตั้งแต่แรกเสมอ แค่ถูกซ่อนด้วย CSS — Google จึงยังเดินตาม
    ลิงก์ไปเจอทุกเวอร์ชันภาษาได้ ถ้าสร้างเมนูตอนคลิกด้วย JS ลิงก์เหล่านี้
    จะหายไปจากสายตา crawler แล้ว hreflang ก็จะไม่มีอะไรมาหนุน

    และเพราะไม่พึ่ง JS เลย ปุ่มจึงยังใช้ได้ถ้าสคริปต์โหลดไม่ขึ้น
    """
    def href(code):
        base = '/' if code == 'en' else f'/{code}/'
        return base + rel_path
    items, now = [], ''
    for code, label in LANG_LABELS:
        if not has_page(code, rel_path):
            continue          # ยังไม่มีหน้านี้ในภาษานั้น อย่าให้กดไปเจอ 404
        cur = ''
        if code == current:
            cur, now = ' aria-current="true"', label
        items.append(f'<a href="{href(code)}" hreflang="{code}"{cur}>{label}</a>')
    aria = SWITCH_ARIA.get(current, SWITCH_ARIA['en'])
    return ('<details class="lang-switch">'
            f'<summary aria-label="{aria}">{now}</summary>'
            f'<div class="lang-menu">{"".join(items)}</div>'
            '</details>')


def hreflangs(rel_path):
    rows = [f'<link rel="alternate" hreflang="en" href="{SITE}/{rel_path}">']
    for code in LANGS:
        # ภาษาที่ยังไม่ได้แปลหน้านี้ ห้ามประกาศ hreflang ไม่งั้นชี้ไปหน้าที่ไม่มีอยู่
        if not has_page(code, rel_path):
            continue
        rows.append(f'<link rel="alternate" hreflang="{LANGS[code]["htmlLang"]}" href="{SITE}/{code}/{rel_path}">')
        # Baidu ตีความ region code (zh-CN) ได้ดีกว่า script code (zh-Hans)
        # ประกาศทั้งคู่ ไม่ขัดกันเพราะชี้ URL เดียวกัน
        also = LANGS[code].get('alsoHreflang') or ()
        for alt in ((also,) if isinstance(also, str) else also):
            rows.append(f'<link rel="alternate" hreflang="{alt}" href="{SITE}/{code}/{rel_path}">')
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

def keep_english(html, code, keep):
    """ภาษาที่ตั้ง keepEnglish: ล็อกเมนูบนสุด (ยกเว้นปุ่ม CTA) และลิงก์/ป้าย
    (a, div, span) ที่มี data-keep-en ไว้เป็นภาษาอังกฤษ

    ใช้ตัวแทนแบบเดียวกับ translate_blocks เพราะ translate_text แปลตามข้อความ
    ล้วน ๆ ไม่รู้บริบท ถ้าลบคำว่า "Media" ออกจากไฟล์แปลแทน หัวข้อและการ์ด
    ทุกที่ที่ใช้คำเดียวกันจะกลายเป็นอังกฤษตามไปด้วย
    ใส่ lang="en" ให้ด้วย โปรแกรมอ่านหน้าจอจะได้ออกเสียงถูก
    ตัวแทนเป็น comment ของ HTML เพื่อให้ข้อความที่ตามหลังลิงก์ (": Torpenguin ...")
    ยังเป็น text node แยกที่ตัวแปลจับได้ ถ้าใช้ตัวแทนเป็นข้อความธรรมดา
    มันจะไปติดหน้าประโยคแล้วประโยคนั้นจะไม่ถูกแปล"""
    if not LANGS[code].get('keepEnglish'):
        return html

    def lock(fragment):
        token = f'<!--PXKEEP{len(keep)}-->'
        keep[token] = re.sub(r'<(a|div|span) ', r'<\1 lang="en" ', fragment, count=1)
        return token

    def nav(m):
        return re.sub(r'<li[^>]*>\s*<a [^>]*>[^<]*</a>\s*</li>',
                      lambda li: li.group(0) if 'nav-cta' in li.group(0) else lock(li.group(0)),
                      m.group(0))
    html = re.sub(r'<ul class="nav-links">.*?</ul>', nav, html, count=1, flags=re.S)
    html = re.sub(r'<(a|div|span) [^>]*\bdata-keep-en\b[^>]*>[^<]*</\1>', lambda m: lock(m.group(0)), html)
    return html

def keep_english_headings(html, code, keep, src=''):
    """หัวข้อ (h1/h2) ที่ติด data-keep-en คงภาษาอังกฤษในภาษาที่ตั้ง keepEnglish

    เจ้าของเว็บต้องการให้หัวข้อ section ในหน้าไทยเป็นภาษาอังกฤษ (พ.ย. 2026)
    เพราะอ่านแล้วเข้าใจง่ายกว่า เนื้อหาข้างใต้ยังเป็นภาษาไทย
    ต้องรันก่อน translate_blocks เพราะหัวข้อพวกนี้มีคำแปลทั้งก้อนใน _html
    และหัวข้อมี <span> ซ้อนอยู่ข้างใน keep_english (ที่จับเฉพาะ element ไม่มีลูก) จึงจับไม่ได้"""
    if not LANGS[code].get('keepEnglish'):
        # ภาษาอื่นแปลหัวข้อตามปกติ คำแปลทั้งก้อนใน _html จับจากแท็กเปิดแบบตรงตัว
        # ถ้าไม่ลบ attribute นี้ทิ้ง หัวข้อจีน/ญี่ปุ่น/เกาหลีจะกลายเป็นอังกฤษหมด
        return re.sub(r'(<(?:h1|h2|div class="(?:section|shorts)-num"|div class="eco-name")[^>]*?) data-keep-en', r'\1', html)

    def lock(m):
        token = f'<!--PXKEEP{len(keep)}-->'
        keep[token] = re.sub(r'^<(h1|h2|div)\b', r'<\1 lang="en"', m.group(0), count=1)
        return token
    # หน้าแรกเลือกเป็นรายหัวข้อด้วย data-keep-en ส่วนหน้าตัวตนบริษัทอื่น (ประวัติ Tor,
    # 4 เสาหลัก, อีเวนต์, ผลงาน) ใช้หัวข้อ h1/h2 ภาษาอังกฤษทั้งหน้า
    # ไม่รวม news/ เพราะพาดหัวข่าวเป็นเนื้อหาที่คนไทยค้นหาและอ่าน
    rel = src.replace('\\', '/')
    whole_page = rel != 'index.html' and not rel.startswith('news/')
    pat = (r'<(h1|h2)\b[^>]*>.*?</\1>' if whole_page
           else r'<(h1|h2)\b[^>]*\bdata-keep-en\b[^>]*>.*?</\1>')
    html = re.sub(pat, lock, html, flags=re.S)
    # ชื่อเสาหลักบนการ์ด (Media / Storytelling) มี <span> ซ้อน ใช้ชื่อเดียวกันทุกภาษา
    return re.sub(r'<div class="eco-name" data-keep-en>.*?</div>', lock, html, flags=re.S)

CJK_CH = r'[぀-ヿ㐀-鿿＀-￯　-〿]'

def cjk_join(html, code):
    """ญี่ปุ่น/จีนไม่เว้นวรรคระหว่างคำ

    หัวข้อที่ต้นฉบับอังกฤษแบ่งคำเป็นหลาย <span> คั่นด้วยช่องว่าง พอแปลทีละชิ้น
    ช่องว่างนั้นติดมาด้วย เลยได้ "同一个 生态系统" "品牌 与 经营者"
    ตัดช่องว่างที่อยู่ระหว่างตัวอักษรจีน/ญี่ปุ่นสองตัวที่คั่นด้วย tag เท่านั้น
    ช่องว่างข้างตัวละติน (PenguinX 如何) ไม่แตะ"""
    if code not in ('zh', 'ja'):
        return html
    tag = r'(?:</?span[^>]*>)+'
    pat = re.compile(r'(' + CJK_CH + r')((?:' + tag + r')?)\s+((?:' + tag + r')?)(?=' + CJK_CH + r')')
    def fix(m):
        if not (m.group(2) or m.group(3)):
            return m.group(0)          # ข้อความล้วนไม่มี tag คั่น ปล่อยไว้ตามคำแปล
        return m.group(1) + m.group(2) + m.group(3)
    return pat.sub(fix, html)

# ---- ตัดบรรทัดหัวข้อภาษาญี่ปุ่น/จีนตามวลี -------------------------------
# ภาษาที่ไม่มีเว้นวรรคถูกเบราว์เซอร์ตัดได้ทุกตัวอักษร หัวข้อเลยแตกกลางคำ
# ("みん|な" "泰|国") ใส่ <wbr> ไว้ระหว่างวลี แล้วให้ CSS (word-break:keep-all)
# ตัดเฉพาะตรงนั้น ใช้ได้ทุกเบราว์เซอร์รวม Safari บน iPhone
# ญี่ปุ่นใช้ BudouX (ของ Google) จีนใช้ jieba ซึ่งแบ่งคำจีนแม่นกว่า
# ถ้ายังไม่ได้ติดตั้ง: pip install budoux jieba  (ไม่มีก็ build ได้ แค่ไม่ใส่ <wbr>)
TITLE_CLASSES = ('hero-title', 'section-title', 'cta-title', 'shorts-title', 'vp-title',
                 'ev-title', 'evd-title', 'article-title', 'news-title', 'ev-name',
                 'eco-name', 'case-name', 'pg-item-title')
_SEGMENTERS = {}

def _segmenter(code):
    if code in _SEGMENTERS:
        return _SEGMENTERS[code]
    seg = None
    try:
        if code == 'ja':
            import budoux
            seg = budoux.load_default_japanese_parser().parse
        elif code == 'zh':
            import jieba, logging
            jieba.setLogLevel(logging.WARNING)
            # คำเฉพาะของเว็บที่ jieba ไม่รู้จัก ถ้าไม่บอกจะตัดเป็น "全|链路" "联合|主办"
            for w in ('全链路', '生态系统', '获客', '餐旅展', '会展场馆', '联合主办', '单店经济模型',
                      '经营者', '夜生活', '品牌认知', '商业对接', '餐饮企业'):
                jieba.add_word(w)
            GLUE = {'的', '了', '地', '得', '之', '们'}
            def seg(text):
                out = []
                for w in jieba.cut(text):
                    if out and (w in GLUE or w[:1] in '，。、：；！？）」”'):
                        out[-1] += w          # คำเชื่อม/เครื่องหมาย ห้ามขึ้นต้นบรรทัด
                    else:
                        out.append(w)
                return out
    except ImportError:
        print(f'  ! ไม่พบตัวตัดวลีภาษา {code} — pip install budoux jieba แล้ว build ใหม่')
    _SEGMENTERS[code] = seg
    return seg

def cjk_phrases(html, code):
    seg = _segmenter(code) if code in ('ja', 'zh') else None
    if not seg:
        return html
    def text_part(m):
        t = m.group(1)
        if not re.search(CJK_CH, t):
            return m.group(0)
        parts = [p for p in seg(t) if p]
        out = parts[0]
        for p in parts[1:]:
            # ใส่ <wbr> เฉพาะระหว่างอักษรจีน/ญี่ปุ่นสองตัว ห้ามแทรกกลางตัวเลขหรือคำอังกฤษ
            # ไม่งั้น "4,500" จะถูกตัดเป็น "4, | 500"
            if re.match(CJK_CH, out[-1]) and re.match(CJK_CH, p[0]):
                out += '<wbr>' + p
            else:
                out += p
        return '>' + out + '<'
    def element(m):
        # หัวข้อที่กำหนดวลีเองด้วย .nw ในไฟล์แปลแล้ว ไม่ต้องแตะ
        # <wbr> ที่อยู่ใน nowrap ยังเป็นจุดตัดได้ ถ้าใส่เพิ่มจะไปทำลายวลีที่ตั้งใจไว้
        if re.search(r'class="[^"]*\bnw\b', m.group(0)):
            return m.group(0)
        return re.sub(r'>([^<>]+)<', text_part, m.group(0))
    cls = '|'.join(TITLE_CLASSES)
    pat = re.compile(r'<(h[1-3]|div)\b[^>]*class="[^"]*\b(?:' + cls + r')\b[^"]*"[^>]*>.*?</\1>', re.S)
    return pat.sub(element, html)

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
        # HTML เขียน &amp; แต่คีย์ในไฟล์แปลเขียน & ตรง ๆ เหมือนกรณี attribute
        # ไม่ลองทั้งสองแบบ ประโยคที่มี & อย่าง "global & F&B brands"
        # จะไม่ถูกแปลเลยทุกภาษา
        for k in (key, key.replace('&amp;', '&')):
            if k in tmap:
                return '>' + raw.replace(key, tmap[k]) + '<'
        return m.group(0)
    html = re.sub(r'>([^<>]+)<', node, html)

    def attr(m):
        name, val = m.group(1), m.group(2)
        # HTML เขียน &amp; แต่คีย์ในไฟล์แปลเขียน & ตรง ๆ ต้องลองทั้งสองแบบ
        # ไม่งั้น meta description ที่มีคำว่า F&B จะไม่ถูกแปลเลย
        for k in (val, val.replace('&amp;', '&')):
            if k in tmap:
                return f'{name}="{tmap[k]}"'
        return m.group(0)
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
    """ลิงก์ภายในให้อยู่ในภาษาเดียวกัน ส่วนไฟล์ภาพ/CSS ปล่อยชี้รากเหมือนเดิม

    ภาษาที่ยังแปลไม่ครบทุกหน้า (เช่นญี่ปุ่นที่มีแค่หน้าแรก) ห้ามเปลี่ยน
    ลิงก์ไปหน้าที่ยังไม่มี ไม่งั้นกดแล้วเจอ 404 กรณีนั้นให้ชี้ไปฉบับ
    ภาษาอังกฤษไว้ก่อน ผู้ใช้ยังอ่านได้ ดีกว่าหน้าไม่พบ"""
    def fix(m):
        pre, url = m.group(1), m.group(2)
        if url.startswith(('http', '#', 'mailto:', 'tel:', '//')) or ASSET.search(url):
            return m.group(0)
        if url == '/':
            return f'{pre}"/{code}/"' if has_page(code, '') else m.group(0)
        if url.startswith(tuple(f'/{c}/' for c in LANGS)):
            return m.group(0)              # ชี้หน้าภาษาเฉพาะอยู่แล้ว เช่น /th/insights/
        if url.startswith('/'):
            target = urllib.parse.unquote(url.lstrip('/').split('#')[0].split('?')[0])
            if not has_page(code, target):
                return m.group(0)          # ปล่อยชี้หน้าอังกฤษ
            return f'{pre}"/{code}{url}"'
        return m.group(0)
    return re.sub(r'(href=)"([^"]+)"', fix, html)


def drop_only_th(html, code):
    """เมนูที่ชี้ไปหน้าซึ่งมีแค่ภาษาไทย (เช่น Insights) ใส่ class="only-th"

    ฉบับจีน/ญี่ปุ่นตัดทิ้งไปเลย ส่วนต้นฉบับอังกฤษซ่อนด้วย CSS
    (html:not([lang="th"]) .only-th) เพราะไฟล์อังกฤษถูกเสิร์ฟตรงจากต้นฉบับ"""
    if code == 'th':
        return html
    html = re.sub(r'\s*<li class="only-th">.*?</li>', '', html, flags=re.S)
    html = re.sub(r'\s*<a class="only-th"[^>]*>.*?</a>', '', html, flags=re.S)
    return html


def strip_injected(html):
    """เอาของที่สคริปต์เคยใส่ไว้ออกก่อนเสมอ
    ไม่งั้นรันซ้ำทีไร hreflang กับปุ่มสลับภาษาจะทบกันไปเรื่อย ๆ"""
    html = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*" href="[^"]*">', '', html)
    html = re.sub(r'\s*<div class="lang-switch">.*?</div>', '', html, flags=re.S)
    html = re.sub(r'\s*<details class="lang-switch">.*?</details>', '', html, flags=re.S)
    html = re.sub(r'\s*<script>window\.__PX_I18N__=.*?</script>', '', html, flags=re.S)
    return html

def sync_faq_schema(html):
    """สร้าง FAQPage JSON-LD จากคำถาม-คำตอบที่มองเห็นบนหน้า (<details class="faq-item">)

    Google กำหนดให้ข้อความใน FAQ schema ตรงกับที่ผู้อ่านเห็นบนหน้า
    ตัวแปลรายคำแปล JSON-LD ไม่ได้ (ทั้งก้อนเป็น text node เดียว) ถ้าไม่สร้างใหม่
    หน้าไทย/จีน/ญี่ปุ่นจะมี schema ภาษาอังกฤษไม่ตรงกับหน้า จึงอ่านจาก HTML ที่แปลแล้วทุกครั้ง
    ใช้กับหน้าที่มี <script type="application/ld+json" id="faq-schema"> เท่านั้น"""
    slot = re.compile(r'<script type="application/ld\+json" id="faq-schema">.*?</script>', re.S)
    if not slot.search(html):
        return html
    def clean(fragment):
        text = html_lib.unescape(re.sub(r'<[^>]+>', '', fragment))
        return re.sub(r'\s+', ' ', text).strip()
    qa = re.findall(r'<details class="faq-item">\s*<summary>(.*?)</summary>\s*<div class="faq-a">(.*?)</div>\s*</details>',
                    html, re.S)
    data = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': clean(q), 'acceptedAnswer': {'@type': 'Answer', 'text': clean(a)}}
        for q, a in qa]}
    body = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    return slot.sub(lambda m: f'<script type="application/ld+json" id="faq-schema">{body}</script>', html, count=1)

def build(src, code):
    cfg = LANGS[code]
    tcode = cfg.get('fromLang', code)     # จีนตัวเต็มใช้คำแปลของจีนตัวย่อ
    tmap = json.load(open(f'i18n/{tcode}.json', encoding='utf-8'))
    html = strip_injected(open(src, encoding='utf-8').read())
    rel = page_url(src)

    blocks = tmap.pop('_html', {})
    cfg_js = tmap.pop('_js', {})

    html = localise_assets(html, src)
    html = localise_links(html, code)
    html = drop_withheld_links(html, code)
    html = drop_only_th(html, code)
    kept = {}
    html = keep_english_headings(html, tcode, kept, src)
    html = translate_blocks(html, blocks, kept)
    html = keep_english(html, tcode, kept)
    html = translate_text(html, tmap)
    for token, dst in kept.items():
        html = html.replace(token, dst, 1)
    html = cjk_join(html, tcode)
    html = cjk_phrases(html, tcode)
    html = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + '\n' + js_config(cfg_js), html, count=1)
    # แปลงตัวเต็มก่อนใส่ปุ่มสลับภาษา ไม่งั้นป้าย "简体中文" ในเมนูจะถูกแปลงไปด้วย
    if cfg.get('opencc'):
        html = to_traditional(html, cfg['opencc'])
        for cn, tw in TW_TERMS:
            html = html.replace(cn, tw)
    html = sync_faq_schema(html)
    html = re.sub(r'<html[^>]*>', f'<html lang="{cfg["htmlLang"]}">', html, count=1)
    html = html.replace('<meta property="og:locale" content="en_US">',
                        f'<meta property="og:locale" content="{cfg["ogLocale"]}">')
    html = re.sub(r'<link rel="canonical" href="[^"]*">',
                  f'<link rel="canonical" href="{SITE}/{code}/{rel}">', html, count=1)
    html = re.sub(r'<meta property="og:url" content="[^"]*">',
                  f'<meta property="og:url" content="{SITE}/{code}/{rel}">', html, count=1)
    html = html.replace('<link rel="canonical"', hreflangs(rel) + '\n<link rel="canonical"', 1)
    if code == 'zh':
        # Baidu: ห้ามแปลงหน้า (转码) เป็นหน้ามือถือของ Baidu เอง และบอกว่าเว็บเป็น responsive
        # ไม่ต้องมีบัญชี Baidu Webmaster ก็ใช้ได้
        html = html.replace('<link rel="canonical"',
            '<meta http-equiv="Cache-Control" content="no-transform">\n'
            '<meta http-equiv="Cache-Control" content="no-siteapp">\n'
            '<meta name="applicable-device" content="pc,mobile">\n<link rel="canonical"', 1)

    sw = switcher(rel, code)
    html = re.sub(r'(<ul class="nav-links">.*?</ul>)', r'\1\n  ' + sw, html, count=1, flags=re.S)

    dst = os.path.join(code, src)
    os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
    open(dst, 'w', encoding='utf-8').write(html)
    return dst

def add_switcher_to_english(src):
    html = strip_injected(open(src, encoding='utf-8').read())
    rel = page_url(src)
    html = re.sub(r'(<ul class="nav-links">.*?</ul>)', r'\1\n  ' + switcher(rel, 'en'),
                  html, count=1, flags=re.S)
    html = html.replace('<link rel="canonical"', hreflangs(rel) + '\n<link rel="canonical"', 1)
    html = sync_faq_schema(html)
    open(src, 'w', encoding='utf-8').write(html)

if __name__ == '__main__':
    targets = sys.argv[1:] or pages()
    for src in targets:
        add_switcher_to_english(src)
        for code in LANGS:
            if not has_page(code, src):
                continue
            print('  สร้าง', build(src, code))
    print(f'\nเสร็จ {len(targets)} หน้า × {len(LANGS)} ภาษา')
