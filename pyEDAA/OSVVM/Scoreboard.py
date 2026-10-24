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
A data model for OSVVM's scoreboard YAML file format (:file:`<test>_sb_<name>.yml`).

At the end of a test, an instance of OSVVM's ``ScoreboardGenericPkg`` writes the statistics of its scoreboards by
``WriteScoreboardYaml``: per scoreboard (and FIFO), its name, the name of its AlertLog parent, and how many items were
pushed, checked, popped and dropped, how many checks failed and how many items are left. The OSVVM scripts move the
file to :file:`reports/<testsuite>/<test>_sb_<name>.yml` and read it to write the test's HTML report, which shows one
table per file.

A file is read in two steps, as in :mod:`pyEDAA.Reports`: :meth:`Document.Analyze` reads the YAML file and checks the
format version it states (:class:`FormatVersion`), :meth:`Document.Convert` converts the content to the model. Each
scoreboard is parsed by :meth:`Scoreboard.Parse`. A key the format doesn't define is reported as
:exc:`~pyEDAA.OSVVM.UnknownKeyWarning`, which must be collected by a :class:`~pyTooling.Warning.WarningCollector`.

.. rubric:: Example

.. code-block:: Python

   from pathlib import Path
   from pyTooling.Warning import WarningCollector
   from pyEDAA.OSVVM.Scoreboard import Document

   with WarningCollector() as warnings:
     document = Document(Path("TbAxi4_TimeOut_sb_slv.yml"), analyzeAndConvert=True)

   print(f"{document.TestcaseName} - {document.Name}: {document.ScoreboardCount} scoreboards")
   for scoreboard in document.IterateScoreboards(lambda scoreboard: scoreboard.ErrorCount > 0):
     print(f"  {scoreboard.AlertLogParentName}/{scoreboard.Name}: {scoreboard.ErrorCount} errors")
