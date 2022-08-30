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

..
   Aiven service management
   ========================

   Logging in
   ==========

   I logged in using the instructions documented for the `Aiven CLI`_, using
   a token::

     avn user login USER-EMAIL-ADDRESS --token

   .. _`Aiven CLI`: https://docs.aiven.io/docs/tools/cli.html

   and then did::

     avn project switch THE-PROJECT-I-USE

   I can list the available clouds with::

     avn cloud list

   and the service plans within a cloud (here, ``google-europe-north1``, which is
   Finland)::

     avn service plans --service-type kafka --cloud google-europe-north1

   ``kafka:startup-2`` is the cheapest.

   Create my Aiven for Apache Kafka® service
   =========================================

   I followed the instructions for `avn service create`_ and created my new
   service (the name needs to be unique and can't be changed - I like to put my
   name in it)::

     avn service create NEW-SERVICE-NAME --service-type kafka --cloud google-europe-north1 --plan startup-2

   .. _`avn service create`: https://docs.aiven.io/docs/tools/cli/service.html#avn-service-create
