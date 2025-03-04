# Main Goals

This package provides OSVVM-specific data models and parsers. The data models can be used as is or converted to generic
data models of the pyEDAA data model family. This includes parsing OSVVM's `*.pro`-files and translating them to a
pyEDAA.ProjectModel instance as well as reading OSVVM's reports in YAML format like test results, alerts or functional
coverage.

Frameworks consuming these data models can build higher level features and services on top of these models, while
using one parser that's aligned with OSVVM's data formats.

# Data Models

## Project Description via `*.pro`-Files


## Testsuite Summary Reports


## Testcase Summary Reports


## Alert and Log Reports


## Scoreboard Reports


## Functional Coverage Reports


## Requirement Reports




# Features



# Use Cases

* Reading OSVVM's `*.pro` files.

# Examples



# Consumers


# References

* [OSVVM/OSVVM-Scripts: OSVVMProjectScripts.tcl](https://GitHub.com/OSVVM/OSVVM-Scripts/blob/master/OSVVMProjectScripts.tcl)


# Contributors

* [Patrick Lehmann](https://GitHub.com/Paebbels) (Maintainer)
* [and more...](https://GitHub.com/edaa-org/pyEDAA.OSVVM/graphs/contributors)

# License

This Python package (source code) licensed under [Apache License 2.0](LICENSE.md).  
The accompanying documentation is licensed under [Creative Commons - Attribution 4.0 (CC-BY 4.0)](doc/Doc-License.rst).

-------------------------
SPDX-License-Identifier: Apache-2.0
