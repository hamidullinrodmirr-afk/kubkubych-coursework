document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();

    const burger = document.querySelector('.header__burger');
    const nav = document.querySelector('.header__nav');
    if (burger && nav) {
        burger.addEventListener('click', () => nav.classList.toggle('open'));
    }

    initMotion();
    initCounters();
});

const prefersReducedMotion = () =>
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

let revealObserver = null;

function initMotion() {
    if (prefersReducedMotion() || !('IntersectionObserver' in window)) return;
    document.body.classList.add('anim');
    revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                e.target.classList.add('in');
                revealObserver.unobserve(e.target);
            }
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));
}

function revealScan(scope) {
    if (!revealObserver) return;
    (scope || document).querySelectorAll('.reveal:not(.in)').forEach(el => revealObserver.observe(el));
}

function countUp(el) {
    const target = parseFloat(el.dataset.count);
    const dec = parseInt(el.dataset.dec || '0', 10);
    const dur = 1300, t0 = performance.now();
    function tick(now) {
        const p = Math.min((now - t0) / dur, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        const val = target * eased;
        el.textContent = dec ? val.toFixed(dec) : Math.round(val).toLocaleString('ru-RU');
        if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

function initCounters() {
    const nums = document.querySelectorAll('[data-count]');
    if (!nums.length) return;
    if (prefersReducedMotion() || !('IntersectionObserver' in window)) {
        nums.forEach(el => {
            const dec = parseInt(el.dataset.dec || '0', 10);
            const t = parseFloat(el.dataset.count);
            el.textContent = dec ? t.toFixed(dec) : t.toLocaleString('ru-RU');
        });
        return;
    }
    const io = new IntersectionObserver((entries) => {
        entries.forEach(e => { if (e.isIntersecting) { countUp(e.target); io.unobserve(e.target); } });
    }, { threshold: 0.5 });
    nums.forEach(el => io.observe(el));
}

async function updateAuthUI() {
    const actions = document.querySelector('.header__actions');
    if (!actions) return;

    if (API.isAuthenticated()) {
        try {
            const profile = await API.getProfile();
            if (profile) {
                actions.innerHTML = `
                    <a href="/profile/" class="header__user">${esc(profile.last_name)} ${esc(profile.first_name)}</a>
                    <button class="btn btn--sm btn--outline" onclick="API.logout()">Выход</button>
                `;
                return;
            }
        } catch (e) {}
    }

    actions.innerHTML = `
        <a href="/login/" class="btn btn--sm btn--green">Войти</a>
    `;
}

function esc(value) {
    if (value === null || value === undefined) return '';
    return String(value).replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[ch]);
}

function renderStars(rating) {
    const full = Math.floor(rating);
    const half = rating - full >= 0.5 ? 1 : 0;
    const empty = 5 - full - half;
    return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(empty);
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

function showAlert(container, message, type = 'error') {
    const div = document.createElement('div');
    div.className = `alert alert--${type}`;
    div.innerHTML = `<span>${esc(message)}</span><button class="alert__close" onclick="this.parentElement.remove()">&times;</button>`;
    container.prepend(div);
    setTimeout(() => { if (div.parentElement) div.remove(); }, 7000);
}

function formatPrice(value) {
    const number = Number(value);
    if (Number.isNaN(number)) return value;
    return number.toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + ' ₽';
}

async function readError(response, fallback) {
    try {
        const data = await response.json();
        if (typeof data === 'string') return data;
        const first = Object.values(data)[0];
        return Array.isArray(first) ? first[0] : (first || fallback);
    } catch (e) {
        return fallback;
    }
}

// Добавляет набор в корзину; при отсутствии входа уводит на страницу логина.
async function addToCart(productId, quantity = 1) {
    if (!API.isAuthenticated()) {
        window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
        return;
    }
    const response = await API.post('/cart/items/', { product: productId, quantity });
    if (response && response.ok) {
        showAlert(document.body, 'Набор добавлен в корзину', 'success');
    } else {
        showAlert(document.body, await readError(response, 'Не удалось добавить набор'), 'error');
    }
}

// Единый HTML карточки набора для главной, каталога и избранного.
function productCard(p) {
    const priceBlock = p.discount_percent > 0
        ? `<b>${formatPrice(p.final_price)}</b> <s class="card__old">${formatPrice(p.price)}</s>`
        : `<b>${formatPrice(p.final_price)}</b>`;
    const rating = p.reviews_count
        ? `<span class="card__rating">★ ${Number(p.average_rating).toFixed(1)}</span> <span class="card__reviews">${p.reviews_count}</span>`
        : '<span class="card__reviews">Нет отзывов</span>';
    const stock = p.in_stock ? `В наличии: ${p.stock}` : 'Нет в наличии';
    const favClass = p.is_favorite ? 'is-active' : '';
    const favText = p.is_favorite ? 'В избранном' : 'В избранное';
    return `<article class="card">
        ${p.discount_percent > 0 ? `<span class="card__badge">−${p.discount_percent}%</span>` : ''}
        <a href="/products/${esc(p.slug)}/"><img class="card__image" src="${esc(p.image_url)}" alt="${esc(p.name)}" loading="lazy"></a>
        <div class="card__body">
            <span class="chip">${esc(p.category_detail.name)}</span>
            <a class="card__title" href="/products/${esc(p.slug)}/">${esc(p.name)}</a>
            <p class="card__subtitle">${esc(p.article)} · ${p.pieces} деталей · ${p.age_from}–${p.age_to} лет</p>
            <div class="card__meta">${rating}<span class="card__stock">${stock}</span></div>
            <div class="card__footer">
                <div class="card__price">${priceBlock}</div>
                <div class="card__actions">
                    <button class="icon-btn fav-btn ${favClass}" onclick="toggleFavorite(${p.id}, this)">${favText}</button>
                    <button class="btn btn--sm btn--green" onclick="addToCart(${p.id})" ${p.in_stock ? '' : 'disabled'}>В корзину</button>
                </div>
            </div>
        </div>
    </article>`;
}

// Переключает избранное для набора и обновляет состояние кнопки.
async function toggleFavorite(productId, button) {
    if (!API.isAuthenticated()) {
        window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
        return;
    }
    const active = button.classList.contains('is-active');
    const response = active
        ? await API.delete(`/products/${productId}/favorite/`)
        : await API.post(`/products/${productId}/favorite/`);
    if (response && response.ok) {
        button.classList.toggle('is-active', !active);
        button.textContent = !active ? 'В избранном' : 'В избранное';
    } else {
        showAlert(document.body, 'Войдите, чтобы пользоваться избранным', 'error');
    }
}
