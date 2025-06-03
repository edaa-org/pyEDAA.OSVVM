Build Summary
#############

The following directives are provided for visualizing OSVVM's build reports.

.. rst:directive:: osvvm:build-summary

   Generate a table summarizing the unittest results per testsuite and testcase. The testsuite hierarchy is visualized by indentation.

   .. rst:directive:option:: class

      Optional: A list of space separated user-defined CSS class names.

      The CSS classes are applied on the HTML ``<table>`` tag.

   .. rst:directive:option:: reportid

      An identifier referencing a dictionary entry (key) in the configuration variable ``osvvm_build_summaries`` defined in :file:`conf.py`.

   .. rst:directive:option:: build-name

      Optional: Override the build report's name.

   .. rst:directive:option:: show-testcases

      Optional: Select if all testcases (``all``) or only flawed testcases (``not-passed``) should be listed per testsuite.

   .. rst:directive:option:: hide-build-summary

      Optional: If this flag is present, hide the summary row.
