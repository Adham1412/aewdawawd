# StarMarket — Yakuniy texnik topshiriq (MVP)

## Maqsad
Telegram bot va Mini App orqali Telegram Stars hamda Telegram Premium mahsulotlari buyurtmasini qabul qilish, to‘lov holatini yuritish va yetkazib berishni rasmiy imkoniyatlar mavjud bo‘lganda avtomatlashtirish.

## MVP komponentlari
- Python + aiogram Telegram bot.
- FastAPI REST API (`/api/v1`) va OpenAPI/Swagger.
- PostgreSQL, SQLAlchemy va Alembic migratsiyalari.
- HTML/CSS/JavaScript Mini App va admin web UI.
- Buyurtmalar, mahsulotlar, foydalanuvchilar, ledger va audit modellari.
- Telegram `initData` tekshiruvi va qisqa muddatli server sessiyasi.
- Idempotent buyurtma yaratish, buyurtma holatini kuzatish.
- Soxta to‘lov provayderi va keyinchalik rasmiy sandbox adapteri.
- CSV/XLSX/PDF hisobotlar, RBAC, real to‘lovlar va to‘liq admin CRUD — ishlab chiqishning keyingi modullari.

## Arxitektura tamoyillari
- Bot va API alohida jarayonlar; biznes qoidalari umumiy modullarda.
- Narx faqat backend ma’lumotlaridan hisoblanadi.
- Moliyaviy yozuvlar append-only ledger tamoyiliga asoslanadi.
- Takroriy so‘rovlar idempotency key bilan boshqariladi.
- To‘lov holati noaniq bo‘lsa, tizim uni muvaffaqiyatli deb hisoblamaydi.
- Xatolik javoblari ichki tafsilotlarni oshkor qilmaydi; request ID kuzatuv uchun beriladi.
- Ishlab chiqarish muhitida schema `create_all` emas, tekshirilgan Alembic migratsiyalari orqali yangilanadi.

## Ochiq ishlab chiqarish shartlari
1. To‘lov provayderi shartlari va rasmiy sandbox tekshirilishi.
2. Stars/Premium yetkazib berish yo‘li va yetkazib beruvchi vakolati tasdiqlanishi.
3. Admin autentifikatsiyasi, RBAC va sessiyalarni darhol bekor qilish mexanizmi to‘liq ishlab chiqilishi.
4. To‘liq ledger tranzaksiyalari, refund, reconciliation va fon vazifalari qo‘shilishi.
5. Hosting, zaxira nusxalari, monitoring, CI va xavfsizlik auditi bajarilishi.

## Chiqarish mezonlari
- Testlar muvaffaqiyatli.
- Noto‘g‘ri initData va muddati o‘tgan sessiyalar rad etiladi.
- Takroriy buyurtma yangi dublikat yaratmaydi.
- To‘lov holati noaniq bo‘lganda pul yoki buyurtma holati taxmin bilan o‘zgarmaydi.
- Xodim ruxsatsiz API amallarini bajara olmaydi.
- Tiklash sinovi va provayder solishtirishi bajariladi.
- Administrator production release’ni alohida tasdiqlaydi.
