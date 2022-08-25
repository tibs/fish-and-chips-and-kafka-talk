#!/usr/bin/env python3

"""poc1.py - Proof of Concept #1 - using a KafkaProducer to send records to Apache Kafka

This helped me work out that I had all the connection details right, that I had
set up my Apache Kafka service correctly, and so on.
"""

import click
import pathlib
import json
import kafka
import time

from kafka.errors import KafkaError

from collections import deque

from datetime import datetime

TOPIC_NAME = 'fish-and-chips'

def background_task(kafka_uri, certs_dir):
    print(f'Creating producer for {kafka_uri}')
    try:
        producer = kafka.KafkaProducer(
            bootstrap_servers=kafka_uri,
            security_protocol="SSL",
            ssl_cafile=f'{certs_dir}/ca.pem',
            ssl_certfile=f'{certs_dir}/service.cert',
            ssl_keyfile=f'{certs_dir}/service.key',
            value_serializer=lambda v: json.dumps(v).encode('ascii'),
        )
    except Exception as e:
        print(f'Producer Exception {e.__class__.__name__} {e}')
        return
    print('Producer created')

    count = 0
    while True:
        time.sleep(0.5)
        count += 1
        message = { 'message': str(count), 'method': 'traditional' }
        print(f'Sending message {message!r}')
        try:
            future = producer.send(TOPIC_NAME, message)
            print(f'Message sent: {future}')
            # We can use the `future` to wait for the message to (have been) sent,
            # or we *could* just use `publisher.flush()` which would block until
            # it has been sent.
            try:
                record_metadata = future.get(timeout=5)
            except KafkaError as e:
                print(f'Future timed out {e}')
                return
        except Exception as e:
            print(f'Send Exception {e.__class__.__name__} {e}')
            print('Stopping')
            return


@click.command(no_args_is_help=True)
@click.argument('kafka_uri', required=True)
@click.option('-d', '--certs-dir', default='creds',
              help='directory containing the ca.pem, service.cert and service.key files')
def main(kafka_uri, certs_dir):
    """A fish and chip shop demo, using Apache Kafka®
    """

    print(f'Kafka URI {kafka_uri}, certs dir {certs_dir}')

    background_task(kafka_uri, certs_dir)


if __name__ == '__main__':
    main()
