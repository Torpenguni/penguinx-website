/* ป้าย "your first penguin" ติดตามตัวเพนกวินที่กำลังกระโดดในภาพ hero
   ภาพเป็น background-size:cover จึงถูกครอปต่างกันทุกขนาดจอ
   สคริปต์นี้คำนวณว่าจุดในภาพไปตกตรงไหนบนจอ แล้ววางป้ายตรงนั้น
   ถ้าเปลี่ยนรูป hero ต้องแก้ IMG_W/IMG_H และพิกัด ANCHOR ให้ตรงกับรูปใหม่ */
(function () {
  var IMG_W = 2148, IMG_H = 1332;      // ขนาดจริงของ cover-penguin-v2.jpg
  var ANCHOR = { x: 1600, y: 655 };     // ขอบล่างกึ่งกลางของข้อความ เหนือปลายปีกตัวที่กระโดด (พิกเซลในภาพ)
  var FONT = 43;                        // ขนาดตัวอักษรเทียบพิกเซลในภาพ (~1.5 เท่าความยาวตัวเพนกวิน)
  var bg = document.querySelector('.hero-bg');
  var tag = document.querySelector('.first-penguin-tag');
  if (!bg || !tag) return;

  function place() {
    var W = bg.clientWidth, H = bg.clientHeight;
    if (!W || !H) return;
    var s = Math.max(W / IMG_W, H / IMG_H);
    var rw = IMG_W * s, rh = IMG_H * s;
    var pos = getComputedStyle(bg).backgroundPosition.split(' ');
    var px = parseFloat(pos[0]) / 100, py = parseFloat(pos[1] || '50%') / 100;
    if (isNaN(px)) px = 0.5; if (isNaN(py)) py = 0.5;
    var x = (W - rw) * px + ANCHOR.x * s;
    var y = (H - rh) * py + ANCHOR.y * s;
    tag.style.left = x + 'px';
    tag.style.top = y + 'px';
    tag.style.fontSize = Math.max(13, FONT * s) + 'px';
    // ถ้าตัวเพนกวินหลุดเฟรม (จอแคบมาก) ก็ซ่อนป้าย
    tag.classList.toggle('is-visible', x > 60 && x < W - 60);
  }

  place();
  window.addEventListener('resize', place);
  window.addEventListener('load', place);
})();
