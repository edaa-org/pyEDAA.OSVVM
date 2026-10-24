.. _DIR/BuildInformation:

Build Information
#################

The directive ``osvvm:build-information`` renders what a build summary states about the build, as OSVVM's HTML build
summary shows it: the build's name and status, the testcases per status, the start and finish time, the elapsed time,
the simulator, OSVVM's version, the build's error code, the analysis and simulation errors, and links to the build's
log files, which Sphinx copies into the build as downloads. A log file the build summary names, but which doesn't
exist, is warned about.

.. code-block:: ReST

   .. osvvm:build-information::
      :reportid: osvvmlibraries

This is how the documentation's demo build renders:

.. osvvm:build-information::
   :reportid: demo


.. _DIR/BuildInformation/Options:

Options
*******

.. rst:directive:: osvvm:build-information

   Renders a build's information as a field list.

   .. rst:directive:option:: reportid: <identifier>

      The build summary, as declared in ``osvvm_build_summaries``. Required.

   .. rst:directive:option:: class: <CSS classes>

      Additional CSS classes on the field list, which carries the class ``osvvm-build-information``.
