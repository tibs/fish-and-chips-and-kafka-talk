#!/usr/bin/env python3

"""demo1-cod-and-chips.py - the first demonstration for my talk "Fish and Chips and Apache Kafka®"

Shows:

* "customer" makes up an order
* TILL sends the order to the ORDER topic
* FOOD-PREPARER receives the order from the ORDER topic

Note on timing:

* We want customers to make orders at perceptibly random intervals, but not so
  slow as to be boring.
* We want the (single) food preparer to have (more than enough) time to make up orders.
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


TOPIC_NAME = 'ORDER'

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

    count = 0
    lines = deque(maxlen=MAX_LINES)

    async def background_task(self):
        try:
            context = aiokafka.helpers.create_ssl_context(
                cafile=CERTS_DIR / "ca.pem",
                certfile=CERTS_DIR / "service.cert",
                keyfile=CERTS_DIR / "service.key",
            )
        except Exception as e:
            self.lines.append(f'Producer SSL Exception {e.__class__.__name__} {e}')
            return
        self.lines.append('Producer SSL context acquired')

        try:
            producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=KAFKA_URI,
                security_protocol="SSL",
                ssl_context=context,
                value_serializer=lambda v: json.dumps(v).encode('ascii'),
            )
        except Exception as e:
            self.lines.append(f'Producer Exception {e.__class__.__name__} {e}')
            return
        self.lines.append('Producer created')

        try:
            await producer.start()
        except Exception as e:
            self.lines.append(f'Producer start Exception {e.__class__.__name__} {e}')
            return
        self.lines.append('Producer started')

        try:
            while True:
                await self.make_order(producer)
        except Exception as e:
            self.lines.append(f'Exception sending message {e}')
            self.refresh()
            self.app.refresh()
        finally:
            self.lines.append(f'Producer stopping')
            self.refresh()
            self.app.refresh()
            await producer.stop()

    async def make_order(self, producer):
        """Make a new order ("from a custoemr")"""
        order = await new_order()

        self.count += 1
        order['count'] = self.count

        self.lines.append(
            f'Got order {self.count}: {pretty_order(order)} at {datetime.now().strftime("%H:%M:%S")}'
        )
        self.refresh()
        self.app.refresh()

        #await producer.send_and_wait(TOPIC_NAME, order)
        await producer.send(TOPIC_NAME, order)

    async def on_mount(self):
        asyncio.create_task(self.background_task())

    def make_text(self, height):
        lines = list(self.lines)
        # The value of 2 seems unnecessarily magical
        # I assume it's the widget height - the panel border
        return '\n'.join(lines[-(height-2):])

    def render(self):
        text = self.make_text(self.size.height)
        return Panel(text, title='Producer (TILL)')


class FoodPreparerWidget(Widget):

    count = 0
    lines = deque(maxlen=MAX_LINES)

    async def background_task(self):
        try:
            context = aiokafka.helpers.create_ssl_context(
                cafile=CERTS_DIR / "ca.pem",
                certfile=CERTS_DIR / "service.cert",
                keyfile=CERTS_DIR / "service.key",
            )
        except Exception as e:
            self.lines.append(f'Consumer SSL Exception {e.__class__.__name__} {e}')
            return
        self.lines.append('Consumer SSL context acquired')

        try:
            consumer = aiokafka.AIOKafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=KAFKA_URI,
                security_protocol="SSL",
                ssl_context=context,
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
        grid.add_column('right', fraction=1, min_size=20)

        grid.add_row('top', fraction=1)

        grid.add_areas(
            area1='left,top',
            area2='right,top',
        )

        grid.place(
            area1=TillWidget(),
            area2=FoodPreparerWidget(),
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
    print(f'Kafka URI {kafka_uri}, certs dir {certs_dir}')
    KAFKA_URI = kafka_uri
    CERTS_DIR = pathlib.Path(certs_dir)

    MyGridApp.run(title="Simple App", log="textual.log")


if __name__ == '__main__':
    main()
