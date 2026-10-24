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

from ruamel.yaml           import YAML

from pyTooling.Warning     import UnhandledCriticalWarningError, WarningCollector
from pyTooling.Testing     import Testcase

from pyEDAA.OSVVM          import UnknownKeyWarning
from pyEDAA.OSVVM.AlertLog import AlertCount, AlertLogError, AlertLogItem, AlertLogStatus, AlreadyInAlertLogError, \
                                  Document, DuplicateAlertLogItemError, Settings

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


DATA = Path("tests/data/OSVVM/AlertLog")


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


class Count(Testcase):
	def test_Default(self) -> None:
		count = AlertCount()

		self.assertEqual(0, count.FailureCount)
		self.assertEqual(0, count.ErrorCount)
		self.assertEqual(0, count.WarningCount)

	def test_Values(self) -> None:
		count = AlertCount(1, 2, -3)

		self.assertEqual(1, count.FailureCount)
		self.assertEqual(2, count.ErrorCount)
		self.assertEqual(-3, count.WarningCount)
		self.assertEqual("AlertCount(failureCount=1, errorCount=2, warningCount=-3)", repr(count))

	def test_Equality(self) -> None:
		self.assertEqual(AlertCount(1, 2, 3), AlertCount(1, 2, 3))
		self.assertNotEqual(AlertCount(1, 2, 3), AlertCount(1, 2, 4))
		self.assertNotEqual(AlertCount(), 0)
		self.assertEqual(hash(AlertCount(1, 2, 3)), hash(AlertCount(1, 2, 3)))

	def test_None(self) -> None:
		with self.assertRaises(ValueError) as context:
			_ = AlertCount(errorCount=None)

		self.assertEqual("Parameter 'errorCount' is None.", str(context.exception))

	def test_Type(self) -> None:
		with self.assertRaises(TypeError) as context:
			_ = AlertCount(warningCount="1")

		self.assertEqual("Parameter 'warningCount' is not of type 'int'.", str(context.exception))

	def test_Parse(self) -> None:
		count = AlertCount.Parse(YAML().load("{Failure: 1, Error: 2, Warning: 3}"))

		self.assertEqual(AlertCount(1, 2, 3), count)

	def test_Parse_UnknownKey(self) -> None:
		with WarningCollector() as warnings:
			count = AlertCount.Parse(YAML().load("{Failure: 1, Error: 2, Warning: 3, Note: 4}"))

		self.assertEqual(AlertCount(1, 2, 3), count)
		self.assertEqual(1, len(warnings))
		self.assertIsInstance(warnings[0], UnknownKeyWarning)
		self.assertEqual("Note", warnings[0].Key)
		self.assertEqual(1, warnings[0].Line)

	def test_Parse_MissingKey(self) -> None:
		with self.assertRaises(AlertLogError) as context:
			_ = AlertCount.Parse(YAML().load("{Failure: 1, Warning: 3}"))

		self.assertEqual("Alert count at line 1 has no key 'Error'.", str(context.exception))

	def test_Parse_Type(self) -> None:
		with self.assertRaises(AlertLogError) as context:
			_ = AlertCount.Parse(YAML().load("{Failure: 1, Error: two, Warning: 3}"))

		self.assertEqual("Key 'Error' of alert count at line 1 is not an integer.", str(context.exception))




class Instantiation(Testcase):
	def test_AlertLogItem(self) -> None:
		item = AlertLogItem("name")

		self.assertIsNone(item.Parent)
		self.assertIs(AlertLogStatus.Unknown, item.Status)
		self.assertEqual("name", item.Name)
		self.assertEqual(0, len(item))
		self.assertEqual(0, len(item.Children))
		self.assertEqual(0, item.TotalErrorCount)
		self.assertEqual(AlertCount(), item.AlertCount)
		self.assertEqual(0, item.AffirmCount)
		self.assertEqual(0, item.PassedCount)
		self.assertEqual(0, item.RequirementsGoalCount)
		self.assertEqual(0, item.PassedRequirementsCount)
		self.assertEqual(AlertCount(), item.DisabledAlertCount)

	def test_AlertLogItem_Values(self) -> None:
		alertCount =         AlertCount(1, 2, 3)
		disabledAlertCount = AlertCount(4, 5, 6)
		item = AlertLogItem("name", AlertLogStatus.Failed, 6, alertCount, 7, 8, 9, 10, disabledAlertCount)

		self.assertIs(AlertLogStatus.Failed, item.Status)
		self.assertEqual(6, item.TotalErrorCount)
		self.assertIs(alertCount, item.AlertCount)
		self.assertEqual(7, item.PassedCount)
		self.assertEqual(8, item.AffirmCount)
		self.assertEqual(9, item.PassedRequirementsCount)
		self.assertEqual(10, item.RequirementsGoalCount)
		self.assertIs(disabledAlertCount, item.DisabledAlertCount)

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
			_ = AlertLogItem("name", alertCount=(0, 0, 0))

		self.assertEqual("Parameter 'alertCount' is not of type 'AlertCount'.", str(context.exception))

	def test_AlertLogItem_Parent(self) -> None:
		with self.assertRaises(TypeError) as context:
			_ = AlertLogItem("name", parent="root")

		self.assertEqual("Parameter 'parent' is not of type 'AlertLogItem'.", str(context.exception))

	def test_Settings(self) -> None:
		externalErrors = AlertCount(-1, 0, 0)
		settings = Settings(externalErrors, True, False, True)

		self.assertIsNone(settings.Parent)
		self.assertIs(externalErrors, settings.ExternalErrors)
		self.assertTrue(settings.FailOnDisabledErrors)
		self.assertFalse(settings.FailOnRequirementErrors)
		self.assertTrue(settings.FailOnWarning)

	def test_Settings_Flags(self) -> None:
		with self.assertRaises(ValueError) as context:
			_ = Settings(AlertCount(), True, None, True)

		self.assertEqual("Parameter 'failOnRequirementErrors' is None.", str(context.exception))

		with self.assertRaises(TypeError) as context:
			_ = Settings(AlertCount(), True, True, "true")

		self.assertEqual("Parameter 'failOnWarning' is not of type 'bool'.", str(context.exception))


