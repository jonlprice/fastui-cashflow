from __future__ import annotations as _annotations

from fastapi import APIRouter

import matplotlib.pyplot as plt
import mpld3
import matplotlib.colors
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase
from fastapi.templating import Jinja2Templates
import datetime as dt
import matplotlib
import numpy as np
import locale
import pandas as pd
import yfinance as yf
import logging
from dateutil.relativedelta import relativedelta

locale.setlocale(locale.LC_ALL, '')
matplotlib.use("AGG")

class Base(DeclarativeBase):
    pass

class Income(BaseModel):
    yearly: float
    cpi: int
    years_in: int
    repeating_years: int
    label: str
    amount: list[float]

class Pot(BaseModel):
    label: str
    start: int
    yearly_limit: int
    amount: list[float]
    spent: list[float]

    def __str__(self) -> str:
        return f"{self.label} {self.start} {self.yearly_limit} {self.amount}"

    def __repr__(self) -> str:
        return f"{self.label} {self.start} {self.yearly_limit} {self.amount}"

    def __lt__(self, other):
        return self.amount < other.amount

class Stock:
    def __init__(
        self,
        start = "1970",
        end = "2023"
    ):
        self.df = pd.DataFrame([])
        self.start = str(start)
        self.end = str(end)
        self.data_populated = False
        self.ticker = ""

    def __str__(self) -> str:
        return f"{self.start} {self.end} {self.df}"

    def __repr__(self) -> str:
        return f"{self.start} {self.end} {self.df}"

    def get_data(self):

        if self.data_populated:
            return
        # tickers = ["^GSPC", "^FTSE", "^RUT", "^FCHI", "^GDAXI"]
        #tickers = ["^GSPC"]
        tickers = ["^GSPC","^FTSE"]
        logger.info(f"Looking up returns data for {tickers}")

        startyear = str(self.start)
        endyear = str(self.end)

        start = str(startyear) + "-01-01"
        end = str(endyear) + "-01-01"

        self.data = yf.download(tickers, start=start, end=end,
                   group_by="ticker")

        print(self.data)

        self.data_populated = True

    def get_yearly_returns(self,start,years,ticker):

        logger.info(f"Returning data for {ticker},{start},{years}")
        self.ticker = ticker

        df = pd.DataFrame(self.data[ticker]['Close'])

        df['date'] = df.index

        # Extract year to group by
        df['year'] = df['date'].dt.year
        #df['year'] = df.index.year

        # Find the last day of each year
        df_last_day_of_year = df.groupby('year').agg(date=('date', 'max')).reset_index()

        resultdf = pd.merge(df_last_day_of_year, df[['Close','date']], on="date")

        resultdf['growth'] = resultdf['Close'].ffill().pct_change()
        resultdf['growth'] = resultdf['growth'] + 1

        df = resultdf[['year','growth']]


        d = df[(df.year >= int(start)) & (df.year < int(start)+int(years))]
        return d['growth'].to_numpy()


    def get_ticker(self):
        return self.ticker


###########################################################################

logger = logging.getLogger('cashflow')

router = APIRouter()

templates = Jinja2Templates(directory="templates")

