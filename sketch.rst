=====================================
Actors and events, thoughts and plans
=====================================

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
