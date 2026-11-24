/* ป้าย "your first penguin" ติดตามตัวเพนกวินที่กำลังกระโดดในภาพ hero
   ภาพเป็น background-size:cover จึงถูกครอปต่างกันทุกขนาดจอ
   สคริปต์นี้คำนวณว่าจุดในภาพไปตกตรงไหนบนจอ แล้ววางป้ายตรงนั้น

   จอกว้าง (เดสก์ท็อป, iPad แนวนอน): ใช้ตำแหน่งภาพจาก CSS ตามเดิม
   จอแคบ/แนวตั้ง (มือถือ, iPad แนวตั้ง): ตำแหน่งเดิมทำให้ตัวที่กระโดดหลุดเฟรมหรือจมอยู่ใต้ตัวหนังสือ
   สคริปต์จึงเปิดช่องว่างระหว่างหัวข้อกับคำอธิบาย แล้วเลื่อน/ขยายภาพให้ตัวที่กระโดดกับป้ายลงในช่องนั้น
   เจ้าของเว็บต้องการให้เห็นตัวที่กระโดดพร้อมป้ายทุกอุปกรณ์

   ถ้าเปลี่ยนรูป hero ต้องแก้ IMG_W/IMG_H, ANCHOR และ BODY ให้ตรงกับรูปใหม่ */
