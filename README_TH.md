# KaoJane TikTok LIVE Alert Bot — GitHub Actions ฟรี

ตรวจ TikTok LIVE: @janeeyeh (เจนเย่) และ @supassra_sp (พี่เก้า) ทุกประมาณ 10 นาที แล้วส่ง Telegram เฉพาะเมื่อพบสถานะ LIVE ใหม่

## วิธีติดตั้ง

1. สร้าง Telegram bot ผ่าน https://t.me/BotFather คำสั่ง `/newbot` แล้ว **เก็บ Token เป็นความลับ**
2. เปิดแชตกับบอทที่สร้าง แล้วส่ง `/start` (บอทไม่สามารถส่ง DM หาคุณก่อนเริ่มแชตได้)
3. หา Chat ID ส่วนตัวด้วย Telegram Bot API `getUpdates` ผ่านเครื่องที่ไว้ใจได้ หรือบอทดู ID ที่คุณไว้ใจ โดย Chat ID ในแชตส่วนตัวมักเป็น Telegram user ID ของคุณ
4. สร้าง GitHub repository แบบ **Public** ที่ https://github.com/new ชื่อ `kaojane-live-alert` (GitHub Actions standard runner สำหรับ public repo ฟรีตามนโยบาย ณ ปัจจุบัน)
5. แตก ZIP แล้วอัปโหลด **รวมโฟลเดอร์ .github/workflows** ไปยัง repository ทั้งหมด (อัปโหลดไฟล์โฟลเดอร์ .github ให้ครบตาม path)
6. ไปที่ repository → Settings → Secrets and variables → Actions → New repository secret แล้วเพิ่ม 2 รายการ:
   - `TELEGRAM_BOT_TOKEN`: Token จาก BotFather
   - `TELEGRAM_CHAT_ID`: ตัวเลข Chat ID ของคุณ
   ห้ามใส่ Token ในไฟล์, issue, commit, screenshot หรือแชต
7. ไปที่ Settings → Actions → General → Workflow permissions เลือก Read and write permissions (เพื่อบันทึกสถานะ LIVE ป้องกันแจ้งซ้ำ)
8. ไปที่แท็บ Actions → KaoJane TikTok LIVE Alerts → Run workflow → ติ๊ก `test_message` → Run workflow เพื่อทดสอบส่ง Telegram
9. เมื่อทดสอบผ่านแล้ว งานตามเวลาจะทำงานอัตโนมัติประมาณทุก 10 นาที แม้ปิดคอม ไม่ต้อง Deploy เซิร์ฟเวอร์

## การทำงาน
- เช็คสถานะ TikTok Live ของ 2 คนผ่าน TikTokLive `is_live()` (ไม่ใช่ TikTok API ทางการ)
- ส่งหนึ่งแจ้งเตือนเมื่อเปลี่ยนจาก offline → live ไม่ส่งซ้ำทุกครั้งที่ตรวจ
- เมื่อ LIVE จบ จะเซ็ตสถานะกลับเป็น offline เพื่อเตรียมการแจ้ง LIVE ครั้งถัดไป
- ถ้าเช็คแล้ว error จะไม่ถือว่า offline เพื่อป้องกันการแจ้งซ้ำ (ดู errors ที่ Actions logs)
- สถานะบันทึกใน `live_state.json` ผ่าน Git commit จาก Actions

## ข้อจำกัด
- **ยังไม่มี IG LIVE หรือวิดีโอใหม่** เพราะไม่มีแหล่งข้อมูลที่รับประกันการตรวจจับบัญชีบุคคลอื่นอย่างถูกต้องและฟรี
- GitHub schedule อาจล่าช้า/ข้ามบางรอบ; ไลฟ์สั้นกว่า 10 นาทีอาจพลาด
- โครงการ TikTokLive เป็น unofficial API; อาจถูกจำกัดหรือใช้งานไม่ได้ในบางช่วง ต้องตรวจสอบ Actions logs
- Public repo ที่ไม่มี activity 60 วันอาจถูกปิด schedule อัตโนมัติ โดยสถานะ LIVE ที่เปลี่ยนจะทำ commit ซึ่งถือเป็น activity แต่ไม่ควรพึ่งพา 100%
- ผู้ใช้ต้องเปิด Telegram notifications ในมือถือ
- ไม่ควรใช้ repo กับข้อมูลลับ; เก็บ Token ใน GitHub Secrets เท่านั้น
- GitHub ฟรีสำหรับ standard hosted runners ใน Public repository ณ วันที่จัดทำ โปรดตรวจสอบ https://docs.github.com/en/billing/concepts/product-billing/github-actions
