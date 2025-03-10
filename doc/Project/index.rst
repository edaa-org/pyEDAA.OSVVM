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

OSVVM Project
=============

VHDLLibrary
===========

VHDLSourceFile
==============

Testsuite
=========

Testcase
========


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
