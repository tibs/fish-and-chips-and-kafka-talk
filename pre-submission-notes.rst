Fish and chips and Apache Kafka®
================================

    The shorter

    * Fish and Chips and Kafka

    is catchier, but it's probably better to be polite and name the product properly...

.. contents::

Target
------

* PyCon UK 2022


Abstract
~~~~~~~~

50 words max

(= 46)

Apache Kafka® is the de facto standard in the data streaming world for sending
messages from multiple producers to multiple consumers, in a fast, reliable
and scalable manner.

Come and learn the basic concepts and how to use it, by modelling a fish and
chips shop!


Description
~~~~~~~~~~~

400 words max

(= 204)

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


Is the talk suitable for beginners?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes.

Notes for me
------------

Inspired by Francesco's talk-and-demo showing a pizza business,
where pizza orders get split up if necessary, and also all go to the
finance endpoint, and there's a "ready for delivery" endpoint. And
Francesco also suggested the fish and chips theme!

Ideas - not quite the same as Francesco's:

* Orders come in from the web and from the till (two producers)
* Initially one consumer, but arrange to split partitions for:

  * cod
  * plaice - prepared individually
  * chips

* All orders also go to the accountant
* Orders from the web also go to the delivery person

If I added an extra thing, it would be *state* - chips and cod are prepared in
batches, so only need re-frying when they are about to run out - so have a
counter (maybe in Redis). But I think that's probably One Step Too Far - it's
going for an implementation, not something to illustrate use of Kafka.

So maybe stay with sending all the data to OpenSearch, so one can do
statistics (but remember GDPR - ideally want Flink as well - not going to demo
that here!)

Hmm - might want to use terminal UI to be the UX for at least some parts -
makes it clear this doesn't have to be "webby". Or maybe I can use ``bottle``
instead of flash?

Nice as a topic because it's interesting (!) and because it can show off
Aiven related stuff.

https://kafka.apache.org/intro

... from wikipedia: "The project aims to provide a unified, high-throughput,
low-latency platform for handling real-time data feeds."

From Francesco:

  When picking a data platform in the past we had to chose between
  performance, scalability or real time consumption. Now we have the luxury to
  have all 3 with Kafka

Further ideas
~~~~~~~~~~~~~

Our local fish and chip shop also sells chinese food. It has a separate
kitchen for that.

So:

* customer producers: external website, and shop "till" (website) - these are
  probably pretty much identical, but would not be in the real world, as the
  shop does not need to work with addresses.

* internal targets: at first just one, but them split according to fish and
  chips or chinese food.

* output consumers: shop till and delivery person.

* recipient for all orders: the accountant

How to cope with an order containing multiple things that come from the two
different kitchens? Or am I overcomplicating things for no good reason.

Maybe I just need an intermediate process (at the till) that checks all
components of an order are complete before notifying the recipient (either the
till keeper or the delivery person). That doesn't seem too unreasonable -
events would be menu items, but with some sort of indicator that allows to
tell when all items of the order are together (could be a simple count, could
be a copy of the whole order as JSON (!!).

That would also cope with my "asking for plaice means having to wait while
it's cooked".

On the other hand, is trying to get OpenSearch in as well then just too much?
