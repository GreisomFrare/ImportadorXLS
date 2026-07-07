// ── Auth ERP ──────────────────────────────────────────────────────────────────

function aguardarContextoERP() {
  return new Promise((resolve) => {
    function tentar() {
      const app = window.delphiApp;
      if (!app) return false;
      const userId  = app?.usuario?.id ?? null;
      const empresa = app?.sistema?.empresaselecionada ?? null;
      resolve({ userId, empresa });
      return true;
    }
    if (tentar()) return;
    let t = 0;
    const iv = setInterval(() => {
      t++;
      if (tentar() || t >= 19) {
        clearInterval(iv);
        if (t >= 19) resolve({ userId: null, empresa: null });
      }
    }, 80);
  });
}

async function verificarAcesso() {
  const { userId, empresa } = await aguardarContextoERP();
  if (userId === 'VIASOFT') { ocultarOverlay(); return; }
  try {
    const r = await fetch('/api/oracle/auth/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId, empresa })
    });
    const d = await r.json();
    if (d.acesso) ocultarOverlay();
    else mostrarAcessoNegado();
  } catch {
    mostrarAcessoNegado();
  }
}

function ocultarOverlay() {
  const el = document.getElementById('loading-overlay');
  if (el) el.remove();
}

function mostrarAcessoNegado() {
  const el = document.getElementById('loading-overlay');
  if (!el) return;
  el.innerHTML = `
    <div class="text-center">
      <i class="bi bi-shield-lock text-danger" style="font-size:3rem;"></i>
      <p class="mt-3 fw-semibold">Acesso não autorizado</p>
      <p class="text-muted small">Seu usuário não possui permissão para acessar este módulo.</p>
    </div>`;
}

// ── Tema ──────────────────────────────────────────────────────────────────────

function alternarTema() {
  const atual = document.documentElement.getAttribute('data-bs-theme');
  const novo = atual === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-bs-theme', novo);
  localStorage.setItem('viasoft-theme', novo);
  document.getElementById('btn-tema-icon').className =
    novo === 'dark' ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill';
}

// ── Toast ─────────────────────────────────────────────────────────────────────

function toast(msg, tipo = 'success') {
  const container = document.getElementById('toast-container');
  const id = 'toast-' + Date.now();
  const cor = tipo === 'success' ? 'bg-success' : tipo === 'danger' ? 'bg-danger' : 'bg-warning text-dark';
  container.insertAdjacentHTML('beforeend', `
    <div id="${id}" class="toast align-items-center text-white ${cor} border-0 show" role="alert">
      <div class="d-flex">
        <div class="toast-body">${msg}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto"
                data-bs-dismiss="toast"></button>
      </div>
    </div>`);
  setTimeout(() => document.getElementById(id)?.remove(), 4000);
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function indicePraLetra(idx) {
  let result = '';
  while (true) {
    result = String.fromCharCode(65 + idx % 26) + result;
    idx = Math.floor(idx / 26) - 1;
    if (idx < 0) break;
  }
  return result;
}

function formatarData(iso) {
  if (!iso) return '-';
  return new Date(iso).toLocaleString('pt-BR');
}
