#!/usr/bin/env python3

"""demo3-cod-and-chips-3tills-2preparers.py - a demonstration for the talk "Fish and Chips and Apache Kafka®"

Shows:

* "customer" makes up an order
* one of the three TILLs sends the order to the ORDER topic
* one of the two FOOD-PREPARERs receives the order from the ORDER topic

NOTE that for this demo we take care to start the producers sending events after
the consumers are ready to listen - if we don't perform that synchronisation, the
consumers seem to start quite a bit later than the producers, which means that
seeking to the "current latest" event will miss some. It's probably a good thing
to do anyway, and should probably be a part of all the demos (except we can get
away without it in the others)

Note on timing:

* We want customers to make orders at perceptibly random intervals, but not so
  slow as to be boring.
* We want the two food preparers to have (more than enough) time to make up an order

TODO items

* I still haven't figured out how to automatically send messages to partitions without
  actually specifiying the target partition number.

* Stopping (by typing `q` seems to give me errors, rather than ending nicely. Probably
  because I'm not telling things to tidy up in the right way.

  Update: implementing `on_shutdown` handlers on the widgets causes me to hang until
  a RequestTimedOutError, instead. Hmm.
"""

# Thanks to the article at
# https://stackoverflow.com/questions/71631247/textual-python-tui-enabling-long-running-external-asyncio-functionality
# for some ideas

import asyncio
import json
import pathlib
import random
import time

import aiokafka
import aiokafka.helpers
import click

# We still need kafka-python for admin tasks
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, UnknownTopicOrPartitionError

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


TOPIC_NAME = 'DEMO3_ORDERS'
CONSUMER_GROUP = 'DEMO3_ALL_ORDERS'


# I'm not keen on globals, but sometimes they're convenient,
# and they're not *quite* so bad in a program (as opposed to
# when writing a library)
global KAFKA_URI    # for the moment
global CERTS_DIR    # for the moment
global SSL_CONTEXT  # for the moment


# Clumsy synchronisation so we can start producing after the consumers
# are ready

PREP_EVENTS = [asyncio.Event(), asyncio.Event()]

async def wait_for_food_preparers():
    """Wait for all three Food Preparers to be ready"""
    for event in PREP_EVENTS:
        await event.wait()


class TillWidget(DemoWidgetMixin):

    producer = None

    async def background_task(self):
        self.add_line(f'Starting {self.name} number {self.instance_number}')

        try:
            producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=KAFKA_URI,
                security_protocol="SSL",
                ssl_context=SSL_CONTEXT,
                value_serializer=lambda v: json.dumps(v).encode('ascii'),
                key_serializer=lambda v: json.dumps(v).encode('ascii'),
            )
        except Exception as e:
            self.add_line(f'Producer Exception {e.__class__.__name__} {e}')
            return
        self.add_line('Producer created')

        try:
            await producer.start()

            self.producer = producer
        except Exception as e:
            self.add_line(f'Producer start Exception {e.__class__.__name__} {e}')
            return
        self.add_line('Producer started')

        # Wait for the food preparers to be ready for us
        self.add_line('Waiting for food preparers')
        waiter_task = asyncio.create_task(wait_for_food_preparers())
        await waiter_task
        self.add_line('Food preparers are ready')

        try:
            while True:
                await self.make_order(producer)
        except Exception as e:
            self.add_line(f'Exception sending message {e}')
        finally:
            self.add_line(f'Producer stopping')
            await producer.stop()

    async def make_order(self, producer):
        """Make a new order ("from a customer")"""
        order = await new_order()

        order['count'] = count = await OrderNumber.get_next_order_number()
        order['till'] = str(self.instance_number)

        self.add_line(f'Order {count}: {pretty_order(order)}')

        # TODO I need to work out what I am doing wrong that means that approaches
        # (1) and (2) don't seem to be working for me.
        #
        # *CHECK* that whether it works in kafka-python, in case it's an aiokafk
        #         problem.
        #
        # Also consider hashing on the order number
        #
        # 1. Specifying a key means that the key will be hashed and used to decide
        #    which partition to send the message to. This also means that the
        #    key value must deserialise as bytes, which is why we set `order['till']`
        #    to a string value above
        #await producer.send(TOPIC_NAME, value=order, key='till')
        #
        # 2. Not specifying a key means that messages will be sent to a random partition
        #await producer.send_and_wait(TOPIC_NAME, value=order)
        #
        # 3. Or I can try specifying a partition directly - this requires me to know
        #    how many partitions there are
        await producer.send(TOPIC_NAME, value=order, partition=self.instance_number-1)

    async def on_mount(self):
        asyncio.create_task(self.background_task())

    async def on_shutdown(self, event: events.Shutdown) -> None:
        """Let's see if this works!"""
        if self.producer:
            await self.producer.stop()
            self.producer = None


class FoodPreparerWidget(DemoWidgetMixin):

    consumer = None

    async def background_task(self):
        try:
            consumer = aiokafka.AIOKafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=KAFKA_URI,
                security_protocol="SSL",
                ssl_context=SSL_CONTEXT,
                value_deserializer=lambda v: json.loads(v.decode('ascii')),
                key_deserializer=lambda v: json.loads(v.decode('ascii')),
                group_id=CONSUMER_GROUP,
                auto_offset_reset="earliest",
            )
        except Exception as e:
            self.add_line(f'Consumer Exception {e.__class__.__name__} {e}')
            return
        self.add_line('Consumer created')

        try:
            await consumer.start()

            self.consumer = consumer
        except Exception as e:
            self.add_lines(f'Consumer start Exception {e.__class__.__name__} {e}')
            return
        self.add_line('Consumer started')

        try:
            await consumer.seek_to_end()
        except Exception as e:
            self.add_line(f'Consumer seek-to-end Exception {e.__class__.__name__} {e}')
            return
        #self.add_line('Consumer sought to end')

        # Indicate we're ready to receive orders
        self.add_line(f'Consumer {self.instance_number} is ready')
        PREP_EVENTS[self.instance_number - 1].set()
        self.add_line(f'Consumer {self.instance_number} done said it is ready')

        try:
            async for message in consumer:
                await self.prepare_order(message.value)
        except Exception as e:
            self.add_line(f'Exception receiving message {e}')
            await consumer.stop()
        finally:
            self.add_line(f'Consumer stopping')
            await consumer.stop()

    async def prepare_order(self, order):
        """Prepare an order"""
        self.add_line(f'Order {order["count"]}: {pretty_order(order)}')

        await asyncio.sleep(random.uniform(PREP_FREQ_MIN, PREP_FREQ_MAX))

        #self.add_line(f'Order {order["count"]}: ready')
        self.change_last_line(f'Order {order["count"]}: ready')

    async def on_mount(self):
        asyncio.create_task(self.background_task())

    async def on_shutdown(self, event: events.Shutdown) -> None:
        """Let's see if this works!"""
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None


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
            area4='left,bottom',
            area5='right,bottom',
        )

        grid.place(
            area1=TillWidget(1, 'Till 1 producer'),
            area2=TillWidget(2, 'Till 2 producer'),
            area3=TillWidget(3, 'Till 3 producer'),
            area4=FoodPreparerWidget(1, 'Food Preparer 1 consumer'),
            area5=FoodPreparerWidget(2, 'Food Preparer 2 consumer'),
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

    setup_topics(KAFKA_URI, SSL_CONTEXT, {TOPIC_NAME: 3})

    MyGridApp.run(title="Simple App", log="textual.log")


if __name__ == '__main__':
    main()
