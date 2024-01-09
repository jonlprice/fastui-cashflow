from __future__ import annotations as _annotations

import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastui import prebuilt_html
from fastui.dev import dev_fastapi_app
from httpx import AsyncClient
from fastapi.staticfiles import StaticFiles

#from .components_list import router as components_router
from .forms import router as forms_router
from .main import router as main_router
from .tables import router as table_router
from .gilts import router as gilts_router
from .charts import router as charts_router


@asynccontextmanager
async def lifespan(app_: FastAPI):
    async with AsyncClient() as client:
        app_.state.httpx_client = client
        yield

def init_logger():
    logger = logging.getLogger('cashflow')
    #Set the threshold logging level of the logger to INFO
    logger.setLevel(logging.INFO)
    #Create a stream-based handler that writes the log entries    #into the standard output stream
    handler = logging.StreamHandler(sys.stdout)
    #Create a formatter for the logs

    time_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt='%(levelname)s:%(asctime)s.%(msecs)03d::%(name)s:%(module)s:%(funcName)s:%(message)s', datefmt=time_format)

    handler.setFormatter(formatter)
        #Set the created formatter as the formatter of the handler    handler.setFormatter(formatter)
    #Add the created handler to this logger
    logger.addHandler(handler)

init_logger()
logger = logging.getLogger('cashflow')

logger.info("Cashflow app started")

frontend_reload = '--reload' in sys.argv
if frontend_reload:
    # dev_fastapi_app reloads in the browser when the Python source changes
    app = dev_fastapi_app(lifespan=lifespan)
else:
    app = FastAPI(lifespan=lifespan)


app.mount("/static", StaticFiles(directory="static"), name="static")

# app.include_router(components_router, prefix='/api/components')
app.include_router(table_router, prefix='/api/table')
app.include_router(forms_router, prefix='/api/forms')
app.include_router(gilts_router, prefix='/api/gilts')
app.include_router(charts_router, prefix='/charts')
app.include_router(main_router, prefix='/api')


@app.get('/robots.txt', response_class=PlainTextResponse)
async def robots_txt() -> str:
    return 'User-agent: *\nAllow: /'


@app.get('/favicon.ico', status_code=404, response_class=PlainTextResponse)
async def favicon_ico() -> str:
    return 'page not found'

@app.get('/chartstest')
async def charts_landing() -> HTMLResponse:
    html='<h1>hello</h1>'
    return HTMLResponse(html)

@app.get('/{path:path}')
async def html_landing() -> HTMLResponse:
    return HTMLResponse(prebuilt_html(title='Cashflow Modeller'))