(function () {
  var IMG_W = 2148, IMG_H = 1332;      // ขนาดจริงของ cover-penguin-v3.jpg (v2 + spotlight อบในภาพ)
  var ANCHOR = { x: 1600, y: 655 };     // ขอบล่างกึ่งกลางของข้อความ เหนือปลายปีกตัวที่กระโดด (พิกเซลในภาพ)
  var BODY = { x1: 1415, x2: 1755, y2: 880 }; // กรอบตัวที่กระโดด ตั้งแต่ปลายเท้าถึงปลายปาก (พิกเซลในภาพ)
  var FONT = 30;                        // ขนาดตัวอักษรเทียบพิกเซลในภาพ (~1.5 เท่าความยาวตัวเพนกวิน)
  var EDGE = 14;                        // ระยะห่างจากขอบจอขั้นต่ำ
  var bg = document.querySelector('.hero-bg');
  var tag = document.querySelector('.first-penguin-tag');
  var title = document.querySelector('.hero-title');
  var desc = document.querySelector('.hero-desc');
  var bottom = document.querySelector('.hero-bottom');
  if (!bg || !tag) return;

  function frame() {
    var r = bg.getBoundingClientRect();
    var rel = function (el, side) { return el ? el.getBoundingClientRect()[side] - r.top : null; };
    return { W: bg.clientWidth, H: bg.clientHeight,
             a: rel(title, 'bottom'), b: rel(desc, 'top') };
  }

  function draw(s, ox, oy) {
    tag.style.left = (ox + ANCHOR.x * s) + 'px';
    tag.style.top = (oy + ANCHOR.y * s) + 'px';
    tag.style.fontSize = Math.max(13, FONT * s) + 'px';
  }

  // ตำแหน่งตาม CSS (background-size:cover + background-position เป็น %)
  function cssPlacement(f) {
    var s = Math.max(f.W / IMG_W, f.H / IMG_H);
    var pos = getComputedStyle(bg).backgroundPosition.split(' ');
    var px = parseFloat(pos[0]) / 100, py = parseFloat(pos[1] || '50%') / 100;
    if (isNaN(px)) px = 0.5; if (isNaN(py)) py = 0.5;
    return { s: s, ox: (f.W - IMG_W * s) * px, oy: (f.H - IMG_H * s) * py };
  }

  // ป้ายกับตัวที่กระโดดอยู่ในเฟรมครบ และไม่ทับหัวข้อหรือคำอธิบาย
  function clear(f, p) {
    draw(p.s, p.ox, p.oy);
    var tw = tag.offsetWidth, th = tag.offsetHeight;
    var ax = p.ox + ANCHOR.x * p.s, ay = p.oy + ANCHOR.y * p.s;
    var left = Math.min(ax - tw / 2, p.ox + BODY.x1 * p.s);
    var right = Math.max(ax + tw / 2, p.ox + BODY.x2 * p.s);
    var top = ay - th, low = p.oy + BODY.y2 * p.s;
    if (left < EDGE || right > f.W - EDGE) return false;
    var o = bg.getBoundingClientRect();
    var hits = function (el) {
      if (!el) return false;
      var e = el.getBoundingClientRect();
      return left < e.right - o.left && right > e.left - o.left &&
             top < e.bottom - o.top && low > e.top - o.top;
    };
    return !hits(title) && !hits(desc) && !hits(bottom && bottom.querySelector('.hero-stats'));
  }

  // จอแคบ: วางตัวที่กระโดดลงในช่องว่างระหว่างหัวข้อ (a) กับคำอธิบาย (b)
  // ขนาดตัวเพนกวินคุมจากความกว้างจอ (~40% ของจอ ไม่เกิน 230px ใกล้เคียงบนเดสก์ท็อป)
  // ถ้าปล่อยให้ภาพ cover ตามความสูงจอแนวตั้ง ตัวเพนกวินจะกว้างเกือบเต็มจอมือถือ
  // ผลคือภาพไม่เต็มความสูง hero ส่วนที่เหลือเป็นสีพื้น navy และขอบบน-ล่างของภาพถูกเฟดด้วย mask
  function bandPlacement(f) {
    var s = Math.max(f.W / IMG_W, Math.min(230, 0.4 * f.W) / (BODY.x2 - BODY.x1));
    var pad = Math.max(13, FONT * s) * 1.7;              // ที่สำหรับป้ายเหนือปลายปีก
    var top = f.a + 14;
    var rw = IMG_W * s;
    var oy = top + pad - ANCHOR.y * s;
    var tw = tag.offsetWidth || 0;
    var ax = 0.6 * f.W;
    ax = Math.min(ax, f.W - EDGE - Math.max(tw / 2, (BODY.x2 - ANCHOR.x) * s));
    ax = Math.max(ax, EDGE + Math.max(tw / 2, (ANCHOR.x - BODY.x1) * s));
    var ox = Math.max(f.W - rw, Math.min(0, ax - ANCHOR.x * s));
    return { s: s, ox: ox, oy: oy, need: top + pad + (BODY.y2 - ANCHOR.y) * s + 12 - f.b };
  }

  function place() {
    bg.style.backgroundSize = ''; bg.style.backgroundPosition = '';
    bg.style.webkitMaskImage = bg.style.maskImage = '';
    if (bottom) bottom.style.marginTop = '';
    var f = frame();
    if (!f.W || !f.H) return;

    var p = cssPlacement(f);
    if (clear(f, p)) { tag.classList.add('is-visible'); return; }
    if (f.a === null || f.b === null) { tag.classList.remove('is-visible'); return; }

    // เปิดช่องว่างให้พอ (ปรับสองรอบ เพราะความสูง hero เปลี่ยนตามช่องว่าง → ขนาดภาพเปลี่ยนตาม)
    var extra = 0;
    for (var i = 0; i < 3; i++) {
      var q = bandPlacement(f);
      if (q.need <= 1) break;
      extra += q.need;
      if (bottom) bottom.style.marginTop = extra + 'px';
      f = frame();
    }
    q = bandPlacement(f);
    bg.style.backgroundSize = (IMG_W * q.s) + 'px ' + (IMG_H * q.s) + 'px';
    bg.style.backgroundPosition = q.ox + 'px ' + q.oy + 'px';
    bg.style.backgroundRepeat = 'no-repeat';
    // เฟดขอบบนและล่างของภาพเข้าสีพื้น ไม่ให้เห็นเป็นเส้นตัด
    var y1 = q.oy, y2 = q.oy + IMG_H * q.s, fade = 0.22 * IMG_H * q.s;
    var m = 'linear-gradient(to bottom, transparent ' + y1 + 'px, #000 ' + (y1 + fade) + 'px, #000 ' +
            (y2 - fade) + 'px, transparent ' + y2 + 'px)';
    bg.style.webkitMaskImage = bg.style.maskImage = m;
    draw(q.s, q.ox, q.oy);
    tag.classList.add('is-visible');
  }

  var t;
  function later() { clearTimeout(t); t = setTimeout(place, 60); }
  place();
  window.addEventListener('resize', later);
  window.addEventListener('load', place);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(place);
})();
