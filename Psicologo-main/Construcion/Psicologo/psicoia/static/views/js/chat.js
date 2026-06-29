/**
 * chat.js — Empathy AI
 * FIX CSRF: se lee el token desde la cookie 'csrftoken' (método robusto)
 * en vez de depender del campo hidden del formulario.
 */

// ── CSRF desde cookie (funciona siempre) ─────────────────────────────
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}
const csrfToken = getCookie('csrftoken');

const chatMessages  = document.getElementById('chat-messages');
const chatForm      = document.getElementById('chat-form');
const inputField    = document.getElementById('id_contenido');
const sendBtn       = document.getElementById('send-btn');
const loadingBubble = document.getElementById('loading-bubble');
const crisisBanner  = document.getElementById('crisis-banner');
const crisisList    = document.getElementById('crisis-resources');

if (inputField) inputField.classList.add('chat-input');

// ── Scroll al fondo ───────────────────────────────────────────────────
function scrollBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}
scrollBottom();

// ── Agregar burbuja ───────────────────────────────────────────────────
function agregarMensaje(rol, texto) {
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const div = document.createElement('div');
  div.className = `msg msg--${rol}`;
  div.innerHTML = `
    <div class="msg__inner">
      <div class="msg__bubble">${texto}</div>
      <span class="msg__time">${now}</span>
    </div>`;
  chatMessages.insertBefore(div, loadingBubble);
  scrollBottom();
}

// ── Crisis ────────────────────────────────────────────────────────────
function mostrarCrisis(recursos) {
  crisisList.innerHTML = '';
  recursos.lineas.forEach(l => {
    const li = document.createElement('li');
    li.textContent = `${l.pais}: ${l.telefono}`;
    crisisList.appendChild(li);
  });
  crisisBanner.style.display = 'block';
}

// ── Envío de mensaje ──────────────────────────────────────────────────
chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const texto = inputField.value.trim();
  if (!texto) return;

  agregarMensaje('user', texto);
  inputField.value = '';
  inputField.disabled = true;
  sendBtn.disabled = true;
  loadingBubble.style.display = 'flex';
  scrollBottom();

  try {
    const res = await fetch(window.URLS.procesarMensaje, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken,
      },
      body: new URLSearchParams({ contenido: texto }),
    });
    const data = await res.json();
    loadingBubble.style.display = 'none';

    if (data.error) {
      agregarMensaje('assistant', 'Lo siento, hubo un problema. Intenta de nuevo.');
    } else {
      agregarMensaje('assistant', data.respuesta);
      if (data.protocolo_crisis && data.recursos_ayuda) {
        mostrarCrisis(data.recursos_ayuda);
      }
    }
  } catch {
    loadingBubble.style.display = 'none';
    agregarMensaje('assistant', 'Error de conexión. Verifica tu internet e intenta de nuevo.');
  } finally {
    inputField.disabled = false;
    sendBtn.disabled = false;
    inputField.focus();
  }
});

// Enter para enviar
inputField.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event('submit'));
  }
});

// ── Menú de perfil ────────────────────────────────────────────────────
const profileToggle = document.getElementById('profile-toggle');
const profileMenu   = document.getElementById('profile-menu');
if (profileToggle && profileMenu) {
  profileToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    profileMenu.classList.toggle('open');
  });
  document.addEventListener('click', () => profileMenu.classList.remove('open'));
}

// ── Cámara ────────────────────────────────────────────────────────────
const video        = document.getElementById('video');
const canvas       = document.getElementById('canvas');
const cameraStatus = document.getElementById('camera-status');

async function iniciarCamara() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    cameraStatus.textContent = '🟢 Análisis activo';
    setInterval(capturarFrame, 8000);
  } catch {
    cameraStatus.textContent = '⚠️ Sin cámara';
  }
}

function capturarFrame() {
  if (!video.videoWidth) return;
  canvas.width  = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  const frame = canvas.toDataURL('image/jpeg', 0.7);

  fetch(window.URLS.analizarFacial, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({ frame }),
  })
  .then(r => r.json())
  .then(d => {
    if (d.rostro_detectado) cameraStatus.textContent = `🟢 ${d.emocion}`;
  })
  .catch(() => {});
}

iniciarCamara();

// ── DASS Progress ─────────────────────────────────────────────────────
const dassBar      = document.getElementById('dass-progress-bar');
const dassFill     = document.getElementById('dass-fill');
const dassCurrent  = document.getElementById('dass-current');
const diagBanner   = document.getElementById('diag-banner');
const headerSub    = document.getElementById('header-subtitle');

function actualizarDASS(itemActual, total) {
  if (!itemActual) return;
  dassBar.style.display = 'flex';
  dassCurrent.textContent = itemActual;
  const pct = Math.round(((itemActual - 1) / total) * 100);
  dassFill.style.width = pct + '%';
  headerSub.textContent = `Evaluación DASS-21 • Pregunta ${itemActual}/${total}`;
}

