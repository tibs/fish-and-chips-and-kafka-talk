
================================
Fish and Chips and Apache Kafka®
================================

By Tibs / Tony Ibbs (they / he)

A talk to be given at PyCon UK 2022

.. contents::

Abstract
========

.. note:: *From the submission*

Apache Kafka® is the de facto standard in the data streaming world for sending
messages from multiple producers to multiple consumers, in a fast, reliable
and scalable manner.

Come and learn the basic concepts and how to use it, by modelling a fish and
chips shop!

Introduction
============

.. note:: *Steal from the submission and prune*

Handling large numbers of events is an increasing challenge in our cloud
centric world. For instance, in the IoT (Internet of Things) industry, devices
are all busy announcing their current state, which we want to
manage and report on, and meanwhile we want to send firmware and other updates
*back* to specific groups of devices.

Traditional messaging solutions don't scale well for this type of problem. We
want to guarantee not to lose events, to handle high volumes in a timely
manner, and to be able to distribute message reception or production across
multiple consumers or producers (compare to sharding for database reads).

As it turns out, there is a good solution available: Apache Kafka® - it
provides all the capabilities we are looking for.

In this talk, rather than considering some imaginary IoT scenario, I'm going
to look at how one might use Kafka to model the events required to run a fish
and chip shop: ordering (plaice and chips for me, please), food preparation,
accounting and so on.

I'll demonstrate handling of multiple producers and consumers, automatic routing of
events as new consumers are added, persistence, which allows a new consumer to
start consuming events from the past, and more.

Actual notes
============

.. note:: Do I start with `What I want from messaging`_, and then do `Fish and
          chip shop`_, or do I reverse the order?

Introduction
------------

I've been working, on and off, with sending messages between systems
throughout my career as a software developer, including messages between
processes on a set top box, messages to/from IoT (Internet of Things)
devices and their support systems, and configuration messages between
microservices.

For many of those purposes, I would now expect to use Apache Kafka, and this
talk aims to show why it is a useful addition to the messaging toolkit.

Stolen introduction
-------------------

Description from the proposal:

Handling large numbers of events is an increasing challenge in our cloud
centric world. For instance, in the IoT (Internet of Things) industry, devices
are all busy announcing their current state, which we want to
manage and report on, and meanwhile we want to send firmware and other updates
*back* to specific groups of devices.

Traditional messaging solutions don't scale well for this type of problem. We
want to guarantee not to lose events, to handle high volumes in a timely
manner, and to be able to distribute message reception or production across
multiple consumers or producers (compare to sharding for database reads).

As it turns out, there is a good solution available: Apache Kafka® - it
provides all the capabilities we are looking for.

In this talk, rather than considering some imaginary IoT scenario, I'm going
to look at how one might use Kafka to model the events required to run a fish
and chip shop: ordering (plaice and chips for me, please), food preparation,
accounting and so on.

I'll demonstrate handling of multiple producers and consumers, automatic routing of
events as new consumers are added, persistence, which allows a new consumer to
start consuming events from the past, and more.

What I want from messaging
--------------------------

Let's consider what I want for a system that can handle large scale systems,
such as the aforementioned IoT examples:

* multiple producers *and* multiple consumers
* single delivery (deliver once to on consumer)
* guaranteed delivery
* no problems if queue crashes and resumes
* no need for back pressure handling (queue filling up)
* ... what else?

Why not to build it around a database
-------------------------------------

Just don't, really.

Mainly it means you have to *implement* all of a queuing system, over
something that is designed for different purposes / constraints.

Brief explanation of Kafka
--------------------------

Producers, Consumers

Events, topics, partitions



Fish and chip shop
------------------

A nice picture of a fish and chip shop, and/or a fryer/hot-cabinet, would be
nice.

Then need to decide where in the slide deck it should go.

The fish and chip shop model
----------------------------

Start with a diagram showing my plan!

*All the participant and topic names could be improved. I've used UPPER-CASE
names to make it easier to change them later on.*

First model
-----------

This model shows the progress of orders through the system, and how there may
be multiple interests in the data.

Participants
------------

