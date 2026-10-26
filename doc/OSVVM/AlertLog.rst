.. _DIR/AlertLog:

AlertLog
########

The directive ``osvvm:alert-log`` renders a testcase's AlertLog report :file:`<test>_alerts.yml` as a table: a row per
AlertLog item - the test first, then its items, each indented by its depth -, with the columns OSVVM's HTML report
shows.

.. code-block:: ReST

   .. osvvm:alert-log::
      :reportid:  osvvmlibraries
      :testsuite: Axi4Full
      :testcase:  TbAxi4_BasicReadWrite

The testcase's settings file :file:`<test>_run.yml` names the report. A testcase without one, e.g. a skipped
testcase, is shown as a sentence saying so.


This is how testcase ``TbDemo_Failed`` of the documentation's demo build renders:

.. osvvm:alert-log::
   :reportid:  demo
   :testsuite: Demo
   :testcase:  TbDemo_Failed


.. _DIR/AlertLog/Options:

Options
*******

.. rst:directive:: osvvm:alert-log

   Renders a testcase's AlertLog hierarchy as a table.

   .. rst:directive:option:: reportid: <identifier>

      The build summary, as declared in ``osvvm_build_summaries``. Required.

   .. rst:directive:option:: testsuite: <name>

      The testsuite. Required.

   .. rst:directive:option:: testcase: <name>

      The testcase, as OSVVM's ``TestCaseFileName`` names it: the test's name, extended by the values of its generics.
      Required.

   .. rst:directive:option:: class: <CSS classes>

      Additional CSS classes on the table.


.. _DIR/AlertLog/Columns:

Columns
*******

Name
  |rarr| The item's name, indented by its depth.
Status
  |rarr| The item's status, e.g. ``PASSED``; the test's status may also be ``STOPLIMIT``, ``TIMEOUT``, ``NOCHECKS`` or
  ``MANUALCHECKS``.
Checks: Total, Passed, Failed
  |rarr| The item's affirmations.
Requirements: Goal, Passed
  |rarr| The requirements to pass, and the passed ones.
Alert Counts: Failures, Errors, Warnings
  |rarr| The item's alerts; an item with errors is marked (CSS class ``osvvm-alerts``).
Disabled Alert Counts: Failures, Errors, Warnings
  |rarr| The item's disabled alerts.

The table carries the class ``osvvm-alertlog-table``; a row carries ``osvvm-alertlog-item`` and its status, e.g.
``osvvm-alertlog-failed``.
