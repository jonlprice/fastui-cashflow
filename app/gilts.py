from __future__ import annotations as _annotations

from fastapi import APIRouter, Request
from fastui import FastUI

import matplotlib.pyplot as plt
import base64
import mpld3
import matplotlib.colors
from app.env import DB
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy import Numeric, create_engine, Column, Integer, String, Date, Float
from sqlalchemy import update
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import matplotlib
import numpy as np
import locale
import pandas as pd
import requests
from io import StringIO
import yfinance as yf
import logging

locale.setlocale(locale.LC_ALL, '')
matplotlib.use("AGG")

class Base(DeclarativeBase):
    pass

class PyGilt(BaseModel):
    gilt_id: int
    close_of_business_date: datetime
    instrument_type: str
    maturity_bracket: str
    instrument_name: str
    isin_code: str
    ticker: str
    redemption_date: datetime
    first_issue_date: datetime
    dividend_dates: str
    current_ex_div_date: datetime
    total_amount_in_issue: float
    total_amount_including_il_uplift: float
    coupon: float
    days_to_redemption: int
    years_to_redemption: float
    clean_price: float
    dirty_price: float
    tradeweb_yield: float
    calculated_yield: float


class Gilt(Base):
    __tablename__ = "gilts"
    gilt_id = Column(Integer, primary_key=True)
    close_of_business_date = Column(Date)
    instrument_type = Column(String)
    maturity_bracket = Column(String)
    instrument_name = Column(String)
    isin_code = Column(String)
    ticker = Column(String)
    redemption_date = Column(Date)
    first_issue_date = Column(Date)
    dividend_dates = Column(String)
    current_ex_div_date = Column(Date)
    total_amount_in_issue = Column(Float)
    total_amount_including_il_uplift = Column(Float)
    coupon = Column(Float)
    days_to_redemption = Column(Integer)
    years_to_redemption = Column(Float)
    clean_price = Column(Float)
    dirty_price = Column(Numeric(6, 2))
    tradeweb_yield = Column(Numeric(6, 2))
    calculated_yield = Column(Numeric(6, 2))

    def __str__(self) -> str:
        return f"{self.gilt_id} {self.instrument_name} {self.clean_price}"

    def __repr__(self) -> str:
        return f"{self.gilt_id} {self.instrument_name} {self.clean_price}"


logger = logging.getLogger('cashflow')
db = DB()
router = APIRouter()

# app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_css():
    css = """
        table {
          width: 250px;
          color: blue;
          font-family:Arial, Helvetica, sans-serif;
          border: 1px solid black;
          text-align: right;
          padding: 0.5em;
          background: white;
        }
        caption {
          color: blue;
          font-family:Arial, Helvetica, sans-serif;
          border-top: 1px solid black;
          border-left: 1px solid black;
          border-right: 1px solid black;
          padding: 0.5em;
          background: white;
          text-align: center;
          white-space: nowrap;
        }
        td.label {
          color: black;
          text-align: left;
        }
        td.negative {
          color: red;
        }
        .label {
          color: black;
          text-align: left;
        }
        td.spendlabel {
          border-top: 1px solid black;
          color: black;
          text-align: left;
        }
        td.spenddata {
          border-top: 1px solid black;
        }
    """
    return css

def last_refresh() -> datetime:

    last_refresh_time = datetime.now()

    engine = create_engine(db.get_connection_string())
    # Session = sessionmaker(bind=engine)
    # session = Session()

    t = text('select close_of_business_date from gilts \
            order by close_of_business_date desc limit 1')

    connection = engine.connect()
    rs = connection.execute(t)

    for row in rs:
        last_refresh_time = row.close_of_business_date

    return last_refresh_time

def hover_table(ticker,instrument_name,clean_price,
                calculated_yield,coupon,redemption_date):

    table_html = "<table><caption>" \
            + str(ticker) \
            + ": " \
            + str(instrument_name) \
            + "</caption>" \
            + "<tr><td class=label>Price:</td><td>£" \
            + str(clean_price) \
            + "<td/></tr>" \
            "<tr><td class=label>Yield:</td><td>" \
            + str(calculated_yield) \
            + "%<td/></tr>" \
            + "<tr><td class=label>Coupon:</td><td>" \
            + str(coupon) \
            + "%</td></tr>" \
            + "<tr><td class=label>End:</td><td>" \
            + str(redemption_date) \
            + "</td></tr>" \
            + "</table>"

    return table_html


