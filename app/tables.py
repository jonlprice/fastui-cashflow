from datetime import date
from functools import cache
from pathlib import Path

import pydantic
from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup, DisplayMode
from fastui.events import BackEvent, GoToEvent, PageEvent
from pydantic import BaseModel, Field, TypeAdapter

from sqlalchemy import Numeric, Column, Integer, String, Date, Float
from sqlalchemy.orm import DeclarativeBase

from datetime import datetime

from .shared import demo_page
from .gilts import read_gilts, PyGilt, last_refresh

from fastapi.responses import HTMLResponse

router = APIRouter()


class City(BaseModel):
    id: int = Field(title='ID')
    city: str = Field(title='Name')
    city_ascii: str = Field(title='City Ascii')
    lat: float = Field(title='Latitude')
    lng: float = Field(title='Longitude')
    country: str = Field(title='Country')
    iso2: str = Field(title='ISO2')
    iso3: str = Field(title='ISO3')
    admin_name: str | None = Field(title='Admin Name')
    capital: str | None = Field(title='Capital')
    population: float = Field(title='Population')

class Base(DeclarativeBase):
    pass

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


@cache
def cities_list() -> list[City]:
    cities_adapter = TypeAdapter(list[City])
    cities_file = Path(__file__).parent / 'cities.json'
    cities = cities_adapter.validate_json(cities_file.read_bytes())
    cities.sort(key=lambda city: city.population, reverse=True)
    return cities


@cache
def cities_lookup() -> dict[id, City]:
    return {city.id: city for city in cities_list()}


class FilterForm(pydantic.BaseModel):
    country: str = Field(json_schema_extra={'search_url': '/api/forms/search', 'placeholder': 'Filter by Country...'})


