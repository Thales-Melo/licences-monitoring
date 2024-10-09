function toggleIntervalFields(index) {
    const tipoPrazo = document.getElementById(`tipo_prazo_${index}`).value;
    const intervalFields = document.getElementById(`interval_fields_${index}`);
    
    if (tipoPrazo === 'intervalado') {
        intervalFields.style.display = 'block';
    } else {
        intervalFields.style.display = 'none';
    }
}

function condicionanteCumprida(index) {
    // Cria um formulário para enviar os dados
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '{{ url_for("main.cumprir_condicionante") }}'; // URL para atualizar o prazo

    // Adiciona os dados ao formulário
    form.innerHTML = `
        <input type="hidden" name="file_id" value="{{ file_id }}">
        <input type="hidden" name="cond_index" value="${index}">
        <input type="hidden" name="cond_cumprida" value="True">
    `;

    // Envia o formulário
    document.body.appendChild(form);
    form.submit();
}

