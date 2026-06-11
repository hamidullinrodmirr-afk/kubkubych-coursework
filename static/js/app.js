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
