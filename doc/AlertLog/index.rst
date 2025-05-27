.. _ALERT:

Alert and Log Report
####################

.. rubric:: Design Goals

* Clearly named classes that model the semantics of an OSVVM AlertLog report.
* The OSVVM AlertLog model instance can be constructed top-down and bottom-up.
* Child objects shall have a reference to their parent.



.. _ALERT:QuickStart:

Quick Start
***********

.. grid:: 2

   .. grid-item::
      :columns: 6

      The following example code opens an OSVVM AlertLog report in YAML format and parses the content. Then the total
      number of warnings, errors and fatal errors is printed. At next it iterates all top-level child items and prints
      its warnings, errors and fatal errors, too. Finally, it prints a summary line.

   .. grid-item::
      :columns: 6

      .. code-block:: Python

         from pathlib import Path
         from pyEDAA.OSVVM.AlertLog import Document as AlertLogDocument

         path = Path("TbAxi4_BasicReadWrite_alerts.yml")
         doc = AlertLogDocument(path, parse=True)

         print(f"{doc.Name}: {doc.AlertCountWarnings}/{doc.AlertCountErrors}/{doc.AlertCountFailures}")
         for item in doc:
            print(f"  {item.Name:<19}: {item.AlertCountWarnings}/{item.AlertCountErrors}/{item.AlertCountFailures}")
         print("=" * 40)
         print(f"Total errors: {doc.TotalErrors}")


.. _ALERT:DataModel:

Data Model
**********

An OSVVM AlertLog report can be summarized as follows:

1. An *AlertLog* report is a tree of :ref:`ALERT:DataModel:AlertLogGroup` instances.
2. The tree's root element is a :ref:`ALERT:DataModel:Document` instance derived from :ref:`ALERT:DataModel:AlertLogGroup`.


.. _ALERT:DataModel:Document:

AlertLog Document
=================

.. grid:: 2

   .. grid-item::
      :columns: 6

      An OSVVM AlertLog :class:`~pyEDAA.OSVVM.AlertLog.Document` class inherits all methods and properties of an
      AlertLog Group (see below: :ref:`ALERT:DataModel:AlertLogGroup`).

      .. todo::

         **Data model: OSVVM AlertLog Document**

         To be documented.

   .. grid-item::
      :columns: 6

      .. code-block:: Python

         @export
         class Document(AlertLogGroup):
            def __init__(self, filename: Path, parse: bool = False) -> None:
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


.. _ALERT:DataModel:AlertLogGroup:

AlertLog Group
==============

.. grid:: 2

   .. grid-item::
      :columns: 6

      An OSVVM AlertLog entry.

      .. todo::

         **Data model: OSVVM AlertLog Group**

         To be documented.

   .. grid-item::
      :columns: 6

      .. code-block:: Python

         @export
         class AlertLogGroup(metaclass=ExtendedType, slots=True):
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
               children: Iterable["AlertLogGroup"] = None,
               parent: Nullable["AlertLogGroup"] = None
            ) -> None:
              ...

            @readonly
            def Parent(self) -> Nullable["AlertLogGroup"]:
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

            def __iter__(self) -> Iterator["AlertLogGroup"]:
              ...

            def __getitem__(self, name: str) -> "AlertLogGroup":
              ...

            def ToTree(self) -> Node:
              ...
