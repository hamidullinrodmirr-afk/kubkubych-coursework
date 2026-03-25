const API = {
    baseURL: '/api',

    getToken() {
        return localStorage.getItem('access_token');
    },

    setTokens(access, refresh) {
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
    },

    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    },

    async request(url, options = {}) {
        const headers = { 'Content-Type': 'application/json', ...options.headers };
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        let response = await fetch(this.baseURL + url, { ...options, headers });

        // Если 401 — пробуем обновить токен
        if (response.status === 401 && localStorage.getItem('refresh_token')) {
            const refreshResp = await fetch(this.baseURL + '/auth/refresh/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: localStorage.getItem('refresh_token') }),
            });
            if (refreshResp.ok) {
                const data = await refreshResp.json();
                this.setTokens(data.access, data.refresh || localStorage.getItem('refresh_token'));
                headers['Authorization'] = `Bearer ${data.access}`;
                response = await fetch(this.baseURL + url, { ...options, headers });
            } else {
                this.clearTokens();
                window.location.href = '/login/';
                return null;
            }
        }

        return response;
    },

    async get(url) {
        const resp = await this.request(url);
        return resp ? resp.json() : null;
    },

    async post(url, data) {
        const resp = await this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
        });
        return resp;
    },

    async patch(url, data) {
        const resp = await this.request(url, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
        return resp;
    },

    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    },

    isAuthenticated() {
        return !!this.getToken();
    },

    async getProfile() {
        return this.get('/auth/me/');
    },

    async login(email, password) {
        const resp = await fetch(this.baseURL + '/auth/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        if (resp.ok) {
            const data = await resp.json();
            this.setTokens(data.access, data.refresh);
        }
        return resp;
    },

    async register(data) {
        return fetch(this.baseURL + '/auth/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
    },

    logout() {
        this.clearTokens();
        window.location.href = '/';
    },
};
