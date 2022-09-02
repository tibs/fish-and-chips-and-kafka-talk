#!/usr/bin/env python3

"""demo5-with-added-cook.py - the first demonstration for my talk "Fish and Chips and Apache Kafka®"

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
import itertools

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


TOPIC_NAME_ORDERS = 'DEMO5-ORDERS'
TOPIC_NAME_COOK = 'DEMO5-COOK'

# Bounds on how often a new order occurs
ORDER_FREQ_MIN = 1.0
ORDER_FREQ_MAX = 1.5

# Bounds on how long it takes to prepare an order
PREP_FREQ_MIN = 0.9
PREP_FREQ_MAX = 1.3

# Bounds on how long it takes to cook an order
COOK_FREQ_MIN = 3.0
COOK_FREQ_MAX = 3.2

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

    die_roll = random.randrange(6) + 1  # die have 1-6 dots :)
    if die_roll == 6:
        order = {
            'order': [
                ['cod', 'chips'],
                ['plaice', 'chips'],
            ]
        }
    elif die_roll == 5:
        order = {
            'order': [
                ['cod', 'chips'],
                ['chips', 'chips'],
            ]
        }
    elif die_roll == 4:
        order = {
            'order': [
                ['chips'],
            ]
        }
    else:
        order = {
            'order': [
                ['cod', 'chips'],
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
    description = ', '.join(parts)

    if 'ready' in order and order['ready']:
        description = f'✓ {description}'

    return description


class TillWidget(Widget):

    count = 0
    lines = deque(maxlen=MAX_LINES)

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

    def add_line(self, text):
        """Add a line of text to our scrolling display"""
        self.lines.append(text)
        self.refresh()
        self.app.refresh()

    async def make_order(self, producer):
        """Make a new order ("from a custoemr")"""
        order = await new_order()

        self.count += 1
        order['count'] = self.count

        order['count'] = count = await OrderNumber.get_next_order_number()
        order['till'] = '1'  # we only have one till

        self.add_line(
            f'Got order {self.count}: {pretty_order(order)} at {datetime.now().strftime("%H:%M:%S")}'
        )

        await producer.send(TOPIC_NAME_ORDERS, order)

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
            consumer = aiokafka.AIOKafkaConsumer(
                TOPIC_NAME_ORDERS,
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
            self.producer = aiokafka.AIOKafkaProducer(
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
            await self.producer.start()
        except Exception as e:
            self.add_line(f'Producer start Exception {e.__class__.__name__} {e}')
            return
        self.add_line('Producer started')

        try:
            while True:
                async for message in consumer:
                    await self.prepare_order(message.value)
        except Exception as e:
            self.add_line(f'Exception receiving message {e}')
            await producer.stop()
        finally:
            self.add_line(f'Consumer stopping')
            await consumer.stop()

    def all_order_available(self, order):
        """Work out if all of the order can be prepared immediately

        Note: alters the order
        """

        # If the order isn't marked "ready or not", look to see if it
        # contains plaice. If it does, it needs that plaice to be cooked
        if 'ready' not in order:
            all_items = itertools.chain(*order['order'])
            order['ready'] = 'plaice' not in all_items

        return order['ready']

    async def prepare_order(self, order):
        """Prepare an order"""
        order_available = self.all_order_available(order)
        start = datetime.now()
        self.add_line(
            f'Received order {order["count"]} at {datetime.now().strftime("%H:%M:%S")}: {pretty_order(order)}'
            )

        if order_available:
            await asyncio.sleep(random.uniform(PREP_FREQ_MIN, PREP_FREQ_MAX))

            lapse = str(datetime.now() - start)[5:-4]  # lost the first and last few digits
            self.change_last_line(
                f'Finished order {order["count"]} of {start.strftime("%H:%M:%S")} after {lapse}: {pretty_order(order)}'
                )
        else:
            await self.producer.send(TOPIC_NAME_COOK, order)
            self.change_last_line(
                f'Sending order {order["count"]} of {start.strftime("%H:%M:%S")} to COOK: {pretty_order(order)}'
                )

    def add_line(self, text):
        """Add a line of text to our scrolling display"""
        self.lines.append(text)
        self.refresh()
        self.app.refresh()

    def change_last_line(self, text):
        """Change the last line of text to our scrolling display"""
        self.lines[-1] = text
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


class CookWidget(Widget):

    count = 0
    lines = deque(maxlen=MAX_LINES)

    async def background_task(self):
        try:
            consumer = aiokafka.AIOKafkaConsumer(
                TOPIC_NAME_COOK,
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
            self.producer = aiokafka.AIOKafkaProducer(
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
            await self.producer.start()
        except Exception as e:
            self.add_line(f'Producer start Exception {e.__class__.__name__} {e}')
            return
        self.add_line('Producer started')

        try:
            async for message in consumer:
                await self.cook_order(message.value)
        except Exception as e:
            self.add_line(f'Exception receiving message {e}')
            await producer.stop()
        finally:
            self.add_line(f'Consumer stopping')
            await consumer.stop()

    async def cook_order(self, order):
        """Cook (the plaice in) an order"""
        start = datetime.now()
        self.add_line(
            f'Received order {order["count"]} at {datetime.now().strftime("%H:%M:%S")}: {pretty_order(order)}'
            )

        # "Cook" the (plaice in the) order
        await asyncio.sleep(random.uniform(COOK_FREQ_MIN, COOK_FREQ_MAX))

        # It's important to remember to mark the order as ready now!
        # (forgetting to do that means the order will keep going round the loop)
        order['ready'] = True

        lapse = str(datetime.now() - start)[5:-4]  # lost the first and last few digits
        self.change_last_line(
            f'Cooked order {order["count"]} of {start.strftime("%H:%M:%S")} after {lapse}: {pretty_order(order)}'
            )

        await self.producer.send(TOPIC_NAME_ORDERS, order)
        self.add_line(
            f'Order {order["count"]} of {start.strftime("%H:%M:%S")} available: {pretty_order(order)}'
            )

    def add_line(self, text):
        """Add a line of text to our scrolling display"""
        self.lines.append(text)
        self.refresh()
        self.app.refresh()

    def change_last_line(self, text):
        """Change the last line of text to our scrolling display"""
        self.lines[-1] = text
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
        return Panel(text, title="Consumer (COOK)")


class MyGridApp(App):

    async def on_load(self, event: events.Load) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        await self.bind("q", "quit", "Quit")

    async def on_mount(self, event: events.Mount) -> None:
        grid = await self.view.dock_grid(edge='left', name='left-grid')

        grid.add_column('left', fraction=1, min_size=20)
        grid.add_column('right', fraction=1, min_size=20)

        grid.add_row('top', fraction=1)
        grid.add_row('bottom', fraction=1)

        grid.add_areas(
            area1='left,top',
            area2='right,top',
            area3='left-start|right-end,bottom',
        )

        grid.place(
            area1=TillWidget(),
            area2=FoodPreparerWidget(),
            area3=CookWidget(),
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
    print(f'Making sure topic {TOPIC_NAME_ORDERS} and {TOPIC_NAME_COOK} are not there')
    for name in (TOPIC_NAME_ORDERS, TOPIC_NAME_COOK):
        try:
            response = admin.delete_topics([name])
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
        if TOPIC_NAME_ORDERS not in topics and TOPIC_NAME_COOK not in topics:
            break
        count += 1
        time.sleep(1)

    print(f'Making sure topic {TOPIC_NAME_ORDERS} and {TOPIC_NAME_COOK} *are* there')
    topic1 = NewTopic(name=TOPIC_NAME_ORDERS, num_partitions=1, replication_factor=1)
    topic2 = NewTopic(name=TOPIC_NAME_COOK, num_partitions=1, replication_factor=1)
    admin.create_topics([topic1, topic2])
    # Because we're meant to have deleted them, we shouldn't get a TopicAlreadyExistsError

    count = 0
    while count < 10:
        topics = admin.list_topics()
        print(f'Topics: {topics}')
        if TOPIC_NAME_ORDERS in topics and TOPIC_NAME_COOK in topics:
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

    setup_partitions(KAFKA_URI, SSL_CONTEXT)

    MyGridApp.run(title="Simple App", log="textual.log")


if __name__ == '__main__':
    main()
