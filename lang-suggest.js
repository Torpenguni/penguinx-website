/* แถบแนะนำภาษา
 *
 * ถ้าภาษาของเบราว์เซอร์ไม่ตรงกับภาษาของหน้า และเว็บมีหน้าภาษานั้น ให้ขึ้นแถบเล็ก ๆ ชวนไปอ่าน
 * เป็นภาษาของผู้อ่าน
 *
 * ทำไมไม่พาไปหน้าภาษาอัตโนมัติ: Google แนะนำไม่ให้ redirect ตามภาษาที่เดาเอา
 * เพราะ Googlebot ส่วนใหญ่เข้าจากสหรัฐฯ จะเห็นแต่ภาษาอังกฤษ แล้วหน้าภาษาอื่นหลุดจาก Google
 * และคนที่ตั้งเบราว์เซอร์คนละภาษากับที่อยากอ่านจะติดอยู่ภาษาเดียว แถบนี้ไม่เปลี่ยนเนื้อหาของหน้า
 *
 * หาหน้าปลายทางจาก <link rel="alternate" hreflang> ของหน้านั้นก่อน
 * ถ้าหน้านั้นไม่มีฉบับภาษานั้น และกำลังอยู่หน้าภาษาอังกฤษ ให้ชวนไปหน้าแรกของภาษานั้นแทน
 * (เช่นคนญี่ปุ่นที่เข้าหน้าอังกฤษ จะถูกชวนไป /ja/ ซึ่งมีทางเข้า 3 กลุ่มลูกค้า)
 *
 * ปิดแถบ หรือเลือกภาษาจากปุ่มสลับภาษาแล้ว จะไม่ขึ้นอีก (จำไว้ใน localStorage ของเบราว์เซอร์นั้น)
 */
(function () {
  var KEY = 'px-lang-pref';
  var LANGS = {
    en: { home: '/',    msg: 'This page is available in English.', cta: 'View in English' },
    th: { home: '/th/', msg: 'หน้านี้มีภาษาไทย',                    cta: 'อ่านภาษาไทย' },
    zh: { home: '/zh/', msg: '本页面有中文版。',                      cta: '查看中文版' },
    ja: { home: '/ja/', msg: '日本語のページがあります。',              cta: '日本語で見る' },
    ko: { home: '/ko/', msg: '한국어 페이지가 있습니다.',              cta: '한국어로 보기' }
  };
  var CLOSE = { en: 'Close', th: 'ปิด', zh: '关闭', ja: '閉じる', ko: '닫기' };

  function norm(tag) {
    tag = String(tag || '').toLowerCase();
    var base = tag.split('-')[0];
    return LANGS[base] ? base : null;
  }
  function store(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }

  // เลือกภาษาจากปุ่มสลับภาษาเอง = ตัดสินใจแล้ว ไม่ต้องชวนอีก
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest && e.target.closest('.lang-menu a[hreflang]');
    if (a) store(norm(a.getAttribute('hreflang')) || 'chosen');
  });

  if (stored()) return;
  if (navigator.webdriver || /bot|crawl|spider|slurp|preview/i.test(navigator.userAgent)) return;

  var page = norm(document.documentElement.lang) || 'en';
  var prefs = (navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language]);
  var want = null;
  for (var i = 0; i < prefs.length; i++) { want = norm(prefs[i]); if (want) break; }
  if (!want || want === page) return;
  // คนไทยจำนวนมากตั้งมือถือ/เบราว์เซอร์เป็นภาษาอังกฤษแต่ตั้งใจอ่านภาษาไทย อย่าชวนออกจากหน้าไทยไปอังกฤษ
  if (page === 'th' && want === 'en') return;

  var target = null;
  var alts = document.querySelectorAll('link[rel="alternate"][hreflang]');
  for (var j = 0; j < alts.length; j++) {
    if (norm(alts[j].getAttribute('hreflang')) === want && alts[j].getAttribute('hreflang') !== 'x-default') {
      target = alts[j].getAttribute('href'); break;
    }
  }
  if (!target && page === 'en') target = LANGS[want].home;
  if (!target) return;
  try { if (new URL(target, location.href).pathname === location.pathname) return; } catch (e) {}

  function show() {
    var t = LANGS[want];
    var bar = document.createElement('div');
    bar.className = 'px-lang-suggest';
    bar.setAttribute('role', 'region');
    bar.setAttribute('aria-label', t.msg);
    bar.setAttribute('lang', want);
    bar.innerHTML =
      '<span class="px-ls-msg"></span>' +
      '<a class="px-ls-cta"></a>' +
      '<button type="button" class="px-ls-close">×</button>';
    bar.querySelector('.px-ls-msg').textContent = t.msg;
    var cta = bar.querySelector('.px-ls-cta');
    cta.textContent = t.cta + ' →';
    cta.href = target;
    cta.setAttribute('hreflang', want);
    var close = bar.querySelector('.px-ls-close');
    close.setAttribute('aria-label', CLOSE[want]);

    cta.addEventListener('click', function () {
      store(want);
      if (window.dataLayer) window.dataLayer.push({ event: 'lang_suggest_click', lang: want });
    });
    close.addEventListener('click', function () {
      store(page);
      bar.remove();
    });

    var css = document.createElement('style');
    css.textContent =
      '.px-lang-suggest{position:fixed;left:50%;bottom:20px;transform:translateX(-50%);z-index:9999;' +
      'display:flex;align-items:center;gap:14px;max-width:calc(100vw - 32px);padding:12px 12px 12px 18px;' +
      'background:#141413;color:#f4f1ea;border:1px solid rgba(244,241,234,.14);border-radius:999px;' +
      'box-shadow:0 10px 30px rgba(0,0,0,.45);font:14px/1.4 system-ui,-apple-system,"Hiragino Sans","Noto Sans JP","Noto Sans KR","Noto Sans SC",sans-serif;' +
      'animation:pxls-in .35s ease-out}' +
      '.px-ls-msg{white-space:nowrap}' +
      '.px-ls-cta{background:#dba93a;color:#0a0a0a;font-weight:600;text-decoration:none;padding:8px 14px;border-radius:999px;white-space:nowrap}' +
      '.px-ls-cta:hover{background:#e8c050}' +
      '.px-ls-close{background:none;border:0;color:#8a8680;font-size:20px;line-height:1;padding:4px 8px;cursor:pointer}' +
      '.px-ls-close:hover{color:#f4f1ea}' +
      '@keyframes pxls-in{from{opacity:0;transform:translate(-50%,10px)}to{opacity:1;transform:translate(-50%,0)}}' +
      '@media (max-width:520px){.px-lang-suggest{bottom:12px;gap:10px;padding:10px 8px 10px 14px;font-size:13px}.px-ls-msg{white-space:normal}}' +
      '@media (prefers-reduced-motion:reduce){.px-lang-suggest{animation:none}}';
    document.head.appendChild(css);
    document.body.appendChild(bar);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', show);
  else show();
})();
