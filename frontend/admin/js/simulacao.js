let contadorCarro = 0;

function criarLinhaCarro(nome = "", bateria = 40, potencia = 22) {
  contadorCarro += 1;
  const id = `carro-${contadorCarro}`;
  const tr = document.createElement("tr");
  tr.id = id;
  tr.innerHTML = `
    <td><input type="text" class="sim-nome" value="${nome || `Carro ${contadorCarro}`}" /></td>
    <td><input type="number" class="sim-bateria" min="0" max="100" value="${bateria}" /></td>
    <td><input type="number" class="sim-potencia" min="1" step="1" value="${potencia}" /></td>
    <td><button type="button" class="remover-carro" title="Remover">x</button></td>
  `;
  tr.querySelector(".remover-carro").addEventListener("click", () => tr.remove());
  document.getElementById("sim-linhas").appendChild(tr);
}

document.getElementById("btn-add-carro").addEventListener("click", () => criarLinhaCarro());

document.getElementById("btn-preset-5").addEventListener("click", () => {
  document.getElementById("sim-linhas").innerHTML = "";
  criarLinhaCarro("Carro A", 15, 50);
  criarLinhaCarro("Carro B", 35, 50);
  criarLinhaCarro("Carro C", 55, 22);
  criarLinhaCarro("Carro D", 75, 50);
  criarLinhaCarro("Carro E", 90, 22);
});

document.getElementById("btn-simular").addEventListener("click", async () => {
  const linhas = [...document.querySelectorAll("#sim-linhas tr")];
  if (linhas.length === 0) {
    alert("Adicione pelo menos um carro para simular.");
    return;
  }

  const carros = linhas.map((tr) => ({
    nome: tr.querySelector(".sim-nome").value || "Carro",
    bateria_atual_percent: Number(tr.querySelector(".sim-bateria").value),
    potencia_max_kw: Number(tr.querySelector(".sim-potencia").value),
  }));

  try {
    const resultado = await api("/api/simulacao/cenario", { method: "POST", body: { carros } });
    renderizarResultadoSimulacao(resultado);
  } catch (err) {
    alert(err.message);
  }
});

function renderizarResultadoSimulacao(resultado) {
  document.getElementById("sim-resultado").classList.remove("hidden");
  document.getElementById("sim-disponivel-texto").textContent =
    `${resultado.potencia_disponivel_kw} kW${resultado.horario_pico ? " (reduzida por horario de pico)" : ""}`;

  const container = document.getElementById("sim-barras");
  const maiorPotencia = Math.max(...resultado.carros.map((c) => c.potencia_solicitada_kw), 1);

  container.innerHTML = resultado.carros
    .map((c) => {
      const percentual = Math.min((c.potencia_alocada_kw / maiorPotencia) * 100, 100);
      return `
      <div class="sim-barra-item">
        <div class="topo">
          <span>${c.nome} <span class="prioridade-badge prioridade-${c.prioridade}">${c.prioridade}</span></span>
          <span>${c.potencia_alocada_kw} / ${c.potencia_solicitada_kw} kW</span>
        </div>
        <div class="trilho"><div class="fill fill-${c.prioridade}" style="width:${percentual}%"></div></div>
      </div>`;
    })
    .join("");
}

// Preenche a tabela com um carro de exemplo ao carregar a secao pela primeira vez
if (document.getElementById("sim-linhas").children.length === 0) {
  criarLinhaCarro("Carro A", 25, 50);
  criarLinhaCarro("Carro B", 60, 22);
}
