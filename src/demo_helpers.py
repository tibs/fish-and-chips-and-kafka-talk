#!/usr/bin/env python3

"""Helpers and common code for the demo programs.
"""

import asyncio
import random

# We need kafka-python for admin tasks
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, UnknownTopicOrPartitionError

def setup_topics(kafka_uri, ssl_context, topic_dict):
    """Make sure that the topi we want exists, with the correct number of partitions.

    Also makes sure that we won't see any old events.

    `topic_dict` is a dictionary of `topic_name`: `num_partitions`
    """

    # For this we still need to use the more traditional kafka-python library
    admin = KafkaAdminClient(
        bootstrap_servers=kafka_uri,
        security_protocol="SSL",
        ssl_context=ssl_context,
    )

    # First, delete the topic if it already exists.
    # This is our so-clumsy way of making sure we don't have any data lying around
    # from a previous run of the demo
    for topic_name in topic_dict:
        print(f'Making sure topic {topic_name} is not there')
        try:
            response = admin.delete_topics([topic_name])
            print(f'Response {response}')
        except UnknownTopicOrPartitionError:
            # If already didn't exist, we're OK with that
            pass

    # TODO The following is icky in various ways, not least because it's not
    # actually checking that we've deleted the topic properly, and also because
    # we're deleting the topic as a proxy for sorting out the "please ignore old
    # data" problem

    count = 0
    while count < 10:
        topics = admin.list_topics()
        print(f'Topics: {topics}')
        if not any(x in topics for x in topic_dict.keys()):  # None of the topic names is present
            break
        count += 1
        time.sleep(1)

    print(f'Making sure topics {", ".join(topic_dict.keys())} now exist')
    topics = [
        NewTopic(name=name, num_partitions=num_partitions, replication_factor=1)
        for name, num_partitions in topic_dict.items()
    ]
    admin.create_topics(topics)
    # Because we're meant to have deleted them, we shouldn't get a TopicAlreadyExistsError

    count = 0
    while count < 10:
        topics = admin.list_topics()
        print(f'Topics: {topics}')
        names = set(topic_dict.keys())
        if names.issubset(topics):  # All our topic names are present
            return
        count += 1
        time.sleep(1)


class OrderNumber:
    """An order number that we can increment safely from different async tasks"""

    lock = asyncio.Lock()
    count = 0

    @classmethod
    async def get_next_order_number(cls):
        async with cls.lock:
            cls.count += 1
            return cls.count


# Bounds on how often a new order occurs
ORDER_FREQ_MIN = 1.0
ORDER_FREQ_MAX = 1.5


async def new_order(allow_plaice=False):
    """Wait a random time, return a random order.

    Note that it doesn't include the order number, because that can only be
    set by the TILL receiving the order.
    """

    # Wait somewhere between 0.5 and 1 seconds (these are fast customers!)
    await asyncio.sleep(random.uniform(ORDER_FREQ_MIN, ORDER_FREQ_MAX))

    die_roll = random.randrange(6) + 1  # die have 1-6 dots :)
    if die_roll == 6 and allow_plaice:
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


class DemoWidgetMixin(Widget):
    """Provide common functionality for our demo widgets

    Subclass, and then make multuple instances of the subclass, which will share
    the same `lines` dictionary.
    """

    lines = {}  # output lines, per preparer

    instance_number = 0
    consumer = None

    def __init__(self, instance_number: int, name: str | None = None) -> None:

        if name is None:
            name = f'{self.__class__.__name__}_{instance_number}'

        self.instance_number = instance_number
        self.lines[instance_number] = deque(maxlen=MAX_LINES)
        super().__init__(name)

    def add_line(self, text):
        """Add a line of text to our scrolling display"""
        self.lines[self.instance_number].append(text)
        self.refresh()
        self.app.refresh()

    def change_last_line(self, text):
        """Change the last line of text to our scrolling display"""
        self.lines[self.instance_number][-1] = text
        self.refresh()
        self.app.refresh()

    def make_text(self, height):
        lines = list(self.lines[self.instance_number])
        # The value of 2 seems unnecessarily magical
        # I assume it's the widget height - the panel border
        return '\n'.join(lines[-(height-2):])

    def render(self):
        text = self.make_text(self.size.height)
        return Panel(text, title=self.name)