class Hierarchy(Testcase):
	def test_TopDown(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1", parent=root)

		self.assertIsNone(root.Parent)
		self.assertIs(item.Parent, root)
		self.assertEqual(1, len(root))
		self.assertEqual(0, len(item))
		self.assertIs(item, root["item1"])

	def test_TopDown_Duplicate(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1", parent=root)

		with self.assertRaises(DuplicateAlertLogItemError) as context:
			_ = AlertLogItem("item1", parent=root)

		self.assertEqual("AlertLog item 'root' has a child 'item1' already.", str(context.exception))
		self.assertIs(item, context.exception.Item)
		self.assertIs(item, root["item1"])

	def test_BottomUp(self) -> None:
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
		self.assertEqual(1, len(root))
		self.assertEqual(0, len(item))

	def test_Parent_Move(self) -> None:
		root1 = AlertLogItem("root1")
		root2 = AlertLogItem("root2")
		item = AlertLogItem("item1", parent=root1)
		item.Parent = root2

		self.assertIs(item.Parent, root2)
		self.assertEqual(0, len(root1))
		self.assertIs(item, root2["item1"])

	def test_Parent_None(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1", parent=root)
		item.Parent = None

		self.assertIsNone(item.Parent)
		self.assertEqual(0, len(root))

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

	def test_Settings_Parent(self) -> None:
		document = Document(DATA / "TbModelParameters_alerts.yml")
		settings = Settings(AlertCount(), True, True, True, parent=document)

		self.assertIs(document, settings.Parent)
		self.assertIs(settings, document.Settings)

		with self.assertRaises(AlertLogError):
			_ = Settings(AlertCount(), True, True, True, parent=document)

		with self.assertRaises(TypeError):
			_ = Settings(AlertCount(), True, True, True, parent=AlertLogItem("root"))


class Iterate(Testcase):
	def test_Iterate(self) -> None:
		child1 = AlertLogItem("item1")
		child2 = AlertLogItem("item2")
		children = child1, child2
		root = AlertLogItem("root", children=children)

		self.assertTupleEqual(children, tuple(root))
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
		self.assertEqual(5, len(document))
		self.assertEqual(40, document["Default"].PassedCount)
		self.assertGreater(document.AnalysisDuration, timedelta())
		self.assertGreater(document.ModelConversionDuration, timedelta())

	def test_TimeOut(self) -> None:
		document = Document(DATA / "TbTimeOut_alerts.yml", analyzeAndConvert=True)

		self.assertIs(AlertLogStatus.TimeOut, document.Status)
		self.assertFalse(document.Settings.FailOnDisabledErrors)
		self.assertTrue(document.Settings.FailOnRequirementErrors)
		self.assertFalse(document.Settings.FailOnWarning)

		default = document["Default"]
		self.assertIs(AlertLogStatus.Failed, default.Status)
		self.assertEqual(3, default.TotalErrorCount)
		self.assertEqual(AlertCount(1, 1, 1), default.AlertCount)
		self.assertEqual(1, default.PassedRequirementsCount)
		self.assertEqual(2, default.RequirementsGoalCount)
		self.assertEqual(AlertCount(0, 2, 0), default.DisabledAlertCount)

	def test_ToTree_Format(self) -> None:
		document = Document(DATA / "TbModelParameters_alerts.yml", analyzeAndConvert=True)

		tree = document.ToTree(lambda node: node["Name"].upper())

		self.assertEqual("TBMODELPARAMETERS\n├─VHDL ASSERTS\n├─DEFAULT\n├─OSVVM\n└─TB\n", tree.Render())

	def test_UnknownKeys(self) -> None:
		with WarningCollector() as warnings:
			document = Document(DATA / "UnknownKeys_alerts.yml", analyzeAndConvert=True)

		self.assertEqual("TbUnknownKeys", document.Name)
		self.assertEqual(1, len(document))
		self.assertEqual(2, len(warnings))
		for warning in warnings:
			self.assertIsInstance(warning, UnknownKeyWarning)

		self.assertListEqual(
			[("FailOnVhdlAssertErrors", 5), ("ReportMode", 11)],
			[(warning.Key, warning.Line) for warning in warnings]
		)

	def test_UnknownKeys_NoCollector(self) -> None:
		with self.assertRaises(UnhandledCriticalWarningError) as context:
			_ = Document(DATA / "UnknownKeys_alerts.yml", analyzeAndConvert=True)

		self.assertIsInstance(context.exception.__cause__, UnknownKeyWarning)

	def test_MissingKey(self) -> None:
		with self.assertRaises(AlertLogError) as context:
			_ = Document(DATA / "MissingStatus_alerts.yml", analyzeAndConvert=True)

		self.assertEqual("AlertLog item at line 7 has no key 'Status'.", str(context.exception))
