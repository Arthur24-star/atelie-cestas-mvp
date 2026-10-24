



(() => {
  const form = document.getElementById("order-form");
  if (!form) return;

  const subtotalEl = document.getElementById("subtotal");
  const freightEl = document.getElementById("freight-value");
  const totalEl = document.getElementById("grand-total");
  const noteEl = document.getElementById("freight-note");
  const calculateButton = document.getElementById("calculate-freight");

  const phoneInput =
    document.getElementById("phone") ||
    document.getElementById("telephone") ||
    document.getElementById("whatsapp");

  const cepInput = document.getElementById("cep");

  let freight = null;
  let quoteAddressKey = null;
  let cepRequest = 0;

  const money = (value) =>
    new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(value);

  // Máscara de telefone brasileiro
  function formatPhone(value) {
    const digits = value.replace(/\D/g, "").slice(0, 11);

    if (digits.length <= 2) {
      return digits.length ? `(${digits}` : "";
    }

    if (digits.length <= 6) {
      return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
    }

    if (digits.length <= 10) {
      return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
    }

    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
  }

  if (phoneInput) {
    phoneInput.addEventListener("input", () => {
      phoneInput.value = formatPhone(phoneInput.value);
    });
  }

  // Máscara de CEP
  function formatCep(value) {
    const digits = value.replace(/\D/g, "").slice(0, 8);

    if (digits.length > 5) {
      return `${digits.slice(0, 5)}-${digits.slice(5)}`;
    }

    return digits;
  }

  if (cepInput) {
    cepInput.addEventListener("input", () => {
      cepInput.value = formatCep(cepInput.value);

      if (cepInput.value.replace(/\D/g, "").length === 8) {
        buscarEnderecoPorCep();
      }
    });
  }

  // Busca endereço pelo ViaCEP
  async function buscarEnderecoPorCep() {
    const cep = cepInput.value.replace(/\D/g, "");
    if (cep.length !== 8) return;

    const requestId = ++cepRequest;

    try {
      if (noteEl) {
        noteEl.textContent = "Consultando endereço pelo CEP...";
      }

      const response = await fetch(
        `https://viacep.com.br/ws/${cep}/json/`
      );

      if (!response.ok) {
        throw new Error("Não foi possível consultar o CEP.");
      }

      const data = await response.json();

      // Ignora respostas de consultas anteriores
      if (requestId !== cepRequest) return;

      if (data.erro) {
        if (noteEl) {
          noteEl.textContent = "CEP não encontrado. Confira os números.";
        }
        return;
      }

      preencherCampo("street", data.logradouro);
      preencherCampo("neighborhood", data.bairro);
      preencherCidade(data.localidade, data.uf);

      invalidarFrete();

      if (noteEl) {
        noteEl.textContent =
          "Endereço preenchido quando havia dados disponíveis. Confira e complete o número.";
      }
    } catch (error) {
      if (requestId === cepRequest && noteEl) {
        noteEl.textContent =
          "Não foi possível consultar o CEP. Preencha o endereço manualmente.";
      }
    }
  }

  function preencherCampo(id, value) {
    const field = document.getElementById(id);
    if (field && value) {
      field.value = value;
      field.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  function preencherCidade(city, state) {
    const field = document.getElementById("city");
    if (!field || !city) return;

    // Se cidade for uma lista suspensa, tenta selecionar a opção correta.
    if (field.tagName === "SELECT") {
      const options = Array.from(field.options);
      const option = options.find((item) =>
        item.value.trim().toLowerCase() === city.trim().toLowerCase() ||
        item.textContent.trim().toLowerCase() === city.trim().toLowerCase()
      );

      if (option) {
        field.value = option.value;
      } else {
        if (noteEl) {
          noteEl.textContent =
            `CEP localizado em ${city}/${state}. Selecione essa cidade na lista.`;
        }
      }
    } else {
      field.value = city;
    }

    field.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function productsSubtotal() {
    let total = 0;

    const basket = form.querySelector(
      'input[name="selected_basket"]:checked'
    );

    if (basket) {
      total += Number(basket.dataset.price || 0);
    }

    const extrasChoice = form.querySelector(
      'input[name="wants_extras"]:checked'
    );

    if (extrasChoice && extrasChoice.value === "yes") {
      form.querySelectorAll(
        'input[name="selected_extras"]:checked'
      ).forEach((item) => {
        total += Number(item.dataset.price || 0);
      });
    }

    return Math.round(total * 100) / 100;
  }

  function updateTotals() {
    const subtotal = productsSubtotal();

    if (subtotalEl) subtotalEl.textContent = money(subtotal);

    if (freightEl) {
      freightEl.textContent =
        freight === null ? "Calcule o frete" : money(freight);
    }

    if (totalEl) {
      totalEl.textContent = money(subtotal + (freight ?? 0));
    }
  }

  function addressKey() {
    return ["city", "street", "number", "neighborhood", "cep"]
      .map((id) =>
        document.getElementById(id)?.value.trim() || ""
      )
      .join("|");
  }

  function invalidarFrete() {
    freight = null;
    quoteAddressKey = null;
    updateTotals();
  }

  async function calculateFreight() {
    const fields = ["city", "street", "number", "neighborhood", "cep"];

    const values = Object.fromEntries(
      fields.map((id) => [
        id,
        document.getElementById(id)?.value.trim() || ""
      ])
    );

    if (Object.values(values).some((value) => !value)) {
      if (noteEl) {
        noteEl.textContent =
          "Preencha cidade, bairro, rua, número e CEP antes de calcular.";
      }
      return;
    }

    if (calculateButton) {
      calculateButton.disabled = true;
      calculateButton.textContent = "Calculando...";
    }

    if (noteEl) {
      noteEl.textContent = "Consultando a distância para calcular o frete.";
    }

    try {
      const params = new URLSearchParams(values);
      const response = await fetch(`/freight-quote?${params}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error || "Não foi possível calcular o frete."
        );
      }

      freight = Number(data.freight);
      quoteAddressKey = addressKey();
      updateTotals();

      if (noteEl) {
        if (data.fixed_rate) {
          noteEl.textContent = "Taxa fixa de Sarzedo: R$ 10,00.";
        } else {
          noteEl.textContent =
            `Distância de ida: ${Number(data.distance_km).toLocaleString(
              "pt-BR",
              { minimumFractionDigits: 2, maximumFractionDigits: 2 }
            )} km. O frete considera ida e volta a R$ 3,00 por quilômetro.`;
        }
      }
    } catch (error) {
      invalidarFrete();

      if (noteEl) {
        noteEl.textContent = error.message;
      }
    } finally {
      if (calculateButton) {
        calculateButton.disabled = false;
        calculateButton.textContent = "Calcular frete";
      }
    }
  }

  form.addEventListener("change", (event) => {
    if (event.target.matches(
      'input[name="selected_basket"], input[name="selected_extras"], input[name="wants_extras"]'
    )) {
      updateTotals();
    }

    if (["city", "street", "number", "neighborhood", "cep"].includes(
      event.target.id
    )) {
      invalidarFrete();

      if (noteEl) {
        noteEl.textContent =
          "O endereço mudou. Calcule o frete novamente.";
      }
    }
  });

  if (calculateButton) {
    calculateButton.addEventListener("click", calculateFreight);
  }

  form.addEventListener("submit", (event) => {
    if (freight === null || quoteAddressKey !== addressKey()) {
      event.preventDefault();

      if (noteEl) {
        noteEl.textContent =
          "Calcule o frete para o endereço informado antes de confirmar o pedido.";
      }

      if (calculateButton) {
        calculateButton.scrollIntoView({
          behavior: "smooth",
          block: "center"
        });
      }
    }
  });

  updateTotals();
})();
