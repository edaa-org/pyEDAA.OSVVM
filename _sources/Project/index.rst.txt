.. _PRO:

OSVVM Project Files
###################

.. rubric:: Design Goals

* Clearly named classes that model the semantics of an OSVVM project.
* The OSVVM project model instance can be constructed top-down and bottom-up.
* Child objects shall have a reference to their parent.
* Referenced files and directories in a ``*.pro`` file are checked for existence when parsing the input file.

.. rubric:: Features

* OSVVM specific variables (``::osvvm::...``) can be configured before parsing to

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


Implemented TCL Procedures
**************************

build
=====

.. code-block:: TCL

   # Examples
   build ref/MyLibrary.pro  ; # explicit pro file
   build ref/build.pro      ; # implicit build.pro file
   build ref/ref.pro        ; # implicit <ref>.pro file

:func:`pyEDAA.OSVVM.Procedures.build` references a ``*.pro`` file, which is then loaded and processed. The context's
current path is changed to the parent directory of the referenced file. The referenced file is added to the list of
included files collected by the context.

The reference can refer to:

* an explicitly named ``<path>/*.pro`` file,
* an implicitly named ``<path>/build.pro`` file,
* an implicitly named ``<path>/<path>.pro`` file.

Each build will create a separate set of reports.



include
=======


library
=======

analyze
=======


simulate
========

generic
=======

TestSuite
=========


TestName
========


RunTest
=======

LinkLibrary
===========

LinkLibraryDirectory
====================


SetVHDLVersion / SetVHDLVersion
===============================

FileExists
==========


DirectoryExists
===============


ChangeWorkingDirectory
======================
