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
 */
(function () {
  var GTM_ID = ''; // ← ใส่ 'GTM-XXXXXXX' ตรงนี้

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }

  // Consent Mode v2 — Google บังคับใช้กับผู้ใช้ใน EEA/UK/CH (ตั้ง denied จนกว่าจะยินยอม)
  // ผู้ใช้ภูมิภาคอื่นรวมไทย: granted ตามค่าเริ่มต้น
  // ถ้าจะทำ cookie banner ตาม PDPA ภายหลัง ให้เปลี่ยนตรงนี้เป็น denied แล้วเรียก gtag('consent','update',...)
  gtag('consent', 'default', {
    ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied',
    analytics_storage: 'denied', wait_for_update: 500,
    region: ['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IE','IT','LV',
             'LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE','IS','LI','NO','GB','CH']
  });
  gtag('consent', 'default', {
    ad_storage: 'granted', ad_user_data: 'granted', ad_personalization: 'granted',
    analytics_storage: 'granted'
  });

  if (/^GTM-[A-Z0-9]+$/.test(GTM_ID)) {
    window.dataLayer.push({ 'gtm.start': Date.now(), event: 'gtm.js' });
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtm.js?id=' + GTM_ID;
    document.head.appendChild(s);
  }

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
      window.dataLayer.push({
        event: 'contact_click',
        contact_method: method,
        contact_target: href.replace(/^(mailto:|tel:)/, '').split('?')[0],
        page_language: lang()
      });
    }
    if (a.classList.contains('cta-btn')) {
      window.dataLayer.push({ event: 'cta_click', cta_id: a.id || 'cta-btn', page_language: lang() });
    }
  }, true);

  // ฟอร์ม lead เรียกใช้ฟังก์ชันนี้เมื่อส่งสำเร็จ
  window.pxTrackLead = function (detail) {
    window.dataLayer.push(Object.assign({ event: 'generate_lead', page_language: lang() }, detail || {}));
  };
})();
