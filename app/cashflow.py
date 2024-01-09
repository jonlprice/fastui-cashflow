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
        tickers = ["^GSPC"]
        logger.info("Looking up returns data for",tickers)

        startyear = str(self.start)
        endyear = str(self.end)

        start = str(startyear) + "-01-01"
        end = str(endyear) + "-01-01"

        self.data = yf.download(tickers, start=start, end=end,
                   group_by="ticker")

        self.data_populated = True

    def get_yearly_returns(self,start,years,ticker):

        logger.info("Returning data for",ticker,start,years)
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
stock_returns = Stock()
stock_returns.get_data()

router = APIRouter()

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

def bar_hover_table(year,age,pensions,growth,inflation,incomes,drawdown):

    total = 0

    pension_html = ""
    for p in pensions:
        pension_html = pension_html + f"<tr><td class=label>{p.label}:</td><td>£" \
            + f"{p.amount[year]:,.0f}" \
            + "<td/></tr>"
        total = total + p.amount[year]
    income_html = ""

    income_total = 0

    for i in incomes:
        income_html = income_html + f"<tr><td class=label>{i.label}:</td><td>£" \
            + f"{i.amount[year]:,.0f}" \
            + "<td/></tr>"
        income_total = income_total + i.amount[year]
    income_total = income_total + drawdown

    growthclass="positive"
    if growth < 1:
        growthclass="negative"

    table_html = "<table><caption>" \
            + "<span class = label>Age:</span> " \
            + f"{age}" \
            + " <span class = label>Total:</span> £" \
            + f"{total:,.0f}" \
            + "</caption>" \
            + "<tr><td class=label>Year:</td><td>" \
            + f"{year + 1:,.0f}" \
            + "<td/></tr>" \
            + f"<tr><td class=label>Growth:</td><td class={growthclass}>" \
            + f"{stock_returns.ticker.replace('^','')} {((growth - 1)*100):,.2f}%" \
            + "<td/></tr>" \
            + "<tr><td class=label>Inflation:</td><td>" \
            + f"{inflation:,.2f}%" \
            + "<td/></tr>" \
            + pension_html \
            + "</table>" \
            + "<table><caption>" \
            + "<span class = label>Age:</span> " \
            + f"{age}" \
            + " <span class = label>Spend:</span> £" \
            + f"{income_total:,.0f}" \
            + "</caption>" \
            + income_html \
            + "<tr><td class=label>Drawdown:</td><td>£" \
            + f"{drawdown:,.0f}" \
            + "</td></tr>" \
            + "</table>"

    return table_html


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

def cashflow_plot(pensionparams, incomeparams, params):
    # create data

    years = params.years
    ticker = params.ticker
    growth = params.growth
    inflation = params.inflation
    charges = params.charges
    age_now = params.age
    retire = params.retirement_age
    historic_start_year = 1990

    house_price = 500000
    h = [house_price := house_price * (1.03) for year in range(years)]

    # growth_profile = [(100 + random.randrange(-20, 20)) / 100
    #                         for years in range(years)]
    if growth > 0:
        growth_profile = [((100 + growth) / 100) for year in range(years)]
    else:
        growth_profile = stock_returns.get_yearly_returns(start=historic_start_year,
                                                          ticker=ticker, years=years)

    age = [retire + year for year in range(years)]

    cpi = inflation / 100
    incomes = []

    pension_start_date = dt.datetime.now().date() + relativedelta(years=(retire-age_now))
    logger.info(f"age now {age_now}, pension start {retire}, pension_start_date {pension_start_date}")

    for y in range(4):
        yearly = incomeparams[y].amount
        # delta_date = incomeparams[y].start_date - dt.datetime.now().date()
        delta_date = incomeparams[y].start_date - pension_start_date
        years_in = round(delta_date.days/365)

        incomes.append(Income( yearly=yearly,cpi = inflation, years_in = years_in,
                repeating_years = 0, label=incomeparams[y].name + ' ' + incomeparams[y].type,
                amount=[(yearly + (yearly * (( (1 + cpi)**year) - 1 )))
                               if year > years_in
                               else 0 for year in range(years)]))

        logger.info(str(years_in) + ' ' + incomeparams[y].name + ' ' + incomeparams[y].type)

    pensions = []

    for y in range(4):

        pen = Pot(label = pensionparams[y].name, start=pensionparams[y].amount,
                  yearly_limit = 0,
                  amount=[pensionparams[y].amount for year in range(years)])

        if pen.start > 100000:
            pen.yearly_limit = 1000000
        else:
            pen.yearly_limit = 12750

        pensions.append(pen)

    # Sort pensions to take from the smallest one first
    pensions.sort()

    plt.close()
    fig = plt.figure(figsize=(12, 6))
    ax1 = fig.add_subplot(211)
    ax3 = fig.add_subplot(212)
    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9,
                        wspace=0.2, hspace=0.4)

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

        for p in pensions:
            if p.amount[y] > 0:
                if drawdown_pot[y] > p.yearly_limit:
                    spent = withdraw(p.amount[y], p.yearly_limit)
                else:
                    spent = withdraw(p.amount[y], drawdown_pot[y])

            p.amount[y+1] = p.amount[y] - spent
            p.amount[y+1] = p.amount[y+1] * growth_profile[y]
            p.amount[y+1] = p.amount[y+1] - ((charges/100)*p.amount[y+1])
            drawdown_pot[y] = drawdown_pot[y] - spent

    np_pensions = []
    for p in pensions:
        np_pensions.append(np.array(p.amount))

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
    bar_colours = ['#a6cee3','#1f78b4','#b2df8a','#33a02c',
                   '#fb9a99','#e31a1c','#fdbf6f']

    for c, p in enumerate(np_pensions):
        box = ax1.bar(age,p, bottom=sum(bars),color=bar_colours[c])
        boxes.append(box)
        bars.append(p)

    legend_labels = []
    for p in pensions:
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
        labels.append(bar_hover_table(i,age[i],pensions,
                                      growth_profile[i],inflation,incomes,np_drawn_down[i]))

    for b in boxes:
        for i, box in enumerate(b.get_children()):
            tooltip = mpld3.plugins.LineHTMLTooltip(box,label=labels[i],css=css)
            mpld3.plugins.connect(fig, tooltip)

    '''
    # Plot Spend
    ======================================================================
    '''
    bars = []
    boxes = []
    legend_labels = []

    for i, income in enumerate(incomes):
        np_income = np.array(income.amount)
        box = ax3.bar(age,np_income, bottom=sum(bars),color=bar_colours[i])
        boxes.append(box)
        bars.append(np_income)
        legend_labels.append(income.label)

    box = ax3.bar(age,np_drawn_down, bottom=sum(bars),color=bar_colours[5])
    boxes.append(box)
    legend_labels.append('Drawdown')

    ax3.set_title('Spend', fontdict=font)
    ax3.set_xlabel('Age', fontdict=font)
    ax3.set_ylabel('Pounds £', labelpad=10, fontdict=font)
    ax3.set_xticks(age)
    ax3.grid(False)
    ax3.legend(legend_labels)

    html = mpld3.fig_to_html(fig)

    return html
