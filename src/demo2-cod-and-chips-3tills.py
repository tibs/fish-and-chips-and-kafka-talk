#!/usr/bin/env python3

"""demo2-cod-and-chips-3tills.py - the second demonstration for my talk "Fish and Chips and Apache Kafka®"

Shows:

* "customer" makes up an order
* one of the three TILLs sends the order to the ORDER topic
* FOOD-PREPARER receives the order from the ORDER topic

Note on timing:

* We want customers to make orders at perceptibly random intervals, but not so
  slow as to be boring.
* We want the (single) food preparer to have (more than enough) time to make up an order
  *if there was one till* (as was the case in demo1), but to get increasingly far behind
  now we've got 3 tills.
"""

# Thanks to the article at
# https://stackoverflow.com/questions/71631247/textual-python-tui-enabling-long-running-external-asyncio-functionality
# for some ideas

import asyncio
import pathlib
import json
import random

import aiokafka
import aiokafka.helpers
import click

from collections import deque

from datetime import datetime

from rich.align import Align
from rich.panel import Panel

from textual import events
from textual.app import App
from textual.widget import Widget
from textual.widgets import Header, Footer, Placeholder, ScrollView


TOPIC_NAME = 'DEMO2-ORDERS'

# Bounds on how often a new order occurs
ORDER_FREQ_MIN = 1.0
ORDER_FREQ_MAX = 1.5

# Bounds on how long it takes to prepare an order
PREP_FREQ_MIN = 0.9
PREP_FREQ_MAX = 1.3

# Maximum number of lines to keep for a widget display
MAX_LINES = 40

# I'm not keen on globals, but sometimes they're convenient,
# and they're not *quite* so bad in a program (as opposed to
# when writing a library)
global KAFKA_URI    # for the moment
global CERTS_DIR    # for the moment


class OrderNumber:
    """An order number that we can increment safely from different async tasks"""

    lock = asyncio.Lock()
    count = 0

    @classmethod
    async def get_next_order_number(cls):
        async with cls.lock:
            cls.count += 1
            return cls.count


async def new_order():
    """Wait a random time, return a random order.

    Note that it doesn't include the order number, because that can only be
    set by the TILL receiving the order.
    """

    # Wait somewhere between 0.5 and 1 seconds (these are fast customers!)
    await asyncio.sleep(random.uniform(ORDER_FREQ_MIN, ORDER_FREQ_MAX))

    # For the moment, our random order is always the same...
    order = {
        'order': [
            ['cod', 'chips'],
            ['chips', 'chips'],
        ]
    }
    return order


def pretty_order(order):
    """Provide a pretty representation of an order's 'order' data.
    """

    # We assume that ['chips', 'chips'] is our way of saying "a large portion
    # of chips". We also assume that ['chips', 'chips', 'chips'] is not a thing,
    # nor is ['cod', 'cod'], and doubtless other oddities.
    parts = []
    for item in order['order']:
        if len(item) == 2 and item[0] == item[1] == 'chips':
            parts.append(f'large chips')
        else:
            parts.append(' and '.join(item))
    return ', '.join(parts)


class TillWidget(Widget):

    lines = {}  # output lines, per till

    def __init__(self, till_number: str, name: str | None = None) -> None:

        self.till_number = till_number
        self.lines[till_number] = deque(maxlen=MAX_LINES)
        super().__init__(name)

    async def background_task(self):
        try:
            producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=KAFKA_URI,
                security_protocol="SSL",
                ssl_context=SSL_CONTEXT,
                value_serializer=lambda v: json.dumps(v).encode('ascii'),
            )
        except Exception as e:
            self.add_line(f'Producer Exception {e.__class__.__name__} {e}')
            return
        self.add_line('Producer created')

        try:
            await producer.start()
        except Exception as e:
            self.add_line(f'Producer start Exception {e.__class__.__name__} {e}')
            return
        self.add_line('Producer started')

        try:
            while True:
                await self.make_order(producer)
        except Exception as e:
            self.add_line(f'Exception sending message {e}')
        finally:
            self.add_line(f'Producer stopping')
            await producer.stop()

    def add_line(self, text, refresh=True):
        """Add a line of text to our scrolling display"""
        self.lines[self.till_number].append(text)
        if refresh:
            self.refresh()
            self.app.refresh()

    async def make_order(self, producer):
        """Make a new order ("from a customer")"""
        order = await new_order()

        order['count'] = count = await OrderNumber.get_next_order_number()

        self.add_line(
            f'Got order {count}: {pretty_order(order)} at {datetime.now().strftime("%H:%M:%S")}'
        )

        await producer.send(TOPIC_NAME, order)

    async def on_mount(self):
        asyncio.create_task(self.background_task())

    def make_text(self, height):
        lines = list(self.lines[self.till_number])
        # The value of 2 seems unnecessarily magical
        # I assume it's the widget height - the panel border
        return '\n'.join(lines[-(height-2):])

    def render(self):
        text = self.make_text(self.size.height)
        return Panel(text, title=f'Producer (TILL {self.till_number})')


