from __future__ import annotations as _annotations

import enum
import re
from collections import defaultdict
from datetime import date
from typing import Annotated, Literal, TypeAlias
from dataclasses import dataclass

from fastapi import APIRouter, Request, UploadFile
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.events import GoToEvent, PageEvent
from fastui.forms import FormFile, SelectSearchResponse, fastui_form
from httpx import AsyncClient
from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator
from pydantic_core import PydanticCustomError

from .shared import demo_page
from .dao import read_pot, update_pot, read_income, update_income, read_parameters, update_parameters
from .env import ENV
import logging


# See  https://martinheinz.dev/blog/78
@dataclass
class RegexEqual(str):
    string: str
    match: re.Match = None

    def __eq__(self, pattern):
        self.match = re.search(pattern, self.string)
        return self.match is not None

    def __getitem__(self, group):
        return self.match[group]


env = ENV()

logger = logging.getLogger('cashflow')
router = APIRouter()

@router.get('/search', response_model=SelectSearchResponse)
async def search_view(request: Request, q: str) -> SelectSearchResponse:
    path_ends = f'name/{q}' if q else 'all'
    client: AsyncClient = request.app.state.httpx_client
    r = await client.get(f'https://restcountries.com/v3.1/{path_ends}')
    if r.status_code == 404:
        options = []
    else:
        r.raise_for_status()
        data = r.json()
        if path_ends == 'all':
            # if we got all, filter to the 20 most populous countries
            data.sort(key=lambda x: x['population'], reverse=True)
            data = data[0:20]
            data.sort(key=lambda x: x['name']['common'])

        regions = defaultdict(list)
        for co in data:
            regions[co['region']].append({'value': co['cca3'], 'label': co['name']['common']})
        options = [{'label': k, 'options': v} for k, v in regions.items()]
    return SelectSearchResponse(options=options)


FormKind: TypeAlias = Literal['login', 'select', 'big', 'pot1','pot2','pot3','pot4','pot5', 'income1','income2','income3','income4','cashflow','parameters']


@router.get('/{kind}', response_model=FastUI, response_model_exclude_none=True)
def forms_view(kind: FormKind) -> list[AnyComponent]:
    #links=[]

    pot_names=env.cashflow_tabs
    income_names=env.cashflow_incomes

    links=[
                c.Link(
                    components=[c.Text(text='Chart')],
                    on_click=PageEvent(name='change-form', push_path='/forms/cashflow', context={'kind': 'cashflow'}),
                    active='/forms/cashflow',
                )]
    links.append(
                c.Link(
                    components=[c.Text(text=pot_names[0])],
                    on_click=PageEvent(name='change-form', push_path='/forms/pot1', context={'kind': 'pot1'}),
                    active='/forms/pot1',
                ))
    links.append(
                c.Link(
                    components=[c.Text(text=pot_names[1])],
                    on_click=PageEvent(name='change-form', push_path='/forms/pot2', context={'kind': 'pot2'}),
                    active='/forms/pot2',
                ))
    links.append(
                c.Link(
                    components=[c.Text(text=pot_names[2])],
                    on_click=PageEvent(name='change-form', push_path='/forms/pot3', context={'kind': 'pot3'}),
                    active='/forms/pot3',
                ))
    links.append(
                c.Link(
                    components=[c.Text(text=pot_names[3])],
                    on_click=PageEvent(name='change-form', push_path='/forms/pot4', context={'kind': 'pot4'}),
                    active='/forms/pot4',
                ))
    links.append(
                c.Link(
                    components=[c.Text(text=income_names[0])],
                    on_click=PageEvent(name='change-form', push_path='/forms/income1', context={'kind': 'income1'}),
                    active='/forms/income1',
                ))
    links.append(
                c.Link(
                    components=[c.Text(text=income_names[1])],
                    on_click=PageEvent(name='change-form', push_path='/forms/income2', context={'kind': 'income2'}),
                    active='/forms/income2',
                ))
    links.append(
                c.Link(
                    components=[c.Text(text=income_names[2])],
                    on_click=PageEvent(name='change-form', push_path='/forms/income3', context={'kind': 'income3'}),
                    active='/forms/income3',
                ))
    links.append(
                c.Link(
                    components=[c.Text(text=income_names[3])],
                    on_click=PageEvent(name='change-form', push_path='/forms/income4', context={'kind': 'income4'}),
                    active='/forms/income4',
                ))
    links.append(
                c.Link(
                    components=[c.Text(text='Parameters')],
                    on_click=PageEvent(name='change-form', push_path='/forms/parameters', context={'kind': 'parameters'}),
                    active='/forms/parameters',
                ))

    return demo_page(
        c.LinkList(links=links,
            mode='tabs',
            class_name='+ mb-4',
        ),
        c.ServerLoad(
            path='/forms/content/{kind}',
            load_trigger=PageEvent(name='change-form'),
            components=form_content(kind),
        ),
        title='Cashflow',
    )


