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
		self.assertEqual(0, item.ChildCount)
		self.assertEqual(0, len(item.Children))
		self.assertEqual(0, item.TotalErrorCount)
		self.assertEqual(0, item.WarningCount)
		self.assertEqual(0, item.ErrorCount)
		self.assertEqual(0, item.FailureCount)
		self.assertEqual(0, item.AffirmCount)
		self.assertEqual(0, item.PassedCount)
		self.assertEqual(0, item.RequirementsGoalCount)
		self.assertEqual(0, item.PassedRequirementsCount)
		self.assertEqual(0, item.DisabledWarningCount)
		self.assertEqual(0, item.DisabledErrorCount)
		self.assertEqual(0, item.DisabledFailureCount)

	def test_AlertLogItem_Values(self) -> None:
		item = AlertLogItem("name", AlertLogStatus.Failed, 6, 1, 2, 3, 7, 8, 9, 10, 4, 5, 6)

		self.assertIs(AlertLogStatus.Failed, item.Status)
		self.assertEqual(6, item.TotalErrorCount)
		self.assertEqual(1, item.WarningCount)
		self.assertEqual(2, item.ErrorCount)
		self.assertEqual(3, item.FailureCount)
		self.assertEqual(7, item.PassedCount)
		self.assertEqual(8, item.AffirmCount)
		self.assertEqual(9, item.PassedRequirementsCount)
		self.assertEqual(10, item.RequirementsGoalCount)
		self.assertEqual(4, item.DisabledWarningCount)
		self.assertEqual(5, item.DisabledErrorCount)
		self.assertEqual(6, item.DisabledFailureCount)

	def test_AlertLogItem_Name(self) -> None:
		with self.assertRaises(ValueError) as context:
			_ = AlertLogItem(None)

		self.assertEqual("Parameter 'name' is None.", str(context.exception))

		with self.assertRaises(TypeError) as context:
			_ = AlertLogItem(1)

		self.assertEqual("Parameter 'name' is not of type 'str'.", str(context.exception))

	def test_AlertLogItem_Status(self) -> None:
		with self.assertRaises(ValueError) as context:
			_ = AlertLogItem("name", None)

		self.assertEqual("Parameter 'status' is None.", str(context.exception))

		with self.assertRaises(TypeError) as context:
			_ = AlertLogItem("name", "PASSED")

		self.assertEqual("Parameter 'status' is not of type 'AlertLogStatus'.", str(context.exception))

	def test_AlertLogItem_Counts(self) -> None:
		with self.assertRaises(ValueError) as context:
			_ = AlertLogItem("name", affirmCount=None)

		self.assertEqual("Parameter 'affirmCount' is None.", str(context.exception))

		with self.assertRaises(TypeError) as context:
			_ = AlertLogItem("name", passedCount=1.0)

		self.assertEqual("Parameter 'passedCount' is not of type 'int'.", str(context.exception))

		with self.assertRaises(TypeError) as context:
			_ = AlertLogItem("name", disabledFailureCount="0")

		self.assertEqual("Parameter 'disabledFailureCount' is not of type 'int'.", str(context.exception))

	def test_AlertLogItem_Parent(self) -> None:
		with self.assertRaises(TypeError) as context:
			_ = AlertLogItem("name", parent="root")

		self.assertEqual("Parameter 'parent' is not of type 'AlertLogItem'.", str(context.exception))


