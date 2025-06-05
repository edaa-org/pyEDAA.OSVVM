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
# Copyright 2021-2025 Electronic Design Automation Abstraction (EDA²)                                                  #
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
from datetime import timedelta
from pathlib import Path
from unittest     import TestCase

from pytest       import mark

from pyEDAA.OSVVM.AlertLog import AlertLogItem, Document as AlertLogDocument, AlertLogStatus, AlertLogException

if __name__ == "__main__": # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unitest <testcase module>'")
	exit(1)


class Instantiation(TestCase):
	def test_AlertLogStatus_dummy(self) -> None:
		with self.assertRaises(AlertLogException):
			_ = AlertLogStatus.Parse("dummy")

	@mark.xfail(reason="Bug in AlertLogStatus. Enum value is still an integer")
	def test_AlertLogStatus_passed(self) -> None:
		passed = AlertLogStatus.Parse("passed")

		self.assertIs(AlertLogStatus.Passed, passed)
		self.assertTrue(passed)

	@mark.xfail(reason="Bug in AlertLogStatus. Enum value is still an integer")
	def test_AlertLogStatus_failed(self) -> None:
		failed = AlertLogStatus.Parse("failed")

		self.assertIs(AlertLogStatus.Failed, failed)
		self.assertFalse(failed)

	def test_AlertLogItem(self) -> None:
		item = AlertLogItem("name")

		self.assertIsNone(item.Parent)
		self.assertEqual(AlertLogStatus.Unknown, item.Status)
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


class Hierarchy(TestCase):
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

	def test_Parent(self) -> None:
		root = AlertLogItem("root")
		item = AlertLogItem("item1")
		item.Parent = root

		self.assertIsNone(root.Parent)
		self.assertIs(item.Parent, root)
		self.assertEqual(1, len(root))
		self.assertEqual(0, len(item))


class Iterate(TestCase):
	def test_Iterate(self) -> None:
		child1 = AlertLogItem("item1")
		child2 = AlertLogItem("item2")
		children = child1, child2
		root = AlertLogItem("root", children=children)

		self.assertTupleEqual(tuple(root), children)
		self.assertDictEqual(root.Children, {c.Name: c for c in children})
