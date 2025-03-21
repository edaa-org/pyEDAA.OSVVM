.. include:: shields.inc

.. image:: _static/logo_on_light.svg
   :height: 90 px
   :align: center
   :target: https://GitHub.com/edaa-org/pyEDAA.OSVVM

.. raw:: html

    <br>

.. raw:: latex

   \part{Introduction}

.. only:: html

   |  |SHIELD:svg:OSVVM-github| |SHIELD:svg:OSVVM-src-license| |SHIELD:svg:OSVVM-ghp-doc| |SHIELD:svg:OSVVM-doc-license|
   |  |SHIELD:svg:OSVVM-pypi-tag| |SHIELD:svg:OSVVM-pypi-status| |SHIELD:svg:OSVVM-pypi-python|
   |  |SHIELD:svg:OSVVM-gha-test| |SHIELD:svg:OSVVM-lib-status| |SHIELD:svg:OSVVM-codacy-quality| |SHIELD:svg:OSVVM-codacy-coverage| |SHIELD:svg:OSVVM-codecov-coverage|

.. Disabled shields: |SHIELD:svg:OSVVM-lib-dep| |SHIELD:svg:OSVVM-req-status| |SHIELD:svg:OSVVM-lib-rank|

.. only:: latex

   |SHIELD:png:OSVVM-github| |SHIELD:png:OSVVM-src-license| |SHIELD:png:OSVVM-ghp-doc| |SHIELD:png:OSVVM-doc-license|
   |SHIELD:png:OSVVM-pypi-tag| |SHIELD:png:OSVVM-pypi-status| |SHIELD:png:OSVVM-pypi-python|
   |SHIELD:png:OSVVM-gha-test| |SHIELD:png:OSVVM-lib-status| |SHIELD:png:OSVVM-codacy-quality| |SHIELD:png:OSVVM-codacy-coverage| |SHIELD:png:OSVVM-codecov-coverage|

.. Disabled shields: |SHIELD:png:OSVVM-lib-dep| |SHIELD:png:OSVVM-req-status| |SHIELD:png:OSVVM-lib-rank|

--------------------------------------------------------------------------------

The pyEDAA.OSVVM Documentation
##############################

Parser and converters for `OSVVM-specific <https://github.com/OSVVM>`__ data models and report formats.


.. _GOALS:

Main Goals
**********

This package provides OSVVM-specific data models and parsers. The data models can be used as-is or converted to generic
data models of the pyEDAA data model family. This includes parsing OSVVM's ``*.pro``-files and translating them to a
`pyEDAA.ProjectModel <https://edaa-org.github.io/pyEDAA.ProjectModel>`__ instance as well as reading OSVVM's reports in
YAML format like test results, alerts or functional coverage.

Frameworks consuming these data models can build higher level features and services on top of these models, while
using one parser that's aligned with OSVVM's data formats.


.. _USECASES:

Use Cases
*********

.. _USECASE:Project:

OSVVM Project
=============

