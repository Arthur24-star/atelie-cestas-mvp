
from datetime import date, timedelta
from pathlib import Path
from typing import Annotated, Optional
from urllib.parse import quote
import re
import os

import requests
from dotenv import load_dotenv

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, String, Float, Date, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


# ==================================================
# CONFIGURAÇÃO DO PROJETO E BANCO DE DADOS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

# Carrega a chave da API a partir do .env na raiz do projeto.
load_dotenv(PROJECT_DIR / ".env")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

DELIVERY_ORIGIN = "Rua Dezenove, 90 - Santa Rosa, Sarzedo, MG, Brasil"
SARZEDO_FREIGHT = 10.00
PRICE_PER_KM = 3.00

engine = create_engine(
    f"sqlite:///{PROJECT_DIR / 'atelie.db'}",
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    whatsapp: Mapped[str] = mapped_column(String(30))
    delivery_date: Mapped[date] = mapped_column(Date)
    items_summary: Mapped[str] = mapped_column(String(1000))
    total: Mapped[float] = mapped_column(Float)
    freight: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    distance_km: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )

    # Endereço de entrega
    cep: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    neighborhood: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True
    )
    street: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    complement: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True
    )

    # Informações adicionais do pedido
    recipient_name: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True
    )
    recipient_phone: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )
    reference_point: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True
    )
    preferred_time: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    card_message: Mapped[Optional[str]] = mapped_column(
        String(300), nullable=True
    )
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )


Base.metadata.create_all(bind=engine)


def migrate_order_columns() -> None:
    """Adiciona colunas ausentes sem apagar os pedidos existentes."""

    columns = {
        "cep": "VARCHAR(9)",
        "city": "VARCHAR(100)",
        "neighborhood": "VARCHAR(120)",
        "street": "VARCHAR(160)",
        "number": "VARCHAR(20)",
        "complement": "VARCHAR(120)",
        "recipient_name": "VARCHAR(120)",
        "recipient_phone": "VARCHAR(30)",
        "reference_point": "VARCHAR(200)",
        "preferred_time": "VARCHAR(100)",
        "card_message": "VARCHAR(300)",
        "payment_method": "VARCHAR(30)",
        "freight": "FLOAT NOT NULL DEFAULT 0",
        "distance_km": "FLOAT",
    }

    with engine.begin() as connection:
        existing_columns = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(orders)"
            ).fetchall()
        }

        for name, column_type in columns.items():
            if name not in existing_columns:
                connection.exec_driver_sql(
                    f"ALTER TABLE orders ADD COLUMN {name} {column_type}"
                )


migrate_order_columns()


# ==================================================
# APLICAÇÃO FASTAPI
# ==================================================

app = FastAPI(title="Ateliê de Cestas MVP")

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ==================================================
# PRODUTOS ANTIGOS - MANTIDOS PARA COMPATIBILIDADE
# ==================================================

PRODUCTS = [
    {"id": "caixa", "name": "Caixa de Madeira Pinho", "price": 25.00},
    {"id": "caneca", "name": "Caneca de Cerâmica", "price": 18.00},
    {"id": "biscoitos", "name": "Biscoitos Artesanais 100g", "price": 12.00},
    {"id": "chocolate", "name": "Chocolate Artesanal", "price": 15.00},
]


# ==================================================
# CESTAS PRONTAS
# ==================================================

