// Por padrao usa o mesmo host de onde a pagina foi carregada, so trocando a
// porta para a da API (funciona em localhost e acesso por IP na rede local).
// Quando o front esta atras de um tunel (ex: cloudflared), cada servico tem
// um dominio diferente, entao um parametro ?api=<url> na propria pagina
// sobrescreve esse calculo automatico.
const API_BASE = new URLSearchParams(window.location.search).get("api") || `http://${window.location.hostname}:8000`;

const state = {
  token: localStorage.getItem("cf_token") || null,
  usuario: JSON.parse(localStorage.getItem("cf_usuario") || "null"),
  veiculos: [],
  veiculoAtual: null,
  estacaoSelecionada: null,
  sessaoAtivaId: null,
  pollSessaoTimer: null,
  pollFilaTimer: null,
  modoNovoVeiculo: false,
};

async function api(path, { method = "GET", body = null } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;

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

function mostrar(tela) {
  document.querySelectorAll(".tela").forEach((el) => el.classList.add("hidden"));
  document.getElementById(`tela-${tela}`).classList.remove("hidden");

  const nav = document.getElementById("bottom-nav");
  nav.classList.toggle("hidden", !state.token);

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.nav === tela);
  });

  document.getElementById("btn-sair").classList.toggle("hidden", !state.token);
}

function formatarMoeda(valor) {
  return `R$ ${Number(valor).toFixed(2).replace(".", ",")}`;
}

// ---------------- AUTENTICACAO ----------------

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const alvo = btn.dataset.tab;
    document.getElementById("form-login").classList.toggle("hidden", alvo !== "login");
    document.getElementById("form-registro").classList.toggle("hidden", alvo !== "registro");
  });
});

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
    aoAutenticar(dados);
  } catch (err) {
    erroEl.textContent = err.message;
  }
});

document.getElementById("form-registro").addEventListener("submit", async (e) => {
  e.preventDefault();
  const erroEl = document.getElementById("reg-erro");
  erroEl.textContent = "";
  try {
    const dados = await api("/api/auth/registrar", {
      method: "POST",
      body: {
        nome: document.getElementById("reg-nome").value,
        email: document.getElementById("reg-email").value,
        senha: document.getElementById("reg-senha").value,
        empresa: document.getElementById("reg-empresa").value || null,
        telefone: document.getElementById("reg-telefone").value || null,
      },
    });
    aoAutenticar(dados);
  } catch (err) {
    erroEl.textContent = err.message;
  }
});

function aoAutenticar(dados) {
  state.token = dados.access_token;
  state.usuario = dados.usuario;
  localStorage.setItem("cf_token", state.token);
  localStorage.setItem("cf_usuario", JSON.stringify(state.usuario));
  depoisDoLogin();
}

document.getElementById("btn-sair").addEventListener("click", () => {
  state.token = null;
  state.usuario = null;
  state.veiculos = [];
  state.veiculoAtual = null;
  clearInterval(state.pollSessaoTimer);
  clearInterval(state.pollFilaTimer);
  localStorage.removeItem("cf_token");
  localStorage.removeItem("cf_usuario");
  mostrar("auth");
});

// ---------------- VEICULO ----------------

document.getElementById("btn-trocar-veiculo").addEventListener("click", () => {
  state.modoNovoVeiculo = true;
  document.getElementById("btn-cancelar-veiculo").classList.remove("hidden");
  document.getElementById("form-veiculo").reset();
  document.getElementById("v-bateria").value = 50;
  document.getElementById("v-limite-percent").value = 80;
  document.getElementById("v-limite-custo").value = 50;
  mostrar("veiculo");
});

document.getElementById("btn-cancelar-veiculo").addEventListener("click", () => {
  document.getElementById("btn-cancelar-veiculo").classList.add("hidden");
  mostrar("home");
});

