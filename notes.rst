
================================
Fish and Chips and Apache Kafka®
================================

By Tibs / Tony Ibbs (they / he)

A talk to be given at PyCon UK 2022

.. contents::

Comments from after CamPUG
==========================

* I normally hate history lessons in talks but your three message system use cases were really good
* someone will explain to you that kafka cannot be exactly-once delivery because that's not how Physics works
* On the slide "Multiple Partitions, Consumer Groups", look at the data in the bottom right. There's an a where I think a b should be
* try not to say "simple"!

The thing that the chips are in ... basket? Fryer?

------

check if the async redis library is called aioredis

  Actually, according to https://github.com/aio-libs/aioredis-py,
  it's now part of the normal `redis-py` package, and one just
  needs to do::

    from redis import asyncio as aioredis

  which is rather wonderful.

  Maybe I should put a note in the README for my Redis talk.

worth putting in (probably) screenshot of web console showing topics and the
distribution of events between topics

would have been nice to show the order queue separately, to give more context
in the UI - this would need me to write the code for that :smile:

Took just over 30 minutes, so need to tighten it up a little, especially if I
(do) add web console screenshots.

-------

* Run all the demos again
* Take screenshots of the Aiven web console for the service, for the topics,
  and for at least one of the topics partitions panel, especially showing the
  bar graph of data distribution between topics

Ideally this would show demo2 using all 3 partitions, and demo3 using all
partitions with data going to both consumers (so that's two screenshots, I
guess)


Comments from first practice session at work
============================================

Note: with a very early stage of things! I've left people's names off the
comments, since they matter to me but not to other readers.

* *I love the slide/talk of the messages problems… it makes the talk real. But
  you don’t define what kafka is, but only where it can used*

  I forgot - definitely need to say something like "Apache Kafka is a
  distributed event store and stream-processing platform." or something a
  little friendlier. https://kafka.apache.org/intro may also give inspiration

* *I believe the analyst will use a database like PG or Bigquery :)*

  Shift to using PostgreSQL then, as it should be a moderately realistic
  simulation. And in that case, should probably just use a Kafka Connector,
  which (a) introduces *that* concept in a nice way, and (b) shows it
  requiring less code - and not in the simulation code, either.

* *I like it very much. I wonder how did you make the slides with the code? I
  found it very nice as well.*

