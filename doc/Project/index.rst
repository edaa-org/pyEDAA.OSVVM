.. _PRJ:

OSVVM Project Files
###################

.. rubric:: Design Goals

* Clearly named classes that model the semantics of an OSVVM project.
* The OSVVM project model instance can be constructed top-down and bottom-up.
* Child objects shall have a reference to their parent.
* Referenced files and directories in a ``*.pro`` file are checked for existence when parsing the input file.

.. rubric:: Features

* OSVVM specific variables (``::osvvm::...``) can be configured before parsing to

.. _PRJ:DataModel:

Data Model
**********


.. rubric:: Overall Hierarchy

An :ref:`PRJ:DataModel:Project` contains one or multiple :ref:`builds <PRJ:DataModel:Build>` (a ``*.pro`` file loaded
via :ref:`PRJ:Procedure:build` command). Each build can contain multiple :ref:`VHDL libraries <PRJ:DataModel:VHDLLibrary>`
as well as multiple :ref:`testsuites <PRJ:DataModel:`Testsuite`>. Each VHDL library references multiple
:ref:`VHDL source files <PRJ:DataModel:VHDLSourceFile>` in compile order. Again, each testsuite contains multiple
:ref:`testcases <PRJ:DataModel:Testcase>` in execution order.

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


.. _PRJ:DataModel:Project:

OSVVM Project
=============

.. todo::

   **Data model: OSVVM Project**

   To be documented.


.. _PRJ:DataModel:Build:

Build
=====

.. todo::

   **Data model: Build**

   To be documented.


.. _PRJ:DataModel:VHDLLibrary:

VHDLLibrary
===========

.. todo::

   **Data model: VHDL Library**

   To be documented.


.. _PRJ:DataModel:VHDLSourceFile:

VHDLSourceFile
==============

.. todo::

   **Data model: VHDL source file**

   To be documented.


.. _PRJ:DataModel:Testsuite:

Testsuite
=========

.. todo::

   **Data model: Testsuite**

   To be documented.


.. _PRJ:DataModel:Testcase:

Testcase
========

.. todo::

   **Data model: Testcase**

   To be documented.


.. _PRJ:Procedure:

Implemented TCL Procedures
**************************

The following TCL procedures are implemented as :mod:`Python functions <pyEDAA.OSVVM.Procedures>` and registered to TCL,
thus they can be called from TCL code. This allows pyEDAA.OSVVM to capture parameters handed over these procedures. The
gathered parameters are then collected in a context object and assembled to a :ref:`PRJ:DataModel`.


.. _PRJ:Procedure:build:

build
=====

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.build` references a ``*.pro`` file, which is then loaded and processed. The
      context's current path is changed to the parent directory of the referenced file. The referenced file is added to
      the list of included files collected by the context.

      The reference can refer to:

      * an explicitly named ``<path>/*.pro`` file,
      * an implicitly named ``<path>/build.pro`` file,
      * an implicitly named ``<path>/<path>.pro`` file.

      Each build will create a separate set of reports.

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         build ref/MyLibrary.pro  ; # explicit pro file
         build ref/build.pro      ; # implicit build.pro file
         build ref/ref.pro        ; # implicit <ref>.pro file


.. _PRJ:Procedure:include:

include
=======

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.include` references a ``*.pro`` file, which is then loaded and processed. The
      context's current path is changed to the parent directory of the referenced file. The referenced file is added
      to the list of included files collected by the context.

      The reference can refer to:

      * an explicitly named ``<path>/*.pro`` file,
      * an implicitly named ``<path>/build.pro`` file,
      * an implicitly named ``<path>/<path>.pro`` file.

      Each build will create a separate set of reports.

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         include ref/MyLibrary.pro  ; # explicit pro file
         include ref/build.pro      ; # implicit build.pro file
         include ref/ref.pro        ; # implicit <ref>.pro file


.. _PRJ:Procedure:library:

library
=======

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.library`

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         library myDesign


.. _PRJ:Procedure:analyze:

analyze
=======

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.analyze`

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         analyze src/TopLevel.vhdl


.. _PRJ:Procedure:simulate:

simulate
========

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.simulate`

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         simulate myTestbench


.. _PRJ:Procedure:generic:

generic
=======

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.generic`

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         simulate myTestharness [generic param value]


.. _PRJ:Procedure:TestSuite:

TestSuite
=========

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.TestSuite`

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         TestSuite AllMyTests


.. _PRJ:Procedure:TestName:

TestName
========

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.TestName`

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         TestName myTest


.. _PRJ:Procedure:RunTest:

RunTest
=======

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.RunTest`

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         RunTest testharness.vhdl [generic param value]


.. _PRJ:Procedure:LinkLibrary:

LinkLibrary
===========

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.LinkLibrary`

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         LinkLibrary vendorLib ../libs/vendorLib


.. _PRJ:Procedure:LinkLibraryDirectory:

LinkLibraryDirectory
====================

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.LinkLibraryDirectory`

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         LinkLibraryDirectory ../lib


.. _PRJ:Procedure:SetVHDLVersion:
.. _PRJ:Procedure:GetVHDLVersion:

SetVHDLVersion / SetVHDLVersion
===============================

.. grid:: 2

   .. grid-item::
      :columns: 6

      :func:`pyEDAA.OSVVM.Procedures.SetVHDLVersion`
      :func:`pyEDAA.OSVVM.Procedures.GetVHDLVersion`

   .. grid-item::
      :columns: 6

      .. code-block:: TCL

         # TCL code examples
         SetVHDLVersion 2019


.. _PRJ:Procedure:FileExists:

FileExists
==========


.. _PRJ:Procedure:DirectoryExists:

DirectoryExists
===============


.. _PRJ:Procedure:ChangeWorkingDirectory:

ChangeWorkingDirectory
======================
