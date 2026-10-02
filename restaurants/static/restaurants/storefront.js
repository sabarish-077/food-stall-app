(() => {
  const api = '/api';
  const $ = (selector) => document.querySelector(selector);
  const grid = $('#menu-grid');
  const cart = new Map((() => { try { return JSON.parse(localStorage.getItem('foodstall_cart') || '[]').map(([id, quantity]) => [Number(id), Number(quantity)]); } catch (_) { return []; } })());
  const specialNotes = new Map();
  let menuItems = [];
  let activeCategory = 'all';
  let favorites = JSON.parse(localStorage.getItem('foodstall_favorites') || '[]').map(Number);
  const demoDeliveryFee = Number($('#cart-panel').dataset.deliveryFee || 0);
  const money = (value) => `₹${Number(value).toFixed(0)}`;
  const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const csrfToken = () => document.cookie.split('; ').find((entry) => entry.startsWith('csrftoken='))?.split('=').slice(1).join('=') || '';

  function toast(message) {
    const box = $('#toast'); box.textContent = message; box.classList.add('show');
    setTimeout(() => box.classList.remove('show'), 2600);
  }
  function closePanels() {
    $('#scrim').classList.remove('open');
    document.querySelectorAll('.side-panel,.modal').forEach((el) => { el.classList.remove('open'); el.setAttribute('aria-hidden', 'true'); });
  }
  function openPanel(id) {
    $('#scrim').classList.add('open');
    const el = document.getElementById(id); el.classList.add('open'); el.setAttribute('aria-hidden', 'false');
  }
  function foodIcon(item) {
    const text = `${item.name} ${item.category}`.toLowerCase();
    if (/tea|coffee|drink|juice|shake/.test(text)) return '🥤';
    if (/sweet|dessert|cake/.test(text)) return '🍰';
    if (/rice|biryani/.test(text)) return '🍛';
    if (/sandwich|burger|roll/.test(text)) return '🥪';
    if (/noodle|pasta/.test(text)) return '🍜';
    return item.is_vegetarian ? '🥗' : '🍲';
  }
  function foodImage(item) {
    const text = `${item.name} ${item.category}`.toLowerCase();
    if (/chai|tea|coffee|drink|juice/.test(text)) return '/static/restaurants/food-chai.svg';
    if (/samosa|snack|savoury|savory/.test(text)) return '/static/restaurants/food-samosa.svg';
    return '/static/restaurants/food-dosa.svg';
  }
  function renderCategories() {
    const categories = ['all', ...new Set(menuItems.map((item) => item.category))];
    $('#categories').innerHTML = categories.map((name) => `<button class="category ${name === activeCategory ? 'active' : ''}" data-category="${escapeHtml(name)}">${name === 'all' ? 'Everything' : escapeHtml(name)}</button>`).join('');
  }
  function renderMenu() {
    const search = $('#menu-search').value.trim().toLowerCase();
    const diet = $('#diet-filter').value;
    const priceLimit = $('#price-filter').value;
    const items = menuItems.filter((item) => (activeCategory === 'all' || item.category === activeCategory)
      && (!search || `${item.name} ${item.description} ${item.category}`.toLowerCase().includes(search))
      && (diet === 'all' || (diet === 'veg' ? item.is_vegetarian : !item.is_vegetarian))
      && (priceLimit === 'all' || Number(item.price) <= Number(priceLimit)));
    if (!items.length) { grid.innerHTML = `<div class="empty-state">${menuItems.length ? 'Nothing in this category yet.' : 'Our menu is getting ready. Please check back soon.'}</div>`; return; }
    grid.innerHTML = items.map((item, index) => `<article class="food-card"><a class="dish-art dish-detail-link" data-tone="${index % 4}" href="/food/${item.id}/" aria-label="View details for ${escapeHtml(item.name)}"><img src="${escapeHtml(item.image_url || foodImage(item))}" alt="${escapeHtml(item.name)}" loading="lazy" onerror="this.onerror=null;this.src='${foodImage(item)}'">${item.is_vegetarian ? '<span class="veg-tag">🌱 VEG</span>' : '<span class="nonveg-tag">NON-VEG</span>'}${item.discount_percent ? `<span class="dish-badge">${item.discount_percent}% OFF</span>` : item.is_bestseller ? '<span class="dish-badge">BESTSELLER</span>' : item.is_new ? '<span class="dish-badge">NEW</span>' : ''}</a><button class="favorite-button ${favorites.includes(item.id) ? 'saved' : ''}" data-favorite="${item.id}" aria-label="Save ${escapeHtml(item.name)}">♥</button><div class="food-info"><div class="dish-line"><h3><a href="/food/${item.id}/">${escapeHtml(item.name)}</a></h3><span class="price-wrap"><span class="price">${money(item.price)}</span>${item.discount_percent ? `<del>${money(item.original_price)}</del>` : ''}</span></div><p>${escapeHtml(item.description || item.category)}</p><div class="dish-meta"><span>★ ${escapeHtml(item.rating || '4.8')}</span><span>${'🌶'.repeat(Math.max(0,Math.min(3,Number(item.spice_level)))) || 'Mild'}</span><span>◷ ${item.preparation_minutes || 15} min</span></div><a class="detail-button" href="/food/${item.id}/">View details <span>→</span></a><button class="add-button" data-add="${item.id}">＋ &nbsp; ADD TO CART</button></div></article>`).join('');
  }
  function renderCart() {
    localStorage.setItem('foodstall_cart', JSON.stringify([...cart]));
    const count = [...cart.values()].reduce((sum, value) => sum + value, 0);
    const subtotal = [...cart].reduce((sum, [id, quantity]) => sum + Number(menuItems.find((item) => item.id === id)?.price || 0) * quantity, 0);
    const fee = $('#fulfillment').value === 'pickup' || !count ? 0 : demoDeliveryFee;
    $('#cart-count').textContent = count; $('#cart-totals').innerHTML = `<div class="totals-line"><span>Subtotal</span><span>${money(subtotal)}</span></div><div class="totals-line"><span>Delivery</span><span>${fee ? money(fee) : 'Free'}</span></div><div class="cart-total"><span>Total</span><b>${money(subtotal + fee)}</b></div>`; $('#checkout-open').disabled = !count;
    if (!count) { $('#cart-lines').innerHTML = '<div class="empty-state">Your cart is ready for something tasty.</div>'; return; }
    $('#cart-lines').innerHTML = [...cart].map(([id, quantity]) => {
      const item = menuItems.find((row) => row.id === id);
      return `<div class="cart-row"><div><h3>${escapeHtml(item.name)}</h3><small>${money(item.price)} each</small><input class="item-note" data-note="${id}" maxlength="240" value="${escapeHtml(specialNotes.get(id) || '')}" placeholder="Special instructions"></div><div class="quantity"><button data-change="${id}" data-by="-1" aria-label="Remove one">−</button><b>${quantity}</b><button data-change="${id}" data-by="1" aria-label="Add one">＋</button></div></div>`;
    }).join('');
  }
  async function loadMenu() {
    try {
      const response = await fetch(`${api}/menu/`); if (!response.ok) throw new Error();
      menuItems = await response.json();
      const addId = Number(new URLSearchParams(location.search).get('add_to_cart'));
      if (addId && menuItems.some((item) => item.id === addId)) { cart.set(addId, (cart.get(addId) || 0) + 1); history.replaceState({}, '', '/#menu'); toast(`${menuItems.find((item) => item.id === addId).name} added to your cart`); }
      renderCategories(); renderMenu(); renderCart();
    } catch (_) { grid.innerHTML = '<div class="empty-state">Could not connect to the kitchen. Refresh the page and try again.</div>'; }
  }
  async function loadOffers() {
    try {
      const response = await fetch(`${api}/offers/`); const offers = await response.json();
      $('#offer-grid').innerHTML = offers.length ? offers.map((offer) => `<article class="offer-card"><span class="offer-icon">✦</span><span class="eyebrow">A TREAT FOR YOU</span><h3>${escapeHtml(offer.title)}</h3><p>${escapeHtml(offer.description)}</p><div class="coupon-row"><code>${escapeHtml(offer.code)}</code><button data-copy-code="${escapeHtml(offer.code)}">Copy code</button></div><small>${offer.discount_percent}% off · Min. order ${money(offer.minimum_order)}</small></article>`).join('') : '<div class="empty-state">No offers today — check back soon.</div>';
    } catch (_) { $('#offer-grid').innerHTML = '<div class="empty-state">Offers will appear here.</div>'; }
  }
  async function loadReviews() {
    try {
      const response = await fetch(`${api}/reviews/`); const reviews = await response.json();
      $('#review-grid').innerHTML = reviews.length ? reviews.map((review) => `<article class="review-card"><div class="stars">${'★'.repeat(review.rating)}${'☆'.repeat(5-review.rating)}</div><p>“${escapeHtml(review.comment)}”</p><b>${escapeHtml(review.customer_name)}</b></article>`).join('') : '<div class="empty-state">Be the first to share a note after your order.</div>';
    } catch (_) { $('#review-grid').innerHTML = '<div class="empty-state">Customer notes will appear here.</div>'; }
  }
  async function updateAvailableTables() {
    const form = $('#booking-form'); const values = new FormData(form);
    const date = values.get('date'), time = values.get('time'), guests = values.get('guests');
    const select = $('#table-select');
    if (!date || !time || !guests) { select.innerHTML = '<option value="">Choose date, time and guests first</option>'; return; }
    select.innerHTML = '<option value="">Checking tables…</option>';
    try {
      const params = new URLSearchParams({date, time, guests}); const response = await fetch(`${api}/tables/?${params}`); const tables = await response.json();
      select.innerHTML = tables.length ? '<option value="">Select a table</option>' + tables.map((table) => `<option value="${table.id}">Table ${escapeHtml(table.number)} · ${table.capacity} seats · ${escapeHtml(table.location)}</option>`).join('') : '<option value="">No tables available for that slot</option>';
    } catch (_) { select.innerHTML = '<option value="">Could not check availability</option>'; }
  }
  function showFavorites() {
    const saved = menuItems.filter((item) => favorites.includes(item.id));
    $('#favorite-list').innerHTML = saved.length ? saved.map((item) => `<div class="favorite-row"><div><b>${escapeHtml(item.name)}</b><small>${money(item.price)}</small></div><button class="add-button" data-fav-add="${item.id}">Add to cart</button><button class="remove-favorite" data-fav-remove="${item.id}" aria-label="Remove favorite">×</button></div>`).join('') : '<div class="empty-state">Tap the heart on a dish to save it here.</div>';
    openPanel('favorites-modal');
  }
  function orderTokens() { try { return JSON.parse(localStorage.getItem('foodstall_order_tokens') || '[]'); } catch (_) { return []; } }
  function bookingTokens() { try { return JSON.parse(localStorage.getItem('foodstall_booking_tokens') || '[]'); } catch (_) { return []; } }
  async function showOrders() {
    openPanel('orders-modal'); const box = $('#order-history'); const tokens = orderTokens(); const reservations = bookingTokens();
    if (!tokens.length && !reservations.length) { box.innerHTML = '<div class="empty-state">Your orders and table reservations will appear here.</div>'; return; }
    box.innerHTML = '<div class="loading-card">Checking your orders…</div>';
    const [responses, reservationResponses] = await Promise.all([Promise.all(tokens.map(async (token) => {
      try { const response = await fetch(`${api}/orders/track/${encodeURIComponent(token)}/`); return response.ok ? {...await response.json(), tracking_token: token} : null; } catch (_) { return null; }
    })), Promise.all(reservations.map(async (token) => {
      try { const response = await fetch(`${api}/bookings/track/${encodeURIComponent(token)}/`); return response.ok ? await response.json() : null; } catch (_) { return null; }
    }))]);
    const orders = responses.filter(Boolean); const bookings = reservationResponses.filter(Boolean);
    const orderMarkup = orders.map((order) => `<article class="order-entry"><b>Order #${order.order_id}</b><span class="status-pill">${escapeHtml(String(order.status).replaceAll('_', ' '))}</span><p>${order.items.map((item) => `${item.quantity} × ${escapeHtml(item.name)}`).join(', ')}</p><p>${escapeHtml(order.fulfillment)} · ${new Date(order.created_at).toLocaleString()}</p><div class="order-steps"><i class="${['placed','confirmed','preparing','ready','out_for_delivery','completed'].indexOf(order.status)>=0?'done':''}">Confirmed</i><i class="${['preparing','ready','out_for_delivery','completed'].includes(order.status)?'done':''}">Preparing</i><i class="${['ready','out_for_delivery','completed'].includes(order.status)?'done':''}">Ready</i><i class="${['out_for_delivery','completed'].includes(order.status)?'done':''}">${order.fulfillment==='pickup'?'Pickup':'On the way'}</i><i class="${order.status==='completed'?'done':''}">Done</i></div>${['placed','confirmed'].includes(order.status) ? `<button class="cancel-order" data-cancel-order="${escapeHtml(order.tracking_token)}" type="button">Cancel order</button>` : ''}</article>`).join('');
    const bookingMarkup = bookings.map((booking) => `<article class="order-entry"><b>Table booking #${booking.booking_id}</b><span class="status-pill">${escapeHtml(booking.status)}</span><p>Table ${escapeHtml(booking.table)} · ${booking.guests} guests · ${escapeHtml(booking.date)} at ${escapeHtml(booking.time)}</p></article>`).join('');
    box.innerHTML = (orderMarkup ? '<h3 class="history-heading">Orders</h3>' + orderMarkup : '') + (bookingMarkup ? '<h3 class="history-heading">Table bookings</h3>' + bookingMarkup : '') || '<div class="empty-state">Could not check your history right now. Please try again.</div>';
  }

  $('#categories').addEventListener('click', (event) => {
    const button = event.target.closest('[data-category]'); if (!button) return;
    activeCategory = button.dataset.category; renderCategories(); renderMenu();
  });
  grid.addEventListener('click', (event) => {
    const favorite = event.target.closest('[data-favorite]');
    if (favorite) { const id = Number(favorite.dataset.favorite); favorites = favorites.includes(id) ? favorites.filter((saved) => saved !== id) : [...favorites, id]; localStorage.setItem('foodstall_favorites', JSON.stringify(favorites)); renderMenu(); return; }
    const button = event.target.closest('[data-add]'); if (!button) return;
    const id = Number(button.dataset.add); cart.set(id, (cart.get(id) || 0) + 1); renderCart();
    toast(`${menuItems.find((item) => item.id === id).name} added to your cart`);
  });
  $('#cart-open').addEventListener('click', () => { renderCart(); openPanel('cart-panel'); });
  $('#orders-open').addEventListener('click', showOrders);
  $('#order-history').addEventListener('click', async (event) => {
    const button = event.target.closest('[data-cancel-order]'); if (!button) return;
    if (!window.confirm('Cancel this order?')) return;
    button.disabled = true;
    try {
      const response = await fetch(`${api}/orders/track/${encodeURIComponent(button.dataset.cancelOrder)}/cancel/`, {
        method: 'POST', headers: {'X-CSRFToken': csrfToken()},
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Could not cancel this order.');
      toast('Order cancelled');
      await showOrders();
    } catch (error) {
      toast(error.message || 'Could not cancel this order.');
      button.disabled = false;
    }
  });
  $('#favorites-open').addEventListener('click', showFavorites);
  $('#menu-search').addEventListener('input', renderMenu);
  $('#diet-filter').addEventListener('change', renderMenu);
  $('#price-filter').addEventListener('change', renderMenu);
  $('#fulfillment').addEventListener('change', renderCart);
  $('#hero-booking').addEventListener('click', () => openPanel('booking-modal'));
  $('#booking-open').addEventListener('click', () => openPanel('booking-modal'));
  $('#review-open').addEventListener('click', () => openPanel('review-modal'));
  ['date','time','guests'].forEach((name) => $('#booking-form').elements[name].addEventListener('change', updateAvailableTables));
  $('#booking-date').min = new Date().toISOString().slice(0, 10);
  $('#booking-form').elements.guests.addEventListener('input', updateAvailableTables);
  $('#offer-grid').addEventListener('click', async (event) => { const button = event.target.closest('[data-copy-code]'); if (!button) return; await navigator.clipboard.writeText(button.dataset.copyCode); $('#coupon-code').value = button.dataset.copyCode; toast('Offer code copied'); });
  $('#favorite-list').addEventListener('click', (event) => {
    const add = event.target.closest('[data-fav-add]'); const remove = event.target.closest('[data-fav-remove]');
    if (add) { const id = Number(add.dataset.favAdd); cart.set(id, (cart.get(id) || 0) + 1); renderCart(); toast('Added to your cart'); }
    if (remove) { favorites = favorites.filter((id) => id !== Number(remove.dataset.favRemove)); localStorage.setItem('foodstall_favorites', JSON.stringify(favorites)); showFavorites(); renderMenu(); }
  });
  $('#scrim').addEventListener('click', closePanels);
  document.querySelectorAll('[data-close]').forEach((button) => button.addEventListener('click', closePanels));
  $('#cart-lines').addEventListener('click', (event) => {
    const button = event.target.closest('[data-change]'); if (!button) return;
    const id = Number(button.dataset.change); const next = (cart.get(id) || 0) + Number(button.dataset.by);
    if (next > 0) cart.set(id, next); else cart.delete(id); renderCart();
  });
  $('#cart-lines').addEventListener('input', (event) => {
    const input = event.target.closest('[data-note]'); if (input) specialNotes.set(Number(input.dataset.note), input.value);
  });
  $('#checkout-open').addEventListener('click', () => {
    if (!cart.size) return; closePanels(); $('#checkout-modal').classList.add('open'); $('#checkout-modal').setAttribute('aria-hidden', 'false');
  });
  $('#fulfillment').addEventListener('change', (event) => {
    const delivery = event.target.value === 'delivery'; $('#address-label').hidden = !delivery; $('#address-label textarea').required = delivery;
  });
  $('#checkout-form').addEventListener('submit', async (event) => {
    event.preventDefault(); const form = new FormData(event.currentTarget); const button = event.currentTarget.querySelector('button[type="submit"]');
    button.disabled = true; $('#checkout-error').textContent = '';
    const order = {customer_name: form.get('customer_name'), phone: form.get('phone'), fulfillment: form.get('fulfillment'), delivery_address: form.get('delivery_address'), payment_method: form.get('payment_method'), coupon_code: form.get('coupon_code'), items: [...cart].map(([menu_item_id, quantity]) => ({menu_item_id, quantity, special_instructions: specialNotes.get(menu_item_id) || ''}))};
    try {
      const response = await fetch(`${api}/orders/`, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken()}, body: JSON.stringify(order)});
      const result = await response.json(); if (!response.ok) throw new Error(result.error || result.detail || 'The order could not be placed. Please try again.');
      const tokens = orderTokens(); tokens.unshift(result.tracking_token); localStorage.setItem('foodstall_order_tokens', JSON.stringify(tokens.slice(0, 20)));
      $('#order-success-greeting').textContent = `Hi, ${order.customer_name}! Thank you for choosing us.`;
      $('#order-success-number').textContent = `Order #${result.order_id}`;
      $('#order-success-items').innerHTML = order.items.map((row) => { const item = menuItems.find((menuItem) => menuItem.id === row.menu_item_id); return `<div><span><b>${row.quantity} ×</b> ${escapeHtml(item?.name || 'Menu item')}</span><strong>${money(Number(item?.price || 0) * row.quantity)}</strong></div>`; }).join('');
      $('#order-success-total').textContent = money(result.total);
      cart.clear(); specialNotes.clear(); renderCart(); event.currentTarget.reset(); closePanels(); openPanel('order-success-modal');
    } catch (error) { $('#checkout-error').textContent = error.message; }
    finally { button.disabled = false; }
  });
  $('#booking-form').addEventListener('submit', async (event) => {
    event.preventDefault(); const button = event.currentTarget.querySelector('button[type="submit"]'); button.disabled = true; $('#booking-error').textContent = '';
    const form = new FormData(event.currentTarget); const payload = Object.fromEntries(form.entries());
    try {
      const response = await fetch(`${api}/bookings/`, {method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrfToken()},body:JSON.stringify(payload)}); const result = await response.json();
      if (!response.ok) throw new Error(result.error || result.detail || 'Booking could not be created.');
      const tokens = bookingTokens(); tokens.unshift(result.booking_token); localStorage.setItem('foodstall_booking_tokens', JSON.stringify(tokens.slice(0, 20)));
      closePanels(); toast(`Booking #${result.booking_id} requested · Table ${result.table}`); event.currentTarget.reset(); $('#table-select').innerHTML = '<option value="">Choose date, time and guests first</option>';
    } catch (error) { $('#booking-error').textContent = error.message; } finally { button.disabled = false; }
  });
  $('#review-form').addEventListener('submit', async (event) => {
    event.preventDefault(); const button = event.currentTarget.querySelector('button[type="submit"]'); button.disabled = true; $('#review-error').textContent = '';
    const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      const response = await fetch(`${api}/reviews/`, {method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrfToken()},body:JSON.stringify(payload)}); const result = await response.json();
      if (!response.ok) throw new Error(result.error || result.detail || 'Review could not be submitted.');
      closePanels(); toast('Thank you! Your review is awaiting approval.'); event.currentTarget.reset();
    } catch (error) { $('#review-error').textContent = error.message; } finally { button.disabled = false; }
  });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closePanels(); });
  loadMenu();
  loadOffers();
  loadReviews();
})();
