.. _DIR/BuildSummary:

Build Summary
#############

The directive ``osvvm:build-summary`` renders OSVVM's build summary :file:`<build>.yml` as a table: a row per testsuite
and testcase, with what OSVVM states for a testcase - its status, checks, alerts, requirements, functional coverage -
and the sums of a testsuite's testcases. The table is pyTooling.Sphinx' unit test table
(:external+pyToolSphinx:ref:`report:unittest-summary <DIR/UnittestSummary>`), with OSVVM's columns.

.. code-block:: ReST

   .. osvvm:build-summary::
      :reportid: osvvmlibraries

A build summary is declared in :file:`conf.py` under ``osvvm_build_summaries`` (see :ref:`OSVVM Domain <OSVVM>`). It
is read once per build, with the settings file :file:`<test>_run.yml` of every testcase that ran. A warning of the
reader - e.g. a key the format doesn't define, or a missing settings file - is logged as a Sphinx warning.


.. _DIR/BuildSummary/Options:

Options
*******

.. rst:directive:: osvvm:build-summary

   Renders a build summary as a table, on landscape pages in LaTeX.

   .. rst:directive:option:: reportid: <identifier>

      The build summary, as declared in ``osvvm_build_summaries``. Required.

   .. rst:directive:option:: columns: <column groups>

      The column groups after the first column, which names the testsuite or testcase, in their order; separated by
      spaces or commas. Default: ``status testcases checks alerts disabled-alerts requirements coverage runtime``.
      See :ref:`DIR/BuildSummary/Columns`.

   .. rst:directive:option:: build-name: <name>

      The name of the row summarizing the build, instead of the build's own name.

   .. rst:directive:option:: show-testcases: all | not-passed

      Which testcases are listed per testsuite: all of them, or only those that didn't pass. A testcase failing as
      expected passed. Default: ``all``.

   .. rst:directive:option:: hide-build-summary

      Leaves out the row summarizing the build above the testsuites.

   .. rst:directive:option:: class: <CSS classes>

      Additional CSS classes on the table.


.. _DIR/BuildSummary/Columns:

Column groups
*************

A testsuite's row and the build's rows sum the counts of their testcases.

+---------------------+-------------------------------------+---------------------------------------------------------+
| Name                | Columns                             | Content                                                 |
+=====================+=====================================+=========================================================+
| ``status``          | Status                              | A testcase's OSVVM status, followed by ``(expected)``   |
|                     |                                     | for an expected status or ``(known)`` for a known       |
|                     |                                     | status; a testsuite's status.                           |
+---------------------+-------------------------------------+---------------------------------------------------------+
| ``testcases``       | Testcases: Passed, Failed, Skipped, | The number of testcases per status, per testsuite.      |
|                     | Total                               |                                                         |
+---------------------+-------------------------------------+---------------------------------------------------------+
| ``checks``          | Checks: Passed, Total               | The affirmations: passed ones and all of them.          |
+---------------------+-------------------------------------+---------------------------------------------------------+
| ``alerts``          | Alerts: Failures, Errors, Warnings  | The alert counts, less the expected alerts, as OSVVM    |
|                     |                                     | counts them; a testcase's count other than 0 is marked. |
+---------------------+-------------------------------------+---------------------------------------------------------+
| ``expected-alerts`` | Expected Alerts: Failures, Errors,  | The alert counts a testcase expects.                    |
|                     | Warnings                            |                                                         |
+---------------------+-------------------------------------+---------------------------------------------------------+
| ``disabled-alerts`` | Disabled Alerts                     | The number of disabled failures, errors and warnings.   |
+---------------------+-------------------------------------+---------------------------------------------------------+
| ``requirements``    | Requirements: Passed, Goal          | The passed requirements and the requirements to pass;   |
|                     |                                     | empty for a testcase without requirements.              |
+---------------------+-------------------------------------+---------------------------------------------------------+
| ``coverage``        | Functional Coverage                 | A testcase's functional coverage in percent.            |
+---------------------+-------------------------------------+---------------------------------------------------------+
| ``simulation-time`` | Simulation Time                     | A testcase's simulated time, e.g. ``3.53 us``.          |
+---------------------+-------------------------------------+---------------------------------------------------------+
| ``runtime``         | Elapsed Time (HH:MM:SS.sss)         | The elapsed time OSVVM measured.                        |
+---------------------+-------------------------------------+---------------------------------------------------------+
| ``generics``        | Generics                            | The generics a testcase was simulated with.             |
+---------------------+-------------------------------------+---------------------------------------------------------+


.. _DIR/BuildSummary/Styling:

Styling
*******

The table carries the classes ``report-unittest-table``, ``osvvm-buildsummary-table`` and
``osvvm-buildsummary-<identifier>``, so pyTooling.Sphinx' stylesheet colours the rows by status. A testcase's status
cell carries ``osvvm-status-<status>``, e.g. ``osvvm-status-failed``; an alert count other than 0 - the alerts weren't
the expected ones - carries ``osvvm-failure-mismatch``, ``osvvm-error-mismatch`` or ``osvvm-warning-mismatch``.
