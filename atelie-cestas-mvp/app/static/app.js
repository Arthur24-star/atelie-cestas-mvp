const form = document.querySelector("#order-form");
const subtotal = document.querySelector("#subtotal");

function updateSubtotal() {
  if (!form || !subtotal) return;
  const checked = form.querySelectorAll('input[name="selected_items"]:checked');
  const total = Array.from(checked).reduce((sum, input) => sum + Number(input.dataset.price || 0), 0);
  subtotal.textContent = total.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

if (form) {
  form.addEventListener("change", updateSubtotal);
  form.addEventListener("submit", (event) => {
    const checked = form.querySelectorAll('input[name="selected_items"]:checked');
    if (checked.length === 0) {
      event.preventDefault();
      alert("Selecione pelo menos um insumo para continuar.");
    }
  });
  updateSubtotal();
}
