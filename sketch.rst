=====================================
Actors and events, thoughts and plans
=====================================

The demo
========

Click_ for the command line (`click docs`_) - I think Laysa has convinced me
that this is a really good option, and it even looks as if it might handle
help text in a way I can appreciate.

Ideally, Textual_ or something similar to give me a terminal-based UI -
Textual leverages Rich_ which is rather wonderful. The only snag with using
Textual is that the documentation is a bit sparse.

  OK. MessagePump provides ``set_interval`` which can call a method every
  ``float`` seconds. Widget inherits this. `The example`__ shows using::

      class Clock(Widget):
          def on_mount(self):
              self.set_interval(1, self.refresh)

  to automatically call ``self.refresh`` every 1.0 seconds. So if I always
  keep N records from the input source, then I should be able to show the (at
  most N) latest records, and allow the Widget to handle resizing for me.

  Populating those N latest records can be done by polling in ``refresh``, or
  by asynchronously updating them, depending on which is easier.

  __ https://github.com/Textualize/textual/tree/css#timers-and-intervals

Ben points out that faust_ is *very nice* for acting as a streaming
intermediary between Kafka and (for instance) Textual, and at first glance it
looks as if it gives me just the sort of interfaces I want for talking to
Kafka.

  Ooh - it has a Redis extension - I wonder if that's going to be useful.

  And https://faust.readthedocs.io/en/latest/userguide/testing.html describes
  testing, which means I can probably write an app without needing to actually
  connect to Kafka in the early stages, which would be nice.

.. _click: https://github.com/pallets/click/
.. _`click docs`: https://click.palletsprojects.com/en/8.1.x/
.. _textual: https://github.com/Textualize/textual
.. _rich: https://github.com/Textualize/rich
.. _faust: https://faust.readthedocs.io/en/latest/

Outline (more bedtime thoughts, 2022-08-22)
===========================================

Talk about what we're trying to do - use a fish and chip shop as a relatively
simple example of micro-service communication.

Things not to do:

* Try to use a database as a messaging service (explain briefly why not -
  mainly it means you have to *implement* all of a queuing system, over
  something that is designed for different purposes / constraints)
* Use traditional messaging solutions (explain briefly why not - back pressure
  handling, problems if queue crashes and resuming, guaranteed delivery, etc.)

So we're going to look at how Apache Kafka is the solution to our problems
<fx: smile>

It *might* be sensible to put the "First things to simulate" section
before the "Things not to do" part - think on it.

First things to simulate:

* Start with an "order, make up order, vend order" setup. We assume there are
  always enough cod and chips ready to satisfy orders (someone in the background
  keeps them stocked)

  * Customer makes order at till and pays for it
  * Order is sent to preparer, who makes up the order and gives it to the customer

  Show:

  * Order information also goes to accountant records
  * Order information also goes to opensearch (for instance) for later analysis

Consider that there are more and more orders, so first show adding multiple
preparers (automatic scaling), then multiple tills (multiple producers)

What about plaice? (I like plaice)

Plaice is cooked seperately, because it's unusual, so not worth keeping in the
hot cabinet.

* Add in orders with plaice being sectioned off to a particular preparer

Then talk briefly about how we can simulate the "stuff needs cooking", using
Redis - see `Bedtime thoughts (2022-08-17)`_ for my original thoughts on this.

Broadly:

* Redis represents the central console between the preparers and the cooks.
* It records how many portions of cod, chips and plaice are already prepared
  (in the hot cabinet / below in the chip basket).

  We shall ignore portion sizes, but if we did not, then (for instance) chip
  portions might be simple multipliers on the "single" portion size, and
  different cod sizes would count as different order items.

* The preparer receives an order and looks to the Redis cache to see if there
  are enough portions to satisfy it.

  * If so, then make up the order, reduce the cache values, send on to the
    customer. Note that we ideally want atomicity here - we don't want to
    check the numbers and then make the order up, only to find the numbers
    have changed in between.

  * If not, then send the order on to the cook, who will cook what is needed:

    * For cod and chips, round the "prepared" quantities up to some standard
      amount that is greater than that needed.
    * For plaice, prepare the requested number.

    When the cache has been updated, send the order back to the preparer.

    Again, think about atomicity. But don't aim for perfection - I don't mind
    if I miss something and get it a bit wrong, since this is "playing", not a
    production system. Might even be worth pointing that out.

  Does this mean the preparer has two queues, one from the till and one from
  the cook? If not, need to have some way to stop the accountant, etc., from
  noticing / taking account of the second time round.

    (Is that just something I can do with Kafka - have the preparer listen to
    two merged even queues?)

  *If* there was a race condition between preparers and stuff being ready,
  the preparer would presumably just send the "cook stuff for me" message
  again.

So by the end, we've shown some interesting use cases of Kafka for event
queues, including multiple producers and consumers, and output to OpenSearch.
We've also introduced the use of a Redis cache, just for the fun of it.

