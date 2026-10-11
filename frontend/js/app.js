// 🟦 Grupo 1 — lógica del frontend

/* =========================================================
   DATOS DE PRUEBA
   Mientras el backend (Django) no esté conectado.
   TODO(API): reemplazar por fetch() — ver sección "API" abajo.
   ========================================================= */
const MOCK_USER = { nombre: 'Salomón Chavarro', rol: 'Administrador' };

const MOCK_PRODUCTS = [
    { id: 1,  codigo: 'PRD-001', nombre: 'Cable THHN 12 AWG',       categoria: 'Cables',        stock: 120, stockMinimo: 30 },
    { id: 2,  codigo: 'PRD-002', nombre: 'Breaker 20A',              categoria: 'Protecciones',  stock: 8,   stockMinimo: 10 },
    { id: 3,  codigo: 'PRD-003', nombre: 'Tomacorriente doble',      categoria: 'Accesorios',    stock: 45,  stockMinimo: 15 },
    { id: 4,  codigo: 'PRD-004', nombre: 'Interruptor sencillo',     categoria: 'Accesorios',    stock: 0,   stockMinimo: 10 },
    { id: 5,  codigo: 'PRD-005', nombre: 'Tubo conduit 3/4"',        categoria: 'Tuberías',      stock: 60,  stockMinimo: 20 },
    { id: 6,  codigo: 'PRD-006', nombre: 'Caja de paso 10x10',       categoria: 'Accesorios',    stock: 5,   stockMinimo: 12 },
    { id: 7,  codigo: 'PRD-007', nombre: 'Cinta aislante',           categoria: 'Consumibles',   stock: 90,  stockMinimo: 25 },
    { id: 8,  codigo: 'PRD-008', nombre: 'Lámpara LED 18W',          categoria: 'Iluminación',   stock: 34,  stockMinimo: 10 },
    { id: 9,  codigo: 'PRD-009', nombre: 'Fusible 15A',              categoria: 'Protecciones',  stock: 0,   stockMinimo: 8  },
    { id: 10, codigo: 'PRD-010', nombre: 'Canaleta 40x25',           categoria: 'Tuberías',      stock: 26,  stockMinimo: 10 },
    { id: 11, codigo: 'PRD-011', nombre: 'Terminal de ojo 10 AWG',   categoria: 'Consumibles',   stock: 4,   stockMinimo: 20 },
    { id: 12, codigo: 'PRD-012', nombre: 'Reflector LED 50W',        categoria: 'Iluminación',   stock: 18,  stockMinimo: 5  }
];

// Últimos 7 días: [etiqueta, entradas, salidas]
const MOCK_MOVEMENTS_WEEK = [
    ['Lun', 12, 8], ['Mar', 15, 10], ['Mié', 9, 14], ['Jue', 18, 11],
    ['Vie', 14, 16], ['Sáb', 6, 5],  ['Dom', 10, 7]
];

/* =========================================================
   API (Django REST) — puntos de integración futura
   No hay contrato de endpoints acordado todavía.
   Cuando el backend lo defina, implementar aquí con fetch().
   ========================================================= */
const api = {
    // TODO(API): GET productos
    async getProducts()   { return MOCK_PRODUCTS; },
    // TODO(API): GET movimientos (últimos 7 días)
    async getWeekMovements() { return MOCK_MOVEMENTS_WEEK; },
    // TODO(API): autenticación / usuario actual
    async getCurrentUser() { return getSession() || MOCK_USER; }
};

/* =========================================================
   SESIÓN (la crea login.js al iniciar sesión)
   ========================================================= */
const SESSION_KEY = 'inventario.session';
const LOGIN_URL = 'login.html';

function getSession() {
    try { return JSON.parse(sessionStorage.getItem(SESSION_KEY)); } catch (e) { return null; }
}

function logout() {
    // TODO(API): avisar al backend para cerrar la sesión (cerrarSesion)
    try { sessionStorage.removeItem(SESSION_KEY); } catch (e) { /* sin almacenamiento */ }
    window.location.href = LOGIN_URL;
}

/* =========================================================
   UTILIDADES
   ========================================================= */
const SVG_NS = 'http://www.w3.org/2000/svg';

