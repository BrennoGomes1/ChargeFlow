let graficoConsumo = null;
let periodoAtual = "dia";

async function carregarVisaoGeral() {
  try {
    const [estacoes, potencia] = await Promise.all([
      api("/api/estacoes"),
      api("/api/estacoes/potencia"),
    ]);

    document.getElementById("vg-potencia-valores").textContent =
      `${potencia.potencia_em_uso_kw} / ${potencia.potencia_max_total_kw} kW`;
    document.getElementById("vg-potencia-fill").style.width = `${Math.min(potencia.percentual_em_uso, 100)}%`;
    document.getElementById("vg-pico-tag").classList.toggle("hidden", !potencia.horario_pico);

    const disponiveis = estacoes.filter((e) => e.status === "disponivel").length;
    const ocupadas = estacoes.filter((e) => e.status === "ocupada").length;
    const indisponiveis = estacoes.length - disponiveis - ocupadas;
    document.getElementById("vg-disponiveis").textContent = disponiveis;
    document.getElementById("vg-ocupadas").textContent = ocupadas;
    document.getElementById("vg-indisponiveis").textContent = indisponiveis;

    const mapa = document.getElementById("mapa-vagas");
    mapa.innerHTML = estacoes
      .map(
        (e) => `
        <div class="vaga ${e.status}">
          <span class="nome">${e.nome}</span>
          <span class="info">${e.localizacao || ""}</span>
          <span class="info">${e.potencia_atual_kw} / ${e.potencia_max_kw} kW</span>
          <span class="info">${e.status}</span>
        </div>`
      )
      .join("");
  } catch (err) {
    console.error(err);
    mostrarErroGeral("Nao foi possivel carregar a visao geral. " + err.message, carregarVisaoGeral);
  }
}

document.querySelectorAll(".periodo-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".periodo-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    periodoAtual = btn.dataset.periodo;
    carregarConsumo();
  });
});

async function carregarConsumo() {
  try {
    const dados = await api(`/api/dashboard/consumo?periodo=${periodoAtual}`);
    document.getElementById("consumo-kwh").textContent = formatarKwh(dados.kwh_total);
    document.getElementById("consumo-custo").textContent = formatarMoeda(dados.custo_total);

    const rotulos = dados.pontos.map((p) => p.periodo);
    const valores = dados.pontos.map((p) => p.kwh_total);

    const ctx = document.getElementById("grafico-consumo").getContext("2d");
    if (graficoConsumo) graficoConsumo.destroy();
    graficoConsumo = new Chart(ctx, {
      type: "bar",
      data: {
        labels: rotulos,
        datasets: [
          {
            label: "kWh consumido",
            data: valores,
            backgroundColor: "#2a78d6",
            borderRadius: 4,
            barThickness: 22,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: "#898781" } },
          y: {
            beginAtZero: true,
            grid: { color: "#e1e0d9" },
            ticks: { color: "#898781" },
          },
        },
      },
    });
  } catch (err) {
    console.error(err);
    mostrarErroGeral("Nao foi possivel carregar o consumo. " + err.message, carregarConsumo);
  }
}

async function carregarSustentabilidade() {
  try {
    const s = await api("/api/dashboard/sustentabilidade");
    document.getElementById("sus-kwh-total").textContent = formatarKwh(s.kwh_total);
    document.getElementById("sus-kwh-solar").textContent = formatarKwh(s.kwh_solar_total);
    document.getElementById("sus-co2").textContent = `${s.co2_evitado_total_kg.toFixed(2)} kg`;
    document.getElementById("sus-percentual-texto").textContent = `${s.percentual_renovavel}%`;
    document.getElementById("sus-percentual-fill").style.width = `${Math.min(s.percentual_renovavel, 100)}%`;
  } catch (err) {
    console.error(err);
    mostrarErroGeral("Nao foi possivel carregar a sustentabilidade. " + err.message, carregarSustentabilidade);
  }
}

async function carregarRanking() {
  try {
    const lista = await api("/api/dashboard/ranking");
    const container = document.getElementById("ranking-lista");
    if (lista.length === 0) {
      container.innerHTML = `<p class="vazio">Sem dados de consumo ainda</p>`;
      return;
    }
    const maiorKwh = Math.max(...lista.map((i) => i.kwh_total), 1);
    container.innerHTML = lista
      .map(
        (item, i) => `
        <div class="ranking-item">
          <span class="ranking-pos">#${i + 1}</span>
          <div class="ranking-info">
            <div class="ranking-nome">${item.nome} ${item.empresa ? `<span class="ranking-empresa">- ${item.empresa}</span>` : ""}</div>
            <div class="ranking-barra-trilho"><div class="ranking-barra-fill" style="width:${(item.kwh_total / maiorKwh) * 100}%"></div></div>
          </div>
          <span class="ranking-valor">${formatarKwh(item.kwh_total)}</span>
        </div>`
      )
      .join("");
  } catch (err) {
    console.error(err);
    mostrarErroGeral("Nao foi possivel carregar o ranking. " + err.message, carregarRanking);
  }
}