* *I was not sure what plaice means. If you want to use the word, maybe an
  image about this food would be useful.* - *It's a kind of flatfish. But
  agree that some of these things, even till, might need explanation if you're
  presenting outside of the UK.*

  Need to explain at least: cod (that it's the traditional default fish),
  chips (sort-of fat greasy "fries"), plaice (a flat fish, anothe traditional
  choice - maybe a picture), till (? what's the term for this ?)

* *+1 for adding the slides with copyrights*

* *OpenSearch, why doing that via custom code and not with Kafka connect? I
  believe it’s better to talk about different consumer groups*

  See above about moving to PG. And definitely I must discuss consumer
  groups - I think I just forgot because I had no code / diagram to react to.

* *Food preparers need to always be less than the number of tills!*

  I think I had that implicitly, but I forgot to say it.

* *Kafka Connect has the benefits of being able on scale as Kafka*

  ...which I must remember to say.

* *Do you know what time of the day you’ll present? Before / after lunch or
  before a networking dinner you could joke about making people hungry.*

  At the moment, at PyCon UK, Friday just after lunch.

* *Add a “may contain traces of seafood” joke to you disclaimer slide (where
  you also talk about working for Aiven)?*

  Hmm. Not sure if I have room on the disclaimer slide, but I'd probably want
  to go for "no traces of actual seafood" (!)

  ...and, of course, Kafka was a vegetarian...

Other notes:

* Need to spell check!
* Need actual diagrams for the Kafka explanation, including for partitions
* I forgot to say what Kafka *is* when I said it suited my needs (see above)
* I should drop the "extra" participants except the ANALYST, to keep things
  simpler. And the ANALYST should use PG. Demo should show some sort of
  statistic that is (repeatedly) computed from the PG data.
* Don't show the "more complex" setup before the "simple setup" - just add it
  in later on - that is, start simple and build up, as I said I would
* Need focussed diagrams when (for instance) adding in the COOK - just showing
  the FOOD-PREPARER / COOK interaction
* Even if I don't have time to talk about (or write) the demo using Redis as a
  cache, it's still worth mentioning this as a possibility
* Redis also allows Kafka Connect - not sure if that helps in this case
* For multiple consumers, remember to talk about consumer groups (see above)
  and what they do for us
* You can write your own interfaces to other services, but Kafka Connect will
  scale with Kafka itself, and doesn't involve having to write new Python code
  (and thus also doesn't take resources from the Python client)
* Remember to work out my "I work for Aiven and we ..." introduction!
* Point out that I use the same JSON order, just adding more information each
  time
* It's much better to show a captured video of the demo than a static picture,
  even if that means swapping focus (which shouldn't actually be too bad if
  there are only two things to flip between)
* Using a video actually means I don't have to worry about trying to fit a
  decent image into a slide - but I still need to remember to go for the
  largest font size I can manage.

"""Since January, I've been working as a Developer Educator at Aiven. Our aim
is to make developers lives easier, by providing managed open source data
services in the cloud. As a Developer Educator, that means I get paid to
understand (and then explain) various things that I'd never before had the
time to get a proper understanding of, and that includes Apache Kafka®, which
I want to tell you about today."""

* demo 1 - simple TILL -> FOOD-PREPARER
* demo 2 - 3 tills, one preparer who can't keep up
* demo 3 - 2 tills, two (or maybe three) preparers who can keep up, using
  partitions
* demo 4 - show the COOK loop. Based on demo 1, for simplicity
* demo 5 - would add a Kafka Connector to PG, and show some sort of statistic
  from a PG query.
* demo 6 - homework - the Redis cache

Note: I think it's quite possible there won't be time to *show* demo 5, so
it may just be something to talk about, like the Redis cache.

NB: implement "while SHOP_IS_OPEN" checking for the Producer loops, where
``q`` unsets that value. Then make sure the Consumers drain the orders -
preferably not by inserting a dummy (sentinel) order, but that might be the
simplest way... (or, just use a decent sized timeout when SHOP_IS_OPEN is False)


JDBC sink connector:

* https://docs.aiven.io/docs/products/kafka/kafka-connect/howto/jdbc-sink.html
* https://docs.aiven.io/docs/tools/cli/service/connector.html#avn-service-connector-create

Kafka streams:

* https://docs.aiven.io/docs/products/kafka/howto/kafka-streams-with-aiven-for-kafka.html
  (example uses Java)

  faust_ provides Kafka Streams, but (a) is a whole different framework,
  and (b) seems to need a background worker to be running (perhaps
  unsurprisngly). It's also not obvious immediately how to write a Producer
  (although the command line does have a ``send`` command), but of course we
  could continue to use the original producers.

.. _faust: https://faust.readthedocs.io/

So it may be easier to do the COOK example by:

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



From proposal
=============

Abstract
--------

Apache Kafka® is the de facto standard in the data streaming world for sending
messages from multiple producers to multiple consumers, in a fast, reliable
and scalable manner.

Come and learn the basic concepts and how to use it, by modelling a fish and
chips shop!

Introduction
------------

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

Questions
=========

Can I specify a particular offset from which to start consuming messages (not
just earliest or latest)?

Make sure I have a good understanding of what happens to *old* messages in a
topic - they can't *actually* keep accumulating forever.

What's the best way of sending to OpenSearch for my demo - just do a POST?

Ditto for retrieving data - probably want to do an asynchronous query.

In the "Introduction", I said " I'll demonstrate ... persistence, which allows
a new consumer to start consuming events from the past". So I need to talk
about how to do that. See, for instance

* https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html#kafka.KafkaConsumer.commit
* https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html#kafka.KafkaConsumer.commit_async
* https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html#kafka.KafkaConsumer.committed
* https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html#kafka.KafkaConsumer.offsets_for_times
* https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html#kafka.KafkaConsumer.seek

-----

https://www.scrapingbee.com/blog/best-python-http-clients/ compares requests,
aiohttp and httpx, which might be useful

https://docs.aiohttp.org/en/stable/

https://www.python-httpx.org/ and https://www.python-httpx.org/async/

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

.. note:: Do I actually show persistence?

   Best way to do that might be to add the ACCOUNTANT, STATISTICIAN and
   STOCKIST in as something that can be enabled in a running demo - they
   would then start at the start of events.

https://opencredo.com/blogs/kafka-vs-rabbitmq-the-consumer-driven-choice/
looks like a VERY useful comparison for my purposes

Maybe also see
https://iasymptote.medium.com/kafka-v-s-zeromq-v-s-rabbitmq-your-15-minute-architecture-guide-426f5920c89f

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

Kafka is a "distributed event streaming platform (which also handles
messages)" (from https://opencredo.com/blogs/kafka-vs-rabbitmq-the-consumer-driven-choice/)

Consumers and consumer groups
-----------------------------

Need consumers to be in different groups if I want them to read the same
messages (as I do for FOOD-PREPARER and ANALYST, for instance)

https://stackoverflow.com/questions/35561110/can-multiple-kafka-consumers-read-same-message-from-the-partition

https://www.oreilly.com/library/view/kafka-the-definitive/9781491936153/ch04.html -
consumers

Consumer can consume from multiple partitions, but only one consumer (in the
same consumer group) can read from each partition. So if there are N
partitions (in a consumer group) and N+X consumers, each wanting to read from
one partition each, X consumers will be idle.

"So the rule in Kafka is only one consumer in a consumer group can be assigned
to consume messages from a partition in a topic and hence multiple Kafka
consumers from a consumer group can not read the same message from a
partition."

https://gist.github.com/andrewlouis93/5fd10d8041aeaf733d3acfbd61f6bbef How are
partitions assigned in a consumer group? (GIST)

https://codingharbour.com/apache-kafka/what-is-a-consumer-group-in-kafka/ --
this looks like a nice article with good explanations

------

https://aozturk.medium.com/kafka-guide-in-depth-summary-5b3cb6dbc83c

https://www.oreilly.com/library/view/kafka-the-definitive/9781491936153/ch01.html -
Meet Kafka

Fish and chip shop
------------------

A nice picture of a fish and chip shop, and/or a fryer/hot-cabinet, would be
nice.

Then need to decide where in the slide deck it should go.

The fish and chip shop model
----------------------------

Start with a diagram showing my plan!

.. note:: *All the participant and topic names could be improved. I've used
   UPPER-CASE names to make it easier to change them later on.*

First model
-----------

This model shows the progress of orders through the system, and how there may
be multiple interests in the data.

Basic Participants
------------------

* CUSTOMER - implicit, makes an order (we don't model them directly)
* TILL - takes order from CUSTOMER, sends order to 'ORDER' topic
* FOOD-PREPARER - Listens to 'ORDER' topic.

  "Makes up" the order (for our model, this doesn't look like much!).

  Sends (completed) order on to 'READY' topic.

* COOK - a notional participant, we don't model them at this stage

* COUNTER - listens to 'READY' topic, passes finished order on to
  customer (again, we don't model the customer directly)

*All these names could be improved*

*Do we actually need the 'READY' topic and the COUNTER, or can we just assume
the FOOD-PREPARER hands the food to the CUSTOMER, who is quick and eager to
take it?*

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

Let's build some code
---------------------

A series of slides showing how to do the above, in sections.

*Do I just show use of python-kafka, for simplicity?*

*Probably worth doing so, but mention the demo is using AIOKafka, and is
asynchronous*


Extra participants (Business value)
-----------------------------------

Add in more participants, who are watching what goes on.

In the demo, have button to show adding them, and show that they start
consuming events from the start of the demo, not just from when they
started work.

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

.. note:: For the slides, probably better to just use the STATISTICIAN, so
          that we only have one example of sending data to OpenSearch

More customers - add queues
---------------------------

<New diagram>

That is, use multiple *producers*

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


Even more customers - add more preparers
----------------------------------------

<New diagram>

That is, use multiple *consumers*

May want to do the same for the counter as well (the split for queues/preparers on the
'order' topic need not be the as the split for orders preparer/counter-person
on the 'ready' topic)


Cod or plaice
-------------

Plaice needs to be cooked. So we alter the sequence to add in asking the cook
to prepare plaice.

Participant changes - add COOK
------------------------------

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

.. note:: For the slides, probably better to just use the STATISTICIAN, so
          that we only have one example of sending data to OpenSearch

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

Redis is a registered trademark of Redis Ltd. Any rights therein are reserved to Redis Ltd.

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