function getStockStatus(product) {
    if (product.stock === 0) return 'agotado';
    if (product.stock <= product.stockMinimo) return 'bajo';
    return 'disponible';
}

const STATUS_BADGE = {
    disponible: { cls: 'badge--ok',  text: 'Disponible' },
    bajo:       { cls: 'badge--low', text: 'Stock bajo' },
    agotado:    { cls: 'badge--out', text: 'Agotado' }
};

const pad2 = n => String(n).padStart(2, '0');

function el(tag, attrs = {}, text) {
    const node = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
    if (text !== undefined) node.textContent = text;
    return node;
}

/* =========================================================
   NAVEGACIÓN ENTRE VISTAS (por hash: #dashboard, #productos…)
   ========================================================= */
const VIEW_TITLES = {
    dashboard: 'Dashboard', productos: 'Productos', categorias: 'Categorías',
    movimientos: 'Movimientos', usuarios: 'Usuarios', reportes: 'Reportes',
    configuracion: 'Configuración'
};

function showView(name) {
    if (!VIEW_TITLES[name]) name = 'dashboard';
    document.querySelectorAll('.view').forEach(v =>
        v.classList.toggle('is-active', v.id === `view-${name}`));
    document.querySelectorAll('.nav__link').forEach(link => {
        const active = link.dataset.view === name;
        link.classList.toggle('is-active', active);
        if (active) link.setAttribute('aria-current', 'page');
        else link.removeAttribute('aria-current');
    });
    document.getElementById('breadcrumbCurrent').textContent = VIEW_TITLES[name];
    closeMenu();
}

function initNavigation() {
    const route = () => showView(location.hash.replace('#', ''));
    window.addEventListener('hashchange', route);
    route();
}

/* Menú lateral en móvil */
function setMenu(open) {
    const app = document.getElementById('app');
    app.classList.toggle('menu-open', open);
    document.getElementById('menuToggle').setAttribute('aria-expanded', String(open));
}
function closeMenu() { setMenu(false); }

function initMenuToggle() {
    document.getElementById('menuToggle').addEventListener('click', () =>
        setMenu(!document.getElementById('app').classList.contains('menu-open')));
    document.getElementById('scrim').addEventListener('click', closeMenu);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });
}

/* =========================================================
   DASHBOARD
   ========================================================= */
const ICONS = {
    box:   '<svg viewBox="0 0 24 24"><path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5M12 13v8"/></svg>',
    check: '<svg viewBox="0 0 24 24"><path d="m5 12 5 5 9-10"/></svg>',
    warn:  '<svg viewBox="0 0 24 24"><path d="M12 3 2 20h20z"/><path d="M12 10v4m0 3h.01"/></svg>',
    out:   '<svg viewBox="0 0 24 24"><path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m9 10 6 6m0-6-6 6"/></svg>'
};

function renderSummaryCards(products) {
    const counts = { disponible: 0, bajo: 0, agotado: 0 };
    products.forEach(p => counts[getStockStatus(p)]++);

    const cards = [
        { title: 'Total de productos',      value: products.length,    hint: 'Productos en el inventario', tone: 'primary', icon: ICONS.box },
        { title: 'Productos disponibles',   value: counts.disponible,  hint: 'Con existencias suficientes', tone: 'ok',      icon: ICONS.check },
        { title: 'Stock bajo',              value: counts.bajo,        hint: 'Requieren reposición',        tone: 'warn',    icon: ICONS.warn },
        { title: 'Productos agotados',      value: counts.agotado,     hint: 'Sin unidades disponibles',    tone: 'danger',  icon: ICONS.out }
    ];

    const container = document.getElementById('summaryCards');
    container.replaceChildren(...cards.map(c => {
        const card = el('article', { class: 'card' });
        const top = el('div', { class: 'card__top' });
        top.append(el('span', {}, c.title));
        const icon = el('span', { class: `card__icon card__icon--${c.tone}`, 'aria-hidden': 'true' });
        icon.innerHTML = c.icon; // íconos fijos definidos arriba (no vienen de datos externos)
        top.append(icon);
        card.append(top,
            el('p', { class: 'card__value' }, pad2(c.value)),
            el('p', { class: 'card__hint' }, c.hint));
        return card;
    }));
}

