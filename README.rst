================================
Fish and Chips and Apache Kafka®
================================

A talk entitled "Fish and Chips and Apache Kafka®"

This is a talk for presentation at `PyCon UK 2022`_,
16th - 18th September 2022.

It will be presented live, but I expect a video to be made of the session, and
will update this README with a link when it is available.

It was also presented beforehand as a live talk at CamPUG_
on `6th September 2022`_.

  *Note to anyone visiting after CamPUG: The tag* `CamPUG` *should give you
  the slides as presented at CamPUG.*

.. _`PyCon UK 2022`: https://2022.pyconuk.org/
.. _CamPUG: https://www.meetup.com/CamPUG/
.. _`6th September 2022`: https://www.meetup.com/campug/events/288163944/

Useful links
~~~~~~~~~~~~

These are the links mentioned in the slides, and also some other links that
may be of interest.

* Aiven_, where I work, and our developer documentation at
  https://docs.aiven.io/ and https://github.com/aiven/devportal
* Get a free trial of Aiven services at https://console.aiven.io/signup/email
* Aiven is hiring (at least as of September 2022, and probably for a good
  while longer). See https://aiven.io/careers

and also:

* My Aiven blog post `Get things done with the Aiven CLI`_, which introduces
  the Aiven command line tool.

* `Apache Kafka® simply explained`_ on the Aiven blog, for a friendly
  explanation of the Apache Kafka fundamentals

* `Teach yourself Apache Kafka® and Python with a Jupyter notebook`_ on the
  Aiven blog. The Jupyter notebook referenced is at
  https://github.com/aiven/python-notebooks-for-apache-kafka

* `Create a JDBC sink connector`_ in the Aiven developer documentation shows
  how to setup Kafka Connect using the Aiven web console, and is thus useful
  for the "homework" on using Kafka Connect to output data to PostgreSQL.

.. _Aiven: https://aiven.io/
.. _`Apache Kafka® simply explained`: https://aiven.io/blog/kafka-simply-explained
.. _`Teach yourself Apache Kafka® and Python with a Jupyter notebook`:
   https://aiven.io/blog/teach-yourself-apache-kafka-and-python-with-a-jupyter-notebook
.. _`Create a JDBC sink connector:
   https://docs.aiven.io/docs/products/kafka/kafka-connect/howto/jdbc-sink.html

For the terminal user interface I used in the demos, see Textual_ and Rich_.

.. _Textual: https://github.com/Textualize/textual
.. _Rich: https://github.com/Textualize/rich

Not used in the demos, but another interesting Kafka library for Python is
faust_, which provides *Kafka Streams*, allowing (for instance) merging of
events from multiple Kafka topics.

.. _faust: https://faust.readthedocs.io/

Lastly, but definitely not least, `The Log: What every software engineer
should know about real-time data's unifying abstraction`_ is the 2013 paper by
Jay Kreps that explains the concepts behind Kafka. It is very worth a read.

.. _`The Log: What every software engineer should know about real-time data's unifying abstraction`:
   https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying

The slides
~~~~~~~~~~

The slides are written using reStructuredText_, and thus intended to be
readable as plain text.

The sources for the slides are in `<slides.rst>`_.

Note that github will present the ``.rst`` files in rendered form as HTML,
albeit using their own styling (which is occasionally a bit odd). If you want
to see the original reStructuredText source, you have to click on the "Raw"
link at the top of the file's page.

The PDF slides at 16x9 aspect ratio (`<rst-slides-16x9.pdf>`_) are stored here
for convenience.

The PDF files may not always be as up-to-date as the source files, so check
their timestamps.

The QR code on the final slide was generated using the command line program
for qrencode_, which I installed with ``brew install qrencode`` on my Mac.

.. _qrencode: https://fukuchi.org/works/qrencode/

The demos
~~~~~~~~~

The source code for the demonstration programs is in the `src <src/>`_ directory. See
the `readme.rst <src/readme.rst>`_ for how to run them.

The videos of the demos (which I use during the talk) are in a separate
repository, at https://github.com/tibs/fish-and-chips-and-kafka-videos (it
seems unfair to make you download them from here if you're not interested).

..
   The slide notes
   ~~~~~~~~~~~~~~~

   There are also notes for the slides. They were part of my process in producing
   the slides, so may not be a great deal of use to others.

     (The notes may continue to change until after `PyCon UK 2022`_.)

   The sources for the notes are in `<notes.rst>`_

   Note that github will present the ``.rst`` files in rendered form as HTML,
   albeit using their own styling (which is occasionally a bit odd). If you want
   to see the original reStructuredText source, you have to click on the "Raw"
   link at the top of the file's page.

   For convenience, there will also be a PDF rendering of the notes,
   `<notes.pdf>`_

Making the PDF files
~~~~~~~~~~~~~~~~~~~~

I use poetry_ to manage the dependencies needed to build the PDFs, and
rst2pdf_ and its dependencies to do the actual work.

.. _poetry: https://python-poetry.org/
.. _rst2pdf: https://rst2pdf.org/

You will also need an appropriate ``make`` program if you want to use the
Makefile.

So, for instance, in this directory I would start a new ``poetry`` shell using::

  $ poetry shell

and then install the dependencies using::

  $ poetry install

After that, you should be able to use the Makefile to create the PDF files.
For instance::

  $ make pdf

to make them all.

For other things the Makefile can do, use::

  $ make help

If you wish, you can exit the ``poetry`` shell using ``exit``.

.. _CamPUG: https://www.meetup.com/CamPUG/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html

--------

Acknowledgements
~~~~~~~~~~~~~~~~

Apache,
Apache Kafka,
Kafka,
and the Kafka logo
are either registered trademarks or trademarks of the Apache Software Foundation in the United States and/or other countries

Postgres and PostgreSQL are trademarks or registered trademarks of the
PostgreSQL Community Association of Canada, and used with their permission

--------

  |cc-attr-sharealike|

  This talk and its related files are released under a `Creative Commons
  Attribution-ShareAlike 4.0 International License`_. The source code for the
  demo programs is dual-licensed as CC Attribution Share Alike and MIT.

.. |cc-attr-sharealike| image:: images/cc-attribution-sharealike-88x31.png
   :alt: CC-Attribution-ShareAlike image

.. _`Creative Commons Attribution-ShareAlike 4.0 International License`: http://creativecommons.org/licenses/by-sa/4.0/
