================================================
Demo for "Fish and Chips and Apache Kafka®" talk
================================================

.. contents::

What we have here
=================

Some "proof of concept" code:

* `<poc1.py>`_ - example code showing how to create a Kafka producer using
  <``python-kafka``, and send some messages.
* `<poc2.py>`_ - the same thing, but using ``aiokafka`` to do it asynchronously.
* `<poc3.py>`_ - me working out how to do Kafka producer and consumer in a
  Textual app.

The demo programs as show in the talk:

* `<demo1-cod-and-chips.py>`_ - a till sending orders to a topic, and a food
  preparer consuming them.
* `<demo2-cod-and-chips-3tills.py>`_ - three tills, but still only one preparer,
  who can't keep up.
* `<demo3-cod-and-chips-3tills-2preparers.py>`_ - three tills and two preparers,
  who can keep up.
* `<demo4-with-added-cook.py>`_ - back to one till and one food preparer, but
  now we have a cook to prepare plaice for us.

and

* `<demo_helpers.py>`_ which has common code for the above.

Known problems:

* If you make the terminal window narrow enough that the text in panels has to
  wrap, then the panels won't display all the lines. My code is counting
  logical lines, not display lines.

Dependencies
============

I use poetry_ to manage the dependencies needed by this demo.

.. _poetry: https://python-poetry.org/

So, for instance, in this directory I would start a new ``poetry`` shell using::

  $ poetry shell

and then install the dependencies using::

  $ poetry install

If you wish, you can exit the ``poetry`` shell using ``exit``.

.. _poetry: https://python-poetry.org/

How to run the demos
====================

Assuming you have a Kafka service, and the SSL credentials for connecting to
it are in the ``creds`` directory, then you can run each demo with:

.. code:: shell

   ./DEMO_FILE HOST_URL:SSL_PORT -d creds

For me, running the first demo against my Kafka service at
``tibs-kafka-fish-dev-sandbox.aivencloud.com:12693``, I would use:

.. code:: shell

   ./demo1-cod-and-chips.py tibs-kafka-fish-dev-sandbox.aivencloud.com:12693 -d creds

How to run the demos with Aiven
===============================

You don't need to run the demos using Aiven services, but I think it's the
easiest option if you don't already have Kafka up and running.

Get an account
--------------

If you don't yet have an Aiven account, you can `sign up for a free trial`_

.. _`sign up for a free trial`: https://console.aiven.io/signup/email
.. _`Create an authentication token`: https://docs.aiven.io/docs/platform/howto/create_authentication_token.html

Log in to Aiven
---------------

Get an authentication token, as described at `Create an authentication token`_,
copy it, and log in using the following command. You'll need to replace
YOUR-EMAIL-ADDRESS with the email address you've registered with Aiven:

.. code:: shell

  avn user login YOUR-EMAIL-ADDRESS --token

This will prompt you to paste in your token.

Choose a project, cloud and service plan
----------------------------------------

Aiven uses "projects" to organise which services you can access. You can list
them with:

.. code:: shell

   avn project list

Choose the project you want to use with the following command, replacing
``PROJECT-NAME`` with the appropriate name:

.. code:: shell

  avn project switch PROJECT_NAME

You then need to decide what cloud you want to run the service in. Use:

.. code:: shell

  avn cloud list

to find the clouds. Since Aiven is based out of Helsinki, I tend to choose
``google-europe-north1``, which is Finland, but you'll want to make your own
choice.

Normally, you'd also want to decide on a service plan (which determines the
number of servers, the memory, CPU and disk resources for the service). You
can find the service plans for a cloud using:

.. code: shell

  avn service plans --service-type kafka --cloud CLOUD-NAME

However, for the these demo programs a ``kafka:startup-2`` plan is sufficient,
and that's also the cheapest.

  **Note** that if you want to use Kafka Connect with your Kafka service,
  you'll need something more powerful than the startup plan, for instance
  ``business-4``.

Create a Kafka service
----------------------

Now it's time to create the actual Kafka service, using the command below.

The service name needs to be unique and can't be changed - I like to put my
name in it (for instance, ``tibs-kafka-fish``).

