Fish and Chips and Apache Kafka®
================================


.. class:: title-slide-info

    By Tibs (they / he)

    .. raw:: pdf

       Spacer 0 30

    Slides and accompanying material at https://github.com/tibs/fish-and-chips-and-kafka-talk

.. footer::

   *tony.ibbs@aiven.io* / *@much_of_a*

   .. Add a bit of space at the bottom of the footer, to stop the underlines
      running into the bottom of the slide
   .. raw:: pdf

      Spacer 0 5

What we'll cover
----------------

* Me and messaging and Apache Kafka®
* Fish and chips

  * How to talk to Kafka
  * Start with a simple model and work up
  * There's a demo you can play with afterwards


Some message problems I've cared about
--------------------------------------

* between components on a Set Top Box

* configuration between microservices

* to / from Internet of Things devices, and their support systems

Kafka is a very good fit for the IoT cases, maybe less so for the others

.. Respectively, maybe want:

   * zeromq or similar - lightweight, fast (or, of course kbus <smile>)
   * a state machine and/or a persistent key/value store
   * Apache Kafka

What I want from messaging
--------------------------

* multiple producers *and* multiple consumers
* single delivery
* guaranteed delivery
* resumes safely if system crashes
* no back pressure handling (queue does not fill up)

Enter, Apache Kafka®
--------------------

.. Actually give the high-level explanation of what Kafka *is*

Kafka explanation, part 1
-------------------------

*Add pictures!*

Messages are *Events*

Can have multiple *Producers* and *Consumers*

A Producer send a message to a named *Topic*,
each Consumer reads from one Topic

Kafka explanation, part 2
-------------------------

*Add pictures!*

*Partitions* can be used to "spread the load" within a Topic

  Messages go to a partition based on their *Key*, and Consumers read from one or
  more partitions in their chosen Topic

Let's model a fish-and-chip shop
--------------------------------

We start with a shop that

* just handles cod and chips
* which are always ready to be served

Glossary
--------

.. I'm sure everyone loves a glossary

* **Cod**: the traditional white fish for english fish-and-chip shops
* **Chips**: fatter, possibly soggier, french fries
* **Plaice**: a flat fish
* **Till**: a cash register

Serving a customer
------------------

.. raw:: pdf

   Spacer 0 30

.. TILL -> [ORDER] -> FOOD-PREPARER

.. image:: images/Fish-Till-Preparer.png
   :width: 100%

An order
--------

.. code:: json

   {
      "order": 271,
      "parts": [
          ["cod", "chips"],
          ["chips", "chips"],
      ]
   }

Show first demo
---------------

.. Yes, this is deliberately repeating the image from above,
   because this is what I intend to demo

   DEMO: simple TILL -> [ORDER] -> FOOD-PREPARER

.. raw:: pdf

   Spacer 0 30

.. TILL -> [ORDER] -> FOOD-PREPARER

.. image:: images/Fish-Till-Preparer.png
   :width: 100%


Libraries
---------

`kafka-python`: https://github.com/dpkp/kafka-python

`aiokafka`: https://github.com/aio-libs/aiokafka

`Textual`: https://github.com/Textualize/textual


Code: Producer
--------------

.. code:: python

    from kafka import KafkaProducer

    producer = kafka.KafkaProducer(
        bootstrap_servers=f"{HOST}:{SSL_PORT}",
        security_protocol="SSL",
        ssl_cafile=f'{certs_dir}/ca.pem',
        ssl_certfile=f'{certs_dir}/service.cert',
        ssl_keyfile=f'{certs_dir}/service.key',
        value_serializer=lambda v: json.dumps(v).encode('ascii'),

    while SHOP_IS_OPEN:
        # get order from CUSTOMER
        producer.send('ORDER'), order)

Code: Consumer
--------------

.. code:: python

    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        "ORDER",
        bootstrap_servers=f"{HOST}:{SSL_PORT}",
        security_protocol="SSL",
        ssl_cafile="ca.pem",
        ssl_certfile="service.cert",
        ssl_keyfile="service.key",
        value_deserializer = lambda v: json.loads(v.decode('ascii')),
    )

    for msg in consumer:
        print(f'Message {msg.value}')

Code: Asynchronous - needs SSL context
--------------------------------------

.. code:: python

    import aiokafka.helpers

    context = aiokafka.helpers.create_ssl_context(
        cafile=CERTS_DIR / "ca.pem",
        certfile=CERTS_DIR / "service.cert",
        keyfile=CERTS_DIR / "service.key",
    )

Code: Asynchronous Producer
---------------------------

.. code:: python

    from aiokafka import AIOKafkaProducer

    producer = aiokafka.AIOKafkaProducer(
        bootstrap_servers=f"{HOST}:{SSL_PORT}",
        security_protocol="SSL",
        ssl_context=context,
        value_serializer=lambda v: json.dumps(v).encode('ascii'),
    )

    await producer.start()

    while SHOP_IS_OPEN:
        # get order from CUSTOMER
        await producer.send_and_wait('ORDERS', message)

