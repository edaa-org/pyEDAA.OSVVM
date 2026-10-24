.. _ALERT:

Alert and Log Report
####################

.. rubric:: Design Goals

* Clearly named classes that model the semantics of an OSVVM AlertLog report.
* The OSVVM AlertLog model instance can be constructed top-down and bottom-up.
* Child objects shall have a reference to their parent.

.. rubric:: Features

* Read OSVVM's AlertLog YAML files (:file:`<test>_alerts.yml`), as written by ``WriteAlertYaml`` of OSVVM's
  ``AlertLogPkg``.
* Validate a file against the JSON Schema of the format version it states; a key the format doesn't define is a
  validation error.
* Convert AlertLog hierarchy into a :external+pyTool:ref:`pyTooling Tree <STRUCT/Tree>`



.. _ALERT/QuickStart:

Quick Start
***********

.. grid:: 2

   .. grid-item::
      :columns: 6

      The following example code opens an OSVVM AlertLog report in YAML format, analyzes the data structure and converts
      the content to an AlertLog hierarchy. Then the total number of failures, errors and warnings is printed. At
      next two nested loops iterate all second-level and third-level child items and prints its failures, errors and
      warnings. Finally, it prints a summary line.

      Analyzing the file validates it against the JSON Schema of its format version: a key the format doesn't define
      raises :exc:`~pyEDAA.OSVVM.AlertLog.AlertLogError`, with a note per violation.

   .. grid-item::
      :columns: 6

      .. tab-set::

         .. tab-item:: Example Code

            .. code-block:: Python

               from pathlib import Path
               from pyEDAA.OSVVM.AlertLog import Document as AlertLogDocument

               def counts(item) -> str:
                 return f"{item.FailureCount}/{item.ErrorCount}/{item.WarningCount}"

               path = Path("TbAxi4_BasicReadWrite_alerts.yml")
               doc = AlertLogDocument(path, analyzeAndConvert=True)

               print(f"{doc.Name}: {counts(doc)}")
               for item in doc.Children.values():
                 print(f"  {item.Name:<19}: {counts(item)}")
                 for innerItem in item.Children.values():
                   print(f"    {innerItem.Name:<17}: {counts(innerItem)}")
               print("=" * 40)
               print(f"Total errors: {doc.TotalErrorCount}")

         .. tab-item:: Console Output

            .. code-block::

               TbAxi4_BasicReadWrite: 0/0/0
                 VHDL Asserts       : 0/0/0
                 Default            : 0/0/0
                 OSVVM              : 0/0/0
                 subordinate_1      : 0/0/0
                   Protocol Error   : 0/0/0
                   Data Check       : 0/0/0
                   No response      : 0/0/0
                 manager_1          : 0/0/0
                   Protocol Error   : 0/0/0
                   Data Check       : 0/0/0
                   No response      : 0/0/0
                   WriteResp SB     : 0/0/0
                   ReadResp SB      : 0/0/0
                   WriteBurstFifo   : 0/0/0
                   ReadBurstFifo    : 0/0/0
               ========================================
               Total errors: 0



.. _ALERT/DataModel:

Data Model
**********

An OSVVM AlertLog report can be summarized as follows:

1. An *AlertLog* report is a tree (or hierarchy) of :ref:`ALERT/DataModel/AlertLogItem` instances.
2. The tree's root element is a :ref:`ALERT/DataModel/Document` instance derived from :ref:`ALERT/DataModel/AlertLogItem`.
3. The root has :ref:`ALERT/DataModel/Settings`, which decide whether the test failed.



.. _ALERT/DataModel/Document:

AlertLog Document
=================

.. grid:: 2

   .. grid-item::
      :columns: 6

      An Alertlog Document represents an OSVVM YAML file and its AlertLog data structure, which is a hierarchy of
      AlertLog items. The OSVVM AlertLog :class:`~pyEDAA.OSVVM.AlertLog.Document` class inherits all methods and
      properties of an :ref:`ALERT/DataModel/AlertLogItem`. In addition, it has the format version, the settings, the
      alerts the test expects and the external errors.

      When a document is instantiated, a path to a YAML file is required. Optionally, the YAML file can be immediately
      analyzed and converted to an AlertLog hierarchy. The given path can be accessed by the
      :data:`~pyEDAA.OSVVM.AlertLog.Document.Path` property. The document class preserves an internal reference
      (:attr:`~pyEDAA.OSVVM.YAMLDocumentMixin._yamlDocument`) to the analyzed YAML document.

      If the document was not analyzed, the :meth:`~pyEDAA.OSVVM.AlertLog.Document.Analyze` and
      :meth:`~pyEDAA.OSVVM.AlertLog.Document.Convert` methods can be used to start these steps. The spent time is
      captured and can be accessed via :data:`~pyEDAA.OSVVM.AlertLog.Document.AnalysisDuration` and
      :data:`~pyEDAA.OSVVM.AlertLog.Document.ModelConversionDuration`.

      :meth:`~pyEDAA.OSVVM.AlertLog.Document.Analyze` validates the file against the JSON Schema of the format version
      it states (:class:`~pyEDAA.OSVVM.AlertLog.FormatVersion`, :data:`~pyEDAA.OSVVM.AlertLog.SCHEMAS`), as every
      document of OSVVM's YAML files does by :class:`~pyEDAA.OSVVM.YAMLDocumentMixin`. The schemas are in the resource
      package :mod:`pyEDAA.OSVVM.Resources`.

   .. grid-item::
      :columns: 6

      .. condensed-class:: pyEDAA.OSVVM.AlertLog.Document


.. _ALERT/DataModel/Settings:

AlertLog Settings
=================

.. grid:: 2

   .. grid-item::
      :columns: 6

      The settings of OSVVM's ``AlertLogPkg``, which decide whether a test failed: whether warnings, disabled alerts and
      failed requirements are errors, and the external errors passed to ``WriteAlertYaml`` less the alerts the test
      expects.

   .. grid-item::
      :columns: 6

      .. condensed-class:: pyEDAA.OSVVM.AlertLog.Settings


.. _ALERT/DataModel/AlertLogItem:

AlertLog Item
=============

.. grid:: 2

   .. grid-item::
      :columns: 6

      An OSVVM AlertLog entry: an AlertLog ID with its status, its alert counts, its affirmations and its requirements.
      Child items are unique by name. :meth:`~pyEDAA.OSVVM.AlertLog.AlertLogItem.IterateItems` iterates all items below
      an item, optionally filtered by a predicate.

   .. grid-item::
      :columns: 6

      .. condensed-class:: pyEDAA.OSVVM.AlertLog.AlertLogItem
