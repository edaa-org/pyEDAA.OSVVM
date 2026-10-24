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
# Copyright 2021-2026 Electronic Design Automation Abstraction (EDA²)                                                  #
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
"""Testcases for OSVVM's AlertLog YAML file format."""
from datetime              import timedelta
from pathlib               import Path

from pyTooling.Testing     import Testcase

from pyEDAA.OSVVM.AlertLog import AlertLogError, AlertLogItem, AlertLogStatus, AlreadyInAlertLogError, Document, \
                                  DuplicateAlertLogItemError

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


class Status(Testcase):
	def test_Parse(self) -> None:
		self.assertIs(AlertLogStatus.Passed, AlertLogStatus.Parse("PASSED"))
		self.assertIs(AlertLogStatus.Failed, AlertLogStatus.Parse("FAILED"))
		self.assertIs(AlertLogStatus.StopLimit, AlertLogStatus.Parse("STOPLIMIT"))
		self.assertIs(AlertLogStatus.TimeOut, AlertLogStatus.Parse("TIMEOUT"))
		self.assertIs(AlertLogStatus.ManualChecks, AlertLogStatus.Parse("MANUALCHECKS"))
		self.assertIs(AlertLogStatus.NoChecks, AlertLogStatus.Parse("NOCHECKS"))

	def test_Parse_Case(self) -> None:
		self.assertIs(AlertLogStatus.Passed, AlertLogStatus.Parse("passed"))
		self.assertIs(AlertLogStatus.Failed, AlertLogStatus.Parse("Failed"))

	def test_Parse_Unknown(self) -> None:
		with self.assertRaises(AlertLogError) as context:
			_ = AlertLogStatus.Parse("dummy")

		self.assertEqual("Unknown AlertLog status 'dummy'.", str(context.exception))
		self.assertIsInstance(context.exception.__cause__, ValueError)

	def test_Bool(self) -> None:
		self.assertTrue(AlertLogStatus.Passed)
		self.assertFalse(AlertLogStatus.Failed)
		self.assertFalse(AlertLogStatus.TimeOut)
		self.assertFalse(AlertLogStatus.Unknown)


class Instantiation(Testcase):
	def test_AlertLogItem(self) -> None:
		item = AlertLogItem("name")

		self.assertIsNone(item.Parent)
		self.assertIs(AlertLogStatus.Unknown, item.Status)
		self.assertEqual("name", item.Name)
		self.assertEqual(0, len(item))
		self.assertEqual(0, len(item.Children))
		self.assertEqual(0, item.TotalErrors)
		self.assertEqual(0, item.AlertCountWarnings)
		self.assertEqual(0, item.AlertCountErrors)
		self.assertEqual(0, item.AlertCountFailures)
		self.assertEqual(0, item.AffirmCount)
		self.assertEqual(0, item.PassedCount)
		self.assertEqual(0, item.RequirementsGoal)
		self.assertEqual(0, item.RequirementsPassed)
		self.assertEqual(0, item.DisabledAlertCountWarnings)
		self.assertEqual(0, item.DisabledAlertCountErrors)
		self.assertEqual(0, item.DisabledAlertCountFailures)


class Hierarchy(Testcase):
	def test_TopDown(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1", parent=root)

		self.assertIsNone(root.Parent)
		self.assertIs(item.Parent, root)
		self.assertEqual(1, len(root))
		self.assertEqual(0, len(item))
		self.assertIs(item, root["item1"])

	def test_BottomUp1(self) -> None:
		child1 = AlertLogItem("item1")
		children = child1,
		root = AlertLogItem("root", children=children)

		self.assertIsNone(root.Parent)
		self.assertEqual(1, len(root))
		for child in children:
			self.assertIs(child.Parent, root)
			self.assertEqual(0, len(child))
			self.assertIs(child, root[child.Name])

	def test_BottomUp2(self) -> None:
		child1 = AlertLogItem("item1")
		child2 = AlertLogItem("item2")
		children = child1, child2
		root = AlertLogItem("root", children=children)

		self.assertIsNone(root.Parent)
		self.assertEqual(2, len(root))
		for child in children:
			self.assertIs(child.Parent, root)
			self.assertEqual(0, len(child))
			self.assertIs(child, root[child.Name])

	def test_TopDown_Duplicate(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1", parent=root)

		with self.assertRaises(DuplicateAlertLogItemError) as context:
			_ = AlertLogItem("item1", parent=root)

		self.assertIs(item, context.exception.Item)

	def test_BottomUp_AlreadyInAlertLog(self) -> None:
		root = AlertLogItem("root")
		child = AlertLogItem("item1", parent=root)

		with self.assertRaises(AlreadyInAlertLogError) as context:
			_ = AlertLogItem("other", children=(child, ))

		self.assertIs(child, context.exception.Item)

	def test_Parent(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1")
		item.Parent = root

		self.assertIsNone(root.Parent)
		self.assertIs(item.Parent, root)
		self.assertEqual(1, len(root))
		self.assertEqual(0, len(item))


class Iterate(Testcase):
	def test_Iterate(self) -> None:
		child1 = AlertLogItem("item1")
		child2 = AlertLogItem("item2")
		children = child1, child2
		root = AlertLogItem("root", children=children)

		self.assertTupleEqual(tuple(root), children)
		self.assertDictEqual(root.Children, {c.Name: c for c in children})


class Parse(Testcase):
	def test_Create(self) -> None:
		path = Path("tests/data/OSVVM/TbAxi4_BasicReadWrite_alerts.yml")
		document = Document(path)

		self.assertEqual(path, document.Path)
		with self.assertRaises(AlertLogError):
			_ = document.AnalysisDuration

		with self.assertRaises(AlertLogError):
			_ = document.ModelConversionDuration

	def test_Create_WithParse(self) -> None:
		path = Path("tests/data/OSVVM/TbAxi4_BasicReadWrite_alerts.yml")
		document = Document(path, analyzeAndConvert=True)

		self.assertEqual(path, document.Path)
		self.assertEqual("TbAxi4_BasicReadWrite", document.Name)
		self.assertIs(AlertLogStatus.Passed, document.Status)
		self.assertEqual(5, len(document))
		self.assertEqual(40, document["Default"].PassedCount)
		self.assertGreater(document.AnalysisDuration, timedelta())
		self.assertGreater(document.ModelConversionDuration, timedelta())
