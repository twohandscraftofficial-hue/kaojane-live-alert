# KaoJane Alert Bot — เลือกศิลปินที่แจ้งเตือนได้

บอทเดิม: https://t.me/KaoJaneAlert_bot

## คำสั่งสำหรับเพื่อน
- `/start` รับแจ้งทั้งเจนเย่และพี่เก้า พร้อมปุ่มเลือก
- `/jane` รับเฉพาะเจนเย่
- `/kao` รับเฉพาะพี่เก้า
- `/both` รับทั้งสองคน
- `/status` ตรวจสอบสิ่งที่เลือกและเปิดเมนู
- `/stop` ยกเลิก

## ติดตั้งใน Repository เดิม
1. เปิดไฟล์ `generate_key.py` บนคอมของตัวเอง และรันหลังติดตั้ง `cryptography` (`pip install cryptography`) เพื่อสร้างคีย์ Fernet; หรือใช้ไฟล์ `PRIVATE_SUBSCRIBERS_KEY.txt` ที่ดาวน์โหลดแยกมาในแชต ห้ามอัปโหลดไฟล์คีย์ขึ้น GitHub
2. ที่ GitHub Settings → Secrets and variables → Actions → New repository secret สร้าง `SUBSCRIBERS_KEY` ด้วยคีย์หนึ่งบรรทัดนั้น เก็บสำรองให้ปลอดภัย การเปลี่ยนคีย์ทำให้ไฟล์สมาชิกเดิมถอดรหัสไม่ได้
3. แทนที่ไฟล์ `check_live.py`, `requirements.txt`, `.github/workflows/live-alert.yml` จากชุดนี้ โดยรักษา path จริงของ workflow และคัดลอก **เนื้อหาไฟล์** ลง GitHub (อย่าอัปโหลดไฟล์ ZIP ตรง ๆ)
4. ไม่ต้องแก้ `live_state.json` และ **ไม่ต้องอัปโหลดไฟล์ `subscribers.enc` เอง** ระบบสร้างเมื่อรันปกติครั้งแรก
5. ไป Actions → KaoJane LIVE Alert → Run workflow → ไม่ติ๊ก `Send test DM to owner only` แล้วตรวจ Log ว่ามี `subscribers=...` และไฟล์ `subscribers.enc` ถูกสร้าง
6. ชวนเพื่อนเข้า https://t.me/KaoJaneAlert_bot และส่ง `/start`; ให้รอบ GitHub Actions ครั้งถัดไปอ่านคำสั่ง (ทุก ~10 นาที แต่ Github อาจล่าช้าหรือข้ามรอบได้)

## สำคัญ
- `SUBSCRIBERS_KEY` และ `TELEGRAM_BOT_TOKEN` ต้องเป็น GitHub Secrets เท่านั้น ห้ามใส่ลง Public Repository
- รายชื่อสมาชิกและตัวเลือกถูกเข้ารหัสในไฟล์ `subscribers.enc` ที่ commit ลง public repo; metadata เช่นเวลา commit ยังคงมองเห็นได้
- `/start` ใหม่หมายถึงเลือกทั้งสองคน ถ้าอยากเลือกคนเดียว ให้กดปุ่มหรือ `/jane` / `/kao`
- คำสั่งจะตอบช้าเพราะ GitHub Actions ไม่ใช่ Webhook real-time
- ไม่ได้เชื่อม Instagram LIVE, TikTok Video หรือ Instagram Reels
- TikTokLive เป็นวิธีไม่ทางการ ตรวจสอบบาง LIVE ไม่ได้ และ GitHub schedule อาจล่าช้า/ข้ามรอบ
- หลีกเลี่ยงการใช้ Telegram Webhook หรือ `getUpdates` จากที่อื่นพร้อมกับ workflow เพราะอาจเกิดการแย่งอ่านอัปเดต
- หาก GitHub Actions แจ้ง error เรื่อง `subscribers.enc` ให้ตรวจ `SUBSCRIBERS_KEY` แทนการลบไฟล์นี้
