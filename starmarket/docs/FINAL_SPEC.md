# StarMarket
## Yakuniy texnik topshiriq — MVP v1.0

**Loyiha turi:** Telegram savdo boti va Mini App
**Mahsulotlar:** Telegram Stars va Telegram Premium
**Boshlang‘ich budjet:** 0 so‘m
**Asosiy texnologiyalar:** Python, aiogram, yengil REST API frameworki, PostgreSQL, HTML, CSS va JavaScript
**Loyiha holati:** Talablar shakllantirilgan; texnik tayyorgarlik va dasturlash bosqichiga o‘tish mumkin.

---

## 1. Loyiha maqsadi

StarMarket — Telegram orqali raqamli mahsulotlarni buyurtma qilish, to‘lov holatini kuzatish, buyurtmalarni boshqarish va xizmatlarni imkon qadar avtomatik yetkazib berish uchun mo‘ljallangan savdo platformasi.

Tizim quyidagi qismlardan tashkil topadi:

1. Telegram bot — mijozlar bilan muloqot va buyurtmalar.
2. Telegram Mini App — katalog, balans, checkout va buyurtmalar tarixi.
3. Admin web-panel — mahsulotlar, buyurtmalar, to‘lovlar, xodimlar va hisobotlar boshqaruvi.
4. Backend API — umumiy biznes qoidalari va autentifikatsiya.
5. Ma’lumotlar bazasi — mijozlar, buyurtmalar, tranzaksiyalar va audit ma’lumotlari.
6. Yetkazib berish integratsiyalari — rasmiy va tekshirilgan usullar mavjud bo‘lganda.

## 2. MVP doirasiga kiradigan funksiyalar

### 2.1. Mijozlar uchun

- Telegram orqali kirish.
- O‘zbek, rus va ingliz tillari.
- Mamlakatga mos valyutani tanlash.
- Telegram Stars paketlari va maxsus miqdorni tanlash.
- Telegram Premium uchun mavjud muddatlarni ko‘rsatish.
- Mahsulotlar katalogi, qidiruv va saralash.
- Mahsulotga mos checkout maydonlari.
- Buyurtma ID va yakuniy narxni tasdiqlash.
- Balansni to‘ldirish va balansdan to‘liq to‘lov qilish.
- Buyurtmalar tarixi va holatlarini kuzatish.
- Referral havolalari, bonus balansi va promo-kodlar.
- Yordam markazi va murojaatlar.
- To‘lov va yetkazib berish holati haqida bildirishnomalar.
- Buyurtma va to‘lov tarixini yuklab olish.

### 2.2. Admin panel

- Buyurtmalar va to‘lovlarni boshqarish.
- Mahsulotlar, narxlar, limitlar va chegirmalarni sozlash.
- Xodimlar uchun individual ruxsatlar.
- Refund so‘rovlarini tekshirish.
- Yetkazib berish xatolarini boshqarish.
- Mijoz murojaatlari va topshiriqlarni taqsimlash.
- Kunlik, haftalik, oylik va maxsus davr hisobotlari.
- CSV, Excel va moliyaviy PDF eksporti.
- Audit jurnali.
- Tizim holati va muhim xatolar monitoringi.
- Zaxiralash va tiklash holatini kuzatish.

### 2.3. Birinchi versiyadan tashqarida

- Telegram sovg‘alari savdosi — keyingi versiyada.
- Mijozlardan Telegram Stars sotib olish yoki ularni qayta qabul qilish — MVP’da yo‘q.
- Tasdiqlanmagan yetkazib beruvchi orqali avtomatlashtirish — yo‘q.
- Telegram akkaunt paroli yoki kirish kodini so‘rash — qat’iyan taqiqlanadi.

## 3. Tavsiya etilgan texnologik stek

| Qism | Texnologiya |
|---|---|
| Telegram bot | Python + aiogram |
| REST API | FastAPI |
| Ma’lumotlar bazasi | PostgreSQL |
| DB migratsiyalari | Alembic |
| ORM | SQLAlchemy |
| Mini App | HTML, CSS, JavaScript |
| Admin panel | HTML, CSS, JavaScript |
| API hujjatlari | OpenAPI / Swagger |
| Python bog‘liqliklari | pyproject.toml + lock-fayl |
| Versiya nazorati | Git |
| Testlar | pytest va integratsion testlar |
| Ishga tushirish | Muhitga mos alohida bot va API xizmatlari |

FastAPI tanlovi yengil framework, REST API va avtomatik OpenAPI hujjatlari talablariga mos keladi. Bu — texnik tavsiya; ishlab chiqarish muhitiga chiqarishdan oldin haqiqiy hosting imkoniyatlari tekshiriladi.

## 4. Arxitektura