And we've reminded people not to try to re-implement queues using a database.

Code: I don't want to do a live demo, but I think it's important to show
output from a demo. So provide code (on github) that automates the various
things I want to show.

* Several "simulation" choices (to match each stage of the talk)
* Common "generate orders" phase
* Other common components
* Visualisation by some means - maybe terminal UI

Bedtime thoughts (2022-08-17)
=============================

* We're assuming some sort of service (a microservice) for each stage of the
  buying fish and chips process.

  We need to communicate between those.

  I've seen people try to use a database for "messaging" like this, but it's
  not really fit for purpose (although it's tempting, because it does look a
  little bit like putting bits of paper up on a line or a board to be
  attended to). Steal some of the objections from Francesco. But basically,
  we don't want to try to implement messaging on top of

* An order for cod and chips arrives

  We assume (at least at first) that there is always plenty of cod and chips
  available - these are refreshed asynchronously as needed (this is *nearly*
  how I've experienced Real Life - occasionally in a small shop one has to
  wait for new chips, for instance)

  The order is sent to the preparer, who makes up the fish and chips, and
  sends the order on to the next stage.

* If we're very busy, there might be multiple tills, and multiple preparers
  (and even multiple whatever the next stage is). Show some of this
  happening with Kafka.

* An order that includes plaice arrives at the till.

  The cache (Redis) shows there is no plaice ready (this is the norm)

  Because of that, the order is sent to the cook (behind the frying machine)

  When the plaice is ready, the number of plaice available will be updated
  in the cache, and the original message will be sent to the preparer. From
  there onwards, it's a normal order.

* I don't think we need to worry about race conditions, but if the
  preparer *does* notice that there is insufficient plaice, they should just
  send the order back to the cook again...

* The accountant will also want to listen to the same orders as the
  preparer, so they can work out income

* The statistician will also want to listen to the same orders, so they can
  understand something about what to order in the future, according to past
  sales. They may actually (instead) want the data to go into OpenSearch so
  they can do statistics on it. They might also want to count the total
  number of messages sent to the till versus the total sent to the
  preparer - this will given an idea of how many times an order had to wait
  for something to be cooked.

* We could generalise the cache concept to cod and chips (or portions of
  chips, anyway) as well - this may not be worth doing as it should be
  "obvious"

* An interesting program would have switches to set the numbers of the
  different participants (tills, producers, cooks, etc.) and some way of
  choosing the proportion of plaice orders (and how often N is greater than
  1 instead of just 1), and then generate random orders, throw them at the
  system, and visualise the result.

* We'd also want a script to create the relevant Aiven services, and to tear
  them down again, to make the demo easier to use.

* I'd quite like to do it as a command line UI, just because - maybe using

  * https://github.com/Textualize/textual
  * https://github.com/Textualize/rich
  * and maybe https://github.com/Textualize/rich-cli

Earlier thoughts
================

Menu: cod, plaice, chips, maybe pie. Size is an optional extra, but doesn't
affect anything. We assume that cod and chips (and pie if offered) are always
ready to be served, as there's a stock above the frier which is kept
up-to-date (this doesn't *quite* match reality, but to do otherwise would mean
counting things).

Customer journeys:

* Web customer.

  * Places order via web, arrives at shop some time later, collects order.
  * Order may be ready before they arrive.

  Can we ignore home delivery, and assume it's out-sourced to someone who acts
  as a stand-in for the customer collection (JustEat and its ilk)

* In person customer.

  * Customer may need to queue (let's not model that).
  * Order is received verbally and placed by cashier at the till. This is very
    similar to the web process.
  * An order that includes only cod and/or chips can be fulfilled immediately.
  * An order that includes plaice needs to wait for plaice to be cooked.
  * Customer takes order as soon as it is all ready

Do we want to support salt and vinegar choices?

Order journeys

* Order contains plaice:

  * Plaice is requessted - this will take a while (it doesn't matter how many
    plaice)
  * Rest of order goes into limbo
  * When plaice is ready, order is completed - it slots in as the next order,
    as if it had just been made

* Order does not contain plaice

  * Order is completed immediately

We assume that orders naturally queue. The cashier need not be the same person
as the person making up orders - let's assume not.

Other journeys:

* All orders are immediately copied to the accountant
* All orders are immediately copied to the stockist, so they know what has
  been cooked

Do we allow for a customer who ordered on the web not turning up, and their
food being wasted?

Do we want a statistics journey, sending the orders and (perhaps) their start
and end times to opensearch?

When there are lots of customers, the non-plaice orders should automatically
start to be distributed to more than one counter person.

As implied, adding *state* would mean we could model more things, and some
state is probably essential for the plaice orders - or we re-queue the whole
order all the time, I suppose.

There probably isn't time to consider a second kitchen for chinese food.
