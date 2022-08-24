#!/usr/bin/env python3

"""shop.py - the demonstration for my talk "Fish and Chips and Apache Kafka®"
"""

import asyncio
import click

from datetime import datetime

from rich.align import Align

from textual import events
from textual.app import App
from textual.widget import Widget
from textual.widgets import Header, Footer, Placeholder, ScrollView


class Clock(Widget):
    def on_mount(self):
        self.set_interval(1, self.refresh)

    def render(self):
        time = datetime.now().strftime("%c")
        return Align.center(time, vertical="middle")


class MyWidget(Widget):

    counter = 0

    def on_mount(self):
        self.set_interval(1, self.refresh)

    def render(self):
        text = f'{self.counter}\n{self.counter+1}\n{self.counter+2}\n{self.counter+3}'
        self.counter += 1
        return Align.left(text, vertical='middle')


class MyGridApp(App):

    async def on_load(self, event: events.Load) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        await self.bind("q", "quit", "Quit")

    async def on_mount(self, event: events.Mount) -> None:
        grid = await self.view.dock_grid(edge='left', name='left-grid')

        grid.add_column('left', fraction=1, min_size=20)
        grid.add_column('right', fraction=1, min_size=20)

        grid.add_row('top', fraction=1)

        grid.add_areas(
            area1='left,top',
            area2='right,top',
        )

        grid.place(
            area1=Clock(),
            area2=MyWidget(),
        )


@click.command(no_args_is_help=True)
@click.option('--go', required=True, is_flag=True, expose_value=False, help="Say --go to make the app run")
def main():
    """A fish and chip shop demo, using Apache Kafka®
    """

    MyGridApp.run(title="Simple App", log="textual.log")


if __name__ == '__main__':
    main()