```text
Mijoz
  ├── Telegram Bot
  └── Telegram Mini App
           │
           ▼
       REST API
        /api/v1
           │
           ▼
   Biznes xizmatlari
  ├── Auth / Permissions
  ├── Catalog / Pricing
  ├── Orders / Queue
  ├── Payments / Wallet
  ├── Fulfilment
  ├── Referrals / Promos
  ├── Support
  ├── Reports / Analytics
  └── Notifications
           │
           ▼
     Ma'lumotlar qatlami
           │
           ▼
       PostgreSQL

Admin Web Panel ── REST API

Tashqi adapterlar:
  ├── To‘lov provayderi
  └── Rasmiy yetkazib berish integratsiyasi
```

Bot va API alohida xizmatlarda ishlaydi. Umumiy biznes qoidalari alohida modullarda saqlanadi. MVP’da mikroxizmatlar sonini sun’iy ravishda oshirmaslik kerak.

## 5. Ma’lumotlar bazasi

Asosiy jadvallar:

- `users` — Telegram ID, profil va sozlamalar.
- `admin_users` — admin hisoblari.
- `permissions` — individual ruxsatlar.
- `products` — mahsulotlar va holati.
- `product_variants` — Stars miqdori yoki Premium muddati.
- `prices` — narxlar, valyuta va amal qilish davri.
- `orders` — buyurtma ma’lumotlari va holati.
- `order_events` — buyurtma holatlari tarixi.
- `payments` — to‘lov urinishlari va provayder identifikatorlari.
- `ledger_accounts` — balans hisoblari.
- `ledger_entries` — balans va moliyaviy yozuvlar.
- `refund_requests` — qaytarish so‘rovlari.
- `referrals` — takliflar va birinchi xarid holati.
- `promo_codes` — promo-kodlar va shartlar.
- `support_tickets` — mijoz murojaatlari.
- `notifications` — bildirishnomalar tarixi.
- `audit_logs` — boshqaruv amallari.
- `idempotency_keys` — takroriy so‘rovlarni nazorat qilish.
- `outbox_events` — ishonchli fon vazifalarini yetkazish.
- `schema_migrations` — sxema versiyalari.

Moliyaviy jurnal append-only tamoyilida yuritiladi: tasdiqlangan yozuvlar o‘zgartirib yuborilmaydi. Xato bo‘lsa, qarama-qarshi tuzatuvchi yozuv yaratiladi.

## 6. Buyurtma va to‘lov holatlari

### Buyurtma

`CREATED → AWAITING_PAYMENT → PAID → QUEUED → PROCESSING → COMPLETED`

Muqobil holatlar:

- `FAILED`
- `NEEDS_REVIEW`
- `CANCELLED`
- `REFUND_PENDING`
- `REFUNDED`

Holatlar o‘zboshimchalik bilan o‘zgartirilmaydi; ruxsat etilgan o‘tishlar backend xizmatida tekshiriladi.

### To‘lov

- `PENDING`
- `CONFIRMED`
- `FAILED`
- `UNKNOWN`
- `REFUND_PENDING`
- `REFUNDED`

Provayder javobi noaniq bo‘lsa, to‘lov muvaffaqiyatli deb taxmin qilinmaydi. Avval provayder holati tekshiriladi.

## 7. Xavfsizlik

- Telegram Mini App `initData` imzosi backendda tekshiriladi.
- Qisqa muddatli server sessiyalari ishlatiladi.
- Admin panelida ikki bosqichli autentifikatsiya talab qilinadi.
- Har bir API endpointi server tomonida ruxsatlarni tekshiradi.
- So‘rovlar limiti va shubhali faollik nazorati qo‘llanadi.
- Muhim amallarda qayta tasdiqlash talab qilinadi.
- Maxfiy kalitlar kodga kiritilmaydi.
- Xatolik javoblarida ichki stack trace yoki maxfiy ma’lumotlar berilmaydi.
- Audit jurnali kim, qachon va qanday amal bajarganini qayd etadi.
- Parol va tokenlar loglarga yozilmaydi.
- Xavfsizlik hodisasida tegishli sessiyalar bekor qilinadi va xavfli amallar cheklanadi.

## 8. To‘lov va balans xavfsizligi

- Har bir moliyaviy operatsiya tranzaksion tarzda bajariladi.
- Bir xil so‘rov takrorlansa, dublikat to‘lov yoki balans o‘zgarishi yuz bermasligi kerak.
- Webhook imzosi va provayder ma’lumotlari tekshiriladi.
- Ichki ledger va provayder hisobotlari solishtiriladi.
- Refund faqat ruxsatli xodim tomonidan tasdiqlanadi.
- Mijoz balansidan buyurtma summasi to‘liq yechiladi; qisman balans va tashqi to‘lovni aralashtirish MVP’da qo‘llanmaydi.
- Mijozga pul qaytarilishi tasdiqlanmaguncha refund yakunlangan deb ko‘rsatilmaydi.