function mostrarDiagnostico(data) {
  dassBar.style.display  = 'none';
  diagBanner.style.display = 'block';
  headerSub.textContent  = 'Evaluación completada ✅';
}

// ── Sobreescribir el handler de submit para incluir DASS ─────────────
const originalSubmit = chatForm.onsubmit;
chatForm.removeEventListener('submit', chatForm._submitHandler);

chatForm._submitHandler = async (e) => {
  e.preventDefault();
  const texto = inputField.value.trim();
  if (!texto) return;

  agregarMensaje('user', texto);
  inputField.value = '';
  inputField.disabled = true;
  sendBtn.disabled = true;
  loadingBubble.style.display = 'flex';
  scrollBottom();

  try {
    const res = await fetch(window.URLS.procesarMensaje, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken,
      },
      body: new URLSearchParams({ contenido: texto }),
    });
    const data = await res.json();
    loadingBubble.style.display = 'none';

    if (data.error) {
      agregarMensaje('assistant', 'Lo siento, hubo un problema. Intenta de nuevo.');
    } else {
      agregarMensaje('assistant', data.respuesta);
      if (data.item_dass)            actualizarDASS(data.item_dass, data.total_dass);
      if (data.diagnostico_calculado) mostrarDiagnostico(data.diagnostico);
      if (data.protocolo_crisis && data.recursos_ayuda) mostrarCrisis(data.recursos_ayuda);
    }
  } catch {
    loadingBubble.style.display = 'none';
    agregarMensaje('assistant', 'Error de conexión. Verifica tu internet e intenta de nuevo.');
  } finally {
    inputField.disabled = false;
    sendBtn.disabled = false;
    inputField.focus();
  }
};

chatForm.addEventListener('submit', chatForm._submitHandler);

// ── Nueva sesión ──────────────────────────────────────────────────────
const nuevaSesionBanner   = document.getElementById('nueva-sesion-banner');
const btnConfirmarNueva   = document.getElementById('btn-confirmar-nueva');
const btnCancelarNueva    = document.getElementById('btn-cancelar-nueva');

// Mostrar banner cuando el bot detecta intención de nueva sesión
function mostrarBannerNuevaSesion() {
  if (nuevaSesionBanner) nuevaSesionBanner.style.display = 'block';
}

// Confirmar: cerrar sesión actual y recargar (el chat_view crea sesión nueva)
if (btnConfirmarNueva) {
  btnConfirmarNueva.addEventListener('click', async () => {
    btnConfirmarNueva.disabled = true;
    btnConfirmarNueva.textContent = 'Cerrando…';
    try {
      await fetch(window.URLS.nuevaSesion, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
      });
      window.location.href = window.URLS.diagnostico.replace('diagnostico/', 'chat/');
    } catch {
      window.location.reload();
    }
  });
}

// Cancelar: ocultar banner
if (btnCancelarNueva) {
  btnCancelarNueva.addEventListener('click', () => {
    if (nuevaSesionBanner) nuevaSesionBanner.style.display = 'none';
  });
}

// Interceptar la respuesta del servidor para detectar solicitud de nueva sesión
// (se engancha en el handler principal que ya existe)
const _origHandler = chatForm._submitHandler;
chatForm.removeEventListener('submit', chatForm._submitHandler);
chatForm._submitHandler2 = async (e) => {
  e.preventDefault();
  const texto = inputField.value.trim();
  if (!texto) return;

  agregarMensaje('user', texto);
  inputField.value = '';
  inputField.disabled = true;
  sendBtn.disabled = true;
  loadingBubble.style.display = 'flex';
  scrollBottom();

  try {
    const res = await fetch(window.URLS.procesarMensaje, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken },
      body: new URLSearchParams({ contenido: texto }),
    });
    const data = await res.json();
    loadingBubble.style.display = 'none';

    if (data.error) {
      agregarMensaje('assistant', 'Lo siento, hubo un problema. Intenta de nuevo.');
    } else {
      agregarMensaje('assistant', data.respuesta);
      if (data.solicitar_nueva_sesion)    mostrarBannerNuevaSesion();
      if (data.item_dass)                 actualizarDASS(data.item_dass, data.total_dass);
      if (data.diagnostico_calculado)     mostrarDiagnostico(data.diagnostico);
      if (data.protocolo_crisis && data.recursos_ayuda) mostrarCrisis(data.recursos_ayuda);
    }
  } catch {
    loadingBubble.style.display = 'none';
    agregarMensaje('assistant', 'Error de conexión. Verifica tu internet e intenta de nuevo.');
  } finally {
    inputField.disabled = false;
    sendBtn.disabled = false;
    inputField.focus();
  }
};
chatForm.addEventListener('submit', chatForm._submitHandler2);
