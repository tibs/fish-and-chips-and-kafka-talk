#!/usr/bin/env python3

"""shop.py - the demonstration for my talk "Fish and Chips and Apache Kafka®"
"""

# Thanks to the article at
# https://stackoverflow.com/questions/71631247/textual-python-tui-enabling-long-running-external-asyncio-functionality
# for some ideas

import asyncio
import click

from datetime import datetime

from rich.align import Align
from rich.panel import Panel

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


class LineWidget(Widget):

    counter = 0

    def on_mount(self):
        self.set_interval(0.5, self.refresh)

    def make_text(self, height):
        lines = [f'{self.counter + n}' for n in range(30)]
        lines = ['TOP'] + lines + [f'BOTTOM height={height}']
        # The value of 2 seems unnecessarily magical
        # I assume it's the widget height - the panel border
        return '\n'.join(lines[-(height-2):])

    def render(self):
        text = self.make_text(self.size.height)
        self.counter += 1
        return Panel(text)


class MyGridApp(App):

    async def on_load(self, event: events.Load) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        await self.bind("q", "quit", "Quit")

    async def on_mount(self, event: events.Mount) -> None:
        grid = await self.view.dock_grid(edge='left', name='left-grid')

        grid.add_column('left', fraction=1, min_size=20)
        grid.add_column('right', fraction=1, min_size=20)

        grid.add_row('top', fraction=1)
        grid.add_row('bottom')

        grid.add_areas(
            area1='left,top',
            area2='right,top',
            area3='left-start|right-end,bottom',
        )

        grid.place(
            area1=Clock(),
            area2=OtherWidget(),
            area3=LineWidget(),
        )


class OtherWidget(Widget):

    counter = 0

    async def background_task(self):
        while True:
            await asyncio.sleep(0.5)
            self.counter += 1
            self.refresh()
            self.app.refresh()

    async def on_mount(self):
        asyncio.create_task(self.background_task())

    def render(self):
        return Panel(f'Other counter {self.counter}')


@click.command(no_args_is_help=True)
@click.option('--go', required=True, is_flag=True, expose_value=False, help="Say --go to make the app run")
def main():
    """A fish and chip shop demo, using Apache Kafka®
    """

    MyGridApp.run(title="Simple App", log="textual.log")


if __name__ == '__main__':
    main()