stock_returns = Stock()
logger.info(stock_returns)

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
          border-collapse: collapse;
        }
        caption {
          color: blue;
          font-family:Arial, Helvetica, sans-serif;
          border-top: 1px solid black;
          border-left: 1px solid black;
          border-right: 1px solid black;
          padding: 0.5em;
          background: white;
          text-align: left;
          white-space: nowrap;
        }
        td {
          padding-top: 0.1em;
          padding-bottom: 0.1em;
          padding-left: 0.5em;
          padding-right: 0.5em;
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
        td.labeltotal {
          border-top: 1px solid black;
          color: black;
          font-weight: bold;
          text-align: left;
        }
        td.total {
          border-top: 1px solid black;
          font-weight: bold;
        }
        tr.parameters td {
          border-bottom: 1px solid black;
        }
    """
    return css

def pot_bar_hover_table(year,pot_start_date,age,pots,growth,inflation):

    total = 0

    pot_html = ""
    for p in pots:
        pot_html = pot_html + f"<tr><td class=label>{p.label}:</td><td>£" \
            + f"{p.amount[year]:,.0f}" \
            + "<td/></tr>"
        total = total + p.amount[year]

    growthclass="positive"
    if growth < 1:
        growthclass="negative"

    table_html = "<table><caption>" \
            + "<span class = label>Savings, Age:</span> " \
            + f"{age}, " \
            + "<span class = label>Year:</span> " \
            + f"{year+1}, {pot_start_date.year+year}" \
            + "</caption>" \
            + f"<tr><td class=label>Growth:</td><td class={growthclass}>" \
            + f"{stock_returns.ticker.replace('^','')} {((growth - 1)*100):,.2f}%" \
            + "<td/></tr>" \
            + "<tr class=parameters><td class=label>Inflation:</td><td>" \
            + f"{inflation:,.2f}%" \
            + "<td/></tr>" \
            + pot_html \
            + "<tr><td class=labeltotal>Total:</td><td class=total>" \
            + f"£{total:,.0f}" \
            + "<td/></tr>" \
            + "</table>"

    return table_html

def spend_bar_hover_table(year,pot_start_date,age,pots,incomes,drawdown):


    spent_html = ""
    for p in pots:
        spent_html = spent_html + f"<tr><td class=label>{p.label}:</td><td>£" \
            + f"{p.spent[year]:,.0f}" \
            + "<td/></tr>"

    income_html = ""

    income_total = 0

    for i in incomes:
        income_html = income_html + f"<tr><td class=label>{i.label}:</td><td>£" \
            + f"{i.amount[year]:,.0f}" \
            + "<td/></tr>"
        income_total = income_total + i.amount[year]
    income_total = income_total + drawdown

    table_html = "<table><caption>" \
            + "<span class = label>Income, Age:</span> " \
            + f"{age}, " \
            + "<span class = label>Year:</span> " \
            + f"{year+1}, {pot_start_date.year+year}" \
            + "</caption>" \
            + income_html \
            + spent_html \
            + "<tr><td class=labeltotal>Total:</td><td class=total>" \
            + f"£{income_total:,.0f}" \
            + "<td/></tr>" \
            + "</table>"

    return table_html


def withdraw(available, request):
    w = 0
    if available >= request:
        w = request
    elif available > 0:
        w = available
    else:
        w = 0
    return w

def cashflow_plot(potparams, incomeparams, params):
    # create data

    years = params.years
    ticker = params.ticker
    growth = params.growth
    inflation = params.inflation
    charges = params.charges
    age_now = params.age
    retire = params.retirement_age
    historical_start_year = params.historical_start_year

    house_price = 500000
    h = [house_price := house_price * (1.03) for year in range(years)]

    # growth_profile = [(100 + random.randrange(-20, 20)) / 100
    #                         for years in range(years)]
    if growth > 0:
        growth_profile = [((100 + growth) / 100) for year in range(years)]
    else:
        stock_returns.get_data()
        growth_profile = stock_returns.get_yearly_returns(start=historical_start_year,
                                                          ticker=ticker, years=years)

    age = [retire + year for year in range(years)]

    cpi = inflation / 100
    incomes = []

    pot_start_date = dt.datetime.now().date() + relativedelta(years=(retire-age_now))
    logger.info(f"age now {age_now}, retirement start {retire}, pot_start_date {pot_start_date}")

    for y in range(4):
        yearly = incomeparams[y].amount
        # delta_date = incomeparams[y].start_date - dt.datetime.now().date()
        delta_date = incomeparams[y].start_date - pot_start_date
        years_in = round(delta_date.days/365)

        incomes.append(Income( yearly=yearly,cpi = inflation, years_in = years_in,
                repeating_years = 0, label=incomeparams[y].name + ' ' + incomeparams[y].type,
                amount=[(yearly + (yearly * (( (1 + cpi)**year) - 1 )))
                               if year > years_in
                               else 0 for year in range(years)]))

        logger.info(str(years_in) + ' ' + incomeparams[y].name + ' ' + incomeparams[y].type)

    pots = []

    for y in range(4):

        pen = Pot(label = potparams[y].name, start=potparams[y].amount,
                  yearly_limit = 0,
                  amount=[potparams[y].amount for year in range(years)],
                  spent=[0 for year in range(years)])

        if pen.start > 100000:
            pen.yearly_limit = 1000000
        else:
            pen.yearly_limit = 12750

        pots.append(pen)

    # Sort pots to take from the smallest one first
    pots.sort()

    plt.close()
    fig1 = plt.figure(figsize=(12, 4))
    ax1 = fig1.add_subplot()

    fig2 = plt.figure(figsize=(12, 4))
    ax3 = fig2.add_subplot()

    plt.subplots(layout='compressed')

    '''
    # Calculate yearly income with inflation
    ======================================================================
    '''

    np_total_income = np.array([0 for year in range(years)])
    #         i = inflation / 100
    # compound interest  p * (( (1 + i)**n) - 1 )
    # where p princpal, i interest, n periods
    np_required_income = np.array([(params.target_income +
                                    (params.target_income *
                                     (( (1+cpi)**year) -1 )))
                                   for year in range(years)])

    for income in incomes:
        np_total_income = np.add(np_total_income,np.array(income.amount))

    drawdown_pot = np.subtract(np_required_income,np_total_income)

    required_spend = drawdown_pot
    np_required_spend = np.array(required_spend)

    '''
    # Calculate yearly drawdown
    ======================================================================
    '''
    for y in range(years-1):
        spent = 0

        for p in pots:
            if p.amount[y] > 0:
                if drawdown_pot[y] > p.yearly_limit:
                    spent = withdraw(p.amount[y], p.yearly_limit)
                else:
                    spent = withdraw(p.amount[y], drawdown_pot[y])

            p.amount[y+1] = p.amount[y] - spent
            p.amount[y+1] = p.amount[y+1] * growth_profile[y]
            p.amount[y+1] = p.amount[y+1] - ((charges/100)*p.amount[y+1])
            drawdown_pot[y] = drawdown_pot[y] - spent
            p.spent[y] = spent

    np_pots = []
    for p in pots:
        np_pots.append(np.array(p.amount))

    np.array(age)
    np.array(h)
    np_drawdown_pot = np.array(drawdown_pot)

    np_drawn_down = np.subtract(np_required_spend,np_drawdown_pot)

    logger.debug("np_required_income", np_required_income)
    logger.debug("np_drawdown_pot", np_drawdown_pot)
    logger.debug("np_drawn_down", np_drawn_down)
    logger.debug("np_total_income", np_total_income)

    '''
    # Plot Cashflow
    ======================================================================
    '''

    boxes = []
    bars = []

    # See https://colorbrewer2.org/#type=qualitative&scheme=Accent&n=7
    bar_colours = ['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00','#cab2d6','#6a3d9a']

    for c, p in enumerate(np_pots):
        box = ax1.bar(age,p, bottom=sum(bars),color=bar_colours[c])
        boxes.append(box)
        bars.append(p)

    legend_labels = []
    for p in pots:
        legend_labels.append(p.label)

    font = {'family': 'serif',
        'color':  'darkred',
        'weight': 'normal',
        'size': 16,
        }

    ax1.set_title('Cash Flow', fontdict=font)
    ax1.set_xlabel('Age', fontdict=font)
    ax1.set_ylabel('Pounds £', labelpad=20, fontdict=font)
    ax1.set_xticks(age)
    ax1.grid(False)
    ax1.legend(legend_labels)

    matplotlib.rcParams['axes.edgecolor'] = '#ff0000'

    css = get_css()

    labels = []
    for i, box in enumerate(boxes[0].get_children()):
        labels.append(pot_bar_hover_table(i,pot_start_date,age[i],pots,
                                      growth_profile[i],inflation))

    for b in boxes:
        for i, box in enumerate(b.get_children()):
            tooltip = mpld3.plugins.LineHTMLTooltip(box,label=labels[i],css=css)
            mpld3.plugins.connect(fig1, tooltip)

    '''
    # Plot Spend
    ======================================================================
    '''
    bars = []
    boxes = []
    legend_labels = []

    bar_count=0
    for i, income in enumerate(incomes):
        np_income = np.array(income.amount)
        box = ax3.bar(age,np_income, bottom=sum(bars),color=bar_colours[i])
        boxes.append(box)
        bars.append(np_income)
        legend_labels.append(income.label)
        bar_count=i

    for i, pot in enumerate(pots):
        np_pot = np.array(pot.spent)
        box = ax3.bar(age,np_pot, bottom=sum(bars),color=bar_colours[i+bar_count])
        boxes.append(box)
        bars.append(np_pot)
        legend_labels.append(pot.label)

    labels = []
    for i, box in enumerate(boxes[0].get_children()):
        labels.append(spend_bar_hover_table(i,pot_start_date,age[i],pots,
                                      incomes,np_drawn_down[i]))

    for b in boxes:
        for i, box in enumerate(b.get_children()):
            tooltip = mpld3.plugins.LineHTMLTooltip(box,label=labels[i],css=css)
            mpld3.plugins.connect(fig2, tooltip)

    ax3.set_title('Spend', fontdict=font)
    ax3.set_xlabel('Age', fontdict=font)
    ax3.set_ylabel('Pounds £', labelpad=10, fontdict=font)
    ax3.set_xticks(age)
    ax3.grid(False)
    ax3.legend(legend_labels)

    htmlpot = mpld3.fig_to_html(fig1)
    htmlspend = mpld3.fig_to_html(fig2)

    html = htmlpot + htmlspend

    return html