def create_image():
    x = []
    y = []
    area = []
    colour = []
    edgecolors = []
    labels = []
    alpha = []
    clean_price = []

    gilts = generate_image_data()

    owned = ("TG24", "T25", "T27A", "TR25")

    for g in gilts:
        x.append(g.years_to_redemption)
        y.append(g.calculated_yield)
        clean_price.append(g.clean_price)
        area.append((g.coupon / 6) * 300)
        if g.clean_price > 100:
            face = "#ff7f0e"  # orange

        else:
            face = "#1f77b4"  # light blue
        colour.append(face)  # orange

        if g.ticker in owned:
            alpha.append(0.9)
            edgecolors.append("black")
        else:
            alpha.append(0.5)
            edgecolors.append(face)

        redemption_date = f"{g.redemption_date.strftime('%d %b %Y')}"

        labels.append(hover_table(g.ticker,g.instrument_name,g.clean_price,
                                  g.calculated_yield,g.coupon,redemption_date)
        )

    css = get_css()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.grid(which="major", linestyle="dashed")
    scatter = ax.scatter(
        x, y, s=area, c=colour, edgecolors=edgecolors, alpha=alpha, label=colour
    )

    ax.set_xlabel("Years to maturity", fontsize=16)
    ax.set_ylabel("Yield", fontsize=16)
    ax.set_title("Yield Curve", fontsize=20)

    plt.style.use("seaborn-v0_8")

    legend_elements = [
        plt.scatter([], [], c="#ff7f0e", alpha=0.5,
                    s=150, label="Greater than £100"),
        plt.scatter([], [], c="#1f77b4", alpha=0.5,
                    s=150, label="Less than or equal to £100"),
        plt.scatter([], [], c="#ff7f0e", alpha=0.9,
                    s=150, label="Greater than £100, in HL", edgecolors='black'),
        plt.scatter([], [], c="#1f77b4", alpha=0.9,
                    s=150, label="Less than or equal to £100, in HL", edgecolors='black'
        ),
    ]

    legend = ax.legend(
        bbox_to_anchor=(1.5, 1.0),
        scatterpoints=1,
        handles=legend_elements,
        loc="upper right",
        borderpad=0.8,
        framealpha=1,
        facecolor="#eaeaf2",
        shadow=True,
        alignment="left",
    )

    legend.set_title("Price", prop={"size": 14})

    tooltip = mpld3.plugins.PointHTMLTooltip(
        scatter, labels=labels, hoffset=20, voffset=20, css=css
    )

    mpld3.plugins.connect(fig, tooltip)

    html = mpld3.fig_to_html(fig)

    with open("static/temp.html", "w") as text_file:
        text_file.write(html)

    return html


