// Por padrao usa o mesmo host de onde a pagina foi carregada, so trocando a
// porta para a da API. Um parametro ?api=<url> na propria pagina sobrescreve
// esse calculo automatico (necessario quando cada servico esta atras de um
// tunel com dominio proprio, ex: cloudflared).
const API_BASE = new URLSearchParams(window.location.search).get("api") || `http://${window.location.hostname}:8000`;

const estadoAuth = {
  token: localStorage.getItem("cf_admin_token") || null,
  usuario: JSON.parse(localStorage.getItem("cf_admin_usuario") || "null"),
};

async function api(path, { method = "GET", body = null } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (estadoAuth.token) headers["Authorization"] = `Bearer ${estadoAuth.token}`;

  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try { data = await resp.json(); } catch (e) { /* sem corpo */ }

  if (!resp.ok) {
    const mensagem = (data && data.detail) ? data.detail : `Erro ${resp.status}`;
    const erro = new Error(mensagem);
    erro.status = resp.status;
    throw erro;
  }
  return data;
}

function formatarMoeda(valor) {
  return `R$ ${Number(valor).toFixed(2).replace(".", ",")}`;
}

function formatarKwh(valor) {
  return `${Number(valor).toFixed(1)} kWh`;
}

document.getElementById("form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  const erroEl = document.getElementById("login-erro");
  erroEl.textContent = "";
  try {
    const dados = await api("/api/auth/login", {
      method: "POST",
      body: {
        email: document.getElementById("login-email").value,
        senha: document.getElementById("login-senha").value,
      },
    });
    if (dados.usuario.role !== "admin") {
      erroEl.textContent = "Acesso restrito a administradores.";
      return;
    }
    estadoAuth.token = dados.access_token;
    estadoAuth.usuario = dados.usuario;
    localStorage.setItem("cf_admin_token", estadoAuth.token);
    localStorage.setItem("cf_admin_usuario", JSON.stringify(estadoAuth.usuario));
    entrarNoPainel();
  } catch (err) {
    erroEl.textContent = err.message;
  }
});

document.getElementById("btn-sair").addEventListener("click", () => {
  estadoAuth.token = null;
  estadoAuth.usuario = null;
  localStorage.removeItem("cf_admin_token");
  localStorage.removeItem("cf_admin_usuario");
  document.getElementById("painel").classList.add("hidden");
  document.getElementById("tela-login").classList.remove("hidden");
});

document.querySelectorAll(".nav-item").forEach((btn) => {
  btn.addEventListener("click", () => mostrarSecao(btn.dataset.secao));
});

function mostrarSecao(secao) {
  document.querySelectorAll(".secao").forEach((el) => el.classList.add("hidden"));
  document.getElementById(`secao-${secao}`).classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach((btn) => btn.classList.toggle("active", btn.dataset.secao === secao));

  if (secao === "visao-geral") carregarVisaoGeral();
  if (secao === "consumo") carregarConsumo();
  if (secao === "sustentabilidade") carregarSustentabilidade();
  if (secao === "ranking") carregarRanking();
}

function entrarNoPainel() {
  document.getElementById("tela-login").classList.add("hidden");
  document.getElementById("painel").classList.remove("hidden");
  mostrarSecao("visao-geral");
}

(function initAdmin() {
  if (estadoAuth.token && estadoAuth.usuario && estadoAuth.usuario.role === "admin") {
    entrarNoPainel();
  }
})();