Code: Asynchronous Consumer
---------------------------

.. code:: python

    consumer = aiokafka.AIOKafkaConsumer(
        'ORDERS',
        bootstrap_servers=f"{HOST}:{SSL_PORT}",
        security_protocol="SSL",
        ssl_context=context,
        value_deserializer = lambda v: json.loads(v.decode('ascii')),
    )

    await consumer.start()

    async for message in consumer:
        print(f'Received {message.value}')

More customers - add more TILLs
-------------------------------

Customers now queue at multiple TILLs, each TILL is a Producer.

Use the *queue number* as the key to split the events up into partitions

Diagram
-------

Diagram with 3 TILLs but still 1 FOOD-PREPARER ::

  TILL
      \
  TILL -> [ORDER with partitions] -> FOOD-PREPARER
      /
  TILL

An order with multiple TILLs
----------------------------

.. code:: json

   {
      "order": 271,
      "till": 3,
      "parts": [
          ["cod", "chips"],
          ["chips", "chips"],
      ]
   }

How we alter the code
---------------------

*Correct this once I know what I'm actually using in the demo*

.. code:: python

        #await producer.send(PARTITIONED_TOPIC_NAME, value=order, key='till')

        #await producer.send_and_wait(PARTITIONED_TOPIC_NAME, value=order)

        await producer.send(PARTITIONED_TOPIC_NAME, value=order, partition=self.till_number-1)

Show demo: multiple TILLs
-------------------------

.. The multiple tills picture again

::

  TILL
      \
  TILL -> [ORDER with partitions] -> FOOD-PREPARER
      /
  TILL

But now the FOOD-PREPARER is too busy
-------------------------------------

So add multiple *consumers*

::

  TILL                             > FOOD-PREPARER
      \                           /
  TILL -> [ORDER with partitions] -> FOOD-PREPARER
      /                           \
  TILL                             > FOOD-PERPARER

How we alter the code
---------------------

...


Show demo: multiple TILLs and multiple FOOD-PREPARERS
-----------------------------------------------------

.. The multiple tills picture again

::

  TILL                             > FOOD-PREPARER
      \                           /
  TILL -> [ORDER with partitions] -> FOOD-PREPARER
      /                           \
  TILL                             > FOOD-PERPARER


Cod or plaice
-------------

Plaice needs to be cooked

So we need a COOK to cook it

.. Keep it to the simple cod-and-chips order from demo 1, with COOK added, so it
   isn't too complicated to explain

Participant changes - add COOK
------------------------------

::

  TILL -> [ORDER] -> FOOD-PREPARER
             ^         |
             |      [COOK]
             |         |
             |         V
             +------- COOK

An order with plaice
--------------------

.. code:: json

   {
      "order": 271,
      "till": 3,
      "parts": [
          ["cod", "chips"],
          ["chips", "chips"],
          ["plaice", "chips"],
      ]
   }

Gets turned into...
-------------------

.. code:: json

   {
      "order": 271,
      "till": 3,
      "parts": [
          ["cod", "chips"],
          ["chips", "chips"],
          ["plaice", "chips"],
      ],
      "ready": <boolean>
   }

Code changes to add COOK
------------------------

... see the notes on this

..
   * All orders have a "ready" boolean, which is initially set to False
   * The PREPARER gets the ORDER

     * If the order has "ready" set to True, then everything is available from
       the hot cabinet, the order can be made up and passed to the customer

     * If the order has "ready" set to False, and there is no "plaice" in
       the order, then the PREPARER sets "ready" to True (everything can be made
       up from the hot cabinet) and the order is done

     * If the order has "ready" set to False, but there is "plaice" in the order,
       then the order is sent to the [COOK] topic for the COOK. The COOK sets the
       "ready" boolean to True, and sends the order back to the [ORDER] topic.

   This allows the PREPARER to continue with just one topic to listen to, at the
   penalty of being a little bit horrible (it would get better if/when the Redis
   cache is provided, because then the check for "ready" would be replaced by a
   check against the cache).

   Question: do we want a separate partition for orders from the COOK? Or do we
   want a random partition? (either explicitly or implicitly random)

Demo with COOK
--------------

Show demo of (simple) cod-and-chips order, with COOK

.. Keep it to the simple cod-and-chips order from demo 1, with COOK added, so it
   isn't too complicated to explain


Adding the ANALYST
------------------

::

  TILL -> [ORDER] -> FOOD-PREPARER
                  \
                   +-> ANALYST -> PG

..
   Keep it to the simple cod-and-chips order from demo 1, with ANALYST added, so it
   isn't too complicated to explain. Show some query result from the PG databse
   being updated - perhaps just total number of orders.

Two ways to do the ANALYST
--------------------------