* CUSTOMER - implicit, makes an order (we don't model them directly)
* TILL - takes order from CUSTOMER, sends order to 'ORDER' topic
* FOOD-PREPARER - Listens to 'ORDER' topic.

  "Makes up" the order (for our model, this doesn't look like much!).

  Sends (completed) order on to 'READY' topic.

* COOK - a notional participant, we don't model them at this stage

* COUNTER - listens to 'READY' topic, passes finished order on to
  customer (again, we don't model the customer directly)

* ACCOUNTANT - listens to 'ORDER' topic, calculates incoming money - may be
  putting each order into a database, or even a spreadsheet(!)

* STATISTICIAN - listens to (all of) 'ORDER' topic, and sends data to
  OpenSearch for analysis. For instance, percentage of orders that needed
  sending to cook, number of orders of each type of food (cod, plaice, chips),
  and so on.

  *Ideally, the demo would show some statistics as they occur*

* STOCKIST - listens to (all of) 'ORDER' topic, to work out what consumables
   (portions of chips, cod, plaice) are being used. May also be using
   OpenSearch, or might be using a database or spreasheet.

*All these names could be improved*

Cod and chips
-------------

We start with a shop that just handles cod and chips, which are always ready
to be served (the cook keeps the hot cabinet topped up as necessary)

An order
--------

.. code:: json

   {
      'order': 271,
      'customer': 'Tibs',
      'parts': [
          ['cod', 'chips'],
          ['chips', 'chips'],
      ]
   }


Cod and chips participants
--------------------------

... all of the above, except the COOK, who doesn't need messages

Let's build some code
---------------------

A series of slides showing how to do the above, in sections.

*Do I just show use of python-kafka, for simplicity?*

*Probably worth doing so, but mention the demo is using AIOKafka, and is
asynchronous*



Show how it works
-----------------

Including some code

More customers - add queues
---------------------------

<New diagram>

That is, use multiple **producers*

Add queues, use *queue number* to distinguish customers and split the messages
up into partitions

Automatically split N queues between <N partitions as the number of partitions
is increased (so it would be nice if these are both controllable in the demo)

An order with queues
--------------------

.. code:: json

   {
      'order': 271,
      'customer': 'Tibs',
      'queue': 3,
      'parts': [
          ['cod', 'chips'],
          ['chips', 'chips'],
      ]
   }


Even more customes - add more preparers
---------------------------------------

<New diagram>

That is, use multiple *consumers*

May want to do the same for the counter as well (the split for queues/preparers on the
'order' topic need not be the as the split for orders preparer/counter-person
on the 'ready' topic)




Cod or plaice
-------------

Plaice needs to be cooked. So we alter the sequence to add in asking the cook
to prepare plaice.

Participant changes
-------------------

We add two new topics, COOK for requests to cook plaice, and HOT-FOOD for
orders that have had their plaice cooked.

We're going to keep using the same order structure, since it's simplest.

* FOOD-PREPARER - makes up the order. Listens to 'ORDER' topic and also the
  new 'HOT-FOOD' topic.

  For message on 'ORDER' topic, checks if it can be made up.
  If the order can be made up immediately, sends (completed)
  order on to 'READY' topic. If not sends order on to 'COOK' topic.

  For message on 'HOT-FOOD' topic, sends (completed) order on to 'READY' topic

* COOK - new role - listens to 'COOK' topic, "cooks" new food. then sends
  order to 'HOT-FOOD' topic.

  Note - we don't need to assume that the same FOOD-PREPARER takes the order
  from the 'HOT-FOOD' topic as placed it on the 'COOK' topic, because the
  'HOT-FOOD' topic should have a lot fewer entries than the 'ORDERS' topic, as
  events only happens for orders with plaice in them

* STATISTICIAN - now listens to (all of) 'ORDER' topic and (all of) 'COOK'
  topic, and sends data to OpenSearch for analysis. For instance, percentage
  of orders that needed sending to cook, number of orders of each type of food
  (cod, plaice, chips), and so on. May also listen to 'HOT-FOOD' topic, to
  allow analysis of how long food took to prepare. In fact, let's put
  everything into OpenSearch(!)

* STOCKIST - now listens to (all of) 'ORDER' topic, and (all of) 'COOK' topic,
  to work out what consumables (portions of chips, cod, plaice) are being
  used. May also be using OpenSearch, or might be using a database.

An order with plaice
--------------------

.. code:: json

   {
      'order': 271,
      'customer': 'Tibs',
      'parts': [
          ['cod', 'chips'],
          ['chips', 'chips'],
          ['plaice', 'chips'].
      ]
   }

...
---

...
---

Sophisticated model, with caching
---------------------------------

Discuss this briefly at the end - there won't be time to go into it during the
talk, but I hope I'll be able to write the demo code for it.

Use a Redis cache to simulate the hot cabinet

<New diagram, just showing the preparer/cook interaction>

* The FOOD-PREPARER receives an order from the 'ORDER' topic, and looks to the
  Redis cache to see if there are enough portions to satisfy it.

  * If so, then make up the order, reduce the cache values, send on to the
    'READY' topic. Note that we ideally want atomicity here - we don't want to
    check the numbers and then make the order up, only to find the numbers
    have changed in between.

  * If not, then send the order on to the 'COOK' topic. The COOK will:

    * For cod and chips, round the "prepared" quantities up to some standard
      amount that is greater than that needed.
    * For plaice, prepare the requested number.

    When the cache has been updated, send the order to the 'HOT-FOOD' topic

  * The FOOD-PREPARER receives the order on the 'HOT-FOOD' topic, and behaves just
    the same as for an order from the 'ORDER' topic (above)

* At the end of the day, the STATISTICIAN looks at the remaining content of
  the Redis cache - this is wasted food.

Again, we don't need to assume that the same FOOD-PREPARER takes the order
from the 'HOT-FOOD' topic as placed it on the 'COOK' topic, as the 'HOT-FOOD'
topic should have a lot fewer entries than the 'ORDERS' topic, because events
only occur when there isn't enough food in the hot cabinets

---------

Apache Kafka Connectors
-----------------------

These make it easier to connect Kafka to databases, OpenSearch, etc., without
needing to write Python (or whatever) code.


Acknowledgements
================

.. note:: Trim to remove those we don't need

Apache,
Apache Kafka,
Kafka,
Apache Flink,
Flink,
are either registered trademarks or trademarks of the Apache Software Foundation in the United States and/or other countries

OpenSearch and
PostgreSQL,
are trademarks and property of their respective owners.

*Redis is a registered trademark of Redis Ltd. Any rights therein are reserved to Redis Ltd.

---------

License
=======

|cc-attr-sharealike| These notes are released under a
`Creative Commons Attribution-ShareAlike 4.0 International License`_.

.. |cc-attr-sharealike| image:: images/cc-attribution-sharealike-88x31.png
   :alt: CC-Attribution-ShareAlike image

.. _`Creative Commons Attribution-ShareAlike 4.0 International License`: http://creativecommons.org/licenses/by-sa/4.0/

.. _CamPUG: https://www.meetup.com/CamPUG/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _`PyCon UK 2022`: https://2022.pyconuk.org/
.. _Aiven: https://aiven.io/
