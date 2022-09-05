#!/usr/bin/env python3

"""demo1-cod-and-chips.py - a demonstration for the talk "Fish and Chips and Apache Kafka®"

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

from demo_helpers import setup_topics
from demo_helpers import OrderNumber, new_order, pretty_order
from demo_helpers import DemoWidgetMixin
from demo_helpers import PREP_FREQ_MIN, PREP_FREQ_MAX


TOPIC_NAME = 'DEMO1-ORDERS'


# I'm not keen on globals, but sometimes they're convenient,
# and they're not *quite* so bad in a program (as opposed to
# when writing a library)
global KAFKA_URI    # for the moment
global CERTS_DIR    # for the moment
global SSL_CONTEXT  # for the moment


class TillWidget(DemoWidgetMixin):

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

    async def make_order(self, producer):
        """Make a new order ("from a custoemr")"""
        order = await new_order()

        order['count'] = count = await OrderNumber.get_next_order_number()

        self.add_line(f'Order {count}: {pretty_order(order)}')

        await producer.send(TOPIC_NAME, order)

    async def on_mount(self):
        asyncio.create_task(self.background_task())


class FoodPreparerWidget(DemoWidgetMixin):

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
            self.add_line(f'Consumer Exception {e.__class__.__name__} {e}')
            return
        self.add_line('Consumer created')

        try:
            await consumer.start()
        except Exception as e:
            self.add_line(f'Consumer start Exception {e.__class__.__name__} {e}')
            return
        self.add_line('Consumer started')

        try:
            await consumer.seek_to_end()
        except Exception as e:
            self.add_line(f'Consumer seek-to-end Exception {e.__class__.__name__} {e}')
            return
        #self.add_line('Consumer sought to end')

        try:
            async for message in consumer:
                await self.prepare_order(message.value)
        except Exception as e:
            self.add_line(f'Exception receiving message {e}')
            await producer.stop()
        finally:
            self.add_line(f'Consumer stopping')
            await consumer.stop()

    async def prepare_order(self, order):
        """Prepare an order"""
        self.add_line(f'Order {order["count"]}: {pretty_order(order)}')

        await asyncio.sleep(random.uniform(PREP_FREQ_MIN, PREP_FREQ_MAX))

        self.change_last_line(f'Order {order["count"]} ready: {pretty_order(order)}')

    async def on_mount(self):
        asyncio.create_task(self.background_task())


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
            area1=TillWidget(1, 'Till producer'),
            area2=FoodPreparerWidget(1, 'Food Preparer consumer'),
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

    setup_topics(KAFKA_URI, SSL_CONTEXT, {TOPIC_NAME: 1})

    MyGridApp.run(title="Simple App", log="textual.log")


if __name__ == '__main__':
    main()
