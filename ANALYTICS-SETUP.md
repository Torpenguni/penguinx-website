# Analytics, SEO & Google Ads — setup guide

โค้ดฝั่งเว็บทำไว้ครบแล้ว เหลืองานฝั่งบัญชี Google ตามลำดับข้างล่าง

## 1. เปิดใช้ GTM (5 นาที)
1. สร้าง container ที่ tagmanager.google.com (ประเภท Web, ชื่อ `penguinx.co`)
2. ใส่ ID ใน `analytics.js` บรรทัด `var GTM_ID = '';` → `'GTM-XXXXXXX'`
3. push ขึ้น `main` → Vercel deploy เอง ทุกหน้า (136 หน้า × 4 ภาษา) โหลดไฟล์นี้ไฟล์เดียว

## 2. ตั้งค่าใน GTM
| Tag | Trigger |
|---|---|
| Google tag (GA4 Measurement ID `G-…`) | Initialization – All Pages |
| Conversion Linker | All Pages |
| GA4 Event `generate_lead` | Custom Event = `generate_lead` |
| GA4 Event `contact_click` (ส่ง parameter `contact_method`) | Custom Event = `contact_click` |
| Google Ads Conversion "Lead – form" | Custom Event = `generate_lead` |

สร้าง Data Layer Variable: `contact_method`, `page_language`, `lead_method`, `cta_id`
แล้ว Preview → ทดสอบส่งฟอร์มและกดอีเมล/โทร → Publish

## 3. Conversion hierarchy (สำคัญต่อ Smart Bidding)
- **Primary:** `generate_lead` (ฟอร์มส่งสำเร็จจริง) — ใช้ประมูล
- **Secondary:** `contact_click` (อีเมล/โทร/LINE) — วัดผลอย่างเดียว ไม่ใช้ประมูล
- อย่า import conversion เดียวกันทั้งจาก GA4 และ Ads tag พร้อมกัน (นับซ้ำ)
- เปิด Enhanced Conversions for leads ใน Google Ads

## 4. ฟอร์ม lead → อีเมล (Vercel env vars)
| Variable | ค่า |
|---|---|
| `RESEND_API_KEY` | key จาก resend.com (จำเป็น) |
| `LEAD_TO_EMAIL` | ผู้รับ เช่น `tor@penguinx.co,supersupp@penguinx.co` |
| `LEAD_FROM_EMAIL` | เช่น `PenguinX <leads@penguinx.co>` (ต้อง verify โดเมนใน Resend) |

ถ้ายังไม่ตั้ง key ฟอร์มจะเปิดแอปอีเมลพร้อมข้อมูลที่กรอกไว้แทน (lead ไม่หาย แต่นับเป็น `contact_click: email_fallback` ไม่ใช่ `generate_lead`)

## 5. เชื่อมบัญชี
- Search Console: ยืนยันแล้ว (meta tag) — แนะนำเพิ่ม Domain property ผ่าน DNS TXT แล้ว submit `https://www.penguinx.co/sitemap.xml`
- GA4 → Admin → Product links: Google Ads, Search Console
- Google Ads → Tools → Linked accounts: GA4

## 6. ถัดไป
- PDPA cookie banner: ถ้าจะทำ เปลี่ยน consent default ใน `analytics.js` เป็น `denied` แล้ว `gtag('consent','update',…)` เมื่อผู้ใช้ยอมรับ
- เพิ่มหน้าใหม่: หน้า HTML ใหม่ต้องมี `<script src="/analytics.js"></script>` ใน `<head>` (หน้าแปลจาก `build-i18n.py` ได้ตามต้นฉบับอัตโนมัติ)
- หลังเพิ่ม/ลบหน้า: `python3 build-sitemap.py` (ต้องมีประวัติ git เต็ม ไม่งั้น lastmod เพี้ยน)