READY_BASKETS = [
    {
        "id": "cafe-bom-dia",
        "name": "Café Bom Dia",
        "description": "Um carinho em forma de café da manhã.",
        "price": 99.90,
        "serves": "Serve 1 pessoa.",
        "items": [
            "Drip Coffee",
            "Suco integral",
            "Mini croissant de frango",
            "Mini pães artesanais",
            "Queijo e blanquet",
            "Manteiga e requeijão",
            "Salada de frutas",
            "Bolo caseiro",
            "Biscoito de maçã ou avelã",
            "Stroopwafel",
            "Fitas, tag personalizada e cartão",
        ],
        "image": "cafe-bom-dia.jpg",
    },
    {
        "id": "cafe-afeto",
        "name": "Café Afeto",
        "description": "Uma forma de expressar gratidão.",
        "price": 119.90,
        "serves": "Serve 1 pessoa.",
        "items": [
            "Drip Coffee",
            "Suco integral",
            "Croissant",
            "Waffle",
            "Stroopwafel",
            "Salame italiano",
            "Queijo e geleia",
            "Frutas da estação",
            "Bolo caseiro",
            "Mini coração de chocolate",
            "Fitas, tag personalizada e cartão",
        ],
        "image": "cafe-afeto.jpg",
    },
    {
        "id": "cafezinho",
        "name": "Cafezinho",
        "description": "Um café especial para acompanhar momentos deliciosos.",
        "price": 159.90,
        "serves": "Serve até 2 pessoas.",
        "items": [
            "Drip Coffee e chá",
            "Croissant de frango",
            "Frutas da estação",
            "Bolo caseiro",
            "Stroopwafel e waffles",
            "Cookies artesanais",
            "Madeleine",
            "Pão de queijo",
            "Fitas, tag personalizada e cartão",
        ],
        "image": "cafezinho.jpg",
    },
    {
        "id": "cafe-entre-conversas",
        "name": "Café Entre Conversas",
        "description": "Café da manhã para compartilhar bons momentos.",
        "price": 189.90,
        "serves": "Serve 1 pessoa.",
        "items": [
            "Croissant e croissant de calabresa",
            "Waffle e stroopwafel",
            "Crostatina de cacau",
            "Pão de mel e bolo caseiro",
            "Queijo e doce de leite",
            "Salada de frutas e iogurte grego",
            "Salame italiano e castanhas",
            "Café especial e suco integral",
            "Fitas, tag personalizada e cartão",
        ],
        "image": "cafe-entre-conversas.jpg",
    },
    {
        "id": "cafe-aconchego",
        "name": "Café Aconchego",
        "description": "Momentos para apreciar com calma.",
        "price": 219.90,
        "serves": "Serve até 2 pessoas.",
        "items": [
            "Drip Coffee",
            "Suco integral",
            "Pães artesanais e grissini",
            "Pão de queijo e queijo",
            "Waffle e iogurte grego",
            "Doce de leite e geleia",
            "Frutas da estação",
            "Salame italiano",
            "Seleção de biscoitos",
            "Lâminas de chocolate e stroopwafel",
            "Castanhas",
            "Fitas, tag personalizada e cartão",
        ],
        "image": "cafe-aconchego.jpg",
    },
    {
        "id": "cafe-celebrar",
        "name": "Café Celebrar",
        "description": "Uma cesta para celebrar momentos especiais.",
        "price": 229.90,
        "serves": "Serve até 2 pessoas; bolo serve até 4.",
        "items": [
            "Drip Coffee",
            "Suco integral",
            "Croissant de frango",
            "Pão de queijo e waffle",
            "Pão artesanal",
            "Doce de leite e geleia",
            "Frutas da estação",
            "Salame italiano",
            "Seleção de biscoitos",
            "Lâminas de chocolate e stroopwafel",
            "Bolo de aniversário",
            "Fitas, tag personalizada e cartão",
        ],
        "image": "cafe-celebrar.jpg",
    },
]


# ==================================================
# ADICIONAIS DE PERSONALIZAÇÃO
# ==================================================

EXTRAS = [
    {"id": "foto-polaroid", "name": "Foto Polaroid", "price": 5.00},
    {"id": "ima-polaroid", "name": "Ímã Polaroid", "price": 10.00},
    {"id": "caneca-personalizada", "name": "Caneca personalizada", "price": 45.00},
    {"id": "mini-bolo", "name": "Mini bolo festivo", "price": 40.00},
    {"id": "mini-buque", "name": "Mini buquê", "price": 10.00},
    {"id": "mini-kalanchoe", "name": "Mini kalanchoe", "price": 10.00},
    {"id": "kalanchoe", "name": "Kalanchoe", "price": 50.00},
    {"id": "orquidea", "name": "Orquídea", "price": 100.00},
    {"id": "mini-orquidea", "name": "Mini orquídea", "price": 60.00},
]

BASKETS_BY_ID = {basket["id"]: basket for basket in READY_BASKETS}
EXTRAS_BY_ID = {extra["id"]: extra for extra in EXTRAS}


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

