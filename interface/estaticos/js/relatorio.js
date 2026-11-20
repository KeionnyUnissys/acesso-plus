// Botão "Salvar relatório em PDF" da tela de resultado.
// Abre todos os "Onde está" antes de imprimir, para o PDF mostrar a localização de cada problema.
document.getElementById('imprimir').addEventListener('click', function () {
  document.querySelectorAll('details').forEach(function (d) { d.open = true; });
  window.print();
});
