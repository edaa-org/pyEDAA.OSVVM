OSVVM Domain
############


Installation
************

.. admonition:: conf.py

   .. code-block:: python

      extensions = [
        ...
        "pyEDAA.OSVVM.Sphinx"
      ]

Configuration
*************

.. admonition:: conf.py

   .. code-block:: python

      osvvm_build_summaries = {
         "osvvmlibraries": {
            "name":        "OsvvmLibraries",
            "yaml_report": "reports/OSVVMLibraries_RunAllTests.yml",
         }
      }