def calculate_freight(
    city: str,
    street: str,
    number: str,
    neighborhood: str,
    cep: str,
) -> tuple[float, Optional[float]]:
    """
    Retorna (frete, distância de ida em km).
    Sarzedo usa taxa fixa; outras cidades consultam a Routes API.
    """

    if city.strip().casefold() == "sarzedo":
        return SARZEDO_FREIGHT, None

    if not GOOGLE_MAPS_API_KEY:
        raise ValueError(
            "A chave do Google Maps não foi configurada no arquivo .env."
        )

    destination = (
        f"{street}, {number}, {neighborhood}, "
        f"{city}, MG, Brasil, CEP {cep}"
    )

    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "routes.distanceMeters",
    }
    payload = {
        "origin": {"address": DELIVERY_ORIGIN},
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "units": "METRIC",
        "languageCode": "pt-BR",
        "regionCode": "BR",
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        routes = data.get("routes", [])

        if not routes or "distanceMeters" not in routes[0]:
            raise ValueError(
                "O Google Maps não encontrou uma rota para esse endereço. "
                "Confira os dados de entrega."
            )

        distance_km = routes[0]["distanceMeters"] / 1000
        freight = round(distance_km * 2 * PRICE_PER_KM, 2)
        return freight, round(distance_km, 2)

    except requests.RequestException as exc:
        # Inclui detalhes retornados pelo Google para facilitar o diagnóstico.
        detail = ""
        if exc.response is not None:
            try:
                detail = exc.response.json().get("error", {}).get("message", "")
            except (ValueError, AttributeError):
                detail = ""

        if detail:
            raise ValueError(
                f"Erro na consulta ao Google Maps: {detail}"
            ) from exc

        raise ValueError(
            "Não foi possível consultar o Google Maps. Confira a chave, "
            "a Routes API, o faturamento e a conexão com a internet."
        ) from exc


def validate_delivery_date(
    value: date,
    today: Optional[date] = None,
) -> bool:
    reference = today or date.today()
    return value >= reference + timedelta(days=1)


def calculate_total(selected_ids: list[str]) -> float:
    """Mantém compatibilidade com testes dos produtos antigos."""
    prices = {product["id"]: product["price"] for product in PRODUCTS}

    return round(
        sum(prices[item] for item in selected_ids if item in prices),
        2,
    )


def format_brl(value: float) -> str:
    return f"R$ {value:.2f}".replace(".", ",")


def format_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)

    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"

    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"

    return value


def page_context():
    return {
        "products": PRODUCTS,
        "ready_baskets": READY_BASKETS,
        "extras": EXTRAS,
        "min_delivery": (
            date.today() + timedelta(days=1)
        ).isoformat(),
    }


def render_form_error(
    request: Request,
    message: str,
) -> HTMLResponse:
    context = page_context()
    context["error"] = message

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
        status_code=400,
    )


# ==================================================
# PÁGINA INICIAL
# ==================================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=page_context(),
    )


# ==================================================
# CÁLCULO DE FRETE PARA O NAVEGADOR
# ==================================================

@app.get("/freight-quote")
def freight_quote(
    city: str,
    street: str,
    number: str,
    neighborhood: str,
    cep: str,
):
    """
    Endpoint chamado pelo app.js quando o cliente clica em Calcular frete.
    Retorna JSON com o frete, a distância e se foi aplicada taxa fixa.
    """

    city = city.strip()
    street = street.strip()
    number = number.strip()
    neighborhood = neighborhood.strip()
    cep_digits = re.sub(r"\D", "", cep)

    if not all([city, street, number, neighborhood]):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Preencha cidade, rua, número e bairro."
            },
        )

    if len(cep_digits) != 8:
        return JSONResponse(
            status_code=400,
            content={"error": "Informe um CEP válido com 8 dígitos."},
        )

    formatted_cep = f"{cep_digits[:5]}-{cep_digits[5:]}"

    try:
        freight, distance_km = calculate_freight(
            city=city,
            street=street,
            number=number,
            neighborhood=neighborhood,
            cep=formatted_cep,
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": str(exc)},
        )

    return {
        "freight": freight,
        "distance_km": distance_km,
        "fixed_rate": city.casefold() == "sarzedo",
    }


# ==================================================
# RECEBIMENTO E VALIDAÇÃO DO PEDIDO
# ==================================================