def generate_image_data():
    plt.rcParams["figure.autolayout"] = True

    engine = create_engine(db.get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    gilts = (
        session.query(Gilt)
        .with_entities(
            Gilt.instrument_name,
            Gilt.ticker,
            Gilt.redemption_date,
            Gilt.years_to_redemption,
            Gilt.calculated_yield,
            Gilt.coupon,
            Gilt.clean_price,
        )
        .filter(Gilt.instrument_type.contains("%Conventional%"))
        .all()
    )
    return gilts


@router.get("/home", response_class=HTMLResponse)
async def get_img(request: Request, background_tasks: BackgroundTasks):
    html = create_image()

    # b = base64.b64encode(bytes(html, 'utf-8')) # bytes
    encoded = base64.b64encode(html.encode())
    encoded_html = encoded.decode()

    last_refresh_time = last_refresh().strftime('%A, %d %b %Y')

    return templates.TemplateResponse(
            "image.html", {"request": request, "img": encoded_html,
                           "last_refresh": last_refresh_time}
    )


def read_gilts():
    engine = create_engine(db.get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    gilts = (
        session.query(Gilt)
        .with_entities(
            Gilt.gilt_id,
            Gilt.close_of_business_date,
            Gilt.instrument_type,
            Gilt.maturity_bracket,
            Gilt.instrument_name,
            Gilt.isin_code,
            Gilt.ticker,
            Gilt.redemption_date,
            Gilt.first_issue_date,
            Gilt.dividend_dates,
            Gilt.current_ex_div_date,
            Gilt.total_amount_in_issue,
            Gilt.total_amount_including_il_uplift,
            Gilt.coupon,
            Gilt.days_to_redemption,
            Gilt.years_to_redemption,
            Gilt.clean_price,
            Gilt.dirty_price,
            Gilt.tradeweb_yield,
            Gilt.calculated_yield,
        )
        .order_by(Gilt.coupon.desc())
        .all()
    )

    return gilts

def lookup_prices():


    hl_url = 'https://www.hl.co.uk/shares/corporate-bonds-gilts/bond-prices/uk-gilts'

    r = requests.get(hl_url)

    logger.info(f"Looking up prices at {hl_url}")

    df = pd.read_html(StringIO(r.content.decode()))[0]

    issuer_df = df['Issuer'].str.split("|",expand=True)
    issuer_df.columns =['Name', 'ISIN', 'Code']

    isin_df = issuer_df[['ISIN']].copy()
    price_df = df[['Price']].copy()

    newdf = price_df.join(isin_df['ISIN'])
    newdf['ISIN'] = newdf['ISIN'].apply(lambda x: x.replace(' ', ''))

    gilts = {}
    for index, row in newdf.iterrows():
        gilts[row['ISIN']] =  row['Price']

    return gilts


@router.get("/update", response_model=FastUI, response_model_exclude_none=True)
async def update_gilt_prices(request: Request, skip: int = 0, limit: int = 100):
    engine = create_engine(db.get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    dbgilts = (
        session.query(Gilt)
        .with_entities(
            Gilt.gilt_id,
            Gilt.isin_code
        )
        .filter(Gilt.instrument_type.contains("%Conventional%"))
        .order_by(Gilt.coupon.desc())
        .all()
    )

    prices = lookup_prices()

    # Get Yesterday
    yesterday = datetime.now() - timedelta(1)
    close_of_business_date = yesterday.strftime('%Y-%m-%d')

    gilts = []
    for g in dbgilts:
        if g.isin_code in prices:
            gilts.append({"gilt_id": g.gilt_id,
                          "close_of_business_date": close_of_business_date,
                          "clean_price": prices[g.isin_code]})

    result = session.execute(
        update(Gilt),
        gilts,
    )
    session.commit()

    for row in result:
        logger.info(f"{row}")

    last_refresh_time = last_refresh().strftime('%A, %d %b %Y')

    return [
            { "text": f"Last time prices refreshed: {last_refresh_time}",
         "type": "Paragraph" }
            ]


@router.get("/gilts/{gilt_id}", response_class=HTMLResponse)
async def read_gilt(request: Request, gilt_id: int):
    engine = create_engine(db.get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    gilt = session.query(Gilt).get(gilt_id)

    return templates.TemplateResponse("gilt.html", {"request": request, "gilt": gilt})


@router.post("/gilts")
async def create_gilt(gilt: PyGilt):
    engine = create_engine(db.get_connection_string())

    with Session(engine) as session:
        g = Gilt(
            close_of_business_date=gilt.close_of_business_date,
            instrument_name=gilt.instrument_name,
            instrument_type=gilt.instrument_type,
            maturity_bracket=gilt.maturity_bracket,
            isin_code=gilt.isin_code,
            ticker=gilt.ticker,
            redemption_date=gilt.redemption_date,
            dividend_dates=gilt.dividend_dates,
            current_ex_div_date=gilt.current_ex_div_date,
            total_amount_in_issue=gilt.total_amount_in_issue,
            total_amount_including_il_uplift=gilt.total_amount_including_il_uplift,
            first_issue_date=gilt.first_issue_date,
            coupon=gilt.coupon,
            days_to_redemption=gilt.days_to_redemption,
            years_to_redemption=gilt.years_to_redemption,
            clean_price=gilt.clean_price,
            dirty_price=gilt.dirty_price,
            tradeweb_yield=gilt.tradeweb_yield,
            calculated_yield=gilt.calculated_yield,
        )

    session.add_all([g])
    session.commit()
    return gilt





