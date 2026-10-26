const API = window.STARMARKET_API_URL || `${location.origin}/api/v1`;
const tg = window.Telegram?.WebApp;
const $ = (s) => document.querySelector(s);
let token = null, tokenExp = 0, products = [], selected = null, idemKey = null, busy = false;

if (tg) { tg.ready(); tg.expand(); }
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = (v, cur) => `${Number(v).toLocaleString('uz-UZ')} ${cur}`;
const showError = (m) => { $('#error').textContent = m || ''; };
function errMsg(data, fallback) {
  if (data && typeof data.detail === 'string') return data.detail;
  if (data && Array.isArray(data.detail)) return 'Ma’lumotlar noto‘g‘ri to‘ldirilgan. Username @username ko‘rinishida bo‘lsin.';
  return fallback;
}
async function api(path, opts = {}) {
  const headers = {'Content-Type': 'application/json', ...(token ? {Authorization: `Bearer ${token}`} : {})};
  const res = await fetch(`${API}${path}`, {...opts, headers});
  let data = null; try { data = await res.json(); } catch (_) {}
  if (!res.ok) throw new Error(errMsg(data, 'So‘rov bajarilmadi'));
  return data;
}
async function auth() {
  if (!tg?.initData) throw new Error('Do‘kon Telegram ichidan (botdagi tugma orqali) ochilishi kerak.');
  const data = await api('/auth/telegram', {method: 'POST', body: JSON.stringify({init_data: tg.initData})});
  token = data.access_token;
  $('#user-label').textContent = data.user.first_name || 'Mijoz';
  tokenExp = Date.now() + (data.expires_in - 60) * 1000;
}
async function ensureAuth() { if (!token || Date.now() > tokenExp) await auth(); }

async function loadProducts() {
  $('#products').innerHTML = '<p class="muted">Yuklanmoqda…</p>';
  try {
    products = await api('/products');
    if (!products.length) { $('#products').innerHTML = '<p class="muted">Hozircha faol mahsulot yo‘q.</p>'; return; }
    $('#products').innerHTML = products.map(p => `<article class="product"><h3>${esc(p.name_uz)}</h3>
      <p>${esc(p.description || '')}</p><p>${p.category === 'stars' ? `${esc(p.amount)} Stars` : `Premium · ${esc(p.amount)} kun`}</p>
      <div class="price">${esc(money(p.price, p.currency))}</div><button data-id="${esc(p.id)}">Tanlash</button></article>`).join('');
    $('#products').querySelectorAll('[data-id]').forEach(b => b.addEventListener('click', () => selectProduct(Number(b.dataset.id))));
  } catch (e) { $('#products').innerHTML = `<p class="muted">${esc(e.message)}</p>`; }
}
function updateTotal() {
  if (!selected) return;
  const q = selected.category === 'premium' ? 1 : Math.max(1, Math.min(100, Number($('#quantity').value) || 1));
  $('#total').textContent = `Jami: ${money(Number(selected.price) * q, selected.currency)}`;
}
function selectProduct(id) {
  selected = products.find(p => p.id === id); if (!selected) return;
  idemKey = crypto.randomUUID();
  $('#checkout').hidden = false; $('#pay').hidden = true;
  $('#selected').textContent = selected.name_uz;
  $('#qty-label').hidden = selected.category === 'premium';
  $('#quantity').value = 1; updateTotal();
  $('#checkout').scrollIntoView({behavior: 'smooth'});
}
$('#quantity').addEventListener('input', updateTotal);
$('#order-form').addEventListener('submit', async (e) => {
  e.preventDefault(); if (busy || !selected) return; busy = true; showError(''); $('#submit').disabled = true;
  try {
    await ensureAuth();
    const qty = selected.category === 'premium' ? 1 : Number($('#quantity').value);
    const order = await api('/orders', {method: 'POST', body: JSON.stringify({
      product_id: selected.id, quantity: qty, idempotency_key: idemKey,
      customer_details: {telegram_username: $('#username').value.trim()}})});
    const info = await api('/payment-info');
    $('#pay-text').textContent = `${info.text}\n\nSumma: ${money(order.total_amount, order.currency)}`;
    $('#pay-order').textContent = `Buyurtma #${order.id.slice(0, 8)}`;
    $('#pay').hidden = false; $('#checkout').hidden = true; selected = null; idemKey = null;
    $('#pay').scrollIntoView({behavior: 'smooth'});
    loadOrders();
  } catch (err) { showError(err.message); }
  finally { busy = false; $('#submit').disabled = false; }
});
$('#close-app').addEventListener('click', () => tg ? tg.close() : null);

async function loadOrders() {
  try {
    await ensureAuth();
    const list = await api('/orders');
    $('#orders').innerHTML = list.length ? list.map(o => `<div class="order"><b>#${esc(o.id.slice(0, 8))}</b> · ${esc(money(o.total_amount, o.currency))}<br>
      <span class="badge">${esc(o.status_text)}</span>
      ${o.status === 'AWAITING_PAYMENT' ? `<button class="secondary small" data-cancel="${esc(o.id)}">Bekor qilish</button>` : ''}</div>`).join('')
      : '<p class="muted">Buyurtmalar yo‘q.</p>';
    $('#orders').querySelectorAll('[data-cancel]').forEach(b => b.addEventListener('click', async () => {
      if (!confirm('Buyurtmani bekor qilasizmi?')) return;
      try { await api(`/orders/${b.dataset.cancel}/cancel`, {method: 'POST'}); loadOrders(); } catch (err) { showError(err.message); }
    }));
  } catch (e) { $('#orders').innerHTML = `<p class="muted">${esc(e.message)}</p>`; }
}
$('#reload').addEventListener('click', loadProducts);
$('#reload-orders').addEventListener('click', loadOrders);
loadProducts(); loadOrders();