## 9. Yetkazib berish

Har bir mahsulot turi adapter orqali yetkazib berish xizmatiga ulanadi.

- Avtomatik yetkazib berish faqat rasmiy va sinovdan o‘tgan usul mavjud bo‘lsa yoqiladi.
- Avtomatik yo‘l mavjud bo‘lmasa, buyurtma admin navbatiga tushadi.
- Qayta urinishlar soni cheklanadi.
- Qayta urinishdan oldin oldingi operatsiya natijasi tekshiriladi.
- Yetkazib berish dalili yetarli bo‘lmasa, buyurtma admin tekshiruviga yuboriladi.
- Mijozning Telegram paroli yoki kirish kodi hech qachon so‘ralmaydi.

## 10. Hosting va zaxiralash

- Avval bepul hosting variantlari tekshiriladi.
- PostgreSQL’ning bepul boshqariladigan varianti mavjud bo‘lsa, u afzal.
- Bepul xizmatning uyqu holati, ma’lumotlarni saqlash muddati, tarmoq va fon vazifalari cheklovlari sinovdan o‘tkaziladi.
- Zaxiralar asosiy serverdan alohida va shifrlangan holda saqlanadi.
- Kunlik zaxiralar 30 kun, oylik zaxiralar 6 oy saqlanadi.
- Tiklash sinovlari test muhitida muntazam bajariladi.
- Xizmat tiklangach, buyurtmalar, to‘lovlar va ledger ma’lumotlari solishtiriladi.

## 11. Test va chiqarish jarayoni

1. Lokal ishlab chiqish.
2. Unit testlar.
3. API va integratsiya testlari.
4. Soxta to‘lov provayderi bilan test.
5. Buyurtma va yetkazib berish xatolarini simulyatsiya qilish.
6. Ruxsatlar va xavfsizlik testlari.
7. Test muhitiga chiqarish.
8. Zaxiradan tiklash va yuklama testlari.
9. Administrator tasdig‘i.
10. Bosqichma-bosqich ishlab chiqarishga chiqarish.
11. Muammo bo‘lsa oldingi versiyaga qaytish.

## 12. Dasturlash tartibi

**1-bosqich:** loyiha skeleti, konfiguratsiya, logging va test muhiti.

**2-bosqich:** PostgreSQL, migratsiyalar, foydalanuvchilar va autentifikatsiya.

**3-bosqich:** katalog, mahsulotlar va narxlar.

**4-bosqich:** buyurtmalar, holatlar, navbat va idempotentlik.

**5-bosqich:** balans va ledger.

**6-bosqich:** soxta to‘lov provayderi va to‘lov testlari.

**7-bosqich:** yetkazib berish adapteri va admin navbati.

**8-bosqich:** Telegram bot interfeysi.

**9-bosqich:** Mini App va admin web-panel.

**10-bosqich:** analitika, hisobotlar, referral va promo-kodlar.

**11-bosqich:** xavfsizlik, monitoring, zaxiralash va yakuniy testlar.

**12-bosqich:** rasmiy integratsiyalar tekshirilgach, beta va ishlab chiqarish muhiti.

## 13. Dasturlashni boshlashdan oldingi ochiq masalalar

Quyidagilar dastlabki kodni yozishga to‘sqinlik qilmaydi, lekin haqiqiy savdoni yoqishdan oldin hal qilinishi shart:

1. Telegram Stars va Premium uchun rasmiy, amalda mavjud yetkazib berish usuli yoki vakolatli yetkazib beruvchi.
2. Click/Payme yoki boshqa mos to‘lov provayderi bilan integratsiya shartlari.
3. Bepul PostgreSQL va ilova hostingining amaliy cheklovlari.
4. Real narxlar, tannarxlar, valyuta kursi va komissiyalar.
5. Ommaviy ishga tushirishdan oldingi qonuniy talablar va foydalanuvchi shartlari.

Bu masalalar tasdiqlanmaguncha soxta provayder va test ma’lumotlari bilan ishlanadi. Haqiqiy pul yoki mahsulot yetkazib berish jarayoni sinov rejimidan ajratiladi.

---

## Yakuniy natija

StarMarket uchun MVP doirasini, asosiy modullarni, ma’lumotlar bazasini, xavfsizlik talablarini va dasturlash ketma-ketligini belgilovchi dastlabki texnik topshiriq tayyor. Keyingi amaliy qadam — loyihaning papka tuzilmasi, konfiguratsiyasi, ma’lumotlar bazasi migratsiyalari va testlar bilan boshlang‘ich kod skeletini yaratish.