class FoodPreparerWidget(Widget):

    count = 0
    lines = deque(maxlen=MAX_LINES)

    async def background_task(self):
        try:
            consumer = aiokafka.AIOKafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=KAFKA_URI,
                security_protocol="SSL",
                ssl_context=SSL_CONTEXT,
                value_deserializer = lambda v: json.loads(v.decode('ascii')),
            )
        except Exception as e:
            self.lines.append(f'Consumer Exception {e.__class__.__name__} {e}')
            return
        self.lines.append('Consumer created')

        try:
            await consumer.start()
        except Exception as e:
            self.lines.append(f'Consumer start Exception {e.__class__.__name__} {e}')
            return
        self.lines.append('Consumer started')

        try:
            while True:
                async for message in consumer:
                    await self.prepare_order(message.value)
        except Exception as e:
            self.lines.append(f'Exception receiving message {e}')
            self.refresh()
            self.app.refresh()
            await producer.stop()
        finally:
            self.lines.append(f'Consumer stopping')
            self.refresh()
            self.app.refresh()
            await consumer.stop()

    async def prepare_order(self, order):
        """Prepare an order"""
        self.lines.append(
            f'Received order {order["count"]} at {datetime.now().strftime("%H:%M:%S")}: {pretty_order(order)}'
            )
        self.refresh()
        self.app.refresh()

        await asyncio.sleep(random.uniform(PREP_FREQ_MIN, PREP_FREQ_MAX))

        self.lines.append(
            f'    finished order at {datetime.now().strftime("%H:%M:%S")}'
            )
        self.refresh()
        self.app.refresh()

    async def on_mount(self):
        asyncio.create_task(self.background_task())

    def make_text(self, height):
        lines = list(self.lines)
        # The value of 2 seems unnecessarily magical
        # I assume it's the widget height - the panel border
        return '\n'.join(lines[-(height-2):])

    def render(self):
        text = self.make_text(self.size.height)
        return Panel(text, title="Consumer (FOOD-PREPARER)")


class MyGridApp(App):

    async def on_load(self, event: events.Load) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        await self.bind("q", "quit", "Quit")

    async def on_mount(self, event: events.Mount) -> None:
        grid = await self.view.dock_grid(edge='left', name='left-grid')

        grid.add_column('left', fraction=1, min_size=20)
        grid.add_column('middle', fraction=1, min_size=20)
        grid.add_column('right', fraction=1, min_size=20)

        grid.add_row('top', fraction=1)
        grid.add_row('bottom')

        grid.add_areas(
            area1='left,top',
            area2='middle,top',
            area3='right,top',
            area4='left-start|right-end,bottom',
        )

        grid.place(
            area1=TillWidget(1),
            area2=TillWidget(2),
            area3=TillWidget(3),
            area4=FoodPreparerWidget(),
        )


@click.command(no_args_is_help=True)
@click.argument('kafka_uri', required=True)
@click.option('-d', '--certs-dir', default='creds',
              help='directory containing the ca.pem, service.cert and service.key files')
def main(kafka_uri, certs_dir):
    """A fish and chip shop demo, using Apache Kafka®
    """

    global KAFKA_URI    # for the moment
    global CERTS_DIR    # for the moment
    global SSL_CONTEXT  # for the moment

    print(f'Kafka URI {kafka_uri}, certs dir {certs_dir}')
    KAFKA_URI = kafka_uri
    CERTS_DIR = pathlib.Path(certs_dir)

    SSL_CONTEXT = aiokafka.helpers.create_ssl_context(
        cafile=CERTS_DIR / "ca.pem",
        certfile=CERTS_DIR / "service.cert",
        keyfile=CERTS_DIR / "service.key",
    )

    MyGridApp.run(title="Simple App", log="textual.log")


if __name__ == '__main__':
    main()
