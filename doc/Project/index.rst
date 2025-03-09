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