@app.post("/orders", response_class=HTMLResponse)
def create_order(
    request: Request,
    customer_name: Annotated[str, Form()],
    whatsapp: Annotated[str, Form()],
    recipient_name: Annotated[str, Form()],
    recipient_phone: Annotated[str, Form()],
    delivery_date: Annotated[date, Form()],
    preferred_time: Annotated[str, Form()],
    payment_method: Annotated[str, Form()],
    order_type: Annotated[str, Form()],
    selected_basket: Annotated[str, Form()],
    cep: Annotated[str, Form()],
    city: Annotated[str, Form()],
    neighborhood: Annotated[str, Form()],
    street: Annotated[str, Form()],
    number: Annotated[str, Form()],
    complement: Annotated[str, Form()],
    reference_point: Annotated[str, Form()],
    card_message: Annotated[str, Form()] = "",
    wants_extras: Annotated[str, Form()] = "no",
    selected_extras: Annotated[Optional[list[str]], Form()] = None,
):
    # Limpeza dos dados recebidos
    customer_name = customer_name.strip()
    recipient_name = recipient_name.strip()
    preferred_time = preferred_time.strip()
    payment_method = payment_method.strip()
    card_message = card_message.strip()

    city = city.strip()
    neighborhood = neighborhood.strip()
    street = street.strip()
    number = number.strip()
    complement = complement.strip()
    reference_point = reference_point.strip()

    whatsapp_digits = re.sub(r"\D", "", whatsapp)
    recipient_phone_digits = re.sub(r"\D", "", recipient_phone)
    cep_digits = re.sub(r"\D", "", cep)

    allowed_payments = {
        "Pix",
        "Cartão de débito",
        "Cartão de crédito",
    }

    # Validação do formulário
    error = None

    if not customer_name:
        error = "Informe o nome de quem está fazendo o pedido."
    elif len(whatsapp_digits) not in (10, 11):
        error = "Informe um WhatsApp válido com DDD."
    elif not recipient_name:
        error = "Informe o nome de quem receberá a cesta."
    elif len(recipient_phone_digits) not in (10, 11):
        error = "Informe um telefone válido de quem receberá a cesta."
    elif len(cep_digits) != 8:
        error = "Informe um CEP válido com 8 dígitos."
    elif not city:
        error = "Informe a cidade de entrega."
    elif not neighborhood:
        error = "Informe o bairro de entrega."
    elif not street:
        error = "Informe a rua ou avenida."
    elif not number:
        error = "Informe o número do imóvel."
    elif not complement:
        error = "Informe o complemento do endereço."
    elif not reference_point:
        error = "Informe um ponto de referência."
    elif not preferred_time:
        error = "Informe o horário preferencial para a entrega."
    elif payment_method not in allowed_payments:
        error = "Selecione uma forma de pagamento válida."
    elif not validate_delivery_date(delivery_date):
        error = "Selecione uma data de entrega a partir de amanhã."
    elif order_type != "ready":
        error = "Selecione uma das cestas prontas."
    elif selected_basket not in BASKETS_BY_ID:
        error = "Selecione uma cesta válida."
    elif wants_extras not in {"yes", "no"}:
        error = "Informe se deseja adicionar personalizações."
    elif len(card_message) > 300:
        error = "A mensagem do cartão deve ter no máximo 300 caracteres."

    selected_extras = selected_extras or []

    if not error and wants_extras == "yes":
        if any(
            extra_id not in EXTRAS_BY_ID
            for extra_id in selected_extras
        ):
            error = "Um dos adicionais selecionados é inválido."

    if error:
        return render_form_error(request, error)

    # Seleção da cesta e dos adicionais
    basket = BASKETS_BY_ID[selected_basket]
    chosen_extras = []

    if wants_extras == "yes":
        unique_ids = list(dict.fromkeys(selected_extras))
        chosen_extras = [
            EXTRAS_BY_ID[extra_id]
            for extra_id in unique_ids
        ]

    # Valores calculados no servidor.
    products_total = round(
        basket["price"] + sum(
            extra["price"] for extra in chosen_extras
        ),
        2,
    )

    formatted_cep = f"{cep_digits[:5]}-{cep_digits[5:]}"

    # Recalcula o frete no servidor para não confiar no navegador.
    try:
        freight, distance_km = calculate_freight(
            city=city,
            street=street,
            number=number,
            neighborhood=neighborhood,
            cep=formatted_cep,
        )
    except ValueError as exc:
        return render_form_error(request, str(exc))

    total = round(products_total + freight, 2)

    formatted_whatsapp = format_phone(whatsapp_digits)
    formatted_recipient_phone = format_phone(recipient_phone_digits)

    address_lines = [
        f"Endereço: {street}, {number}",
        f"Complemento: {complement}",
        f"Bairro: {neighborhood}",
        f"Cidade: {city}",
        f"CEP: {formatted_cep}",
        f"Ponto de referência: {reference_point}",
    ]

    # Resumo salvo no banco de dados
    summary_parts = [
        f"Cesta: {basket['name']} ({format_brl(basket['price'])})",
    ]

    summary_parts.extend(
        f"{extra['name']} ({format_brl(extra['price'])})"
        for extra in chosen_extras
    )

    summary_parts.extend([
        f"Quem compra: {customer_name}",
        f"WhatsApp de quem compra: {formatted_whatsapp}",
        f"Quem recebe: {recipient_name}",
        f"Telefone de quem recebe: {formatted_recipient_phone}",
        *address_lines,
        f"Data de entrega: {delivery_date.strftime('%d/%m/%Y')}",
        f"Horário preferencial: {preferred_time}",
        f"Forma de pagamento: {payment_method}",
        f"Mensagem do cartão: {card_message or 'Não informada'}",
        f"Subtotal dos produtos: {format_brl(products_total)}",
        f"Taxa de entrega: {format_brl(freight)}",
        (
            f"Distância de ida: {distance_km:.2f} km"
            if distance_km is not None
            else "Distância: não consultada (taxa fixa de Sarzedo)"
        ),
        f"Total com entrega: {format_brl(total)}",
    ])

    summary = "; ".join(summary_parts)

    # Salva o pedido sem apagar os registros anteriores.
    with SessionLocal() as db:
        order = Order(
            customer_name=customer_name,
            whatsapp=formatted_whatsapp,
            delivery_date=delivery_date,
            items_summary=summary,
            total=total,
            freight=freight,
            distance_km=distance_km,
            cep=formatted_cep,
            city=city,
            neighborhood=neighborhood,
            street=street,
            number=number,
            complement=complement,
            recipient_name=recipient_name,
            recipient_phone=formatted_recipient_phone,
            reference_point=reference_point,
            preferred_time=preferred_time,
            card_message=card_message or None,
            payment_method=payment_method,
        )

        db.add(order)
        db.commit()
        db.refresh(order)
        order_id = order.id

    # Mensagem para encaminhar pelo WhatsApp.
    message_lines = [
        "Olá! Gostaria de confirmar meu pedido no Ateliê de Cestas.",
        f"Número do pedido: {order_id}",
        f"Quem está fazendo o pedido: {customer_name}",
        f"WhatsApp: {formatted_whatsapp}",
        f"Quem recebe: {recipient_name}",
        f"Telefone de quem recebe: {formatted_recipient_phone}",
        f"Cesta: {basket['name']} - {format_brl(basket['price'])}",
    ]

    if chosen_extras:
        message_lines.append("Adicionais:")
        message_lines.extend(
            f"- {extra['name']}: {format_brl(extra['price'])}"
            for extra in chosen_extras
        )
    else:
        message_lines.append("Adicionais: nenhum.")

    message_lines.extend([
        f"Subtotal dos produtos: {format_brl(products_total)}",
        f"Taxa de entrega: {format_brl(freight)}",
        f"Total com entrega: {format_brl(total)}",
        *address_lines,
        f"Data de entrega: {delivery_date.strftime('%d/%m/%Y')}",
        f"Horário preferencial: {preferred_time} (sujeito a confirmação)",
        f"Forma de pagamento preferida: {payment_method}",
        f"Mensagem para o cartão: {card_message or 'Não informada'}",
    ])

    message = "\n".join(message_lines)

    chosen = [
        {
            "id": basket["id"],
            "name": basket["name"],
            "price": basket["price"],
        },
        *[
            {
                "id": extra["id"],
                "name": extra["name"],
                "price": extra["price"],
            }
            for extra in chosen_extras
        ],
    ]

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "order_id": order_id,
            "customer_name": customer_name,
            "whatsapp": formatted_whatsapp,
            "recipient_name": recipient_name,
            "recipient_phone": formatted_recipient_phone,
            "delivery_date": delivery_date.strftime("%d/%m/%Y"),
            "preferred_time": preferred_time,
            "payment_method": payment_method,
            "card_message": card_message,
            "reference_point": reference_point,
            "chosen": chosen,
            "chosen_basket": basket,
            "chosen_extras": chosen_extras,
            "total": f"{total:.2f}".replace(".", ","),
            "products_total": f"{products_total:.2f}".replace(".", ","),
            "freight": f"{freight:.2f}".replace(".", ","),
            "distance_km": distance_km,
            "message": message,
            "address_lines": address_lines,
            "cep": formatted_cep,
            "city": city,
            "neighborhood": neighborhood,
            "street": street,
            "number": number,
            "complement": complement,
            "whatsapp_url": (
                "https://wa.me/553199521841?text=" + quote(message)
            ),
        },
    )
