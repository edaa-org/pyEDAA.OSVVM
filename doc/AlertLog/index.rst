.. _ALERT:

Alert and Log Report
####################

.. rubric:: Design Goals

* Clearly named classes that model the semantics of an OSVVM AlertLog report.
* The OSVVM AlertLog model instance can be constructed top-down and bottom-up.
* Child objects shall have a reference to their parent.

.. rubric:: Features

* Convert AlertLog hierarchy into a :external+pyTool:ref:`pyTooling Tree <STRUCT/Tree>`



.. _ALERT/QuickStart:

Quick Start
***********

.. grid:: 2

   .. grid-item::
      :columns: 6

      The following example code opens an OSVVM AlertLog report in YAML format, analyzes the data structure and converts
      the content to an AlertLog hierarchy. Then the total number of warnings, errors and failures is printed. At
      next two nested loops iterate all second-level and third-level child items and prints its warnings, errors and
      failures. Finally, it prints a summary line.

   .. grid-item::
      :columns: 6

      .. tab-set::

         .. tab-item:: Example Code

            .. code-block:: Python

               from pathlib import Path
               from pyEDAA.OSVVM.AlertLog import Document as AlertLogDocument

               path = Path("TbAxi4_BasicReadWrite_alerts.yml")
               doc = AlertLogDocument(path, analyzeAndConvert=True)

               print(f"{doc.Name}: {doc.AlertCountWarnings}/{doc.AlertCountErrors}/{doc.AlertCountFailures}")
               for item in doc:
                 print(f"  {item.Name:<19}: {item.AlertCountWarnings}/{item.AlertCountErrors}/{item.AlertCountFailures}")
                 for innerItem in item:
                   print(f"    {innerItem.Name:<17}: {innerItem.AlertCountWarnings}/{innerItem.AlertCountErrors}/{innerItem.AlertCountFailures}")
               print("=" * 40)
               print(f"Total errors: {doc.TotalErrors}")

         .. tab-item:: Console Output

            .. code-block::

               TbAxi4_BasicReadWrite: 0/0/0
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
               ========================================
               Total errors: 0



.. _ALERT/DataModel:

Data Model
**********

An OSVVM AlertLog report can be summarized as follows:

1. An *AlertLog* report is a tree (or hierarchy) of :ref:`ALERT/DataModel/AlertLogItem` instances.
2. The tree's root element is a :ref:`ALERT/DataModel/Document` instance derived from :ref:`ALERT/DataModel/AlertLogItem`.



.. _ALERT/DataModel/Document:

AlertLog Document
=================

.. grid:: 2

   .. grid-item::
      :columns: 6

      An Alertlog Document represents an OSVVM YAML file and its AlertLog data structure, which is a hierarchy of
      AlertLog items. The OSVVM AlertLog :class:`~pyEDAA.OSVVM.AlertLog.Document` class inherits all methods and
      properties of an :ref:`ALERT/DataModel/AlertLogItem`.

      When a document is instantiated, a path to a YAML file is required. Optionally, the YAML file can be immediately
      analyzed and converted to an AlertLog hierarchy. The given path can be accessed by the
      :data:`~pyEDAA.OSVVM.AlertLog.Document.Path` property. The document class preserves an internal reference
      (:attr:`~pyEDAA.OSVVM.AlertLog.Document._yamlDocument`) to the analyzed YAML document.

      If the document was not analyzed, the :meth:`~pyEDAA.OSVVM.AlertLog.Document.Analyze` and
      :meth:`~pyEDAA.OSVVM.AlertLog.Document.Parse` methods can be used to start these steps. The spent time is captured
      and can be accessed via :data:`~pyEDAA.OSVVM.AlertLog.Document.AnalysisDuration` and
      :data:`~pyEDAA.OSVVM.AlertLog.Document.ModelConversionDuration`.

   .. grid-item::
      :columns: 6

      .. code-block:: Python

         @export
         class Document(AlertLogItem, Settings):
            def __init__(self, filename: Path, analyzeAndConvert: bool = False) -> None:
              ...

            @property
            def Path(self) -> Path:
              ...

            @readonly
            def AnalysisDuration(self) -> timedelta:
              ...

            @readonly
            def ModelConversionDuration(self) -> timedelta:
              ...

            def Analyze(self) -> None:
              ...

            def Parse(self) -> None:
              ...


.. _ALERT/DataModel/Settings:

AlertLog Settings
=================

.. grid:: 2

   .. grid-item::
      :columns: 6

      tbd

   .. grid-item::
      :columns: 6

      .. code-block:: Python

         @export
         class Settings(metaclass=ExtendedType, mixin=True):


.. _ALERT/DataModel/AlertLogItem:

AlertLog Item
=============

.. grid:: 2

   .. grid-item::
      :columns: 6

      An OSVVM AlertLog entry.

      .. todo::

         **Data model: OSVVM AlertLog Item**

         To be documented.

   .. grid-item::
      :columns: 6

      .. code-block:: Python

         @export
         class AlertLogItem(metaclass=ExtendedType, slots=True):
            def __init__(
               self,
               name: str,
               status: AlertLogStatus = AlertLogStatus.Unknown,
               totalErrors: int = 0,
               alertCountWarnings: int = 0,
               alertCountErrors: int = 0,
               alertCountFailures: int = 0,
               passedCount: int = 0,
               affirmCount: int = 0,
               requirementsPassed: int = 0,
               requirementsGoal: int = 0,
               disabledAlertCountWarnings: int = 0,
               disabledAlertCountErrors: int = 0,
               disabledAlertCountFailures: int = 0,
               children: Iterable["AlertLogItem"] = None,
               parent: Nullable["AlertLogItem"] = None
            ) -> None:
              ...

            @readonly
            def Parent(self) -> Nullable["AlertLogItem"]:
              ...

            @readonly
            def Name(self) -> str:
              ...

            @readonly
            def Status(self) -> AlertLogStatus:
              ...

            @readonly
            def TotalErrors(self) -> int:
              ...

            @readonly
            def AlertCountWarnings(self) -> int:
              ...

            @readonly
            def AlertCountErrors(self) -> int:
              ...

            @readonly
            def AlertCountFailures(self) -> int:
              ...

            @readonly
            def PassedCount(self) -> int:
              ...

            @readonly
            def AffirmCount(self) -> int:
              ...

            @readonly
            def RequirementsPassed(self) -> int:
              ...

            @readonly
            def RequirementsGoal(self) -> int:
              ...

            @readonly
            def DisabledAlertCountWarnings(self) -> int:
              ...

            @readonly
            def DisabledAlertCountErrors(self) -> int:
              ...

            @readonly
            def DisabledAlertCountFailures(self) -> int:
              ...

            def __iter__(self) -> Iterator["AlertLogItem"]:
              ...

            def __getitem__(self, name: str) -> "AlertLogItem":
              ...

            def ToTree(self) -> Node:
              ...
