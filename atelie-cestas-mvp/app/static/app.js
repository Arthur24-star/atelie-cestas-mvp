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

const whatsappInput = document.querySelector('input[name="whatsapp"]');

if (whatsappInput) {
  whatsappInput.addEventListener("input", () => {
    let digits = whatsappInput.value.replace(/\D/g, "").slice(0, 11);

    if (digits.length > 10) {
      digits = digits.replace(
        /^(\d{2})(\d{5})(\d{0,4}).*/,
        "($1) $2-$3"
      );
    } else if (digits.length > 6) {
      digits = digits.replace(
        /^(\d{2})(\d{4})(\d{0,4}).*/,
        "($1) $2-$3"
      );
    } else if (digits.length > 2) {
      digits = digits.replace(/^(\d{2})(\d*)/, "($1) $2");
    } else if (digits.length > 0) {
      digits = digits.replace(/^(\d*)/, "($1");
    }

    whatsappInput.value = digits;
  });
}