"""
from __future__            import annotations

from datetime              import timedelta
from pathlib               import Path
from typing                import Callable, Generator, Optional as Nullable, Self

from ruamel.yaml           import YAML, CommentedMap, CommentedSeq, YAMLError

from pyTooling.Common      import getFullyQualifiedName, StringEnum
from pyTooling.Decorators  import export, readonly
from pyTooling.MetaClasses import ExtendedType
from pyTooling.Stopwatch   import Stopwatch
from pyTooling.Warning     import WarningCollector

from pyEDAA.OSVVM          import OSVVMException, UnknownKeyWarning


@export
class ScoreboardError(OSVVMException):
	"""
	The exception is raised by the scoreboard data model.

	E.g., a scoreboard YAML file can't be read or converted.
	"""


@export
class FormatVersion(StringEnum):
	"""
	Version of OSVVM's scoreboard YAML format, as a file's ``Version`` states it.

	OSVVM writes ``SCOREBOARD_YAML_VERSION`` of ``OsvvmScriptSettingsPkg``, so far only ``0.1``.
	"""

	Version0_1 = "0.1"  #: Format version 0.1.


@export
class Scoreboard(metaclass=ExtendedType, slots=True):
	"""
	An entry of ``Scoreboards``: the statistics of one scoreboard (or FIFO) of a ``ScoreboardGenericPkg`` instance.

	A scoreboard is named by its AlertLog ID. The name isn't unique: two scoreboards of the same name may have different
	AlertLog parents, and even the same.
	"""

	_parent:             Nullable[Document]  #: The document the scoreboard belongs to.
	_name:               str                 #: Name of the scoreboard's AlertLog ID.
	_alertLogParentName: str                 #: Name of the AlertLog parent of the scoreboard's AlertLog ID.
	_itemCount:          int                 #: Number of items pushed.
	_errorCount:         int                 #: Number of failed checks.
	_checkedItemCount:   int                 #: Number of items checked.
	_poppedItemCount:    int                 #: Number of items popped.
	_droppedItemCount:   int                 #: Number of items dropped.
	_fifoCount:          int                 #: Number of items left in the scoreboard.

	def __init__(
		self,
		name:               str,
		alertLogParentName: str,
		itemCount:          int = 0,
		errorCount:         int = 0,
		checkedItemCount:   int = 0,
		poppedItemCount:    int = 0,
		droppedItemCount:   int = 0,
		fifoCount:          int = 0,
		*,
		parent:             Nullable[Document] = None
	) -> None:
		"""
		Initializes a scoreboard's statistics, and adds the scoreboard to its document.

		:param name:               Name of the scoreboard's AlertLog ID.
		:param alertLogParentName: Name of the AlertLog parent of the scoreboard's AlertLog ID.
		:param itemCount:          Optional, number of items pushed. Default: ``0``.
		:param errorCount:         Optional, number of failed checks. Default: ``0``.
		:param checkedItemCount:   Optional, number of items checked. Default: ``0``.
		:param poppedItemCount:    Optional, number of items popped. Default: ``0``.
		:param droppedItemCount:   Optional, number of items dropped. Default: ``0``.
		:param fifoCount:          Optional, number of items left in the scoreboard. Default: ``0``.
		:param parent:             Optional, the document the scoreboard belongs to; the scoreboard is appended to its
		                           scoreboards. Default: ``None``.
		:raises ValueError:        If parameter ``name`` or ``alertLogParentName`` is ``None``.
		:raises TypeError:         If parameter ``name`` or ``alertLogParentName`` isn't of type :class:`str`.
		:raises ValueError:        If parameter ``itemCount``, ``errorCount``, ``checkedItemCount``, ``poppedItemCount``,
		                           ``droppedItemCount`` or ``fifoCount`` is ``None``.
		:raises TypeError:         If parameter ``itemCount``, ``errorCount``, ``checkedItemCount``, ``poppedItemCount``,
		                           ``droppedItemCount`` or ``fifoCount`` isn't of type :class:`int`.
		:raises TypeError:         If parameter ``parent`` isn't of type :class:`Document`.
		"""
		for parameterName, text in (
			("name",               name),
			("alertLogParentName", alertLogParentName)
		):
			if text is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(text, str):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'str'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(text)}'.")
				raise ex

		for parameterName, count in (
			("itemCount",        itemCount),
			("errorCount",       errorCount),
			("checkedItemCount", checkedItemCount),
			("poppedItemCount",  poppedItemCount),
			("droppedItemCount", droppedItemCount),
			("fifoCount",        fifoCount)
		):
			if count is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(count, int):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'int'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(count)}'.")
				raise ex

		if parent is not None and not isinstance(parent, Document):
			ex = TypeError("Parameter 'parent' is not of type 'Document'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
			raise ex

		self._parent =             parent
		self._name =               name
		self._alertLogParentName = alertLogParentName
		self._itemCount =          itemCount
		self._errorCount =         errorCount
		self._checkedItemCount =   checkedItemCount
		self._poppedItemCount =    poppedItemCount
		self._droppedItemCount =   droppedItemCount
		self._fifoCount =          fifoCount

		if parent is not None:
			parent._scoreboards.append(self)

	@classmethod
	def Parse(cls, node: CommentedMap, *, parent: Nullable[Document] = None) -> Self:
		"""
		Parse an entry of ``Scoreboards``.

		A key the format doesn't define is reported as :exc:`~pyEDAA.OSVVM.UnknownKeyWarning`.

		:param node:                           The YAML mapping of the entry.
		:param parent:                         Optional, the document the scoreboard belongs to. Default: ``None``.
		:returns:                              The scoreboard.
		:raises ScoreboardError:               If the mapping lacks a key the format requires.
		:raises ScoreboardError:               If a value isn't of the type the format requires.
		:raises UnhandledCriticalWarningError: If the mapping has an unknown key, and no warning collector collects the
		                                       warning.
		"""
		line = node.lc.line + 1
		for key in node:
			if key not in (
				"Name", "ParentName", "ItemCount", "ErrorCount", "ItemsChecked", "ItemsPopped", "ItemsDropped", "FifoCount"
			):
				keyLine = node.lc.key(key)[0] + 1
				WarningCollector.Raise(
					UnknownKeyWarning(f"Unknown key '{key}' in scoreboard at line {keyLine}.", key=key, line=keyLine)
				)

		for key, keyType, typeName in (
			("Name",         str, "a string"),
			("ParentName",   str, "a string"),
			("ItemCount",    int, "an integer"),
			("ErrorCount",   int, "an integer"),
			("ItemsChecked", int, "an integer"),
			("ItemsPopped",  int, "an integer"),
			("ItemsDropped", int, "an integer"),
			("FifoCount",    int, "an integer")
		):
			if key not in node:
				raise ScoreboardError(f"Scoreboard at line {line} has no key '{key}'.")
			elif not isinstance(node[key], keyType):
				ex = ScoreboardError(f"Key '{key}' of scoreboard at line {line} is not {typeName}.")
				ex.add_note(f"Got type '{getFullyQualifiedName(node[key])}'.")
				raise ex

		return cls(
			node["Name"],
			node["ParentName"],
			node["ItemCount"],
			node["ErrorCount"],
			node["ItemsChecked"],
			node["ItemsPopped"],
			node["ItemsDropped"],
			node["FifoCount"],
			parent=parent
		)

	@readonly
	def Parent(self) -> Nullable[Document]:
		"""
		Read-only property to access the document the scoreboard belongs to (:attr:`_parent`).

		:returns: The document, or ``None`` if the scoreboard belongs to no document.
		"""
		return self._parent

	@readonly
	def Name(self) -> str:
		"""
		Read-only property to access the name of the scoreboard's AlertLog ID (:attr:`_name`).

		:returns: The scoreboard's name.
		"""
		return self._name

	@readonly
	def AlertLogParentName(self) -> str:
		"""
		Read-only property to access the name of the AlertLog parent of the scoreboard's AlertLog ID
		(:attr:`_alertLogParentName`).

		It's the name of the verification component or test the scoreboard belongs to. The YAML key is ``ParentName``.

		:returns: The name of the AlertLog parent.
		"""
		return self._alertLogParentName

	@readonly
	def ItemCount(self) -> int:
		"""
		Read-only property to access the number of items pushed (:attr:`_itemCount`).

		:returns: Number of items pushed.
		"""
		return self._itemCount

	@readonly
	def ErrorCount(self) -> int:
		"""
		Read-only property to access the number of failed checks (:attr:`_errorCount`).

		:returns: Number of failed checks.
		"""
		return self._errorCount

	@readonly
	def CheckedItemCount(self) -> int:
		"""
		Read-only property to access the number of items checked (:attr:`_checkedItemCount`).

		The YAML key is ``ItemsChecked``. A FIFO checks no items: its items are popped only.

		:returns: Number of items checked.
		"""
		return self._checkedItemCount

	@readonly
	def PoppedItemCount(self) -> int:
		"""
		Read-only property to access the number of items popped (:attr:`_poppedItemCount`).

		The YAML key is ``ItemsPopped``.

		:returns: Number of items popped.
		"""
		return self._poppedItemCount

	@readonly
	def DroppedItemCount(self) -> int:
		"""
		Read-only property to access the number of items dropped (:attr:`_droppedItemCount`).

		The YAML key is ``ItemsDropped``.

		:returns: Number of items dropped.
		"""
		return self._droppedItemCount

	@readonly
	def FifoCount(self) -> int:
		"""
		Read-only property to access the number of items left in the scoreboard at the end of the test (:attr:`_fifoCount`).

		:returns: Number of items left.
		"""
		return self._fifoCount


# A class with a property named like a class - ``Path`` - can't name that class in the annotation of a field: the class
# body's namespace, where annotations are evaluated, binds the name to the property.
_Path = Path


@export
class Document(metaclass=ExtendedType, slots=True):
	"""
	An OSVVM scoreboard YAML file: the statistics of the scoreboards of one ``ScoreboardGenericPkg`` instance in a test.

	When analyzing and converting the document, the YAML analysis duration as well as the model conversion duration gets
	captured.
	"""

	_path:                    _Path                    #: Path to the YAML file.
	_name:                    Nullable[str]            #: Name of the scoreboard package's instance, from the file name.
	_yamlDocument:            Nullable[CommentedMap]   #: The parsed YAML document, after :meth:`Analyze`.
	_version:                 Nullable[FormatVersion]  #: Version of the format.
	_testcaseName:            Nullable[str]            #: Name of the test.
	_scoreboards:             list[Scoreboard]         #: The scoreboards, in the order of the file.

	_analysisDuration:        Nullable[timedelta]      #: YAML file analysis duration.
	_modelConversionDuration: Nullable[timedelta]      #: Data structure conversion duration.

	def __init__(self, path: Path, analyzeAndConvert: bool = False) -> None:
		"""
		Initializes a scoreboard YAML document.

		:param path:              Path to the YAML file.
		:param analyzeAndConvert: Optional, if true, analyze the YAML document and convert the content to a scoreboard
		                          data model instance. Default: ``False``.
		:raises ValueError:       If parameter ``path`` is ``None``.
		:raises TypeError:        If parameter ``path`` isn't of type :class:`~pathlib.Path`.
		"""
		if path is None:
			raise ValueError("Parameter 'path' is None.")
		elif not isinstance(path, Path):
			ex = TypeError("Parameter 'path' is not of type 'Path'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(path)}'.")
			raise ex

		_, separator, name = path.stem.rpartition("_sb_")

		self._path =                    path
		self._name =                    name if separator != "" else None
		self._yamlDocument =            None
		self._version =                 None
		self._testcaseName =            None
		self._scoreboards =             []

		self._analysisDuration =        None
		self._modelConversionDuration = None

		if analyzeAndConvert:
			self.Analyze()
			self.Convert()

	@readonly
	def Path(self) -> Path:
		"""
		Read-only property to access the path to the YAML file of this document (:attr:`_path`).

		:returns: The document's path to the YAML file.
		"""
		return self._path

	@readonly
	def Name(self) -> Nullable[str]:
		"""
		Read-only property to access the name of the scoreboard package's instance (:attr:`_name`).

		It's the file name's part after the last ``_sb_``: ``WriteScoreboardYaml`` writes
		:file:`<test>_sb_<name>.yml`, and the OSVVM scripts name the scoreboard report after it.

		:returns: The name; ``None``, if the file name has no ``_sb_``.
		"""
		return self._name

	@readonly
	def Version(self) -> Nullable[FormatVersion]:
		"""
		Read-only property to access the version of the format (:attr:`_version`).

		:returns: The version; ``None`` before the document was converted.
		"""
		return self._version

	@readonly
	def TestcaseName(self) -> Nullable[str]:
		"""
		Read-only property to access the name of the test (:attr:`_testcaseName`).

		The YAML key is ``TestCase``. A test with generics states its name without their values, while the file name has
		them.

		:returns: The test's name; ``None`` before the document was converted.
		"""
		return self._testcaseName

	@readonly
	def Scoreboards(self) -> list[Scoreboard]:
		"""
		Read-only property to access the scoreboards (:attr:`_scoreboards`).

		:returns: The scoreboards, in the order of the file.
		"""
		return self._scoreboards

	@readonly
	def ScoreboardCount(self) -> int:
		"""
		Read-only property to return the number of scoreboards.

		:returns: Number of scoreboards.
		"""
		return len(self._scoreboards)

	def IterateScoreboards(
		self,
		predicate: Nullable[Callable[[Scoreboard], bool]] = None
	) -> Generator[Scoreboard, None, None]:
		"""
		Iterate the scoreboards, in the order of the file.

		:param predicate: Optional, a filter function; only scoreboards it returns ``True`` for are yielded. Default:
		                  ``None``, all scoreboards.
		:returns:         A generator of the scoreboards.
		"""
		if predicate is None:
			yield from self._scoreboards
		else:
			for scoreboard in self._scoreboards:
				if predicate(scoreboard):
					yield scoreboard

	@readonly
	def AnalysisDuration(self) -> timedelta:
		"""
		Read-only property to access the time spent for YAML file analysis (:attr:`_analysisDuration`).

		:returns:                The YAML file analysis duration.
		:raises ScoreboardError: If the document wasn't analyzed.
		"""
		if self._analysisDuration is None:
			raise ScoreboardError(f"Document '{self._path}' was not analyzed.")

		return self._analysisDuration

	@readonly
	def ModelConversionDuration(self) -> timedelta:
		"""
		Read-only property to access the time spent for data structure to scoreboard model conversion
		(:attr:`_modelConversionDuration`).

		:returns:                The data structure conversion duration.
		:raises ScoreboardError: If the document wasn't converted.
		"""
		if self._modelConversionDuration is None:
			raise ScoreboardError(f"Document '{self._path}' was not converted.")

		return self._modelConversionDuration

	def Analyze(self) -> None:
		"""
		Read the YAML file (specified by :attr:`_path`), check the format version it states, and store the YAML document in
		:attr:`_yamlDocument`.

		:raises ScoreboardError: If the YAML file doesn't exist.
		:raises ScoreboardError: If the YAML file can't be read.
		:raises ScoreboardError: If the YAML file isn't valid YAML.
		:raises ScoreboardError: If the YAML file's content isn't a mapping, e.g. an empty file. |br|
		                         OSVVM writes an empty file, if the package instance has no scoreboards.
		:raises ScoreboardError: If the YAML file states no format version. |br|
		                         The note lists the supported format versions.
		:raises ScoreboardError: If the YAML file states an unsupported format version. |br|
		                         The note lists the supported format versions.
		"""
		if not self._path.exists():
			raise ScoreboardError(f"OSVVM scoreboard YAML file '{self._path}' does not exist.") \
				from FileNotFoundError(f"File '{self._path}' not found.")

		with Stopwatch() as sw:
			try:
				yamlDocument = YAML().load(self._path)
			except OSError as ex:
				raise ScoreboardError(f"Couldn't read OSVVM scoreboard YAML file '{self._path}'.") from ex
			except YAMLError as ex:
				raise ScoreboardError(f"YAML syntax error in OSVVM scoreboard YAML file '{self._path}'.") from ex

			if not isinstance(yamlDocument, CommentedMap):
				ex = ScoreboardError(f"OSVVM scoreboard YAML file '{self._path}' is not a YAML mapping.")
				ex.add_note(f"Got type '{getFullyQualifiedName(yamlDocument)}'.")
				raise ex

			version = yamlDocument.get("Version", None)
			try:
				formatVersion = FormatVersion.Parse(version)
			except (TypeError, ValueError) as cause:
				ex = ScoreboardError(
					f"OSVVM scoreboard YAML file '{self._path}' states unsupported format version '{version}'."
				)
				ex.add_note(f"Supported format versions: {', '.join(FormatVersion)}.")
				raise ex from cause

			if formatVersion is None:
				ex = ScoreboardError(f"OSVVM scoreboard YAML file '{self._path}' states no format version.")
				ex.add_note(f"Supported format versions: {', '.join(FormatVersion)}.")
				raise ex

			self._yamlDocument = yamlDocument

		self._analysisDuration = sw.Duration

	def Convert(self) -> None:
		"""
		Convert the YAML document to the scoreboard model: the test's name and the scoreboards.

		A key the format doesn't define is reported as :exc:`~pyEDAA.OSVVM.UnknownKeyWarning`.

		:raises ScoreboardError:               If the YAML file was not analyzed before. |br|
		                                       Call 'Document.Analyze()' or create the document using
		                                       'Document(path, analyzeAndConvert=True)'.
		:raises ScoreboardError:               If a mapping lacks a key the format requires. |br|
		                                       The note names the YAML file.
		:raises ScoreboardError:               If a value isn't of the type the format requires. |br|
		                                       The note names the YAML file.
		:raises UnhandledCriticalWarningError: If a mapping has an unknown key, and no warning collector collects the
		                                       warning.
		"""
		if self._yamlDocument is None:
			ex = ScoreboardError(f"OSVVM scoreboard YAML file '{self._path}' needs to be read and analyzed by a YAML parser.")
			ex.add_note("Call 'Document.Analyze()' or create the document using 'Document(path, analyzeAndConvert=True)'.")
			raise ex

		root = self._yamlDocument
		with Stopwatch() as sw:
			try:
				for key in root:
					if key not in ("Version", "TestCase", "Scoreboards"):
						keyLine = root.lc.key(key)[0] + 1
						WarningCollector.Raise(
							UnknownKeyWarning(f"Unknown key '{key}' in scoreboard root at line {keyLine}.", key=key, line=keyLine)
						)

				if "TestCase" not in root:
					raise ScoreboardError("Scoreboard root has no key 'TestCase'.")
				elif not isinstance(root["TestCase"], str):
					ex = ScoreboardError("Key 'TestCase' of scoreboard root is not a string.")
					ex.add_note(f"Got type '{getFullyQualifiedName(root['TestCase'])}'.")
					raise ex

				if "Scoreboards" not in root:
					raise ScoreboardError("Scoreboard root has no key 'Scoreboards'.")
				elif root["Scoreboards"] is not None and not isinstance(root["Scoreboards"], CommentedSeq):
					ex = ScoreboardError("Key 'Scoreboards' of scoreboard root is not a sequence.")
					ex.add_note(f"Got type '{getFullyQualifiedName(root['Scoreboards'])}'.")
					raise ex

				self._version =      FormatVersion.Parse(root["Version"])
				self._testcaseName = root["TestCase"]

				for entry in () if root["Scoreboards"] is None else root["Scoreboards"]:
					if not isinstance(entry, CommentedMap):
						ex = ScoreboardError("Entry of 'Scoreboards' is not a mapping.")
						ex.add_note(f"Got type '{getFullyQualifiedName(entry)}'.")
						raise ex

					Scoreboard.Parse(entry, parent=self)
			except ScoreboardError as ex:
				ex.add_note(f"In OSVVM scoreboard YAML file '{self._path}'.")
				raise

		self._modelConversionDuration = sw.Duration
