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
# Copyright 2025-2025 Patrick Lehmann - Boetzingen, Germany                                                            #
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
from argparse import Namespace
from pathlib  import Path
from sys      import stdin
from typing   import NoReturn

from pyTooling.Decorators                     import readonly
from pyTooling.MetaClasses                    import ExtendedType
from pyTooling.Common                         import count
from pyTooling.Attributes.ArgParse            import CommandHandler
from pyTooling.Attributes.ArgParse.Flag       import LongFlag
from pyTooling.Attributes.ArgParse.ValuedFlag import LongValuedFlag
from pyTooling.Stopwatch                      import Stopwatch

from pyEDAA.OSVVM.TCL import OsvvmProFileProcessor


class ProjectHandlers(metaclass=ExtendedType, mixin=True):
	@CommandHandler("project", help="Parse OSVVM project description.", description="Merge and/or transform unit testing results.")
	@LongFlag("--stdin", dest="stdin", help="OSVVM build file (PRO).")
	@LongValuedFlag("--regressionTCL", dest="regressionTCL", metaName='TCL file', optional=True, help="Regression file (TCL).")
	@LongValuedFlag("--buildPro", dest="buildPro", metaName='PRO file', optional=True, help="OSVVM build file (PRO).")
	@LongValuedFlag("--render", dest="render", metaName='format', optional=True, help="Render unit testing results to <format>.")
	def HandleUnittest(self, args: Namespace) -> None:
		"""Handle program calls with command ``unittest``."""
		self._PrintHeadline()

		returnCode = 0
		if (args.stdin is None and args.regressionTCL is None and args.buildPro is None):
			self.WriteError(f"Either option '--stdin' or '--regressionTCL=<TCL file>' or '--buildPro=<PRO file>' is missing.")
			returnCode = 3

		if returnCode != 0:
			self.Exit(returnCode)

		sw = Stopwatch(preferPause=True)
		processor = OsvvmProFileProcessor()

		if args.stdin is True:
			self.WriteNormal(f"Reading TCL code from STDIN ...")
			tclCode = stdin.read()

			with sw:
				processor.EvaluateTclCode(tclCode)

			project = processor.Context.ToProject("unnamed")

		elif args.regressionTCL is not None:
			self.WriteNormal(f"Reading regression TCL file ...")

			with sw:
				project = processor.LoadRegressionFile(Path(args.regressionTCL))

		elif args.buildPro is not None:
			for proFile in args.buildPro.split(":"):
				file = Path(proFile)
				self.WriteNormal(f"Reading OSVVM build file '{file}' ...")

				with sw:
					processor.LoadBuildFile(file)

			project = processor.Context.ToProject("unnamed")

		else:
			self.Exit(1)

		self.WriteNormal(f"  Parsing duration: {sw.Duration:.3f} s")
		self.WriteNormal(f"  Builds:           {len(project.Builds)}")
		self.WriteNormal(f"  Processed files:  {count(project.IncludedFiles)}")

		if args.render == "all":
			for build in project.Builds.values():
				print(f"Build: {build.Name}")
				for libraryName, lib in build.VHDLLibraries.items():
					print(f"  Library: {libraryName} ({len(lib.Files)})")
					for file in lib.Files:
						print(f"    {file}")

				print("-" * 60)
				for testsuiteName, ts in build.Testsuites.items():
					print(f"  Testsuite: {testsuiteName} ({len(ts.Testcases)})")
					for tc in ts.Testcases.values():
						print(f"    {tc.Name}")

				print("=" * 60)

		self.ExitOnPreviousErrors()
