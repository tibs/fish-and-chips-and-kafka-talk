Fish and Chips and Apache Kafke®
================================


.. class:: title-slide-info

    By Tibs / Tony Ibbs (they / he)

    .. raw:: pdf

       Spacer 0 30

    Slides and accompanying material at https://github.com/tibs/fish-and-chips-and-kafka-talk

.. footer::

   *tony.ibbs@aiven.io* / *@much_of_a*

   .. Add a bit of space at the bottom of the footer, to stop the underlines
      running into the bottom of the slide
   .. raw:: pdf

      Spacer 0 5

Lo, there shall be slides
-------------------------

...but this isn't really one


Something about our general purpose
-----------------------------------

..
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

Decisions
---------

*Start with "what we want to model"*

*or start with "what I want from messaging"*

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

Participants: 1
---------------

* CUSTOMER
* TILL - takes order from CUSTOMER, sends order to 'ORDER' topic
* FOOD-PREPARER - makes up the order. Listens to 'ORDER' topic and 'HOT-FOOD'
  topic.

  For message on 'ORDER' topic, checks if it can be made up. For the simple
  model, we assume that chips and cod are always ready in the hot food
  cabinet, so this just means "is there plaice in the order", since plaice is
  not pre-cooked. If the order can be made up immediately, sends (completed)
  order on to 'READY' topic. If not sends order on to 'COOK' topic.

  For message on 'HOT-FOOD' topic, sends (completed) order on to 'READY' topic

* COOK - listens to 'COOK' topic, "cooks" new food. then sends order to
  'HOT-FOOD' topic.

  Note - we don't need to assume that the same FOOD-PREPARER takes the order
  from the 'HOT-FOOD' topic as placed it on the 'COOK' topic, because the
  'HOT-FOOD' topic should have a lot fewer entries than the 'ORDERS' topic, as
  events only happens for orders with plaice in them

* COUNTER - listens to 'READY' topic, (implicitly) passes finished order on to
  customer

Participants: 2
---------------

* ACCOUNTANT - listens to 'ORDER' topic, calculates incoming money

* STATISTICIAN - listens to (all of) 'ORDER' topic and to (all of)'COOK'
  topic, and sends data to OpenSearch for analysis. For instance, percentage
  of orders that needed sending to cook, number of orders of each type of food
  (cod, plaice, chips), and so on. May also listen to 'HOT-FOOD' topic, to
  allow analysis of how long food took to prepare. In fact, let's put
  everything into OpenSearch(!)

  *Ideally, the demo would show some statistics as they occur*

* STOCKIST - in the simple model, listens to (all of) 'ORDER' topic, but in
  the more complex model, listens to (all of) 'COOK' topic, to work out what
  consumables (portions of chips, cod, plaice) are being used. May also be
  using OpenSearch, or might be using a database.

*All these names could be improved*

What I want from messaging
--------------------------

Why not traditional message solutions
-------------------------------------

I want:

* multiple producers *and* multiple consumers
* only sending some messages to some consumers (not duplicating when scaling)
* no need for back pressure handling (queue filling up)
* no problems if queue crashes and resuming
* guaranteed delivery
* ... what else?

Why not to build it around a database
-------------------------------------

mainly it means you have to *implement* all of a queuing system, over
something that is designed for different purposes / constraints

Brief explanation of Kafka
--------------------------

Producers, Consumers

Events, topics, partitions

...
---

Let's build some code
---------------------

A series of slides showing how to do the above, in sections.

*Do I just show use of python-kafka, for simplicity?*

*Probably worth doing so, but mention the demo is using AIOKafka, and is
asynchronous*

...
---

More customers - add queues
---------------------------

<New diagram>

That is, use multiple **producers*

Add queues, use *queue number* to distinguish customers and split the messages
up into partitions

Automatically split N queues between <N partitions as the number of partitions
is increased (so it would be nice if these are both controllable in the demo)

Even more customes - add more preparers
---------------------------------------

<New diagram>

That is, use multiple *consumers*

May want to do the same for the counter as well (the split for queues/preparers on the
'order' topic need not be the as the split for orders preparer/counter-person
on the 'ready' topic)

Sophisticated model, with caching
---------------------------------

Discuss this briefly at the end

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

Again, we don't need to assume that the same FOOD-PREPARER takes the order
from the 'HOT-FOOD' topic as placed it on the 'COOK' topic, as the 'HOT-FOOD'
topic should have a lot fewer entries than the 'ORDERS' topic, because events
only occur when there isn't enough food in the hot cabinets

Acknowledgements
----------------

Apache,
Apache Kafka,
Kafka,
Apache Flink,
Flink,
are either registered trademarks or trademarks of the Apache Software Foundation in the United States and/or other countries

OpenSearch and
PostgreSQL,
are trademarks and property of their respective owners.

\*Redis is a registered trademark of Redis Ltd. Any rights therein are reserved to Redis Ltd.

.. -----------------------------------------------------------------------------

.. raw:: pdf

    PageBreak twoColumnNarrowRight

Fin
---

Slides and accompanying material at https://github.com/tibs/fish-and-chips-and-kafka-talk

Written in reStructuredText_, converted to PDF using rst2pdf_

|cc-attr-sharealike| This slideshow is released under a
`Creative Commons Attribution-ShareAlike 4.0 International License`_

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
