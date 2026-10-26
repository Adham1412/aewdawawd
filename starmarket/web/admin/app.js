const API = window.STARMARKET_API_URL || `${location.origin}/api/v1`;
const tg = window.Telegram?.WebApp; const $ = (s) => document.querySelector(s);
let token = null, tokenExp = 0;
if (tg) { tg.ready(); tg.expand(); }
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const say = (m, ok) => { const el = $('#msg'); el.textContent = m || ''; el.className = 'msg' + (ok ? ' ok' : ''); };
// Mirror of backend transitions; the server enforces them regardless.
const NEXT = {PAYMENT_SUBMITTED: [['PAID', '✅ To‘lov tushdi'], ['AWAITING_PAYMENT', '↩ Chek noto‘g‘ri'], ['CANCELLED', '✖ Bekor']],
  AWAITING_PAYMENT: [['CANCELLED', '✖ Bekor']], PAID: [['PROCESSING', '▶ Bajarishni boshlash'], ['REFUND_PENDING', '💸 Qaytarish']],
  PROCESSING: [['COMPLETED', '✔ Yetkazildi'], ['FAILED', '⚠ Muammo']], FAILED: [['PROCESSING', '▶ Qayta urinish'], ['REFUND_PENDING', '💸 Qaytarish']],
  REFUND_PENDING: [['REFUNDED', '✔ Pul qaytarildi']]};
async function api(path, opts = {}) {
  if (!token || Date.now() > tokenExp) {
    if (!tg?.initData) throw new Error('Admin panel faqat Telegram ichida (botdagi Admin tugmasi) ochiladi.');
    const r = await fetch(`${API}/auth/telegram`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({init_data: tg.initData})});
    const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.detail || 'Kirish rad etildi');
    token = d.access_token; tokenExp = Date.now() + (d.expires_in - 60) * 1000;
  }
  const res = await fetch(`${API}${path}`, {...opts, headers: {'Content-Type': 'application/json', Authorization: `Bearer ${token}`}});
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : 'Ma’lumot noto‘g‘ri yoki so‘rov bajarilmadi');
  return data;
}
const wrap = (fn) => async (...a) => { try { say(''); await fn(...a); } catch (e) { say(e.message); } };

const loadOrders = wrap(async () => {
  const f = $('#flt').value; const list = await api(`/admin/orders?limit=100${f ? `&status=${encodeURIComponent(f)}` : ''}`);
  $('#orders').innerHTML = list.length ? list.map(o => `<div class="card"><b>#${esc(o.id.slice(0, 8))}</b> · ${esc(o.product_name)} ×${esc(o.quantity)} · <b>${esc(Number(o.total_amount).toLocaleString('uz-UZ'))} ${esc(o.currency)}</b><br>
    Mijoz: ${esc(o.customer_telegram_id)} @${esc(o.customer_username || '-')} · Qabul qiluvchi: <b>${esc(o.customer_details.telegram_username || '?')}</b><br>
    <span class="badge">${esc(o.status)}</span> <small>${esc(new Date(o.created_at).toLocaleString())}</small><div class="actions">
    ${(NEXT[o.status] || []).map(([to, label]) => `<button data-o="${esc(o.id)}" data-to="${esc(to)}">${esc(label)}</button>`).join('')}</div></div>`).join('') : '<p>Buyurtma yo‘q.</p>';
  $('#orders').querySelectorAll('[data-o]').forEach(b => b.addEventListener('click', wrap(async () => {
    if (b.dataset.to === 'PAID' && !confirm('Pul haqiqatan kartaga tushganini bank ilovasida tekshirdingizmi?')) return;
    if (!confirm(`Holat: ${b.dataset.to}. Tasdiqlaysizmi?`)) return;
    await api(`/admin/orders/${b.dataset.o}/transition`, {method: 'POST', body: JSON.stringify({to_status: b.dataset.to})});
    say('Bajarildi', true); loadOrders();
  })));
});
const loadProducts = wrap(async () => {
  const list = await api('/admin/products');
  $('#products').innerHTML = list.map(p => `<div class="card"><b>${esc(p.name_uz)}</b> <small>${esc(p.code)} · ${esc(p.category)} · ${esc(p.amount)}</small><br>
    ${esc(Number(p.price).toLocaleString('uz-UZ'))} ${esc(p.currency)} · <span class="badge">${p.is_active ? 'FAOL' : 'nofaol'}</span>
    <div class="actions"><button data-pid="${esc(p.id)}" data-act="toggle" data-on="${p.is_active}">${p.is_active ? 'O‘chirish' : 'Yoqish'}</button>
    <button data-pid="${esc(p.id)}" data-act="price">Narxni o‘zgartirish</button></div></div>`).join('') || '<p>Mahsulot yo‘q.</p>';
  $('#products').querySelectorAll('[data-pid]').forEach(b => b.addEventListener('click', wrap(async () => {
    const body = b.dataset.act === 'toggle' ? {is_active: b.dataset.on !== 'true'} : (() => { const v = prompt('Yangi narx:'); return v ? {price: v} : null; })();
    if (!body) return;
    await api(`/admin/products/${b.dataset.pid}`, {method: 'PATCH', body: JSON.stringify(body)}); loadProducts();
  })));
});
$('#pform').addEventListener('submit', wrap(async (e) => {
  e.preventDefault(); const f = Object.fromEntries(new FormData(e.target));
  await api('/admin/products', {method: 'POST', body: JSON.stringify({...f, amount: Number(f.amount), price: String(f.price), is_active: false})});
  e.target.reset(); say('Yaratildi (nofaol). Narx va tarkibni tekshirib, "Yoqish" ni bosing.', true); loadProducts();
}));
const loadStats = wrap(async () => { $('#stats').textContent = JSON.stringify(await api('/admin/stats'), null, 2); });
const loadAudit = wrap(async () => { $('#audit').textContent = (await api('/admin/audit?limit=50')).map(a => `${a.at} · ${a.actor ?? '-'} · ${a.action} · ${a.target}`).join('\n'); });
const LOAD = {orders: loadOrders, products: loadProducts, stats: loadStats, audit: loadAudit};
document.querySelectorAll('[data-tab]').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('[data-tab]').forEach(x => x.classList.toggle('on', x === b));
  Object.keys(LOAD).forEach(t => { $(`#tab-${t}`).hidden = t !== b.dataset.tab; }); LOAD[b.dataset.tab]();
}));
$('#flt').addEventListener('change', loadOrders);
wrap(async () => { const me = await api('/admin/me'); $('#who').textContent = `admin ${me.telegram_id}`; loadOrders(); })();