@router.get('/content/{kind}', response_model=FastUI, response_model_exclude_none=True)
def form_content(kind: FormKind):
    match RegexEqual(kind):
        case "login":
            return [
                c.Heading(text='Login Form', level=2),
                c.Paragraph(text='Simple login form with email and password.'),
                c.ModelForm(model=LoginForm, submit_url='/api/forms/login',initial={'email':'jlp@jlp'}),
            ]
        case "select":
            return [
                c.Heading(text='Select Form', level=2),
                c.Paragraph(text='Form showing different ways of doing select.'),
                c.ModelForm(model=SelectForm, submit_url='/api/forms/select'),
            ]
        case "big":
            return [
                c.Heading(text='Large Form', level=2),
                c.Paragraph(text='Form with a lot of fields.'),
                c.ModelForm(model=BigModel, submit_url='/api/forms/big'),
            ]
        case "cashflow":
            return [
                c.Iframe(src='http://127.0.0.1/charts/cashflow',
                         width=1300, height=800)
            ]
        case "^pot(.*$)" as capture:

            id=capture[1]
            dbpot = read_pot(int(id))
            return [
                c.ModelForm(model=PotModel, submit_url='/api/forms/pot',
                            initial={'pot_id':dbpot.pot_id,
                                     'name':dbpot.name,
                                     'type':dbpot.type,
                                     'amount':dbpot.amount}),
            ]

        case "^income(.*$)" as capture:
            id=capture[1]
            dbincome = read_income(int(id))
            return [
                c.ModelForm(model=IncomeModel, submit_url='/api/forms/income',
                            initial={'income_id':dbincome.income_id,
                           'name':dbincome.name,
                           'type':dbincome.type,
                           'amount':dbincome.amount,
                           'inflation_yearly':dbincome.inflation_yearly,
                           'repeating_yearly':dbincome.repeating_yearly,
                           'start_date':dbincome.start_date,
                           })
            ]
        case "parameters":
            id = 1
            dbp = read_parameters(int(id))
            return [
                c.ModelForm(model=ParametersModel, submit_url='/api/forms/parameters',
                            initial={
                           'cashflow_id':dbp.cashflow_id,
                           'target_income':dbp.target_income,
                           'inflation':dbp.inflation,
                           'growth':dbp.growth,
                           'age':dbp.age,
                           'retirement_age':dbp.retirement_age,
                           'historical_start_year':dbp.historical_start_year,
                           'years':dbp.years,
                           'ticker':dbp.ticker,
                           'charges':dbp.charges
                           })
            ]
        case _:
            raise ValueError(f'Invalid kind {kind!r}')


class LoginForm(BaseModel):
    email: EmailStr = Field(title='Email Address', description="Try 'x@y' to trigger server side validation")
    password: SecretStr


@router.post('/login')
async def login_form_post(form: Annotated[LoginForm, fastui_form(LoginForm)]):
    return [c.FireEvent(event=GoToEvent(url='/'))]


class ToolEnum(str, enum.Enum):
    hammer = 'hammer'
    screwdriver = 'screwdriver'
    saw = 'saw'
    claw_hammer = 'claw_hammer'


class SelectForm(BaseModel):
    select_single: ToolEnum = Field(title='Select Single')
    select_multiple: list[ToolEnum] = Field(title='Select Multiple')
    search_select_single: str = Field(json_schema_extra={'search_url': '/api/forms/search'})
    search_select_multiple: list[str] = Field(json_schema_extra={'search_url': '/api/forms/search'})


@router.post('/select')
async def select_form_post(form: Annotated[SelectForm, fastui_form(SelectForm)]):
    return [c.FireEvent(event=GoToEvent(url='/'))]


class SizeModel(BaseModel):
    width: int = Field(description='This is a field of a nested model')
    height: int = Field(description='This is a field of a nested model')


class BigModel(BaseModel):
    name: str | None = Field(
        None, description='This field is not required, it must start with a capital letter if provided'
    )
    profile_pic: Annotated[UploadFile, FormFile(accept='image/*', max_size=16_000)] = Field(
        description='Upload a profile picture, must not be more than 16kb'
    )
    profile_pics: Annotated[list[UploadFile], FormFile(accept='image/*')] | None = Field(
        None, description='Upload multiple images'
    )
    dob: date = Field(title='Date of Birth', description='Your date of birth, this is required hence bold')
    human: bool | None = Field(
        None, title='Is human', description='Are you human?', json_schema_extra={'mode': 'switch'}
    )
    size: SizeModel

    @field_validator('name')
    def name_validator(cls, v: str | None) -> str:
        if v and v[0].islower():
            raise PydanticCustomError('lower', 'Name must start with a capital letter')
        return v


@router.post('/big')
async def big_form_post(form: Annotated[BigModel, fastui_form(BigModel)]):
    return [c.FireEvent(event=GoToEvent(url='/'))]

