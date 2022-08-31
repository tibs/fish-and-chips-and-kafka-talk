================================================
Demo for "Fish and Chips and Apache Kafka®" talk
================================================

*Why no, it's not even remotely ready yet!*

Dependencies
============

I use poetry_ to manage the dependencies needed by this demo.

Thus::

  poetry shell

to start a new virtual environment, and then::

  poetry install

to set it up with the necessary dependencies.

.. _poetry: https://python-poetry.org/


Aiven service management
========================

*I'm noting what I did. You'll need to replace parts of it with your own
information, and in particular what cloud/region you want to use.*

Logging in
==========

If you don't yet have an Aiven account, you can sign up for a free trial at
https://console.aiven.io/signup/email

I logged in using the instructions documented for the `Aiven CLI`_, using
a token:

.. code: shell

  avn user login USER-EMAIL-ADDRESS --token

.. _`Aiven CLI`: https://docs.aiven.io/docs/tools/cli.html

and then did:

.. code: shell

  avn project switch $PROJECT_NAME

I can list the available clouds with::

  avn cloud list

and the service plans within a cloud (here, ``google-europe-north1``, which is
Finland):

.. code: shell

  avn service plans --service-type kafka --cloud google-europe-north1

``kafka:startup-2`` is the cheapest.

Create my Aiven for Apache Kafka® service
=========================================

I followed the instructions for `avn service create`_ and created my new
service (the name needs to be unique and can't be changed - I like to put my
name in it). The extra ``-c`` switches enable the REST API to the service, the
ability to create new topics by publishing to them (very useful), use of the
schema registry (which we actually don't need in this demo)

.. code: shell

  avn service create $KAFKA_NAME \
      --service-type kafka \
      --cloud google-europe-north1 \
      --plan startup-2 \
      -c kafka_rest=true \
      -c kafka.auto_create_topics_enable=true \
      -c schema_registry=true

.. _`avn service create`: https://docs.aiven.io/docs/tools/cli/service.html#avn-service-create

**Note** If I later want Kafka Connect support (``-c kafka_connect=true``)
then I need to use a more capable plan, for instance ``business-4``

**Note** If there are VPCs in the region I've chosen, then I also need to
specify ``--no-project-vpc`` to guarantee that I don't use the VPC.

Get the certificates:

.. code:: shell

  mkdir -p creds
  avn service user-creds-download $KAFKA_NAME --project $PROJECT_NAME -d creds --username avnadmin

******Note** the following are in no way in logical order or anything

.. code:: shell

   avn service update $KAFKA_SERVICE --power-off  # when not using

   avn service update $KAFKA_SERVICE --power-on   # to start again
   avn service wait $KAFKA_NAME                   # wait for it to be ready


Other resources
===============

You may also be interested in
https://github.com/aiven/python-notebooks-for-apache-kafka,
which is a series of Jupyter Notebooks on how to start with Apache Kafka® and
Python, using Aiven managed services.
