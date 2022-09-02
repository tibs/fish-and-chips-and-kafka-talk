#!/usr/bin/env python3

"""demo2-cod-and-chips-3tills-2preparers.py - the third demonstration for my talk "Fish and Chips and Apache Kafka®"

Shows:

* "customer" makes up an order
* one of the three TILLs sends the order to the ORDER topic
* one of the two FOOD-PREPARERs receives the order from the ORDER topic

Note on timing:

* We want customers to make orders at perceptibly random intervals, but not so
  slow as to be boring.
* We want the two food preparers to have (more than enough) time to make up an order

TODO items

* I still haven't figured out how to automatically send messages to partitions without
  actually specifiying the target partition number.
* Ideally, I'd start the consumers before the producers, so I need to set up some sort
  of synchronisation.
* Stopping (by typing `q` seems to give me errors, rather than ending nicely. Probably
  because I'm not telling things to tidy up in the right way.
* If I don't clear out the events from previous runs, then I still tend to see them.
  So either do that (perhaps delete the topic and then reinvent it), or (better) do
  proper "start listening to events after time X" setup, which would be nice to show
  anyway.

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


TOPIC_NAME = 'DEMO3_ORDERS'

CONSUMER_GROUP = 'DEMO3_ALL_ORDERS'

# Bounds on how long it takes to prepare an order
PREP_FREQ_MIN = 1.0
PREP_FREQ_MAX = 2.0

# Maximum number of lines to keep for a widget display
MAX_LINES = 40

# I'm not keen on globals, but sometimes they're convenient,
# and they're not *quite* so bad in a program (as opposed to
# when writing a library)
global KAFKA_URI    # for the moment
global CERTS_DIR    # for the moment
global SSL_CONTEXT  # for the moment


class TillWidget(Widget):

    lines = {}  # output lines, per till

    till_number = 0
    producer = None

    def __init__(self, till_number: int, name: str | None = None) -> None:

        if name is None:
            name = f'Till_{till_number}'

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

        try:
            while True:
                await self.make_order(producer)
        except Exception as e:
            self.add_line(f'Exception sending message {e}')
        finally:
            self.add_line(f'Producer stopping')
            await producer.stop()

    def add_line(self, text):
        """Add a line of text to our scrolling display"""
        self.lines[self.till_number].append(text)
        self.refresh()
        self.app.refresh()

    async def make_order(self, producer):
        """Make a new order ("from a customer")"""
        order = await new_order()

        order['count'] = count = await OrderNumber.get_next_order_number()
        order['till'] = str(self.till_number)

        self.add_line(
            f'Got order {count}: {pretty_order(order)} at {datetime.now().strftime("%H:%M:%S")}'
        )

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
        await producer.send(TOPIC_NAME, value=order, partition=self.till_number-1)

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

    async def on_shutdown(self, event: events.Shutdown) -> None:
        """Let's see if this works!"""
        if self.producer:
            await self.producer.stop()
            self.producer = None


class FoodPreparerWidget(Widget):

    lines = {}  # output lines, per preparer

    prep_number = 0
    consumer = None

    def __init__(self, prep_number: int, name: str | None = None) -> None:

        if name is None:
            name = f'Preparer_{prep_number}'

        self.prep_number = prep_number
        self.lines[prep_number] = deque(maxlen=MAX_LINES)
        super().__init__(name)

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
            while True:
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
        start = datetime.now()
        self.add_line(
            f'Received order {order["count"]} at {start.strftime("%H:%M:%S")}: {pretty_order(order)}'
            )

        await asyncio.sleep(random.uniform(PREP_FREQ_MIN, PREP_FREQ_MAX))

        lapse = datetime.now() - start
        self.change_last_line(
            f'Finished order {order["count"]} of {start.strftime("%H:%M:%S")} after {lapse}: {pretty_order(order)}'
            )

    def add_line(self, text):
        """Add a line of text to our scrolling display"""
        self.lines[self.prep_number].append(text)
        self.refresh()
        self.app.refresh()

    def change_last_line(self, text):
        """Change the last line of text to our scrolling display"""
        self.lines[self.prep_number][-1] = text
        self.refresh()
        self.app.refresh()

    async def on_mount(self):
        asyncio.create_task(self.background_task())

    def make_text(self, height):
        lines = list(self.lines[self.prep_number])
        # The value of 2 seems unnecessarily magical
        # I assume it's the widget height - the panel border
        return '\n'.join(lines[-(height-2):])

    def render(self):
        text = self.make_text(self.size.height)
        return Panel(text, title=f"Consumer (FOOD-PREPARER {self.prep_number})")

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
            area1=TillWidget(1),
            area2=TillWidget(2),
            area3=TillWidget(3),
            area4=FoodPreparerWidget(1),
            area5=FoodPreparerWidget(2),
        )


def setup_partitions(kafka_uri, ssl_context):
    # For this we still need to use the more traditional kafka-python library
    admin = KafkaAdminClient(
        bootstrap_servers=KAFKA_URI,
        security_protocol="SSL",
        ssl_context=SSL_CONTEXT,
    )

    # First, delete the topic if it already exists.
    # This is our so-clumsy way of making sure we don't have any data lying around
    # from a previous run of the demo
    print(f'Making sure topic {TOPIC_NAME} is not there')
    try:
        response = admin.delete_topics([TOPIC_NAME])
        print(f'Response {response}')
    except UnknownTopicOrPartitionError as e:
        # If it already exists, we'll assume it has the right form
        return

    # TODO The following is icky in various ways, not least because it's not
    # actually checking that we've deleted the topic properly, and also because
    # we're deleting the topic as a proxy for sorting out the "please ignore old
    # data" problem

    count = 0
    while count < 10:
        topics = admin.list_topics()
        print(f'Topics: {topics}')
        if TOPIC_NAME not in topics:
            break
        count += 1
        time.sleep(1)

    print(f'Making sure topic {TOPIC_NAME} *is* there')
    topic = NewTopic(name=TOPIC_NAME, num_partitions=3, replication_factor=1)
    admin.create_topics([topic])
    # Because we're meant to have deleted it, we shouldn't get a TopicAlreadyExistsError

    count = 0
    while count < 10:
        topics = admin.list_topics()
        print(f'Topics: {topics}')
        if TOPIC_NAME in topics:
            return
        count += 1
        time.sleep(1)

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
