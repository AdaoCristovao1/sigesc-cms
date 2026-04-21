
function openModal(acao, usuarioId) {
    document.getElementById('usuarioIdInput').value = usuarioId;
    document.getElementById('acaoInput').value = acao;
    const modal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
    modal.show();
}

