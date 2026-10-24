# ==================================================================================================================== #
#              _____ ____    _        _      ___  ______     ____     ____  __                                         #
#  _ __  _   _| ____|  _ \  / \      / \    / _ \/ ___\ \   / /\ \   / /  \/  |                                        #
# | '_ \| | | |  _| | | | |/ _ \    / _ \  | | | \___ \\ \ / /  \ \ / /| |\/| |                                        #
# | |_) | |_| | |___| |_| / ___ \  / ___ \ | |_| |___) |\ V /    \ V / | |  | |                                        #
# | .__/ \__, |_____|____/_/   \_\/_/   \_(_)___/|____/  \_/      \_/  |_|  |_|                                        #
# |_|    |___/                                                                                                         #
# ==================================================================================================================== #
# Authors:                                                                                                             #
#   Patrick Lehmann                                                                                                    #
#                                                                                                                      #
# License:                                                                                                             #
# ==================================================================================================================== #
# Copyright 2026-2026 Electronic Design Automation Abstraction (EDA²)                                                  #
#                                                                                                                      #
# Licensed under the Apache License, Version 2.0 (the "License");                                                      #
# you may not use this file except in compliance with the License.                                                     #
# You may obtain a copy of the License at                                                                              #
#                                                                                                                      #
#   http://www.apache.org/licenses/LICENSE-2.0                                                                         #
#                                                                                                                      #
# Unless required by applicable law or agreed to in writing, software                                                  #
# distributed under the License is distributed on an "AS IS" BASIS,                                                    #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                             #
# See the License for the specific language governing permissions and                                                  #
# limitations under the License.                                                                                       #
#                                                                                                                      #
# SPDX-License-Identifier: Apache-2.0                                                                                  #
# ==================================================================================================================== #
#
"""
A resource package of the JSON Schemas of OSVVM's YAML files, one per file format and format version.

The files are named :file:`OSVVM-<Format>-<FormatVersion>.schema.json`. A document derived from
:class:`~pyEDAA.OSVVM.YAMLDocumentMixin` names its schema file per format version in ``_SCHEMAS``.

.. rubric:: Resources

* :file:`OSVVM-BuildSummary-0.1.schema.json` - OSVVM's build summary :file:`<build>.yml`, format version 0.1.
* :file:`OSVVM-BuildIndex-0.1.schema.json` - OSVVM's build index :file:`index.yml`, format version 0.1.
* :file:`OSVVM-TestcaseSettings-0.1.schema.json` - OSVVM's test case settings :file:`<TestCaseFileName>_run.yml`, format
  version 0.1.
* :file:`OSVVM-AlertLog-0.1.schema.json` - OSVVM's AlertLog :file:`<TestCaseFileName>_alerts.yml`, format version 0.1.

.. rubric:: Usage

:func:`~pyTooling.Common.readResourceFile` returns a resource file's content.

.. admonition:: ``example.py``

   .. code-block:: python

      from pyTooling.Common import readResourceFile

      from pyEDAA.OSVVM     import Resources

      schema = readResourceFile(Resources, "OSVVM-BuildSummary-0.1.schema.json")
"""
