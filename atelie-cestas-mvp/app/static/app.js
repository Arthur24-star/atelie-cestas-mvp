
const form = document.querySelector("#order-form");
const subtotal = document.querySelector("#subtotal");
const whatsappInput = document.querySelector('input[name="whatsapp"]');

function updateSubtotal() {
  if (!form || !subtotal) return;

  const checked = form.querySelectorAll(
    'input[name="selected_items"]:checked'
  );

  const total = Array.from(checked).reduce(
    (sum, input) => sum + Number(input.dataset.price || 0),
    0
  );

  subtotal.textContent = total.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL"
  });
}

if (form) {
  form.addEventListener("change", updateSubtotal);

  form.addEventListener("submit", (event) => {
    const checked = form.querySelectorAll(
      'input[name="selected_items"]:checked'
    );

    if (checked.length === 0) {
      event.preventDefault();
      alert("Selecione pelo menos um insumo para continuar.");
    }
  });

  updateSubtotal();
}

if (whatsappInput) {
  whatsappInput.addEventListener("input", () => {
    const digits = whatsappInput.value
      .replace(/\D/g, "")
      .slice(0, 11);

    let formatted = digits;

    if (digits.length > 7) {
      formatted = digits.replace(
        /^(\d{2})(\d{5})(\d{1,4})$/,
        "($1) $2-$3"
      );
    } else if (digits.length > 2) {
      formatted = digits.replace(
        /^(\d{2})(\d*)$/,
        "($1) $2"
      );
    } else if (digits.length > 0) {
      formatted = `(${digits}`;
    }

    whatsappInput.value = formatted;
  });
}
