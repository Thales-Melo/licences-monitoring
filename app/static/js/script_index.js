   // Função para filtro das tabelas
   function searchLicenses() {
    // Pega o valor de busca
    var input = document.getElementById("search-input");
    var filter = input.value.toLowerCase();
    
    // Seleciona todas as linhas das tabelas
    var rows = document.querySelectorAll("table tr[data-type]");
    
    rows.forEach(function(row) {
        var cells = row.getElementsByTagName("td");
        var found = false;
        
        // Itera sobre as células da linha
        for (var i = 0; i < cells.length; i++) {
            if (cells[i].innerText.toLowerCase().includes(filter)) {
                found = true;
                break;
            }
        }
        
        // Mostra ou esconde a linha com base no resultado da busca
        if (found) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}

        function confirmarMovimento() {
            return confirm("Tem certeza de que deseja mover este arquivo para a categoria 'Entregues'?");
        }

        function confirmarDescarimbamento() {
            return confirm("Tem certeza de que deseja descarimbar este arquivo?");
        }

        function confirmarEncerramento() {
            return confirm("Tem certeza de que deseja arquivar este arquivo?");
        }

        function confirmarDesarquivamento() {
            return confirm("Tem certeza de que deseja desarquivar este arquivo?");
        }


        document.addEventListener('DOMContentLoaded', function() {
        // Restaura a posição da rolagem
        if (sessionStorage.getItem('scrollPosition')) {
            window.scrollTo(0, sessionStorage.getItem('scrollPosition'));
            sessionStorage.removeItem('scrollPosition');
        }
        });

        document.addEventListener('click', function(e) {
            // Salva a posição da rolagem antes de atualizar a ordem
            if (e.target && e.target.matches('.sortable-link')) {
                sessionStorage.setItem('scrollPosition', window.scrollY);
            }
        });
