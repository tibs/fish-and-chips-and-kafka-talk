#!/usr/bin/env python3

"""poc2.py - Proof of Concept #2 - using an AIOKafkaProducer to send records to Apache Kafka

This is a version of PoC #1 just changed to use AIOKafka, without any other additional
complexity. This allowed me to check that I was doing the async handling correctly.
"""

import asyncio
import click
import pathlib
import json
import aiokafka
import aiokafka.helpers

from collections import deque

from datetime import datetime

TOPIC_NAME = 'fish-and-chips'

async def background_task(kafka_uri, certs_dir):
    try:
        context = aiokafka.helpers.create_ssl_context(
            cafile=certs_dir / "ca.pem",
            certfile=certs_dir / "service.cert",
            keyfile=certs_dir / "service.key",
        )
    except Exception as e:
        print(f'SSL Exception {e.__class__.__name__} {e}')
        return
    print('SSL context acquired')

    print(f'Creating producer for {kafka_uri}')
    try:
        producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=kafka_uri,
            security_protocol="SSL",
            ssl_context=context,
            value_serializer=lambda v: json.dumps(v).encode('ascii'),
        )
    except Exception as e:
        print(f'Producer Exception {e.__class__.__name__} {e}')
        return
    print('Producer created')

    try:
        await producer.start()
    except Exception as e:
        print(f'Producer start Exception {e.__class__.__name__} {e}')
        return
    print('Producer started')

    count = 0
    while True:
        await asyncio.sleep(0.5)
        count += 1
        message = { 'message': str(count), 'method': 'async' }
        print(f'Sending message {message!r}')
        try:
            await producer.send(TOPIC_NAME, message)
            print('Message sent')
        except Exception as e:
            print(f'Send Exception {e.__class__.__name__} {e}')
            print('Stopping')
            await producer.stop()
            print('Stopped')


@click.command(no_args_is_help=True)
@click.argument('kafka_uri', required=True)
@click.option('-d', '--certs-dir', default='creds',
              help='directory containing the ca.pem, service.cert and service.key files')
def main(kafka_uri, certs_dir):
    """A fish and chip shop demo, using Apache Kafka®
    """

    print(f'Kafka URI {kafka_uri}, certs dir {certs_dir}')

    task = background_task(kafka_uri, pathlib.Path(certs_dir))
    asyncio.run(task)


if __name__ == '__main__':
    main()
