.. _OSVVM:

OSVVM Domain
############


Installation
************

.. admonition:: conf.py

   .. code-block:: python

      extensions = [
        ...
        "pyEDAA.OSVVM.Sphinx"
      ]

Configuration
*************

The extension sets up :mod:`pyTooling.Sphinx`, whose nodes and stylesheet the tables use. A build summary is declared in
``osvvm_build_summaries``, with an identifier the directives name in their ``:reportid:`` option:

.. admonition:: conf.py

   .. code-block:: python

      osvvm_build_summaries = {
         "osvvmlibraries": {
            "yaml_report": "reports/OSVVMLibraries_RunAllTests.yml",
         }
      }

``yaml_report``
  |rarr| The build summary :file:`<build>.yml`. The paths it and the settings files of its testcases state are relative
  to its directory.
``pages``
  |rarr| Optional, the document name the :ref:`pages per testsuite and testcase <DIR/BuildSummary/Pages>` are generated
  below, e.g. ``osvvm/osvvmlibraries``.
