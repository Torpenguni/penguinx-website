/* ฟอร์ม "Book a call" — ส่งไป /api/lead แล้วยิง event generate_lead
 * ถ้า API ยังไม่พร้อม (ยังไม่ตั้ง RESEND_API_KEY) หรือเน็ตล่ม จะเปิดอีเมลที่กรอกข้อมูลไว้ให้แทน
 * ข้อความสถานะอ่านจาก <span hidden data-msg=...> ในฟอร์ม เป็น text node เพื่อให้ build-i18n.py แปลได้ */
(function () {
  var form = document.getElementById('leadForm');
  if (!form) return;
  var status = form.querySelector('.lead-status');
  var btn = form.querySelector('button[type="submit"]');

  function msg(key) {
    var el = form.querySelector('[data-msg="' + key + '"]');
    return el ? el.textContent.trim() : '';
  }
  function say(text, kind) {
    status.textContent = text;
    status.className = 'lead-status' + (kind ? ' is-' + kind : '');
  }

  function mailtoFallback(d) {
    var body = 'Name: ' + d.name + '\nCompany: ' + d.company + '\nEmail: ' + d.email +
               '\nPhone / LINE: ' + d.phone + '\n\n' + d.message;
    location.href = 'mailto:tor@penguinx.co?subject=' + encodeURIComponent('Discovery call with PenguinX') +
                    '&body=' + encodeURIComponent(body);
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!form.reportValidity()) return;
    var fd = new FormData(form);
    var d = {};
    fd.forEach(function (v, k) { d[k] = String(v); });
    d.page = location.pathname;
    d.lang = document.documentElement.lang || 'en';

    btn.disabled = true;
    say(msg('sending'));

    fetch('/api/lead', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(d)
    }).then(function (r) {
      if (r.ok) {
        if (window.pxTrackLead) window.pxTrackLead({ lead_method: 'form', company: d.company ? 'yes' : 'no' });
        form.reset();
        say(msg('success'), 'ok');
      } else if (r.status === 422) {
        say(msg('invalid'), 'err');
      } else {
        throw new Error('api ' + r.status);
      }
    }).catch(function () {
      // ไม่นับเป็น generate_lead เพราะไม่รู้ว่าผู้ใช้กดส่งอีเมลจริงหรือไม่ — นับเป็น contact_click แทน
      (window.dataLayer = window.dataLayer || []).push({ event: 'contact_click', contact_method: 'email_fallback', page_language: d.lang });
      say(msg('fallback'));
      mailtoFallback(d);
    }).then(function () { btn.disabled = false; });
  });
})();
