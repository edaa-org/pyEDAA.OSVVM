.. _FC:

Functional Coverage Report
##########################

OSVVM's ``CoveragePkg`` writes the functional coverage of a testcase into a YAML file :file:`<testcase>_cov.yml`
(``WriteCovYaml``); OSVVM's script :file:`ReportCov2Html.tcl` reads it to write the coverage section of the testcase's
HTML report. :mod:`pyEDAA.OSVVM.FunctionalCoverage` reads the file into a model of the format, and converts it to the
tool-neutral functional coverage model of pyEDAA.Reports (:mod:`pyEDAA.Reports.FunctionalCoverage`).


.. _FC/QuickStart:

Quick Start
***********

.. grid:: 2

   .. grid-item::
      :columns: 6

      The following example code reads an OSVVM coverage file, and converts it to the functional coverage model of
      pyEDAA.Reports. Then it prints the testcase's coverage, and the bins and hit coverage of the coverage models of a
      weight above 0.

   .. grid-item::
      :columns: 6

      .. tab-set::

         .. tab-item:: Example Code

            .. code-block:: Python

               from pathlib import Path
               from pyEDAA.OSVVM.FunctionalCoverage import Document

               document = Document(Path("TbStream_SendGetPacketBurst1_cov.yml"), analyzeAndConvert=True)
               report = document.ConvertToFunctionalCoverageReport()

               print(f"{report.Name}: {report.HitCoverage:.1%} (OSVVM: {document.Coverage:.2f} %)")
               for covergroup in report.IterateCovergroups(lambda covergroup: covergroup.Weight > 0):
                 for coverpoint in covergroup.IterateCoverpoints():
                   bins = f"{coverpoint.CoveredBinCount}/{coverpoint.BinCount} bins"
                   print(f"  {coverpoint.Name}: {bins}, hits {coverpoint.HitCoverage:.1%}")

         .. tab-item:: Console Output

            .. code-block::

               TbStream_SendGetPacketBurst1: 50.0% (OSVVM: 50.00 %)
                 Cov2a: 16/32 bins, hits 50.0%
                 Cov1a: 16/32 bins, hits 50.0%


.. _FC/DataModel:

Data Model
**********

The model of the format keeps what the file states.

.. py:currentmodule:: pyEDAA.OSVVM.FunctionalCoverage

* :class:`Document` - the file: its :class:`FormatVersion` (``Version``), the testcase's coverage in percent
  (``Coverage``), the setting ``WritePassFail``, and the coverage models (``Models``). OSVVM lists the models of weight
  0 last.
* :class:`CoverageModel` - an item of ``Models``: its name, the testcases, which sampled it (``TestCases``), its
  coverage in percent, its settings, the names of its fields - one per dimension (``BinInfo.FieldNames``) -, and its
  bins. The names of models needn't be unique.
* :class:`ModelSettings` - a model's ``Settings``: its weight in the testcase's coverage (``CovWeight``), its goal in
  percent (``Goal``), its :class:`WeightMode`, :class:`CountMode` and :class:`IllegalMode`, its two seeds, its
  threshold, whether the threshold is enabled, whether the model is a requirement, and its total counts
  (``TotalCovCount``, ``TotalCovGoal``).
* :class:`Bin` - an item of a model's ``Bins``: its name - empty, if unnamed -, its :class:`BinType` (``COUNT``,
  ``IGNORE``, ``ILLEGAL``), one range of values per dimension (``Range``), its count, its *at least* count, and its
  count in percent of the *at least* count (``PercentCov``).

The file's format version ``0.1`` is the one OSVVM writes since OSVVM 2026.02; the file doesn't state the OSVVM version.
A file of another version is rejected. :meth:`Document.Analyze` validates the file against the JSON Schema of its
format version, :file:`OSVVM-FunctionalCoverage-0.1.schema.json` in :mod:`pyEDAA.OSVVM.Resources`, derived from OSVVM's
writer: every key is required, a key the schema doesn't name is rejected, and so is a value of another type or out of
the values OSVVM writes - each error is a note of the :exc:`CoverageError`. ``BinInfo.Dimensions`` and
``BinInfo.NumBins`` are checked against the field names and the bins.


.. _FC/Conversion:

Conversion to pyEDAA.Reports
****************************

:meth:`Document.ConvertToFunctionalCoverageReport` converts the model of the format to the functional coverage model
of pyEDAA.Reports, and aggregates it:

* The report is named after the testcase: the file's name without ``_cov``. The setting ``WritePassFail`` becomes a
  key-value pair of the report.
* A coverage model becomes a covergroup of the model's weight, goal and testcases; the other settings become key-value
  pairs of the covergroup, named as OSVVM names them, e.g. ``covergroup["Seeds"]``.
* The covergroup has one coverage item, named as the model: a coverpoint for a model of one dimension - its expression
  is the field name -, a cross of the field names for a model of more dimensions.
* A bin becomes a coverpoint bin or a cross bin of the same name - ``None``, if unnamed -, kind, ranges, count and
  *at least* count.
* The model's and testcase's coverage, the total counts and the bins' percentages aren't copied: the model of
  pyEDAA.Reports computes them. Its hit coverage is the coverage OSVVM writes, for the default goal of 100 %.