function renderAttentionTable(products) {
    const tbody = document.getElementById('attentionRows');
    const rows = products
        .filter(p => getStockStatus(p) !== 'disponible')
        .sort((a, b) => a.stock - b.stock);

    if (!rows.length) {
        const tr = el('tr'); const td = el('td', { class: 'empty', colspan: '6' }, 'Todo el inventario está en niveles normales.');
        tr.append(td); tbody.replaceChildren(tr); return;
    }

    tbody.replaceChildren(...rows.map(p => {
        const status = STATUS_BADGE[getStockStatus(p)];
        const tr = el('tr');
        const badgeCell = el('td'); badgeCell.append(el('span', { class: `badge ${status.cls}` }, status.text));
        tr.append(
            el('td', {}, p.codigo), el('td', {}, p.nombre), el('td', {}, p.categoria),
            el('td', { class: 'num' }, String(p.stock)),
            el('td', { class: 'num' }, String(p.stockMinimo)),
            badgeCell);
        return tr;
    }));
}

/* Gráfico de barras agrupadas en SVG (sin librerías) */
function renderMovementsChart(week) {
    const W = 720, H = 260, m = { top: 12, right: 12, bottom: 28, left: 34 };
    const innerW = W - m.left - m.right, innerH = H - m.top - m.bottom;
    const max = Math.max(...week.flatMap(([, i, o]) => [i, o]));
    const top = Math.ceil(max / 5) * 5 || 5;
    const y = v => m.top + innerH - (v / top) * innerH;

    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('aria-hidden', 'true');
    const add = (tag, attrs, text) => {
        const n = document.createElementNS(SVG_NS, tag);
        Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
        if (text !== undefined) n.textContent = text;
        svg.append(n); return n;
    };

    for (let t = 0; t <= top; t += top / 4) {
        add('line', { x1: m.left, x2: W - m.right, y1: y(t), y2: y(t), stroke: '#e6e8ec', 'stroke-width': 1 });
        add('text', { x: m.left - 8, y: y(t) + 4, 'text-anchor': 'end' }, Math.round(t));
    }

    const group = innerW / week.length, bar = Math.min(22, group / 3);
    week.forEach(([label, inn, out], i) => {
        const cx = m.left + group * i + group / 2;
        add('rect', { x: cx - bar - 2, y: y(inn), width: bar, height: m.top + innerH - y(inn), rx: 4, fill: '#1666e0' });
        add('rect', { x: cx + 2,       y: y(out), width: bar, height: m.top + innerH - y(out), rx: 4, fill: '#f59e0b' });
        add('text', { x: cx, y: H - 8, 'text-anchor': 'middle' }, label);
    });

    const chart = document.getElementById('movementsChart');
    chart.replaceChildren(svg);
    const totalIn = week.reduce((s, d) => s + d[1], 0), totalOut = week.reduce((s, d) => s + d[2], 0);
    chart.setAttribute('aria-label',
        `Últimos 7 días: ${totalIn} unidades de entrada y ${totalOut} de salida.`);
}

function renderToday() {
    const text = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date());
    document.getElementById('todayChip').textContent = text;
}

function renderUser(user) {
    document.getElementById('userName').textContent = user.nombre;
    document.getElementById('userRole').textContent = user.rol;
    document.getElementById('welcomeName').textContent = user.nombre.split(' ')[0];
    document.getElementById('userInitials').textContent =
        user.nombre.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
}

/* =========================================================
   ARRANQUE
   ========================================================= */
async function init() {
    if (!getSession()) { window.location.replace(LOGIN_URL); return; } // sin sesión → login
    document.getElementById('btnLogout').addEventListener('click', logout);
    initNavigation();
    initMenuToggle();
    renderToday();

    const [user, products, week] = await Promise.all([
        api.getCurrentUser(), api.getProducts(), api.getWeekMovements()
    ]);

    renderUser(user);
    document.getElementById('navProductCount').textContent = products.length;
    renderSummaryCards(products);
    renderAttentionTable(products);
    renderMovementsChart(week);

    // TODO: abrir formulario/modal de "Registrar movimiento" (vista Movimientos)
    document.getElementById('btnRegisterMovement').addEventListener('click', () => { location.hash = '#movimientos'; });
}

document.addEventListener('DOMContentLoaded', init);
