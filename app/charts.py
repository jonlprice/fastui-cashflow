from __future__ import annotations as _annotations


from fastapi.responses import HTMLResponse
from fastapi import APIRouter

from .gilts import create_image
from .cashflow import cashflow_plot
from .forms import PotModel, PotEnum, IncomeModel, ParametersModel
from .dao import read_pot, read_income, read_parameters
import logging

logger = logging.getLogger('cashflow')
router = APIRouter()

@router.get('/cashflow')
async def charts_cashflow_landing() -> HTMLResponse:

    pots = []
    for i in range(1,5):
        db = read_pot(i)
        p = PotModel(pot_id=db.pot_id,name=db.name, type=db.type, amount=db.amount, select_single = PotEnum('isa'))
        pots.append(p)

    incomes = []
    for i in range(1,5):
        dbi = read_income(i)
        income = IncomeModel(income_id=dbi.income_id,name=dbi.name, type=dbi.type, amount=dbi.amount,
                    inflation_yearly=True, repeating_yearly=True, start_date = dbi.start_date)
        incomes.append(income)


    cashflow_id = 1
    pm = read_parameters(cashflow_id)

    params = ParametersModel(target_income=pm.target_income, inflation=pm.inflation,growth=pm.growth,
                             age=pm.age, retirement_age=pm.retirement_age,
                             charges=pm.charges,historical_start_year=pm.historical_start_year,years=pm.years,ticker=pm.ticker)


    html = cashflow_plot(pots, incomes,params)

    return HTMLResponse(html)

@router.get('/gilts')
async def charts_gilts_landing() -> HTMLResponse:
    html=create_image()
    return HTMLResponse(html)