The extra ``-c`` switches enable the REST API to the service, the ability to
create new topics by publishing to them (very useful), use of the schema
registry (which we actually don't need in this demo).

Again, remember to replace ``KAFKA_FISH_DEMO`` with your actual service name,
and ``CLOUD_NAME`` with the cloud name:

.. code: shell

  avn service create KAFKA_FISH_DEMO \
      --service-type kafka \
      --cloud CLOUD-NAME \
      --plan startup-2 \
      -c kafka_rest=true \
      -c kafka.auto_create_topics_enable=true \
      -c schema_registry=true

  **Note** If you did want Kafka Connect support then you also need to specify
  ``-c kafka_connect=true`` - remember that won't work with a "startup" plan.

  **Note** If you're using an existing account which has VPCs in the region
  you've chosen, then you also need to specify ``--no-project-vpc`` to
  guarantee that you don't use the VPC.

It takes a little while for a service to start up. You can wait for it using:

.. code:: shell

   avn service wait KAFKA_FISH_DEMO

which will update you on the progress of the service, and exit when it is
``RUNNING``.

Download certificates
---------------------

In order to let the demo programs talk to the Kafka service, you need to
download the appropriate certificate files. Create a directory to put them
into:

.. code:: shell

  mkdir -p creds

and then download them:

.. code:: shell

  avn service user-creds-download KAFKA_FISH_DEMO -d creds --username avnadmin

Get the connection information
------------------------------

To connect to the Kafka service, you need its service URI. You can find that
out with:

.. code:: shell

   avn service get KAFKA_FISH_DEMO --format '{service_uri}'

Run a demo
----------

*And now you're ready to run the demo programs*

    This is the same information as at `How to run the demos`_ earlier in this
    README, put here so you don't need to scroll all the way to the top again.

Given the service URI you found using ``avn service get`` (just above here),
and assuming you saved the credentials to a directory called ``creds``, then
run a demo with:

.. code:: shell

   ./DEMO_FILE SERVICE_URI -d creds

For me, running the first demo against my Kafka service at
``tibs-kafka-fish-dev-sandbox.aivencloud.com:12693``, I would use:

.. code:: shell

   ./demo1-cod-and-chips.py tibs-kafka-fish-dev-sandbox.aivencloud.com:12693 -d creds

Exploring your service
----------------------

To find out more information about a Kafka topic, look at the documentation
for `avn service topic`_.

.. _`avn service topic`: https://docs.aiven.io/docs/tools/cli/service/topic.html

You can also find useful information about a service using the `Aiven web
console`_, on the **Services** page for your Kafka service.

.. _`Aiven web console`: https://console.aiven.io/


After you're done
-----------------

If you're not using your Kafka service for a while, and don't mind losing any
data in its event stream, then it makes sense to power it off, as you don't
get charged (real money or free trial credits) when a service is powered off.

You can power off the service (remember, this will discard all your data) with:

.. code:: shell

   avn service update $KAFKA_SERVICE --power-off

and bring it back again with:

.. code:: shell

   avn service update $KAFKA_SERVICE --power-on

This will take a little while to finish, so wait for it with:

.. code:: shell

   avn service wait KAFKA_FISH_DEMO

If you've entirely finished using the Kafka service, you can delete it with:

.. code:: shell

   avn service terminate KAFKA_FISH_DEMO

Other resources
===============

You may also be interested in

* My Aiven blog post `Get things done with the Aiven CLI`_
* The Aiven github repository `Python Jupyter Notebooks for Apache Kafka®`_
  which is a series of Jupyter Notebooks on how to start with Apache Kafka®
  and Python, using Aiven managed services.
* The `Aiven for Apache Kafka®`_ section of the `Aiven developer documentation`_

.. _`Get things done with the Aiven CLI`: https://aiven.io/blog/aiven-cmdline
.. _`Python Jupyter Notebooks for Apache Kafka®`: https://github.com/aiven/python-notebooks-for-apache-kafka
.. _`Aiven for Apache Kafka®`: https://docs.aiven.io/docs/products/kafka.html
.. _`Aiven developer documentation`: https://docs.aiven.io/index.html

------

  |cc-attr-sharealike|

  The source code in this directory is dual-licensed under the MIT license
  (see `LICENSE.txt <LICENSE.txt>`_) and `Creative Commons
  Attribution-ShareAlike 4.0 International License`_. Choose whichever seems
  most appropriate for your use.

.. |cc-attr-sharealike| image:: images/cc-attribution-sharealike-88x31.png
   :alt: CC-Attribution-ShareAlike image

.. _`Creative Commons Attribution-ShareAlike 4.0 International License`: http://creativecommons.org/licenses/by-sa/4.0/