.. grid:: 2

   .. grid-item::
      :columns: 5

      OSVVM describes its projects using imperative TCL code in so called ``*.pro`` files. These contain lots of
      information like VHDL library names, used VHDL standard, or compile order. Besides compilation information, these
      files also contain information about grouping testcases into testsuites as well as variants of a test by applying
      top-level generics to a simulation. In addition various tool options can be enabled and disabled, e.g. code
      coverage collection. These options can be set globally, locally or per item.

      pyEDAA.OSVVM provides an :ref:`artificial TCL environment <PRJ:Procedure>`, so OSVVM's ``*.pro`` files can be
      executed and contained information is collected in a data model representing :ref:`builds <PRJ:DataModel:Build>`,
      :ref:`VHDL libraries <PRJ:DataModel:VHDLLibrary>`, :ref:`VHDL source files <PRJ:DataModel:VHDLSourceFile>`,
      :ref:`testsuites <PRJ:DataModel:Testsuite>`, and :ref:`testcases <PRJ:DataModel:Testcase>`.

      Afterwards, the :ref:`OSVVM project model <PRJ>` can be used as-is, or it can be converted to other data or file
      formats. One unified data model is `pyEDAA.ProjectModel <https://edaa-org.github.com/pyEDAA.ProjectModel>`__.

   .. grid-item::
      :columns: 7

      .. tab-set::

         .. tab-item:: Usage
            :sync: usage

            .. code-block:: Python

               from pathlib import Path
               from pyEDAA.OSVVM.TCL import OsvvmProFileProcessor

               processor = OsvvmProFileProcessor()
               processor.LoadBuildFile(Path("OSVVM/OSVVMLibraries/OsvvmLibraries.pro"))
               processor.LoadBuildFile(Path("OSVVM/OSVVMLibraries/RunAllTests.pro"))

               project = processor.Context.ToProject("OsvvmLibraries")
               for buildName, build in project.Builds.items():
                 for libraryName, lib in build.Libraries.items():
                   for file in lib.Files:
                     ...

                 for testsuiteName, ts in build.Testsuites.items():
                   for tc in ts.Testcases.values():
                     ...

         .. tab-item:: Data Model
            :sync: datamodel
            :selected:

            .. mermaid::

               graph TD;
                 P[Project<br/>&quot;OSVVM&quot;]:::clsPrj-->B1[Build<br/>&quot;OsvvmLibraries&quot;]:::clsBld
                 P   -->B2[Build<br/>&quot;RunAllTests&quot;]:::clsBld
                 B1  -->Lib1[VHDLLibrary<br/>&quot;osvvm&quot;]:::clsLib
                 B1  -->Lib2[VHDLLibrary<br/>&quot;osccm_common&quot;]:::clsLib

                 Lib1-->F1[VHDLSourceFile<br/>&quot;file1.vhdl&quot;]:::clsFile
                 Lib1-->F2[VHDLSourceFile<br/>&quot;file2.vhdl&quot;]:::clsFile
                 Lib2-->F3[VHDLSourceFile<br/>&quot;file3.vhdl&quot;]:::clsFile
                 Lib2-->F4[VHDLSourceFile<br/>&quot;file4.vhdl&quot;]:::clsFile

                 B2  -->Lib4[VHDLLibrary<br/>&quot;osvvm_uart&quot;]:::clsLib
                 Lib4-->F7[VHDLSourceFile<br/>&quot;file7.vhdl&quot;]:::clsFile
                 Lib4-->F8[VHDLSourceFile<br/>&quot;file8.vhdl&quot;]:::clsFile
                 B2  -->TS1[Testsuite<br/>&quot;UART&quot;]:::clsTS
                 B2  -->TS2[Testsuite<br/>&quot;AXI4_Lite&quot;]:::clsTS
                 TS1 -->TC1[Testcase<br/>&quot;SendGet&quot;]:::clsTC
                 TS1 -->TC2[Testcase<br/>&quot;SetOption&quot;]:::clsTC
                 TS2 -->TC3[Testcase<br/>&quot;ReadWrite&quot;]:::clsTC
                 TS2 -->TC4[Testcase<br/>&quot;SetOption&quot;]:::clsTC

                 classDef clsPrj  fill:#bf80ff
                 classDef clsBld  fill:#9f9fdf
                 classDef clsLib  fill:#ffdf80
                 classDef clsFile fill:#d5ff80
                 classDef clsTS   fill:#8080ff
                 classDef clsTC   fill:#80ff80

.. _USECASE:Reports:

OSVVM Reports
=============

OSVVM provides multiple reports in YAML files.

* Reading OSVVM's reports from ``*.yaml`` files.

  * Convert to other data or file format.
  * Investigate reports.
  * Merge reports.


.. _NEWS:

News
****

.. only:: html

   March 2025 - Reading ``*.pro`` Files
   ====================================

.. only:: latex

   .. rubric:: Reading ``*.pro`` Files

* Previously, reading OSVVM's ``*.pro`` files was achieved via `pyEDAA.ProjectModel <https://GitHub.com/edaa-org/pyEDAA.ProjectModel>`__,
  but OSVVM's file format became more complicated, so a new approach was needed. Moreover, OSVVM created more data
  formats, thus this package was outsourced from ``pyEDAA.ProjectModel``.
* Thus, OSVVM became a new citizen of `EDA² <https://GitHub.com/edaa-org>`__ and got integrated into the ``pyEDAA``
  namespace at PyPI.


.. _CONTRIBUTORS:

Contributors
************

* :gh:`Patrick Lehmann <Paebbels>` (Maintainer)
* `and more... <https://GitHub.com/edaa-org/pyEDAA.OSVVM/graphs/contributors>`__


.. _LICENSE:

License
*******

.. only:: html

   This Python package (source code) is licensed under `Apache License 2.0 <Code-License.html>`__. |br|
   The accompanying documentation is licensed under `Creative Commons - Attribution 4.0 (CC-BY 4.0) <Doc-License.html>`__.

.. only:: latex

   This Python package (source code) is licensed under **Apache License 2.0**. |br|
   The accompanying documentation is licensed under **Creative Commons - Attribution 4.0 (CC-BY 4.0)**.


.. toctree::
   :hidden:

   Used as a layer of EDA² ➚ <https://edaa-org.github.io/>


.. toctree::
   :caption: Introduction
   :hidden:

   Installation
   Dependency


.. raw:: latex

   \part{Main Documentation}

.. toctree::
   :caption: Main Documentation
   :hidden:

   Project/index
   Testsuite/index
   Testcase/index
   AlertLog/index
   Scoreboard/index
   FunctionalCoverage/index
   Requirements/index

.. raw:: latex

   \part{References and Reports}

.. toctree::
   :caption: References and Reports
   :hidden:

   Python Class Reference <pyEDAA.OSVVM/pyEDAA.OSVVM>
   unittests/index
   coverage/index
   Doc. Coverage Report <DocCoverage>
   Static Type Check Report ➚ <typing/index>

.. Coverage Report ➚ <coverage/index>

.. raw:: latex

   \part{Appendix}

.. toctree::
   :caption: Appendix
   :hidden:

   License
   Doc-License
   Glossary
   genindex
   Python Module Index <modindex>
   TODO