document.getElementById("form-veiculo").addEventListener("submit", async (e) => {
  e.preventDefault();
  const erroEl = document.getElementById("v-erro");
  erroEl.textContent = "";
  try {
    const veiculo = await api("/api/veiculos", {
      method: "POST",
      body: {
        placa: document.getElementById("v-placa").value.toUpperCase(),
        modelo: document.getElementById("v-modelo").value,
        marca: document.getElementById("v-marca").value || null,
        capacidade_bateria_kwh: Number(document.getElementById("v-capacidade").value),
        bateria_atual_percent: Number(document.getElementById("v-bateria").value),
        limite_percent_padrao: Number(document.getElementById("v-limite-percent").value || 80),
        limite_custo_padrao: Number(document.getElementById("v-limite-custo").value || 50),
      },
    });
    state.veiculos.push(veiculo);
    state.veiculoAtual = veiculo;
    document.getElementById("btn-cancelar-veiculo").classList.add("hidden");
    await loadHome();
    mostrar("home");
  } catch (err) {
    erroEl.textContent = err.message;
  }
});

function renderVeiculoCard() {
  const container = document.getElementById("home-veiculo-card");
  if (!state.veiculoAtual) {
    container.innerHTML = `<p class="vazio">Nenhum veiculo cadastrado</p>`;
    return;
  }
  const v = state.veiculoAtual;
  const opcoes = state.veiculos
    .map((x) => `<option value="${x.id}" ${x.id === v.id ? "selected" : ""}>${x.placa} - ${x.modelo}</option>`)
    .join("");

  container.innerHTML = `
    <div style="width:100%">
      ${state.veiculos.length > 1 ? `<select id="seletor-veiculo" style="margin-bottom:10px;width:100%;padding:8px;border-radius:8px;border:1px solid var(--borda)">${opcoes}</select>` : ""}
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <div class="placa">${v.placa}</div>
          <div class="modelo">${v.marca ? v.marca + " " : ""}${v.modelo}</div>
        </div>
        <div class="bateria">${Number(v.bateria_atual_percent).toFixed(0)}%</div>
      </div>
    </div>`;

  const seletor = document.getElementById("seletor-veiculo");
  if (seletor) {
    seletor.addEventListener("change", (e) => {
      state.veiculoAtual = state.veiculos.find((x) => x.id === Number(e.target.value));
      renderVeiculoCard();
    });
  }
}

// ---------------- HOME / ESTACOES / POTENCIA ----------------

async function loadHome() {
  renderVeiculoCard();
  await Promise.all([carregarEstacoes(), carregarPotencia()]);
}

async function carregarEstacoes() {
  const estacoes = await api("/api/estacoes");
  const container = document.getElementById("lista-estacoes");
  if (estacoes.length === 0) {
    container.innerHTML = `<p class="vazio">Nenhuma estacao cadastrada</p>`;
    return;
  }
  container.innerHTML = estacoes
    .map(
      (e) => `
      <div class="estacao-item ${e.status}" data-id="${e.id}">
        <div>
          <div class="nome">${e.nome}</div>
          <div class="local">${e.localizacao || ""} - ${Number(e.potencia_max_kw)} kW</div>
        </div>
        <div class="status-tag status-${e.status}">${e.status}</div>
      </div>`
    )
    .join("");

  container.querySelectorAll(".estacao-item.disponivel").forEach((el) => {
    el.addEventListener("click", () => {
      const estacao = estacoes.find((e) => e.id === Number(el.dataset.id));
      selecionarEstacao(estacao);
    });
  });
}

async function carregarPotencia() {
  const p = await api("/api/estacoes/potencia");
  document.getElementById("home-potencia-uso").textContent = `${p.potencia_em_uso_kw} kW em uso`;
  document.getElementById("home-potencia-max").textContent = `/ ${p.potencia_max_total_kw} kW`;
  document.getElementById("home-barra-fill").style.width = `${Math.min(p.percentual_em_uso, 100)}%`;
  document.getElementById("home-pico-tag").classList.toggle("hidden", !p.horario_pico);
}

document.getElementById("btn-atualizar-estacoes").addEventListener("click", carregarEstacoes);

document.getElementById("btn-liberar-entrada").addEventListener("click", async () => {
  try {
    const resp = await api("/api/acesso/entrada", { method: "POST" });
    alert(resp.mensagem);
    carregarEstacoes();
  } catch (err) {
    alert(err.message);
  }
});

