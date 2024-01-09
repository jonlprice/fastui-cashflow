from __future__ import annotations as _annotations

from fastui import AnyComponent
from fastui import components as c
from fastui.events import GoToEvent


def demo_page(*components: AnyComponent, title: str | None = None) -> list[AnyComponent]:
    return [
        c.PageTitle(text=f'FastUI Demo — {title}' if title else 'FastUI Demo'),
        c.Navbar(
            title='Cashflow App',
            title_event=GoToEvent(url='/'),
            links=[
                c.Link(
                    components=[c.Text(text='Gilts')],
                    #on_click=GoToEvent(url='/table/cities'),
                    on_click=GoToEvent(url='/table/gilts'),
                    active='startswith:/gilts',
                ),
                c.Link(
                    components=[c.Text(text='Cashflow')],
                    on_click=GoToEvent(url='/forms/cashflow'),
                    active='startswith:/cashflow',
                ),
                #c.Link(
                #    components=[c.Text(text='Forms')],
                #    on_click=GoToEvent(url='/forms/login'),
                #    active='startswith:/forms',
                #),
            ],
        ),
        c.Page(
            components=[
                *((c.Heading(text=title),) if title else ()),
                *components,
            ],
        ),
    ]
