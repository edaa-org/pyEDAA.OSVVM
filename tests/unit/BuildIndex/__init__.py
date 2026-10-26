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
"""Testcases for reading OSVVM's build index file."""
from datetime                import datetime, timedelta, timezone
from pathlib                 import Path
from tempfile                import TemporaryDirectory

from pyTooling.Testing       import Testcase
from pyTooling.Versioning    import YearMonthVersion

from pyEDAA.OSVVM.BuildIndex import BuildIndexError, BuildStatus, BuildEntry, BuildIndex, BuildIndexDocument

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


class Model(Testcase):
	def test_BuildEntry(self) -> None:
		index = BuildIndex()
		startTime = datetime(2026, 10, 10, 16, 50, 45, tzinfo=timezone.utc)
		entry = BuildEntry(
			"RunAllTests", Path("RunAllTests"), BuildStatus.Passed, 3, 1, 2, 0, 0, 0,
			startTime, startTime + timedelta(seconds=5), timedelta(seconds=4.5), "NVC", "1.23.0", YearMonthVersion(2026, 9),
			parent=index
		)

		self.assertIs(index, entry.Parent)
		self.assertEqual([entry], index.Builds)
		self.assertEqual(6, entry.TestcaseCount)
		self.assertEqual(Path("RunAllTests/RunAllTests.yml"), entry.BuildSummaryFile)

	def test_BuildEntry_Status(self) -> None:
		startTime = datetime(2026, 10, 10, 16, 50, 45, tzinfo=timezone.utc)
		with self.assertRaises(TypeError) as context:
			_ = BuildEntry(
				"RunAllTests", Path("RunAllTests"), "PASSED", 3, 1, 2, 0, 0, 0,
				startTime, startTime, timedelta(), "NVC", "1.23.0", YearMonthVersion(2026, 9)
			)

		self.assertEqual("Parameter 'status' is not of type 'BuildStatus'.", str(context.exception))


class Document(Testcase):
	def test_Index(self) -> None:
		doc = BuildIndexDocument(Path("tests/data/OSVVM/BuildIndex/index.yml"), analyzeAndConvert=True)

		self.assertEqual(4, doc.BuildCount)
		builds = list(doc.IterateBuilds())
		self.assertEqual("Osvvm-Libraries_RunAllTests", builds[1].Name)
		self.assertIs(BuildStatus.Passed, builds[1].Status)
		self.assertEqual(314, builds[1].TestcaseCount)
		self.assertEqual("NVC", builds[1].ToolName)
		self.assertEqual(YearMonthVersion(2026, 9), builds[1].OSVVMVersion)
		self.assertEqual(datetime(2026, 10, 10, 19, 41, 16, tzinfo=timezone.utc), builds[1].StartTime)
		self.assertEqual(
			Path("Osvvm-Libraries_RunAllTests/Osvvm-Libraries_RunAllTests.yml"),
			builds[1].BuildSummaryFile
		)

	def test_IterateBuilds_Predicate(self) -> None:
		doc = BuildIndexDocument(Path("tests/data/OSVVM/BuildIndex/index.yml"), analyzeAndConvert=True)

		self.assertEqual(3, len(list(doc.IterateBuilds(lambda build: build.TestcaseCount > 0))))

	def test_Missing(self) -> None:
		path = Path("tests/data/OSVVM/BuildIndex/missing.yml")
		with self.assertRaises(BuildIndexError) as context:
			_ = BuildIndexDocument(path, analyzeAndConvert=True)

		self.assertEqual(f"OSVVM build index '{path}' does not exist.", str(context.exception))

	def test_UnknownKey(self) -> None:
		with TemporaryDirectory() as directory:
			path = Path(directory) / "index.yml"
			content = Path("tests/data/OSVVM/BuildIndex/index.yml").read_text(encoding="utf-8")
			with path.open("w", encoding="utf-8") as file:
				tests = '    Tests:               0\n'
				file.write(content.replace(tests, tests + '    Color:               "red"\n', 1))

			with self.assertRaises(BuildIndexError) as context:
				_ = BuildIndexDocument(path, analyzeAndConvert=True)

		expected = "Additional properties are not allowed ('Color' was unexpected)"
		self.assertEqual([f"/Builds/0 (line 3): {expected}"], context.exception.__notes__)
