.. _DIR/FunctionalCoverage:

Functional Coverage
###################

The directive ``osvvm:functional-coverage`` renders a testcase's functional coverage report :file:`<test>_cov.yml`: per
coverage model a title with the model's coverage, and a table of its bins, with the columns OSVVM's HTML report shows.

.. code-block:: ReST

   .. osvvm:functional-coverage::
      :reportid:  osvvmlibraries
      :testsuite: Axi4Full
      :testcase:  TbAxi4_BasicReadWrite

A model of weight 0 - e.g. the delay coverage of OSVVM's verification components - is ignored in the testcase's
coverage, which its title says. A testcase without a coverage model is shown as a sentence saying so.


This is how testcase ``TbAxi4_BasicReadWrite`` of the documentation's demo build renders:

.. osvvm:functional-coverage::
   :reportid:  demo
   :testsuite: Axi4Full
   :testcase:  TbAxi4_BasicReadWrite


.. _DIR/FunctionalCoverage/Options:

Options
*******

.. rst:directive:: osvvm:functional-coverage

   Renders a testcase's coverage models as tables, one per model.

   .. rst:directive:option:: reportid: <identifier>

      The build summary, as declared in ``osvvm_build_summaries``. Required.

   .. rst:directive:option:: testsuite: <name>

      The testsuite. Required.

   .. rst:directive:option:: testcase: <name>

      The testcase, as OSVVM's ``TestCaseFileName`` names it. Required.

   .. rst:directive:option:: model: <name>

      Renders only the coverage model of this name.

   .. rst:directive:option:: settings

      Adds a table of each model's settings, named as OSVVM names them, e.g. ``CovWeight`` and ``Seeds``.

   .. rst:directive:option:: class: <CSS classes>

      Additional CSS classes on the tables.


.. _DIR/FunctionalCoverage/Columns:

Columns
*******

Name, Type
  |rarr| The bin's name - empty, if unnamed - and its type: ``COUNT``, ``IGNORE`` or ``ILLEGAL``.
A column per field
  |rarr| The bin's range of the field's values: a value, ``<low> to <high>``, ``≥ <low>`` or ``≤ <high>`` for an open
  end, or ``ALL``. A cross has a column per crossed field.
Count, At Least, Coverage (%)
  |rarr| How often the bin was hit, how often it has to be hit, and its coverage.
Status
  |rarr| ``PASSED``, ``FAILED`` or ``IGNORED``, if the report states pass or fail (``WritePassFail``) or the model is a
  requirement; ``-`` for a model of weight 0.

The last row states the model's coverage. The tables carry the classes ``osvvm-coverage-table`` and
``osvvm-coverage-settings``; a bin's row carries its type, e.g. ``osvvm-bin-ignore``.
