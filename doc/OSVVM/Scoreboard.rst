.. _DIR/Scoreboards:

Scoreboards
###########

The directive ``osvvm:scoreboards`` renders a testcase's scoreboard reports :file:`<test>_sb_<instance>.yml`, one per
scoreboard package instance - e.g. ``slv`` of ``ScoreboardPkg_slv`` -: a title and a table with a row per scoreboard,
with the columns OSVVM's HTML report shows.

.. code-block:: ReST

   .. osvvm:scoreboards::
      :reportid:  osvvmlibraries
      :testsuite: Axi4Full
      :testcase:  TbAxi4_BasicReadWrite

A testcase without a scoreboard is shown as a sentence saying so.


This is how testcase ``TbDemo_Failed`` of the documentation's demo build renders:

.. osvvm:scoreboards::
   :reportid:  demo
   :testsuite: Demo
   :testcase:  TbDemo_Failed


.. _DIR/Scoreboards/Options:

Options
*******

.. rst:directive:: osvvm:scoreboards

   Renders a testcase's scoreboards as tables, one per scoreboard package instance.

   .. rst:directive:option:: reportid: <identifier>

      The build summary, as declared in ``osvvm_build_summaries``. Required.

   .. rst:directive:option:: testsuite: <name>

      The testsuite. Required.

   .. rst:directive:option:: testcase: <name>

      The testcase, as OSVVM's ``TestCaseFileName`` names it. Required.

   .. rst:directive:option:: instance: <name>

      Renders only the scoreboard package instance of this name, e.g. ``slv``.

   .. rst:directive:option:: class: <CSS classes>

      Additional CSS classes on the tables.


.. _DIR/Scoreboards/Columns:

Columns
*******

Name, Parent
  |rarr| The scoreboard's AlertLog name, and the name of its AlertLog parent.
Items, Errors
  |rarr| The items pushed, and the failed checks; a scoreboard with failed checks is marked (CSS class
  ``osvvm-scoreboard-errors``).
Checked, Popped, Dropped, In FIFO
  |rarr| The items checked, popped and dropped, and the items left in the scoreboard.

The table carries the class ``osvvm-scoreboard-table``.