class ParametersModel(BaseModel):
    cashflow_id: int = Field(description='Cashflow ID',default=1)
    target_income: int = Field(description='Target Income',default=50000)
    inflation: int = Field(description='Inflation',default=3)
    growth: int = Field(description='Growth',default=5)
    age: int = Field(description='Age',default=55)
    retirement_age: int = Field(description='Retirement Age',default=60)
    years: int = Field(description='Years',default=30)
    ticker: str = Field(description='Ticker',default='^GSPC')
    historical_start_year: int = Field(description='Historical Start Year',default=1993)
    charges: float = Field(description='Charges',default=5)

class PotEnum(str, enum.Enum):
    pension = 'pension'
    isa = 'isa'
    savings = 'savings'

class PotModel(BaseModel):
    pot_id: int = Field(description='Id')
    name: str = Field(description='Name of account holder'
    )
    type: str = Field(description='What type of account is this ?'
    )
    amount: int = Field(description='Amount in £',default=800000)
    select_single: PotEnum = Field(title='Select type of saving ',default=PotEnum('pension'))

class IncomeModel(BaseModel):
    income_id: int = Field(description='Id')
    name: str | None = Field(
        None, description='Name of account holder'
    )
    type: str | None = Field(
        None, description='What type of income is this ?'
    )
    amount: int = Field(description='Amount in £', default=10600)
    inflation_yearly: bool | None = Field(
        None, title='Increase with CPI?', description='Does this payment increase yearly with cpi?', json_schema_extra={'mode': 'switch'}
    )
    repeating_yearly: bool | None = Field(
        None, title='Repeating Yearly', description='Does this payment repeat yearly?', json_schema_extra={'mode': 'switch'}
    )
    start_date: date = Field(title='Start Date', description='What date does this income start to pay out ?')

class CashFlowModel(BaseModel):
    pot: PotModel
    income: IncomeModel
    parameters: ParametersModel

pot_form = PotModel(pot_id=1,name='', type='', amount=800000, select_single = PotEnum('isa'))
income_form = IncomeModel(income_id=1,name='', type='', amount=10600, inflation_yearly=True, repeating_yearly=True, start_date = date(day=27, month=2, year=1967))
parameters_form = ParametersModel(cashflow_id=1,target_income=50000, inflation=3,growth=5,age=55,retirement_age=60,charges=0.5,historical_start_year=1990,years=30,ticker='^GSPC')
cashflow_form = CashFlowModel(pot=pot_form,income=income_form,parameters=parameters_form)


@router.post('/pot')
async def pot_form_post(form: Annotated[PotModel, fastui_form(PotModel)]):
    # write stuff to db
    cashflow_form.pot.name = form.name
    cashflow_form.pot.type = form.type
    cashflow_form.pot.amount = form.amount
    cashflow_form.pot.select_single = form.select_single
    pots = []
    pots.append(PotModel(pot_id=form.pot_id,name = form.name, type = form.type, amount=form.amount))

    update_pot(pots)

    return [c.FireEvent(event=PageEvent(name='change-form', push_path='/forms/cashflow', context={'kind': 'cashflow'}))]

@router.post('/income')
async def income_form_post(form: Annotated[IncomeModel, fastui_form(IncomeModel)]):
    # write stuff to db
    cashflow_form.income.name = form.name
    cashflow_form.income.type = form.type
    cashflow_form.income.amount = form.amount
    cashflow_form.income.inflation_yearly = form.inflation_yearly
    cashflow_form.income.repeating_yearly = form.repeating_yearly
    cashflow_form.income.start_date = form.start_date
    incomes=[]
    incomes.append(IncomeModel(income_id=form.income_id,name = form.name,
                               type = form.type,
                               amount=form.amount,
                               inflation_yearly=form.inflation_yearly,
                               repeating_yearly=form.repeating_yearly,
                               start_date = form.start_date))

    update_income(incomes)

    return [c.FireEvent(event=PageEvent(name='change-form', push_path='/forms/cashflow', context={'kind': 'cashflow'}))]

@router.post('/parameters')
async def parameters_form_post(form: Annotated[ParametersModel, fastui_form(ParametersModel)]):
    # write stuff to db
    cashflow_form.parameters.target_income = form.target_income
    cashflow_form.parameters.inflation = form.inflation
    cashflow_form.parameters.growth = form.growth
    cashflow_form.parameters.age = form.age
    cashflow_form.parameters.retirement_age = form.retirement_age
    cashflow_form.parameters.charges = form.charges

    cashflow_id =1
    parameters=[]
    parameters.append(ParametersModel(cashflow_id=cashflow_id,
                                        target_income=form.target_income,
                                        inflation=form.inflation,
                                        growth=form.growth,
                                        age=form.age,
                                        retirement_age=form.retirement_age,
                                        years=form.years,
                                        ticker=form.ticker,
                                        historical_start_year=form.historical_start_year,
                                        charges=form.charges,
        ))

    update_parameters(parameters)

    return [c.FireEvent(event=PageEvent(name='change-form', push_path='/forms/cashflow', context={'kind': 'cashflow'}))]