class Hierarchy(Testcase):
	def test_TopDown(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1", parent=root)

		self.assertIsNone(root.Parent)
		self.assertIs(item.Parent, root)
		self.assertEqual(1, root.ChildCount)
		self.assertEqual(0, item.ChildCount)
		self.assertIs(item, root.Children["item1"])

	def test_TopDown_Duplicate(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1", parent=root)

		with self.assertRaises(DuplicateAlertLogItemError) as context:
			_ = AlertLogItem("item1", parent=root)

		self.assertEqual("AlertLog item 'root' has a child 'item1' already.", str(context.exception))
		self.assertIs(item, context.exception.Item)
		self.assertIs(item, root.Children["item1"])

	def test_BottomUp(self) -> None:
		child1 = AlertLogItem("item1")
		child2 = AlertLogItem("item2")
		children = child1, child2
		root = AlertLogItem("root", children=children)

		self.assertIsNone(root.Parent)
		self.assertEqual(2, root.ChildCount)
		for child in children:
			self.assertIs(child.Parent, root)
			self.assertEqual(0, child.ChildCount)
			self.assertIs(child, root.Children[child.Name])

	def test_BottomUp_Duplicate(self) -> None:
		child1 = AlertLogItem("item1")
		child2 = AlertLogItem("item1")

		with self.assertRaises(DuplicateAlertLogItemError) as context:
			_ = AlertLogItem("root", children=(child1, child2))

		self.assertEqual("AlertLog item 'root' has a child 'item1' already.", str(context.exception))
		self.assertIs(child1, context.exception.Item)

	def test_BottomUp_AlreadyInAlertLog(self) -> None:
		root = AlertLogItem("root")
		child = AlertLogItem("item1", parent=root)

		with self.assertRaises(AlreadyInAlertLogError) as context:
			_ = AlertLogItem("other", children=(child, ))

		self.assertEqual("AlertLog item 'item1' is a child of 'root' already.", str(context.exception))
		self.assertIs(child, context.exception.Item)
		self.assertIs(root, child.Parent)

	def test_BottomUp_Types(self) -> None:
		with self.assertRaises(TypeError) as context:
			_ = AlertLogItem("root", children=1)

		self.assertEqual("Parameter 'children' is not iterable.", str(context.exception))

		with self.assertRaises(TypeError) as context:
			_ = AlertLogItem("root", children=("item1", ))

		self.assertEqual("Parameter 'children' contains an element not of type 'AlertLogItem'.", str(context.exception))

	def test_Parent(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1")
		item.Parent = root

		self.assertIsNone(root.Parent)
		self.assertIs(item.Parent, root)
		self.assertEqual(1, root.ChildCount)
		self.assertEqual(0, item.ChildCount)

	def test_Parent_Move(self) -> None:
		root1 = AlertLogItem("root1")
		root2 = AlertLogItem("root2")
		item = AlertLogItem("item1", parent=root1)
		item.Parent = root2

		self.assertIs(item.Parent, root2)
		self.assertEqual(0, root1.ChildCount)
		self.assertIs(item, root2.Children["item1"])

	def test_Parent_None(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1", parent=root)
		item.Parent = None

		self.assertIsNone(item.Parent)
		self.assertEqual(0, root.ChildCount)

	def test_Parent_Duplicate(self) -> None:
		root = AlertLogItem("root")
		item1 = AlertLogItem("item1", parent=root)
		item2 = AlertLogItem("item1")

		with self.assertRaises(DuplicateAlertLogItemError) as context:
			item2.Parent = root

		self.assertIs(item1, context.exception.Item)
		self.assertIsNone(item2.Parent)

	def test_Parent_Cycle(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1", parent=root)

		with self.assertRaises(AlertLogError) as context:
			root.Parent = item

		self.assertEqual("AlertLog item 'root' can't be a child of itself or of its descendants.", str(context.exception))
		self.assertIsNone(root.Parent)

	def test_Parent_Type(self) -> None:
		item = AlertLogItem("item1")

		with self.assertRaises(TypeError) as context:
			item.Parent = "root"

		self.assertEqual("Parameter 'value' is not of type 'AlertLogItem'.", str(context.exception))


class Iterate(Testcase):
	def test_Iterate(self) -> None:
		child1 = AlertLogItem("item1")
		child2 = AlertLogItem("item2")
		children = child1, child2
		root = AlertLogItem("root", children=children)

		self.assertTupleEqual(children, tuple(root.Children.values()))
		self.assertDictEqual({c.Name: c for c in children}, root.Children)

	def test_IterateItems(self) -> None:
		root = AlertLogItem("root")
		item1 = AlertLogItem("item1", parent=root)
		item11 = AlertLogItem("item11", AlertLogStatus.Failed, parent=item1)
		item2 = AlertLogItem("item2", AlertLogStatus.Failed, parent=root)

		self.assertListEqual([item1, item11, item2], list(root.IterateItems()))
		self.assertListEqual([item11], list(item1.IterateItems()))

	def test_IterateItems_Predicate(self) -> None:
		root = AlertLogItem("root")
		item1 = AlertLogItem("item1", parent=root)
		item11 = AlertLogItem("item11", AlertLogStatus.Failed, parent=item1)
		item2 = AlertLogItem("item2", AlertLogStatus.Failed, parent=root)

		self.assertListEqual([item11, item2], list(root.IterateItems(lambda item: item.Status is AlertLogStatus.Failed)))


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
		self.assertEqual(5, document.ChildCount)
		self.assertEqual(40, document.Children["Default"].PassedCount)
		self.assertGreater(document.AnalysisDuration, timedelta())
		self.assertGreater(document.ModelConversionDuration, timedelta())
