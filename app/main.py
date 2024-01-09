from __future__ import annotations as _annotations

from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.events import PageEvent
from fastapi.staticfiles import StaticFiles
from fastui.events import BackEvent, GoToEvent

from .shared import demo_page
from .gilts import create_image

router = APIRouter()

router.mount("/static", StaticFiles(directory="static"), name="static")

@router.get('/', response_model=FastUI, response_model_exclude_none=True)
def api_index() -> list[AnyComponent]:
    # language=markdown
    markdown = """\
This site providers a demo of [FastUI](https://github.com/samuelcolvin/FastUI), the code for the demo
is [here](https://github.com/samuelcolvin/FastUI/tree/main/python/demo).

The following components are demonstrated:

* `Markdown` — that's me :-)
* `Text`— example [here](/components#text)
* `Paragraph` — example [here](/components#paragraph)
* `PageTitle` — you'll see the title in the browser tab change when you navigate through the site
* `Heading` — example [here](/components#heading)
* `Code` — example [here](/components#code)
* `Button` — example [here](/components#button-and-modal)
* `Link` — example [here](/components#link-list)
* `LinkList` — example [here](/components#link-list)
* `Navbar` — see the top of this page
* `Modal` — static example [here](/components#button-and-modal), dynamic content example [here](/components#dynamic-modal)
* `ServerLoad` — see [dynamic modal example](/components#dynamic-modal) and [SSE example](/components#server-load-sse)
* `Iframe` - example [here](/components#iframe)
* `Table` — See [cities table](/table/cities) and [users table](/table/users)
* `Pagination` — See the bottom of the [cities table](/table/cities)
* `ModelForm` — See [forms](/forms/login)
"""
    create_image()
    #return demo_page(c.Markdown(text=markdown))
    # return demo_page(c.Markdown(text=markdown), c.Div(components=[c.Text(text=html)]))
    return demo_page(
        c.Div(
            components=[
                c.Heading(text='Iframe', level=2),
                c.Markdown(text='`Iframe` can be used to embed external content.'),
                #c.Iframe(src='https://pydantic.dev'),
                c.LinkList(
                    links=[
                        c.Link(
                            components=[c.Text(text='Internal Link - the the home page')],
                            on_click=GoToEvent(url='/'),
                        ),
                        c.Link(
                            components=[c.Text(text='Pydantic (External link)')],
                            on_click=GoToEvent(url='https://pydantic.dev'),
                        ),
                    ],
                ),
            ],
            class_name='border-top mt-3 pt-1',
        ),
            c.Markdown(text=markdown),
                     c.Div(components=[
                         c.Button(text='Load', on_click=PageEvent(name='server-load')),
                         c.Div(
                             components=[
                                 c.ServerLoad(
                                    path='/static/temp.html',
                                    load_trigger=PageEvent(name='server-load'),
                                    components=[c.Text(text='before')],
                                )
                            ],
                             class_name='py-2',
                        )

                         ],
                        )
            )


@router.get('/{path:path}', status_code=404)
async def api_404():
    # so we don't fall through to the index page
    return {'message': 'Not Found'}