// ---------------- PREFERENCIAS / INICIAR RECARGA ----------------

function selecionarEstacao(estacao) {
  if (!state.veiculoAtual) {
    alert("Cadastre um veiculo primeiro.");
    return;
  }
  state.estacaoSelecionada = estacao;
  document.getElementById("pref-estacao-nome").textContent = `${estacao.nome} - ${estacao.localizacao || ""}`;
  document.getElementById("pref-limite-percent").value = state.veiculoAtual.limite_percent_padrao;
  document.getElementById("pref-limite-custo").value = state.veiculoAtual.limite_custo_padrao ?? 50;
  document.getElementById("pref-erro").textContent = "";
  mostrar("preferencias");
}

document.getElementById("btn-cancelar-preferencias").addEventListener("click", () => mostrar("home"));

document.getElementById("form-preferencias").addEventListener("submit", async (e) => {
  e.preventDefault();
  const erroEl = document.getElementById("pref-erro");
  erroEl.textContent = "";
  try {
    const sessao = await api("/api/sessoes/iniciar", {
      method: "POST",
      body: {
        veiculo_id: state.veiculoAtual.id,
        estacao_id: state.estacaoSelecionada.id,
        limite_percent: Number(document.getElementById("pref-limite-percent").value),
        limite_custo: Number(document.getElementById("pref-limite-custo").value),
      },
    });
    state.sessaoAtivaId = sessao.id;
    mostrar("sessao");
    iniciarPollingSessao();
  } catch (err) {
    if (err.status === 409) {
      erroEl.textContent = `${err.message} Entrando na fila de espera...`;
      setTimeout(() => entrarFila(), 1200);
    } else {
      erroEl.textContent = err.message;
    }
  }
});

// ---------------- SESSAO ATIVA ----------------

function atualizarUISessao(s) {
  const pct = Math.min(Math.max(s.bateria_atual_percent, 0), 100);
  document.getElementById("sessao-bateria-fill").parentElement.style.background =
    `conic-gradient(var(--verde) ${pct * 3.6}deg, var(--borda) 0deg)`;
  document.getElementById("sessao-bateria-texto").textContent = `${pct.toFixed(0)}%`;
  document.getElementById("sessao-potencia").textContent = `${s.potencia_alocada_kw} kW`;
  document.getElementById("sessao-kwh").textContent = `${Number(s.kwh_consumido).toFixed(2)} kWh`;
  document.getElementById("sessao-custo").textContent = formatarMoeda(s.custo_total);
  document.getElementById("sessao-tempo").textContent =
    s.tempo_estimado_restante_min != null ? `${Math.round(s.tempo_estimado_restante_min)} min` : "--";
}

function iniciarPollingSessao() {
  clearInterval(state.pollSessaoTimer);
  const executar = async () => {
    try {
      const s = await api(`/api/sessoes/status/${state.sessaoAtivaId}`);
      if (s.status !== "carregando") {
        clearInterval(state.pollSessaoTimer);
        alert(`Recarga finalizada - ${Number(s.kwh_consumido).toFixed(1)} kWh, ${formatarMoeda(s.custo_total)}`);
        await atualizarVeiculoAtual();
        mostrar("home");
        loadHome();
        return;
      }
      atualizarUISessao(s);
    } catch (err) {
      clearInterval(state.pollSessaoTimer);
    }
  };
  executar();
  state.pollSessaoTimer = setInterval(executar, 4000);
}

async function atualizarVeiculoAtual() {
  const lista = await api("/api/veiculos");
  state.veiculos = lista;
  state.veiculoAtual = lista.find((v) => v.id === state.veiculoAtual.id) || lista[0] || null;
}

document.getElementById("btn-parar-sessao").addEventListener("click", async () => {
  try {
    const resp = await api(`/api/sessoes/${state.sessaoAtivaId}/parar`, { method: "POST" });
    clearInterval(state.pollSessaoTimer);
    alert(resp.mensagem);
    await atualizarVeiculoAtual();
    mostrar("home");
    loadHome();
  } catch (err) {
    alert(err.message);
  }
});

// ---------------- FILA DE ESPERA ----------------