@router.get('/gilts', response_model=FastUI, response_model_exclude_none=True)
def gilts_view(page: int = 1, country: str | None = None) -> list[AnyComponent]:

    jpgilt = PyGilt(gilt_id=1,
    close_of_business_date = datetime.now(),
    instrument_type="instr",
    maturity_bracket="str",
    instrument_name="str",
    isin_code="str",
    ticker="str",
    redemption_date= datetime.now(),
    first_issue_date = datetime.now(),
    dividend_dates="str",
    current_ex_div_date = datetime.now(),
    total_amount_in_issue= 10,
    total_amount_including_il_uplift= 10,
    coupon= 10,
    days_to_redemption= 10,
    years_to_redemption= 10,
    clean_price= 10,
    dirty_price= 10,
    tradeweb_yield= 10,
    calculated_yield= 10,
                    )

    gilts = []
    pygilts = []

    gilts = read_gilts()
    for g in gilts:
        pygilts.append(db_to_pydantic(g))


    # gilts.append(jpgilt)
    page_size = 50
    filter_form_initial = {}
    """
    # filter on instrument_type
    if country:
        cities = [city for city in cities if city.iso3 == country]
        country_name = cities[0].country if cities else country
        filter_form_initial['country'] = {'value': country, 'label': country_name}
    """
    return demo_page(
        *tabs(),
        c.ModelForm(model=FilterForm,
            submit_url='.',
            initial=filter_form_initial,
            method='GOTO',
            submit_on_change=True,
            display_mode='inline',
        ),
        c.Table(data_model=PyGilt,
            data=pygilts[(page - 1) * page_size : page * page_size],
            columns=[
                DisplayLookup(field='instrument_type', table_width_percent=5),
                DisplayLookup(field='maturity_bracket', table_width_percent=5),
                DisplayLookup(field='instrument_name', table_width_percent=5),
                DisplayLookup(field='isin_code',  on_click=GoToEvent(url='./{isin_code}'), table_width_percent=5),
                DisplayLookup(field='ticker', table_width_percent=5),
                DisplayLookup(field='redemption_date', table_width_percent=5),
                DisplayLookup(field='dividend_dates', table_width_percent=5),
                DisplayLookup(field='current_ex_div_date', table_width_percent=5),
                DisplayLookup(field='coupon', table_width_percent=5),
                DisplayLookup(field='days_to_redemption', table_width_percent=5),
                DisplayLookup(field='years_to_redemption', table_width_percent=5),
                DisplayLookup(field='clean_price', table_width_percent=5),
                DisplayLookup(field='dirty_price', table_width_percent=5),
                DisplayLookup(field='tradeweb_yield', table_width_percent=5),
                DisplayLookup(field='calculated_yield', table_width_percent=5)
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(pygilts)),
        title='Gilts',
    )

@router.get('/yieldcurve', response_model=FastUI, response_model_exclude_none=True)
def yieldcurve_view():

    last_refresh_time = last_refresh().strftime('%A, %d %b %Y')

    text = f"Last time prices refreshed: {last_refresh_time}"

    return demo_page(
        *tabs(),
        c.Button(text='Load new prices', on_click=PageEvent(name='server-load')),
        c.Div(
            components=[c.ServerLoad(
                path='/gilts/update',
                load_trigger=PageEvent(name='server-load'),
                components=[c.Text(text=text)],
            ),
                        ], class_name='py-2',
            ),
        c.Iframe(src='http://127.0.0.1/charts/gilts',  width=1300, height=800),
        )

@router.get('/cities', response_model=FastUI, response_model_exclude_none=True)
def cities_view(page: int = 1, country: str | None = None):
    cities = cities_list()
    page_size = 50
    filter_form_initial = {}
    if country:
        cities = [city for city in cities if city.iso3 == country]
        country_name = cities[0].country if cities else country
        filter_form_initial['country'] = {'value': country, 'label': country_name}


    return demo_page(
        *tabs(),
        c.ModelForm(model=FilterForm,
            submit_url='.',
            initial=filter_form_initial,
            method='GOTO',
            submit_on_change=True,
            display_mode='inline',
        ),
        c.Table(data_model=City,
            data=cities[(page - 1) * page_size : page * page_size],
            columns=[
                DisplayLookup(field='city', on_click=GoToEvent(url='./{id}'), table_width_percent=33),
                DisplayLookup(field='country', table_width_percent=33),
                DisplayLookup(field='population', table_width_percent=33),
            ],
        ),
        c.Pagination(page=page, page_size=page_size, total=len(cities)),
        title='Cities',
        )

@router.get('/cities/{city_id}', response_model=FastUI, response_model_exclude_none=True)
def city_view(city_id: int) -> list[AnyComponent]:
    city = cities_lookup()[city_id]
    return demo_page(
        *tabs(),
        c.Link(components=[c.Text(text='Back')], on_click=BackEvent()),
        c.Details(data=city),
        title=city.city,
    )


class User(BaseModel):
    id: int = Field(title='ID')
    name: str = Field(title='Name')
    dob: date = Field(title='Date of Birth')
    enabled: bool | None = None


users: list[User] = [
    User(id=1, name='John', dob=date(1990, 1, 1), enabled=True),
    User(id=2, name='Jane', dob=date(1991, 1, 1), enabled=False),
    User(id=3, name='Jack', dob=date(1992, 1, 1)),
]


@router.get('/users', response_model=FastUI, response_model_exclude_none=True)
def users_view() -> list[AnyComponent]:
    return demo_page(
        *tabs(),
        c.Table(data_model=User,
            data=users,
            columns=[
                DisplayLookup(field='name', on_click=GoToEvent(url='/table/users/{id}/')),
                DisplayLookup(field='dob', mode=DisplayMode.date),
                DisplayLookup(field='enabled'),
            ],
        ),
        title='Users',
    )


def tabs() -> list[AnyComponent]:
    return [
        c.LinkList(
            links=[
                c.Link(
                    components=[c.Text(text='Cities')],
                    on_click=GoToEvent(url='/table/cities'),
                    active='startswith:/table/cities',
                ),

                c.Link(
                    components=[c.Text(text='Gilts')],
                    on_click=GoToEvent(url='/table/gilts'),
                    active='startswith:/table/gilts',
                ),
                c.Link(
                    components=[c.Text(text='Yield Curve')],
                    on_click=GoToEvent(url='/table/yieldcurve'),
                    active='startswith:/table/yieldcurve',
                ),
            ],
            mode='tabs',
            class_name='+ mb-4',
        ),
    ]


@router.get('/users/{id}/', response_model=FastUI, response_model_exclude_none=True)
def user_profile(id: int) -> list[AnyComponent]:
    user: User | None = users[id - 1] if id <= len(users) else None
    return demo_page(
        *tabs(),
        c.Link(components=[c.Text(text='Back')], on_click=BackEvent()),
        c.Details(
            data=user,
            fields=[
                DisplayLookup(field='name'),
                DisplayLookup(field='dob', mode=DisplayMode.date),
                DisplayLookup(field='enabled'),
            ],
        ),
        title=user.name,
    )

def db_to_pydantic(gilt) -> PyGilt:

    pygilt = PyGilt(gilt_id=gilt.gilt_id,
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
            calculated_yield=gilt.calculated_yield)

    return pygilt
