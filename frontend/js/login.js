// 🟦 Grupo 1 — lógica de la pantalla de login
// Flujo (diagrama del PDF): mostrar formulario → validar campos y credenciales
//   → si falla: mostrar error y permitir corregir → si es válido: abrir panel principal.

const SESSION_KEY = 'inventario.session';
const DASHBOARD_URL = 'index.html#dashboard';

/* =========================================================
   API (Django) — punto de integración futura
   No hay contrato de endpoints acordado todavía.
   ========================================================= */
const authApi = {
    // TODO(API): reemplazar por fetch() al endpoint de autenticación de Django.
    // Debe devolver { nombre, rol } o lanzar un Error con el mensaje a mostrar.
    // Mientras tanto (SIN credenciales reales en el código) acepta cualquier dato válido.
    async login({ usuario }) {
        await new Promise(r => setTimeout(r, 400)); // simula la espera del servidor
        const nombre = usuario.includes('@') ? usuario.split('@')[0] : usuario;
        return { nombre: nombre.charAt(0).toUpperCase() + nombre.slice(1), rol: 'Administrador' };
    }
};

/* =========================================================
   Sesión
   ========================================================= */
function saveSession(user) {
    try { sessionStorage.setItem(SESSION_KEY, JSON.stringify(user)); } catch (e) { /* almacenamiento no disponible */ }
}
function hasSession() {
    try { return !!sessionStorage.getItem(SESSION_KEY); } catch (e) { return false; }
}

/* =========================================================
   Formulario
   ========================================================= */
const form = document.getElementById('loginForm');
const userInput = document.getElementById('loginUser');
const passInput = document.getElementById('loginPassword');
const submitBtn = document.getElementById('loginSubmit');
const formError = document.getElementById('loginError');

function setFieldError(input, message) {
    const errorEl = document.getElementById(`${input.id}Error`);
    errorEl.textContent = message || '';
    errorEl.hidden = !message;
    input.setAttribute('aria-invalid', message ? 'true' : 'false');
}

function showFormError(message) {
    formError.textContent = message || '';
    formError.hidden = !message;
}

function validate() {
    const usuario = userInput.value.trim();
    const password = passInput.value;
    let valid = true;

    if (!usuario) { setFieldError(userInput, 'Ingresa tu usuario o correo.'); valid = false; }
    else if (usuario.includes('@') && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(usuario)) {
        setFieldError(userInput, 'El correo no tiene un formato válido.'); valid = false;
    } else setFieldError(userInput, '');

    if (!password) { setFieldError(passInput, 'Ingresa tu contraseña.'); valid = false; }
    else setFieldError(passInput, '');

    if (!valid) {
        showFormError('Completa los campos para continuar.');
        (userInput.getAttribute('aria-invalid') === 'true' ? userInput : passInput).focus();
    } else showFormError('');

    return valid ? { usuario, password } : null;
}

form.addEventListener('submit', async event => {
    event.preventDefault();
    const credentials = validate();
    if (!credentials) return; // "No": mostrar error y permitir corregir

    submitBtn.disabled = true;
    submitBtn.textContent = 'Ingresando...';
    try {
        const user = await authApi.login(credentials);
        saveSession(user);
        window.location.href = DASHBOARD_URL; // "Sí": abrir panel principal
    } catch (error) {
        showFormError(error.message || 'Usuario o contraseña incorrectos.');
        passInput.value = '';
        passInput.focus();
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Ingresar';
    }
});

[userInput, passInput].forEach(input =>
    input.addEventListener('input', () => { setFieldError(input, ''); showFormError(''); }));

const toggleBtn = document.getElementById('togglePassword');
toggleBtn.addEventListener('click', () => {
    const show = passInput.type === 'password';
    passInput.type = show ? 'text' : 'password';
    toggleBtn.textContent = show ? 'Ocultar' : 'Mostrar';
    toggleBtn.setAttribute('aria-label', show ? 'Ocultar contraseña' : 'Mostrar contraseña');
    toggleBtn.setAttribute('aria-pressed', String(show));
});

// Si ya hay sesión iniciada, ir directo al panel
if (hasSession()) window.location.replace(DASHBOARD_URL);
