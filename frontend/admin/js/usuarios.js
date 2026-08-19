async function carregarUsuarios() {
  try {
    const dados = await api("/api/usuarios");
    document.getElementById("us-total").textContent = dados.total_usuarios;
    document.getElementById("us-empresas").textContent = dados.total_empresas;

    const container = document.getElementById("usuarios-lista");
    if (dados.usuarios.length === 0) {
      container.innerHTML = `<p class="vazio">Nenhum usuário cadastrado ainda</p>`;
      return;
    }

    container.innerHTML = dados.usuarios
      .map((u) => {
        const cadastro = new Date(u.criado_em).toLocaleDateString("pt-BR");
        return `
        <div class="usuario-item">
          <div class="usuario-info">
            <div class="usuario-nome">${u.nome}${u.empresa ? ` <span class="usuario-empresa">- ${u.empresa}</span>` : ""}</div>
            <div class="usuario-email">${u.email}${u.telefone ? ` · ${u.telefone}` : ""}</div>
            <div class="usuario-email">cadastrado em ${cadastro}</div>
          </div>
          <div class="usuario-stats">
            <span class="usuario-stat"><strong>${formatarMoeda(u.saldo)}</strong><small>saldo</small></span>
            <span class="usuario-stat"><strong>${u.qtd_veiculos}</strong><small>veículo${u.qtd_veiculos === 1 ? "" : "s"}</small></span>
            <span class="usuario-stat"><strong>${u.qtd_sessoes_finalizadas}</strong><small>recarga${u.qtd_sessoes_finalizadas === 1 ? "" : "s"}</small></span>
          </div>
        </div>`;
      })
      .join("");
  } catch (err) {
    console.error(err);
    mostrarErroGeral("Não foi possível carregar os usuários. " + err.message, carregarUsuarios);
  }
}
