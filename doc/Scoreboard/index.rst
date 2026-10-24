.. _SB:

Scoreboard Report
#################

.. rubric:: Design Goals

* Clearly named classes that model the semantics of an OSVVM scoreboard report.
* Child objects shall have a reference to their parent.

.. rubric:: Features

* Read OSVVM's scoreboard YAML files (:file:`<test>_sb_<name>.yml`), as written by ``WriteScoreboardYaml`` of OSVVM's
  ``ScoreboardGenericPkg``.
* Validate a file against the JSON Schema of the format version it states; a key the format doesn't define is a
  validation error.



.. _SB/QuickStart:

Quick Start
***********

.. grid:: 2

   .. grid-item::
      :columns: 6

      The following example code opens an OSVVM scoreboard report in YAML format, analyzes the data structure and
      converts the content to a list of scoreboards. Then it prints the scoreboards, which had failed checks.

      Analyzing the file validates it against the JSON Schema of its format version: a key the format doesn't define
      raises :exc:`~pyEDAA.OSVVM.Scoreboard.ScoreboardError`, with a note per violation.

   .. grid-item::
      :columns: 6

      .. tab-set::

         .. tab-item:: Example Code

            .. code-block:: Python

               from pathlib import Path
               from pyEDAA.OSVVM.Scoreboard import Document

               path = Path("TbAxi4_TimeOut_sb_slv.yml")
               doc = Document(path, analyzeAndConvert=True)

               print(f"{doc.TestcaseName} - {doc.Name}: {doc.ScoreboardCount} scoreboards")
               for sb in doc.IterateScoreboards(lambda sb: sb.ErrorCount > 0):
                 print(f"  {sb.AlertLogParentName}/{sb.Name}: {sb.ErrorCount} errors")

         .. tab-item:: Console Output

            .. code-block::

               TbAxi4_TimeOut - slv: 13 scoreboards
                 manager_1/WriteResp SB: 2 errors
                 manager_1/ReadResp SB: 2 errors



.. _SB/DataModel:

Data Model
**********

An OSVVM scoreboard report can be summarized as follows:

1. A scoreboard report is a :ref:`SB/DataModel/Document` of one instance of OSVVM's ``ScoreboardGenericPkg``.
2. The document lists the statistics of each scoreboard (or FIFO) of that package instance as a
   :ref:`SB/DataModel/Scoreboard`, in the order of the file.



.. _SB/DataModel/Document:

Scoreboard Document
===================

.. grid:: 2

   .. grid-item::
      :columns: 6

      A scoreboard document represents an OSVVM YAML file: the format version, the test's name and the scoreboards. The
      name of the package instance is taken from the file name, :file:`<test>_sb_<name>.yml`.

      If the document was not analyzed, the :meth:`~pyEDAA.OSVVM.Scoreboard.Document.Analyze` and
      :meth:`~pyEDAA.OSVVM.Scoreboard.Document.Convert` methods can be used to start these steps. The spent time is
      captured and can be accessed via :data:`~pyEDAA.OSVVM.Scoreboard.Document.AnalysisDuration` and
      :data:`~pyEDAA.OSVVM.Scoreboard.Document.ModelConversionDuration`.

      :meth:`~pyEDAA.OSVVM.Scoreboard.Document.Analyze` validates the file against the JSON Schema of the format
      version it states (:data:`~pyEDAA.OSVVM.Scoreboard.SCHEMAS`), a file of the resource package
      :mod:`pyEDAA.OSVVM.Resources`, as every document of OSVVM's YAML files does by
      :class:`~pyEDAA.OSVVM.YAMLDocumentMixin`.

   .. grid-item::
      :columns: 6

      .. condensed-class:: pyEDAA.OSVVM.Scoreboard.Document


.. _SB/DataModel/Scoreboard:

Scoreboard
==========

.. grid:: 2

   .. grid-item::
      :columns: 6

      The statistics of one scoreboard: how many items were pushed, checked, popped and dropped, how many checks failed,
      and how many items are left at the end of the test. A scoreboard is named by its AlertLog ID; the name is not
      unique, not even together with the name of its AlertLog parent.

   .. grid-item::
      :columns: 6

      .. condensed-class:: pyEDAA.OSVVM.Scoreboard.Scoreboard
