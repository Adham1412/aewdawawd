# StarMarket — Telegram Stars/Premium do‘koni (MVP v0.2)

Telegram bot + Mini App + admin panel + FastAPI + SQLAlchemy.
**To‘lov qo‘lda tasdiqlanadi** (karta + chek), **yetkazib berish qo‘lda** (admin). Avtomatik to‘lov provayderi va avtomatik yetkazib berish ulanmagan; ular rasmiy yo‘li tasdiqlangach qo‘shiladi (`docs/FINAL_SPEC.md`).

## Oqim
1. Mijoz botda `/start` → «Do‘konni ochish» (Mini App) → mahsulot, `@username` → buyurtma (holat `AWAITING_PAYMENT`).
2. Mijoz `PAYMENT_INSTRUCTIONS` dagi rekvizitga to‘laydi va **chek rasmini bot chatiga yuboradi** → `PAYMENT_SUBMITTED`, adminlarga rasm boradi.
3. Admin bank ilovasida pul tushganini tekshirib, **Admin panel**da «✅ To‘lov tushdi» ni bosadi → `PAID` (ledger’ga bir marta yoziladi), mijozga xabar ketadi.
4. Admin Stars/Premium’ni Telegram’ning rasmiy imkoniyatlari bilan yuboradi → «Bajarishni boshlash» → «Yetkazildi» → `COMPLETED`.
5. Muammo bo‘lsa: `FAILED`, qaytarish: `REFUND_PENDING` → `REFUNDED` (ledger’ga teskari yozuv).

Ruxsat etilgan holat o‘tishlari `app/services/order_states.py` da; boshqa o‘tishlar server tomonidan rad etiladi.

## Xavfsizlik
- Mini App `initData` serverda tekshiriladi; qisqa muddatli imzolangan sessiya.
- Admin = `ADMIN_TELEGRAM_IDS` dagi Telegram ID, **har so‘rovda** tekshiriladi. Admin panel faqat Telegram ichida (Mini App) ochiladi; parol yo‘q.
- Narx faqat serverda hisoblanadi. Buyurtma idempotent. Foydalanuvchi uchun ochiq buyurtmalar soni cheklangan.
- Tezlik limiti (jarayon ichida), audit jurnali, xato javoblarida stack trace yo‘q, tokenlar loglarga yozilmaydi.
- Bot/Mini App parol yoki SMS-kod so‘ramaydi (sxema `password`, `code` kabi maydonlarni rad etadi).

## Lokal ishga tushirish (SQLite, 0 so‘m)
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -e '.[dev]'
cp .env.example .env                                    # Windows: copy .env.example .env
```
`.env` da to‘ldiring: `BOT_TOKEN` (@BotFather), `SESSION_SECRET` (`python -c "import secrets; print(secrets.token_urlsafe(48))"`), `ADMIN_TELEGRAM_IDS` (@userinfobot), `PAYMENT_INSTRUCTIONS`.
```bash
pytest -q                          # avval testlar
python scripts/seed_products.py --file scripts/products.example.json   # avval faylda narxlarni o‘zingiz yozing; yoki admin paneldan yarating
uvicorn app.main:app --reload      # API + Mini App: http://127.0.0.1:8000/app/ , docs: /docs
python -m app.bot.main             # bot (boshqa terminalda)
```
Mini App va admin panel Telegram ichida ochilishi shart (`initData` kerak) va **HTTPS** manzil talab qiladi. Lokal sinov uchun bepul HTTPS tunnel (masalan Cloudflare Tunnel yoki ngrok) ishlating, so‘ng `.env` da:
`MINIAPP_URL=https://<tunnel>/app/` va `ADMIN_URL=https://<tunnel>/admin-ui/`, botni qayta ishga tushiring.

## Docker + PostgreSQL
```bash
cp .env.example .env     # POSTGRES_PASSWORD, BOT_TOKEN, SESSION_SECRET, ADMIN_TELEGRAM_IDS ni to‘ldiring
docker compose up --build
```
`api` konteyneri ishga tushganda `alembic upgrade head` ni bajaradi (PostgreSQL’da jadvallar faqat migratsiya orqali yaratiladi). Ishlab chiqarishda `APP_ENV=production` qo‘ying: hujjat sahifalari o‘chadi, maxfiy kalitlar tekshiriladi.

## Mahsulotlar
Admin panel → «Mahsulotlar»: yaratish (nofaol holatda), narx va «Yoqish». `amount` — Stars soni yoki Premium kunlari. Narxni **o‘zingiz** tannarx + foyda bo‘yicha belgilang.

## Cheklovlar (halol)
- Pul tushganini admin qo‘lda tekshiradi; chek soxtalashtirilishi mumkin — faqat bank ilovasidagi tushumga ishoning.
- Tezlik limiti bitta jarayon xotirasida; bir nechta nusxa ishlatilsa umumiy saqlash (Redis/DB) kerak.
- Sessiya tokeni stateless: alohida sessiyani darhol bekor qilib bo‘lmaydi (muddati qisqa: `SESSION_TTL_SECONDS`). Adminni o‘chirish uchun `ADMIN_TELEGRAM_IDS` dan olib tashlang — keyingi so‘rovdan kuchga kiradi.
- Hali yo‘q: referral/promo, avtomatik to‘lov provayderi (Click/Payme), CSV/PDF eksport, to‘liq RBAC (hozir: admin / mijoz), zaxiralash skriptlari.
- Telegram Stars/Premium qayta sotish Telegram shartlari va O‘zbekiston qonunchiligiga (soliq, to‘lov qabul qilish) mos kelishini haqiqiy savdodan oldin o‘zingiz tekshiring.
