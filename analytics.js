/* PenguinX — analytics loader (Google Tag Manager + conversion events)
 *
 * วิธีเปิดใช้: ใส่ GTM Container ID ข้างล่าง (เช่น 'GTM-ABC1234') แล้ว push ขึ้น main
 * ทุกหน้าโหลดไฟล์นี้ไฟล์เดียว เปลี่ยน ID ที่นี่ที่เดียวพอ ไม่ต้องไล่แก้ 150+ หน้า
 * ถ้าเว้นว่างไว้ = ไม่โหลด GTM เลย (event ยังเข้า dataLayer แต่ไม่ถูกส่งไปไหน)
 *
 * Event ที่ส่งเข้า dataLayer (ไปตั้ง Trigger แบบ Custom Event ใน GTM ด้วยชื่อเหล่านี้):
 *   generate_lead   — ส่งฟอร์ม "Book a call" สำเร็จ          → Primary conversion
 *   contact_click   — กดอีเมล / โทร / LINE (contact_method)  → Secondary conversion
 *   cta_click       — กดปุ่ม CTA หลัก (cta_id)
 *   consent_update  — ผู้ใช้กดยอมรับ/ปฏิเสธคุกกี้ (consent)
 */
(function () {
  // ใส่อย่างใดอย่างหนึ่ง (ถ้าใส่ทั้งคู่ จะใช้ GTM และให้ GTM เป็นคนโหลด GA4 เอง)
  var GTM_ID = '';  // ← 'GTM-XXXXXXX'  ใช้เมื่อต้องการจัดการ tag หลายตัวผ่าน GTM
  var GA4_ID = 'G-2CGLNQ8R5R';  // PenguinX Website (GA4 property 565233510) — เดิม: 'G-XXXXXXXXXX' ส่งเข้า GA4 ตรง ไม่ต้องมี GTM

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }

  // ---- Consent (PDPA / Consent Mode v2) ----
  // ค่าเริ่มต้น denied ทุกภูมิภาค: Google ยังส่ง ping แบบไม่มี cookie ให้ระบบประมาณ conversion ได้
  // เมื่อผู้ใช้กดยอมรับ → update เป็น granted และจำไว้ 12 เดือนใน localStorage
  var CONSENT_KEY = 'px_consent';
  var CONSENT_TTL = 365 * 24 * 3600 * 1000;
  function readConsent() {
    try {
      var c = JSON.parse(localStorage.getItem(CONSENT_KEY) || 'null');
      return c && Date.now() - c.t < CONSENT_TTL ? c.v : null;
    } catch (e) { return null; }
  }
  function consentState(v) {
    var g = v === 'granted' ? 'granted' : 'denied';
    return { ad_storage: g, ad_user_data: g, ad_personalization: g, analytics_storage: g };
  }
  var saved = readConsent();
  var dflt = consentState('denied');
  dflt.wait_for_update = 500;
  gtag('consent', 'default', dflt);
  if (saved) gtag('consent', 'update', consentState(saved));

  if (/^GTM-[A-Z0-9]+$/.test(GTM_ID)) {
    window.dataLayer.push({ 'gtm.start': Date.now(), event: 'gtm.js' });
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtm.js?id=' + GTM_ID;
    document.head.appendChild(s);
  } else if (/^G-[A-Z0-9]+$/.test(GA4_ID)) {
    var g = document.createElement('script');
    g.async = true;
    g.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA4_ID;
    document.head.appendChild(g);
    gtag('js', new Date());
    gtag('config', GA4_ID);
  }
  var DIRECT = !/^GTM-/.test(GTM_ID) && /^G-/.test(GA4_ID);

  // ส่ง event ทางเดียว: GTM อ่านจาก dataLayer object, โหมด GA4 ตรงใช้ gtag('event')
  function track(name, params) {
    params = params || {};
    if (DIRECT) gtag('event', name, params);
    else window.dataLayer.push(Object.assign({ event: name }, params));
  }
  window.pxTrack = track;

  // ---- Conversion events (ใช้ event delegation จับได้ทุกหน้าโดยไม่ต้องแก้ HTML) ----
  function lang() { return document.documentElement.lang || 'en'; }

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var href = a.getAttribute('href') || '';
    var method = null;
    if (href.indexOf('mailto:') === 0) method = 'email';
    else if (href.indexOf('tel:') === 0) method = 'phone';
    else if (/(^|\/\/)(lin\.ee|line\.me)\//.test(href)) method = 'line';

    if (method) {
      track('contact_click', {
        contact_method: method,
        contact_target: href.replace(/^(mailto:|tel:)/, '').split('?')[0],
        page_language: lang()
      });
    }
    if (a.classList.contains('cta-btn')) {
      track('cta_click', { cta_id: a.id || 'cta-btn', page_language: lang() });
    }
  }, true);

  // ---- Cookie banner ----
  var TXT = {
    en: ['We use cookies to measure site performance and the results of our ads. You can accept or decline.', 'Accept', 'Decline'],
    th: ['เว็บไซต์นี้ใช้คุกกี้เพื่อวัดผลการใช้งานเว็บไซต์และประสิทธิภาพโฆษณา คุณเลือกยอมรับหรือปฏิเสธได้', 'ยอมรับ', 'ปฏิเสธ'],
    zh: ['本网站使用 Cookie 衡量网站表现和广告效果。你可以选择接受或拒绝。', '接受', '拒绝'],
    ja: ['当サイトはサイトの利用状況と広告効果の測定に Cookie を使用します。同意または拒否を選択できます。', '同意する', '拒否する'],
    ko: ['이 웹사이트는 사이트 이용 현황과 광고 효과를 측정하기 위해 쿠키를 사용합니다. 동의 여부를 선택하실 수 있습니다.', '동의', '거부']
  };
  function setConsent(v) {
    try { localStorage.setItem(CONSENT_KEY, JSON.stringify({ v: v, t: Date.now() })); } catch (e) {}
    gtag('consent', 'update', consentState(v));
    track('consent_update', { consent: v });
  }
  function showBanner() {
    if (document.getElementById('pxConsent')) return;
    var t = TXT[(lang().split('-')[0])] || TXT.en;
    var css = document.createElement('style');
    css.textContent =
      '#pxConsent{position:fixed;left:16px;right:16px;bottom:16px;z-index:9999;max-width:720px;margin:0 auto;' +
      'display:flex;gap:16px;align-items:center;padding:16px 18px;background:#141413;color:#f4f1ea;' +
      'border:1px solid rgba(244,241,234,.12);border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.45);' +
      'font:14px/1.5 Anuphan,sans-serif}' +
      '#pxConsent p{flex:1;margin:0;color:#c9c5bd}' +
      '#pxConsent button{font:inherit;font-weight:600;border-radius:100px;padding:9px 18px;cursor:pointer;white-space:nowrap}' +
      '#pxConsent .ok{background:#dba93a;color:#0a0a0a;border:0}' +
      '#pxConsent .no{background:transparent;color:#f4f1ea;border:1px solid rgba(244,241,234,.25)}' +
      '@media(max-width:560px){#pxConsent{flex-direction:column;align-items:stretch;text-align:center}}';
    var box = document.createElement('div');
    box.id = 'pxConsent';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-live', 'polite');
    box.innerHTML = '<p></p><button type="button" class="no"></button><button type="button" class="ok"></button>';
    box.querySelector('p').textContent = t[0];
    box.querySelector('.ok').textContent = t[1];
    box.querySelector('.no').textContent = t[2];
    box.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      setConsent(b.classList.contains('ok') ? 'granted' : 'denied');
      box.remove();
    });
    document.head.appendChild(css);
    document.body.appendChild(box);
  }
  // เปิดแบนเนอร์ใหม่ได้จากลิงก์ใดก็ได้ที่มี data-cookie-settings
  window.pxConsent = { open: showBanner, set: setConsent };
  document.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('[data-cookie-settings]')) { e.preventDefault(); showBanner(); }
  });
  if (!saved) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', showBanner);
    else showBanner();
  }

  // ฟอร์ม lead เรียกใช้ฟังก์ชันนี้เมื่อส่งสำเร็จ
  window.pxTrackLead = function (detail) {
    track('generate_lead', Object.assign({ page_language: lang() }, detail || {}));
  };
})();
