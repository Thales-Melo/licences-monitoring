function toggleIntervalFields(index) {
    const tipoPrazo = document.getElementById(`tipo_prazo_${index}`).value;
    const intervalFields = document.getElementById(`interval_fields_${index}`);
    
    if (tipoPrazo === 'intervalado') {
        intervalFields.style.display = 'block';
    } else {
        intervalFields.style.display = 'none';
    }
}

function atualizarPrazo(index) {
    // Coleta os valores dos campos
    const tipoPrazo = document.getElementById(`tipo_prazo_${index}`)?.value || '';
    const intervaloPrazo = document.getElementById(`intervalo_prazo_${index}`)?.value || '';
    const dataInicial = document.getElementById(`data_inicial_${index}`)?.value || '';
    const dataFinal = document.getElementById(`data_final_${index}`)?.value || '';
    const quantidadePrazo = document.getElementById(`quantidade_prazo_${index}`)?.value || '';

    // Depuração
    console.log(`tipoPrazo: ${tipoPrazo}`);
    console.log(`intervaloPrazo: ${intervaloPrazo}`);
    console.log(`dataInicial: ${dataInicial}`);
    console.log(`dataFinal: ${dataFinal}`);
    console.log(`quantidadePrazo: ${quantidadePrazo}`);

    // Cria um formulário para enviar os dados
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '{{ url_for("main.atualizar_prazo") }}'; // URL para atualizar o prazo

    // Adiciona os dados ao formulário
    form.innerHTML = `
        <input type="hidden" name="file_id" value="{{ file_id }}">
        <input type="hidden" name="cond_index" value="${index}">
        <input type="hidden" name="tipo_prazo" value="${tipoPrazo}">
        <input type="hidden" name="intervalo_prazo" value="${intervaloPrazo}">
        <input type="hidden" name="data_inicial" value="${dataInicial}">
        <input type="hidden" name="data_final" value="${dataFinal}">
        <input type="hidden" name="quantidade_prazo" value="${quantidadePrazo}">
    `;

    // Envia o formulário
    document.body.appendChild(form);
    form.submit();
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