async function entrarFila() {
  try {
    await api("/api/fila/entrar", { method: "POST", body: { veiculo_id: state.veiculoAtual.id } });
    mostrar("fila");
    iniciarPollingFila();
  } catch (err) {
    alert(err.message);
    mostrar("home");
  }
}

function atualizarUIFila(f) {
  document.getElementById("fila-posicao").textContent = f.posicao_fila;
  document.getElementById("fila-prioridade").textContent = `prioridade ${f.prioridade.toLowerCase()}`;
  document.getElementById("fila-previsao").textContent =
    f.pessoas_a_frente > 0
      ? `${f.pessoas_a_frente} na sua frente - previsao de ${f.previsao_espera_min} min`
      : "voce e o proximo!";

  if (f.status === "notificada") {
    clearInterval(state.pollFilaTimer);
    alert("Uma estacao esta disponivel para voce! Voce tem 10 minutos para ocupar. Escolha a estacao na tela inicial.");
    mostrar("home");
    loadHome();
  }
}

function iniciarPollingFila() {
  clearInterval(state.pollFilaTimer);
  const executar = async () => {
    try {
      const f = await api("/api/fila/posicao");
      atualizarUIFila(f);
    } catch (err) {
      clearInterval(state.pollFilaTimer);
      mostrar("home");
      loadHome();
    }
  };
  executar();
  state.pollFilaTimer = setInterval(executar, 5000);
}

document.getElementById("btn-atualizar-fila").addEventListener("click", async () => {
  try {
    const f = await api("/api/fila/posicao");
    atualizarUIFila(f);
  } catch (err) {
    alert(err.message);
  }
});

// ---------------- HISTORICO ----------------

async function carregarHistorico() {
  const lista = await api("/api/sessoes/historico");
  const container = document.getElementById("lista-historico");
  if (lista.length === 0) {
    container.innerHTML = `<p class="vazio">Nenhuma sessao ainda</p>`;
    return;
  }
  container.innerHTML = lista
    .map((s) => {
      const data = new Date(s.inicio).toLocaleString("pt-BR");
      return `
      <div class="historico-item">
        <div class="topo">
          <span>${data}</span>
          <span>${formatarMoeda(s.custo_total)}</span>
        </div>
        <div class="detalhes">
          <span>${Number(s.kwh_consumido).toFixed(2)} kWh</span>
          <span>status: ${s.status}</span>
          <span class="eco">${Number(s.co2_evitado_kg).toFixed(3)} kg CO2 evitado</span>
        </div>
      </div>`;
    })
    .join("");
}

// ---------------- NAVEGACAO ----------------

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const destino = btn.dataset.nav;
    if (destino === "home") {
      mostrar("home");
      loadHome();
    } else if (destino === "historico") {
      mostrar("historico");
      carregarHistorico();
    }
  });
});

// ---------------- BOOTSTRAP ----------------

async function depoisDoLogin() {
  try {
    state.veiculos = await api("/api/veiculos");
  } catch (err) {
    document.getElementById("btn-sair").click();
    return;
  }

  if (state.veiculos.length === 0) {
    document.getElementById("btn-cancelar-veiculo").classList.add("hidden");
    mostrar("veiculo");
    return;
  }
  state.veiculoAtual = state.veiculos[0];

  try {
    const ativas = await api("/api/sessoes/ativas");
    const minha = ativas.find((s) => state.veiculos.some((v) => v.id === s.veiculo_id));
    if (minha) {
      state.sessaoAtivaId = minha.id;
      state.veiculoAtual = state.veiculos.find((v) => v.id === minha.veiculo_id) || state.veiculoAtual;
      mostrar("sessao");
      iniciarPollingSessao();
      return;
    }
  } catch (err) { /* segue fluxo normal */ }

  try {
    const posicao = await api("/api/fila/posicao");
    mostrar("fila");
    atualizarUIFila(posicao);
    iniciarPollingFila();
    return;
  } catch (err) { /* nao esta na fila */ }

  await loadHome();
  mostrar("home");
}

(function init() {
  if (state.token && state.usuario) {
    depoisDoLogin();
  } else {
    mostrar("auth");
  }
})();
