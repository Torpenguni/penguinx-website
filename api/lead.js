// Vercel Edge Function — รับฟอร์ม "Book a call" แล้วส่งอีเมลแจ้งทีมผ่าน Resend
//
// ตั้งค่าใน Vercel → Project → Settings → Environment Variables:
//   RESEND_API_KEY   (จำเป็น)  key จาก resend.com
//   LEAD_TO_EMAIL    (ไม่บังคับ) ผู้รับ คั่นด้วย , ได้ — ค่าเริ่มต้น tor@penguinx.co
//   LEAD_FROM_EMAIL  (ไม่บังคับ) ผู้ส่ง ต้องเป็นโดเมนที่ verify ใน Resend แล้ว
//                    ค่าเริ่มต้น 'PenguinX Website <onboarding@resend.dev>' (ใช้ทดสอบได้ทันที)
//
// ถ้ายังไม่ตั้ง key ฟังก์ชันตอบ 503 และหน้าเว็บจะเปิดอีเมลที่กรอกข้อมูลไว้ให้แทน
// ลูกค้าจึงติดต่อได้เสมอ lead ไม่หาย
export const config = { runtime: 'edge' };

const MAX = { name: 120, company: 160, email: 200, phone: 60, message: 3000, page: 300, lang: 10 };

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' }
  });
}
function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export default async function handler(req) {
  if (req.method !== 'POST') return json({ error: 'method_not_allowed' }, 405);

  let data;
  try { data = await req.json(); } catch { return json({ error: 'bad_request' }, 400); }

  // honeypot: บอทกรอกช่องที่ซ่อนไว้ — ตอบ ok หลอกแต่ไม่ส่ง
  if (data.website) return json({ ok: true }, 200);

  const f = {};
  for (const k of Object.keys(MAX)) f[k] = String(data[k] || '').trim().slice(0, MAX[k]);
  if (!f.name || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) return json({ error: 'invalid' }, 422);

  const key = process.env.RESEND_API_KEY;
  if (!key) return json({ error: 'not_configured' }, 503);

  const to = (process.env.LEAD_TO_EMAIL || 'tor@penguinx.co').split(',').map(s => s.trim()).filter(Boolean);
  const from = process.env.LEAD_FROM_EMAIL || 'PenguinX Website <onboarding@resend.dev>';

  const rows = [['Name', f.name], ['Company / Brand', f.company], ['Email', f.email],
                ['Phone / LINE', f.phone], ['Page', f.page], ['Language', f.lang]]
    .map(([k, v]) => `<tr><td style="padding:4px 12px 4px 0;color:#666">${k}</td><td>${esc(v || '-')}</td></tr>`).join('');
  const html = `<h2>New discovery-call request</h2><table>${rows}</table>
    <p style="white-space:pre-wrap;border-left:3px solid #dba93a;padding-left:12px">${esc(f.message || '-')}</p>`;

  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { authorization: `Bearer ${key}`, 'content-type': 'application/json' },
    body: JSON.stringify({
      from, to, reply_to: f.email,
      subject: `[PenguinX lead] ${f.name}${f.company ? ' — ' + f.company : ''}`,
      html
    })
  });
  if (!r.ok) return json({ error: 'send_failed' }, 502);
  return json({ ok: true }, 200);
}