1. Add a new (independent) consumer of [ORDER], and have them write to
   PostgreSQL®

2. Use an Apache Kafka® Connector to connect the [ORDER] topic to PostgreSQL
   without needing to alter the Python code

If I do (1), then we get to choose when to start the ANALYST consuming, and I
can do the toggle to start it. But (2) introduces something nice to know
about, and is probably more realistic.

(Option 1) What we need to do in the code
-----------------------------------------

... *add code for ANALYST consumer, and make it write to PG*

... *add code to read some sort of statistic from PG and report as it changes*

(Option 1) Demo with ANALYST
----------------------------

::

  TILL -> [ORDER] -> FOOD-PREPARER
                  \
                   +-> ANALYST -> PG

*Maybe with a toggle button to start the ANALYST*

(Option 2) Apache Kafka Connectors
----------------------------------

These make it easier to connect Kafka to databases, OpenSearch, etc., without
needing to write Python (or whatever) code.

We shall use this to add our ANALYST

(Option 2) What we need to do in the code
-----------------------------------------

... *add code to *read* some sort of statistic from PG and report as it changes*

(Option 2) Setting up the PostgreSQL table
------------------------------------------

... we assume there's already a database

... we need to define the necessary table

(Option 2) Setting up the Kafka Connector
-----------------------------------------

...

(Option 2) Demo with ANALYST
----------------------------

::

  TILL -> [ORDER] -> FOOD-PREPARER
                  \
                   +-> ANALYST -> PG


Start consuming from a specific offset
--------------------------------------

.. This is probably not going to be in the demo, but I should make sure to
   talk about how to do it, given I said I would in the talk Introduction

*To be added: talking about starting at other offsets*

... to make the new participants start from the start of the events

.. code:: python

        auto_offset_reset="earliest",

(the default is `"latest"`)

Summary so far
--------------

We know how to model the ordering and serving of our cod and chips

We know how to share the order information with other data users

We know how to scale with multiple Producers and Consumers


Homework: Sophisticated model, with caching
-------------------------------------------

Use a Redis cache to simulate the hot cabinet

Redis has entries for the hot cabinet content, keyed by ``cod``, (portions of)
``chips`` and ``plaice``. We start with 0 for all of them.

Homework continued
------------------

PRODUCER compares the order to the counts in the cache. If there's enough
"stuff" to make the order up, decrements the cache appropriately, and that's
done.

If not, sends the order to the COOK, who updates the cache - for ``plaice``
just adds as many as are needed, for the others, if they go below a threshold,
adds a standard quantity back in ("cooking in batches"). Then sends the order
back into the [ORDER] topic.

.. This last is why the slightly icky "setting a boolean flag" trick isn't so
   bad, as it is sort of simulating what we are doing above. It would be worth
   explaining this, at this point

Final summary
-------------


We know how to model the ordering and serving of our cod and chips

We know how to scale with multiple Producers and Consumers

We know how to share the order information with other data users

We had a brief look at modelling "plaice" orders

We talked briefly about how one might model the hot cabinet in more detail

Acknowledgements
----------------

Apache,
Apache Kafka,
Kafka,
are either registered trademarks or trademarks of the Apache Software Foundation in the United States and/or other countries

Postgres and PostgreSQL are trademarks or registered trademarks of the
PostgreSQL Community Association of Canada, and used with their permission

.. I think I can omit the Redis ``*`` in the context of the slides

Redis is a registered trademark of Redis Ltd. Any rights therein are reserved to Redis Ltd.

.. -----------------------------------------------------------------------------

.. raw:: pdf

    PageBreak twoColumnNarrowRight

Fin
---

Get a free trial of Aiven services at
https://console.aiven.io/signup/email

Also, we're hiring! See https://aiven.io/careers

Written in reStructuredText_, converted to PDF using rst2pdf_

..
    |cc-attr-sharealike| This slideshow is released under a
    `Creative Commons Attribution-ShareAlike 4.0 International License`_

Slides and accompanying material
|cc-attr-sharealike|
at https://github.com/tibs/fish-and-chips-and-kafka-talk

.. image:: images/qr_fish_chips_kafka.png
    :align: right
    :scale: 90%

.. And that's the end of the slideshow

.. |cc-attr-sharealike| image:: images/cc-attribution-sharealike-88x31.png
   :alt: CC-Attribution-ShareAlike image
   :align: middle

.. _`Creative Commons Attribution-ShareAlike 4.0 International License`: http://creativecommons.org/licenses/by-sa/4.0/

.. _`Write the Docs Prague 2022`: https://www.writethedocs.org/conf/prague/2022/
.. _reStructuredText: http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html
.. _rst2pdf: https://rst2pdf.org/
.. _Aiven: https://aiven.io/
.. _`Write the Docs slack`: https://writethedocs.slack.com
.. _`#testthedocs`: https://writethedocs.slack.com/archives/CBWQQ5E57
