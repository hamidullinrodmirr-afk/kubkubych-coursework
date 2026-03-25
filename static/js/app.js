document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();

    // Burger menu
    const burger = document.querySelector('.header__burger');
    const nav = document.querySelector('.header__nav');
    if (burger && nav) {
        burger.addEventListener('click', () => nav.classList.toggle('open'));
    }
});

async function updateAuthUI() {
    const actions = document.querySelector('.header__actions');
    if (!actions) return;

    if (API.isAuthenticated()) {
        try {
            const profile = await API.getProfile();
            if (profile) {
                actions.innerHTML = `
                    <a href="/profile/" class="header__user">${profile.last_name} ${profile.first_name}</a>
                    <button class="btn btn--sm btn--outline" style="border-color: #fff; color: #fff;" onclick="API.logout()">Выход</button>
                `;
                return;
            }
        } catch (e) {}
    }

    actions.innerHTML = `
        <a href="/login/" class="btn btn--sm btn--green">Войти</a>
    `;
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
    div.textContent = message;
    container.prepend(div);
    setTimeout(() => div.remove(), 5000);
}
