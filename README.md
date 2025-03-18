[![Sourcecode on GitHub](https://img.shields.io/badge/pyEDAA-OSVVM-ab47bc.svg?longCache=true&style=flat-square&logo=github&longCache=true&logo=GitHub&labelColor=6a1b9a)](https://GitHub.com/edaa-org/pyEDAA.OSVVM)
[![Sourcecode License](https://img.shields.io/pypi/l/pyEDAA.OSVVM?longCache=true&style=flat-square&logo=Apache&label=code)](LICENSE.md)
[![Documentation](https://img.shields.io/website?longCache=true&style=flat-square&label=edaa-org.github.io%2FpyEDAA.OSVVM&logo=GitHub&logoColor=fff&up_color=blueviolet&up_message=Read%20now%20%E2%9E%9A&url=https%3A%2F%2Fedaa-org.github.io%2FpyEDAA.OSVVM%2Findex.html)](https://edaa-org.github.io/pyEDAA.OSVVM/)
[![Documentation License](https://img.shields.io/badge/doc-CC--BY%204.0-green?longCache=true&style=flat-square&logo=CreativeCommons&logoColor=fff)](LICENSE.md)  
[![PyPI](https://img.shields.io/pypi/v/pyEDAA.OSVVM?longCache=true&style=flat-square&logo=PyPI&logoColor=FBE072)](https://pypi.org/project/pyEDAA.OSVVM/)
![PyPI - Status](https://img.shields.io/pypi/status/pyEDAA.OSVVM?longCache=true&style=flat-square&logo=PyPI&logoColor=FBE072)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyEDAA.OSVVM?longCache=true&style=flat-square&logo=PyPI&logoColor=FBE072)  
[![GitHub Workflow - Build and Test Status](https://img.shields.io/github/actions/workflow/status/edaa-org/pyEDAA.OSVVM/Pipeline.yml?longCache=true&style=flat-square&label=Build%20and%20test&logo=GitHub%20Actions&logoColor=FFFFFF)](https://GitHub.com/edaa-org/pyEDAA.OSVVM/actions/workflows/Pipeline.yml)
[![Libraries.io status for latest release](https://img.shields.io/librariesio/release/pypi/pyEDAA.OSVVM?longCache=true&style=flat-square&logo=Libraries.io&logoColor=fff)](https://libraries.io/github/edaa-org/pyEDAA.OSVVM)

<!--
[![Dependent repos (via libraries.io)](https://img.shields.io/librariesio/dependent-repos/pypi/pyEDAA.OSVVM?longCache=true&style=flat-square&logo=GitHub)](https://github.com/edaa-org/pyEDAA.OSVVM/network/dependents)
[![Requires.io](https://img.shields.io/requires/github/edaa-org/pyEDAA.OSVVM?longCache=true&style=flat-square)](https://requires.io/github/edaa-org/pyEDAA.OSVVM/requirements/?branch=main)
[![Libraries.io SourceRank](https://img.shields.io/librariesio/sourcerank/pypi/pyEDAA.OSVVM)](https://libraries.io/github/edaa-org/pyEDAA.OSVVM/sourcerank)  
-->

# Main Goals

This package provides OSVVM-specific data models and parsers. The data models can be used as-is or converted to generic
data models of the pyEDAA data model family. This includes parsing OSVVM's `*.pro`-files and translating them to a
[pyEDAA.ProjectModel](https://github.com/edaa-org/pyEDAA.ProjectModel) instance as well as reading OSVVM's reports in
YAML format like test results, alerts or functional coverage.

Frameworks consuming these data models can build higher level features and services on top of these models, while using
one parser that's aligned with OSVVM's data formats.

# Data Models

## Project Description via `*.pro`-Files

**Features:**

* Parse OSVVM's `*.pro` files including complex TCL code structures like nested `if`-statements.
* Emulate tool specific TCL variables: `::osvvm::ToolVendor`, `::osvvm::ToolName` `::osvvm::ToolNameVersion`, ... 
* Convert the project description stored in one or more `*.pro` files to a
 [`pyEDAA.ProjectModel`](https://github.com/edaa-org/pyEDAA.ProjectModel) instance.


**Basic Data Model:**

* VHDL source files are accumulated in VHDL libraries.
* The order of source files is preserved in a library.
* Test cases are accumulated in test suites.
* Configuration changes are collected in a context.    
  * When a new item is added to the model, certain default values or collected configuration values are used to create
  this new item.

**Quick Example**

```python
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
```

## Testsuite Summary Reports

> [!NOTE]  
> *TBD*

## Testcase Summary Reports

> [!NOTE]  
> *TBD*

## Alert and Log Reports

> [!NOTE]  
> *TBD*

## Scoreboard Reports

> [!NOTE]  
> *TBD*

## Functional Coverage Reports

> [!NOTE]  
> *TBD*

## Requirement Reports

> [!NOTE]  
> *TBD*


# Use Cases

* Reading OSVVM's project description from `*.pro` files.
  * Convert to other data or file format.
* Reading OSVVM's reports from `*.yaml` files.
  * Convert to other data or file format.
  * Investigate reports.
  * Merge reports.


# Examples

```python
from pathlib import Path
from pyEDAA.OSVVM.TCL import OsvvmProFileProcessor

def main() -> None:
  processor = OsvvmProFileProcessor()

  processor.LoadProFile(Path("OSVVM/OSVVMLibraries/OsvvmLibraries.pro"))
  processor.LoadProFile(Path("OSVVM/OSVVMLibraries/RunAllTests.pro"))

  for libraryName, lib in processor.Context.Libraries.items():
    print(f"Library: {libraryName} ({len(lib.Files)})")
    for file in lib.Files:
      print(f"  {file.Path}")

  print()
  for testsuiteName, ts in processor.Context.Testsuites.items():
    print(f"Testsuite: {testsuiteName} ({len(ts.Testcases)})")
    for tc in ts.Testcases.values():
      print(f"  {tc.Name}")
```

# Consumers


# References

* [OSVVM/OSVVM-Scripts](https://github.com/OSVVM/OSVVM-Scripts)


# Contributors

* [Patrick Lehmann](https://GitHub.com/Paebbels) (Maintainer)
* [and more...](https://GitHub.com/edaa-org/pyEDAA.OSVVM/graphs/contributors)

# License

This Python package (source code) licensed under [Apache License 2.0](LICENSE.md).  
The accompanying documentation is licensed under [Creative Commons - Attribution 4.0 (CC-BY 4.0)](doc/Doc-License.rst).

-------------------------
SPDX-License-Identifier: Apache-2.0
