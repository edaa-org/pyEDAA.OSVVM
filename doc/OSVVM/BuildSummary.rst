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


This is how the documentation's demo build renders, declared with pages:

.. osvvm:build-summary::
   :reportid: demo
   :columns: status testcases checks alerts requirements coverage simulation-time


.. _DIR/BuildSummary/Options:

Options
*******

.. rst:directive:: osvvm:build-summary

   Renders a build summary as a table, on landscape pages in LaTeX.

   .. rst:directive:option:: reportid: <identifier>

      The build summary, as declared in ``osvvm_build_summaries``. Required.

   .. rst:directive:option:: columns: <column groups>

      The column groups after the first column, which names the testsuite or testcase, in their order; separated by
      spaces or commas. Default: ``testcases errored alerts expected-alerts checks requirements coverage runtime``,
      the columns of the directive before this option existed. OSVVM's own HTML build summary shows
      ``status testcases checks alerts disabled-alerts requirements coverage runtime``. See
      :ref:`DIR/BuildSummary/Columns`.

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
| ``errored``         | Errored                             | The number of errored testcases, per testsuite: their   |
|                     |                                     | analysis failed or they wrote no reports.               |
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


.. _DIR/BuildSummary/Pages:

Pages per testsuite and testcase
********************************

A build summary declared with the key ``pages`` gets a page per testsuite and per testcase. They are generated when the
documentation is built - no source file is written - below the document name the key states: ``<pages>/<testsuite>``
and ``<pages>/<testsuite>/<testcase>``, e.g. ``osvvm/demo/Axi4Full/TbAxi4_BasicReadWrite``. They are pyTooling.Sphinx'
:external+pyToolSphinx:ref:`unit test pages <DIR/UnittestSummary/Pages>`, with what OSVVM states:

* A **testcase's page** shows its status and OSVVM status, its elapsed and simulation time, its checks, alerts,
  expected and disabled alerts, requirements, functional coverage, generics and testsuite, and links to the YAML
  reports the page is built from (settings, AlertLog, coverage, scoreboards) and to the transcripts, which Sphinx copies
  into the build as downloads; a file the settings name, but which doesn't exist, is warned about. The
  reason of a skipped testcase or of an expected or known status follows as *Message*. Then the testcase's AlertLog,
  functional coverage and scoreboards, as the directives :ref:`osvvm:alert-log <DIR/AlertLog>`,
  :ref:`osvvm:functional-coverage <DIR/FunctionalCoverage>` and :ref:`osvvm:scoreboards <DIR/Scoreboards>` show them.
* A **testsuite's page** shows its status and counts, and a table of its testcases - status, elapsed time, checks,
  alerts, requirements, functional coverage and simulation time -, each linked to its page.

The :rst:dir:`osvvm:build-summary` table links every testsuite and testcase to its page, and lists the testsuites in a
hidden table of contents, so the pages are below the summary's document in the navigation. The document showing the
summary is the build's overview page: a title, the :ref:`build's information <DIR/BuildInformation>` and the summary.


.. _DIR/BuildSummary/Roles:

Roles
*****

.. rst:role:: osvvm:tc

   Refers to a testcase's page: ``:osvvm:tc:`[<report ID>:]<testsuite>.<testcase>```. A suffix of the qualified name
   - e.g. only the testcase - is accepted, if it's unique. Without a report ID, the first build summary of
   ``osvvm_build_summaries`` is meant.

.. rst:role:: osvvm:ts

   Refers to a testsuite's page, as :rst:role:`osvvm:tc` refers to a testcase's.

The roles are pyTooling.Sphinx' :external+pyToolSphinx:ref:`report roles <DIR/UnittestSummary/Roles>`, in domain
``osvvm``. A target matching nothing or several objects is warned about.


.. _DIR/BuildSummary/Styling:

Styling
*******

The table carries the classes ``report-unittest-table``, ``osvvm-buildsummary-table`` and
``osvvm-buildsummary-<identifier>``, so pyTooling.Sphinx' stylesheet colours the rows by status. A testcase's status
cell carries ``osvvm-status-<status>``, e.g. ``osvvm-status-failed``; an alert count other than 0 - the alerts weren't
the expected ones - carries ``osvvm-failure-mismatch``, ``osvvm-error-mismatch`` or ``osvvm-warning-mismatch``.
