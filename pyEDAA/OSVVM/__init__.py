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
# Copyright 2025-2026 Patrick Lehmann - Boetzingen, Germany                                                            #
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
Parser and converters for OSVVM-specific data models and report formats.

OSVVM's YAML files are read by documents derived from :class:`YAMLDocumentMixin`: it reads a file, parses the format
version the file states, and validates the file against the version's JSON Schema from :mod:`pyEDAA.OSVVM.Resources`.
"""
from __future__            import annotations

__author__ =            "Patrick Lehmann"
__email__ =             "Paebbels@gmail.com"
__copyright__ =         "2025-2026, Patrick Lehmann"
__license__ =           "Apache License, Version 2.0"
__version__ =           "0.9.0rc1"
__keywords__ =          ["eda project", "model", "abstract", "osvvm", "reports", "data format", "unit test", "test suite", "test bench", "test harness"]
__project_url__ =       "https://github.com/edaa-org/pyEDAA.OSVVM"
__documentation_url__ = "https://edaa-org.github.io/pyEDAA.OSVVM"
__issue_tracker_url__ = "https://GitHub.com/edaa-org/pyEDAA.OSVVM/issues"

from datetime              import datetime
from json                  import JSONDecodeError, loads
from typing                import TYPE_CHECKING, Any, ClassVar, Mapping, Optional as Nullable

from pyTooling.Common      import getFullyQualifiedName, readResourceFile, StringEnum
from pyTooling.Decorators  import export, readonly
from pyTooling.Exceptions  import ExceptionBase, ToolingException
from pyTooling.MetaClasses import ExtendedType
from pyTooling.Warning     import CriticalWarning

if TYPE_CHECKING:
	from ruamel.yaml         import CommentedMap


@export
class OSVVMException(ExceptionBase):
	"""Base-class for all pyEDAA.OSVVM specific exceptions."""


@export
class UnknownKeyWarning(CriticalWarning):
	"""
	A YAML mapping of an OSVVM report file has a key the file format doesn't define.

	The parser skips the key and its value, and continues. A newer OSVVM version may have added the key.

	.. important::

	   This warning is critical: it must be collected by a :class:`~pyTooling.Warning.WarningCollector` up the
	   call-hierarchy, otherwise :meth:`~pyTooling.Warning.WarningCollector.Raise` raises an
	   :exc:`~pyTooling.Warning.UnhandledCriticalWarningError`.
	"""

	_key:  str  #: The unknown key.
	_line: int  #: The line of the key in the YAML file, 1-based.

	def __init__(self, message: str, /, *, key: str, line: int) -> None:
		"""
		Initializes the warning with the unknown key and its line.

		:param message: The warning's message.
		:param key:     The unknown key.
		:param line:    The line of the key in the YAML file, 1-based.
		"""
		super().__init__(message)
		self._key =  key
		self._line = line

	@readonly
	def Key(self) -> str:
		"""
		Read-only property to access the unknown key (:attr:`_key`).

		:returns: The key.
		"""
		return self._key

	@readonly
	def Line(self) -> int:
		"""
		Read-only property to access the line of the key in the YAML file (:attr:`_line`).

		:returns: The line, 1-based.
		"""
		return self._line


@export
class YAMLDocumentMixin(metaclass=ExtendedType, mixin=True, expects=("_path", )):
	"""
	A mixin-class for a document of an OSVVM YAML file: reads the file and validates it against its JSON Schema.

	The host class names its file format (:attr:`_DESCRIPTION`), the exception to raise (:attr:`_ERROR`), the format's
	version enumeration (:attr:`_FORMAT_VERSION`) and the schema file per format version (:attr:`_SCHEMAS`), a file of
	the resource package :mod:`pyEDAA.OSVVM.Resources` named :file:`OSVVM-<Format>-<FormatVersion>.schema.json`. It
	provides the file's path as field ``_path`` and calls :meth:`_AnalyzeYAML` from its ``Analyze`` method.

	The schemas are strict: a key a schema doesn't define is an error. A key OSVVM added within a format version is an
	optional property of the version's schema.

	OSVVM restarted the format versions of its YAML files at ``0.1`` with OSVVM 2026.01. Files of older OSVVM releases
	state other versions (``1.0``, ``1.1`` or a date) or none, and aren't supported.

	An empty file - no bytes, or no YAML node - is checked before the format version: a format, whose writer creates an
	empty file for a valid case, sets :attr:`_ALLOW_EMPTY`; the document is then empty (:attr:`_yamlDocument` is an empty
	mapping, :attr:`Version` is ``None``). Otherwise, an empty file is an error.
	"""

	_DESCRIPTION:    ClassVar[str]                        #: Name of the file format in messages.
	_ERROR:          ClassVar[type[OSVVMException]]       #: Exception raised, if the file can't be analyzed.
	_FORMAT_VERSION: ClassVar[type[StringEnum]]           #: Enumeration of the format's versions.
	_SCHEMAS:        ClassVar[Mapping[StringEnum, str]]   #: Schema file per format version.
	_ALLOW_EMPTY:    ClassVar[bool] = False               #: An empty file is a valid, empty document.
	_OLD_VERSIONS:   ClassVar[str] = (
		"OSVVM restarted its YAML format versions at 0.1 with OSVVM 2026.01; files of older releases aren't supported."
	)                                                     #: Note explaining an unsupported or missing format version.

	_yamlDocument:   Nullable[CommentedMap]               #: The parsed and validated YAML document.
	_version:        Nullable[StringEnum]                 #: Format version the file states.

	def __init__(self) -> None:
		"""
		Initializes the mixin-class: the file wasn't analyzed yet.
		"""
		self._yamlDocument = None
		self._version =      None

	@readonly
	def Version(self) -> Nullable[StringEnum]:
		"""
		Read-only property to access the format version the file states (:attr:`_version`).

		:returns: The format version, or ``None`` if the file wasn't analyzed yet or is empty.
		"""
		return self._version

	def _AnalyzeYAML(self) -> None:
		"""
		Read the YAML file, read the format version it states and validate it against the version's JSON Schema.

		YAML timestamps, which ruamel.yaml reads as :class:`~datetime.datetime`, are validated as ISO 8601 strings. A
		violation of an alternative (``oneOf``, ``anyOf``) is reported by its most relevant cause.

		:raises OSVVMException: If the file doesn't exist. The exception is of type :attr:`_ERROR`, as all below.
		:raises OSVVMException: If the file can't be read.
		:raises OSVVMException: If the file isn't UTF-8 encoded.
		:raises OSVVMException: If the file isn't valid YAML.
		:raises OSVVMException: If the file is empty and the format doesn't allow it (:attr:`_ALLOW_EMPTY`).
		:raises OSVVMException: If the file's content isn't a YAML mapping.
		:raises OSVVMException: If the file states no format version. |br|
		                        The notes list the supported format versions and name the OSVVM release, which
		                        restarted the format versions at ``0.1``.
		:raises OSVVMException: If the file states an unsupported format version. |br|
		                        The notes list the supported format versions and name the OSVVM release, which
		                        restarted the format versions at ``0.1``.
		:raises OSVVMException: If the JSON Schema can't be read.
		:raises OSVVMException: If the file isn't valid according to the JSON Schema. |br|
		                        A note per violation names its path and line.
		"""
		from jsonschema            import Draft202012Validator
		from jsonschema.exceptions import best_match
		from ruamel.yaml           import YAML, CommentedMap, CommentedSeq, YAMLError

		from pyEDAA.OSVVM          import Resources

		def toJSON(node: Any) -> Any:
			"""
			Nested function for recursion, copying YAML data to JSON data: timestamps become ISO 8601 strings.

			:param node: The YAML data.
			:returns:    The JSON data.
			"""
			if isinstance(node, dict):
				return {key: toJSON(value) for key, value in node.items()}
			elif isinstance(node, list):
				return [toJSON(value) for value in node]
			elif isinstance(node, datetime):
				return node.isoformat()

			return node

		def lineOf(path: Any) -> int:
			"""
			Nested function finding the line of a value in the YAML file.

			:param path: The path of the value, as a sequence of keys and indices.
			:returns:    The line of the value, or of the innermost mapping or sequence of its path, 1-based.
			"""
			node = yamlDocument
			line = 1
			for part in path:
				if isinstance(node, CommentedMap) and part in node:
					line = node.lc.key(part)[0] + 1
				elif isinstance(node, CommentedSeq) and isinstance(part, int) and part < len(node):
					line = node.lc.item(part)[0] + 1
				else:
					break

				node = node[part]

			return line

		if not self._path.exists():
			raise self._ERROR(f"{self._DESCRIPTION} '{self._path}' does not exist.") \
				from FileNotFoundError(f"File '{self._path}' not found.")

		try:
			content = self._path.read_text(encoding="utf-8")
		except OSError as ex:
			raise self._ERROR(f"Couldn't read {self._DESCRIPTION} '{self._path}'.") from ex
		except UnicodeDecodeError as ex:
			raise self._ERROR(f"{self._DESCRIPTION} '{self._path}' is not UTF-8 encoded.") from ex

		try:
			yamlDocument = YAML().load(content)
		except YAMLError as ex:
			raise self._ERROR(f"YAML syntax error in {self._DESCRIPTION} '{self._path}'.") from ex

		if yamlDocument is None:
			if not self._ALLOW_EMPTY:
				raise self._ERROR(f"{self._DESCRIPTION} '{self._path}' is empty.")

			self._yamlDocument = CommentedMap()
			self._version =      None
			return

		if not isinstance(yamlDocument, CommentedMap):
			ex = self._ERROR(f"{self._DESCRIPTION} '{self._path}' is not a YAML mapping.")
			ex.add_note(f"Got type '{getFullyQualifiedName(yamlDocument)}'.")
			raise ex

		version = yamlDocument.get("Version", None)
		try:
			formatVersion = self._FORMAT_VERSION.Parse(version)
		except (TypeError, ValueError) as cause:
			ex = self._ERROR(f"{self._DESCRIPTION} '{self._path}' states unsupported format version '{version}'.")
			ex.add_note(f"Supported format versions: {', '.join(self._FORMAT_VERSION)}.")
			ex.add_note(self._OLD_VERSIONS)
			raise ex from cause

		if formatVersion is None:
			ex = self._ERROR(f"{self._DESCRIPTION} '{self._path}' states no format version.")
			ex.add_note(f"Supported format versions: {', '.join(self._FORMAT_VERSION)}.")
			ex.add_note(self._OLD_VERSIONS)
			raise ex

		schemaFile = self._SCHEMAS[formatVersion]
		try:
			schema = loads(readResourceFile(Resources, schemaFile))
		except (ToolingException, JSONDecodeError) as ex:
			raise self._ERROR(f"Couldn't read JSON Schema '{schemaFile}' from package resources.") from ex

		validator = Draft202012Validator(schema)
		errors =    sorted(validator.iter_errors(toJSON(yamlDocument)), key=lambda error: list(error.absolute_path))
		if len(errors) > 0:
			ex = self._ERROR(f"Validation error for {self._DESCRIPTION} '{self._path}' using JSON Schema '{schemaFile}'.")
			for error in errors:
				error = best_match((error, ))
				path = error.absolute_path
				ex.add_note(f"/{'/'.join(str(part) for part in path)} (line {lineOf(path)}): {error.message}")
			raise ex

		self._yamlDocument = yamlDocument
		self._version =      formatVersion
