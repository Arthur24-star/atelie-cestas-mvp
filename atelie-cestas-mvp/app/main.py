from datetime import date, timedelta
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, String, Float, Date, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
engine = create_engine(f"sqlite:///{PROJECT_DIR / 'atelie.db'}",
                       connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


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


Base.metadata.create_all(bind=engine)
app = FastAPI(title="Ateliê de Cestas MVP")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

PRODUCTS = [
    {"id": "caixa", "name": "Caixa de Madeira Pinho", "price": 25.00},
    {"id": "caneca", "name": "Caneca de Cerâmica", "price": 18.00},
    {"id": "biscoitos", "name": "Biscoitos Artesanais 100g", "price": 12.00},
    {"id": "chocolate", "name": "Chocolate Artesanal", "price": 15.00},
]


def validate_delivery_date(value: date, today: date | None = None) -> bool:
    reference = today or date.today()
    return value >= reference + timedelta(days=1)


def calculate_total(selected_ids: list[str]) -> float:
    prices = {p["id"]: p["price"] for p in PRODUCTS}
    return round(sum(prices[item] for item in selected_ids if item in prices), 2)


def page_context():
    return {"products": PRODUCTS, "min_delivery": (date.today() + timedelta(days=1)).isoformat()}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context=page_context())


@app.post("/orders", response_class=HTMLResponse)
def create_order(
    request: Request,
    customer_name: Annotated[str, Form()],
    whatsapp: Annotated[str, Form()],
    delivery_date: Annotated[date, Form()],
    selected_items: Annotated[list[str], Form()] = [],
):
    valid_ids = {p["id"] for p in PRODUCTS}
    selected_items = [item for item in selected_items if item in valid_ids]
    error = None
    if not customer_name.strip():
        error = "Informe o nome do cliente."
    elif not whatsapp.strip():
        error = "Informe o WhatsApp para contato."
    elif not selected_items:
        error = "Selecione pelo menos um insumo."
    elif not validate_delivery_date(delivery_date):
        error = "Selecione uma data de entrega a partir de amanhã."

    if error:
        context = page_context()
        context["error"] = error
        return templates.TemplateResponse(request=request, name="index.html",
                                           context=context, status_code=400)

    chosen = [p for p in PRODUCTS if p["id"] in selected_items]
    total = calculate_total(selected_items)
    summary = ", ".join(f"{p['name']} (R$ {p['price']:.2f})" for p in chosen)
    with SessionLocal() as db:
        order = Order(customer_name=customer_name.strip(), whatsapp=whatsapp.strip(),
                      delivery_date=delivery_date, items_summary=summary, total=total)
        db.add(order)
        db.commit()
        db.refresh(order)
        order_id = order.id

    message = (f"Olá! Gostaria de encomendar uma cesta para {customer_name.strip()}. "
               f"Itens: {summary}. Total: R$ {total:.2f}. "
               f"Entrega: {delivery_date.strftime('%d/%m/%Y')}.")
    return templates.TemplateResponse(
        request=request, name="success.html",
        context={"order_id": order_id, "customer_name": customer_name.strip(),
                 "whatsapp": whatsapp.strip(), "delivery_date": delivery_date.strftime("%d/%m/%Y"),
                 "chosen": chosen, "total": f"{total:.2f}".replace(".", ","),
                 "message": message, "whatsapp_url": "https://wa.me/?text=" + quote(message)}
    )
