from argparse import Namespace
from pathlib  import Path
from typing   import NoReturn

from pyTooling.Decorators                     import readonly
from pyTooling.MetaClasses                    import ExtendedType
from pyTooling.Attributes.ArgParse            import CommandHandler
from pyTooling.Attributes.ArgParse.ValuedFlag import LongValuedFlag
from pyTooling.Stopwatch                      import Stopwatch

from pyEDAA.OSVVM.TCL import OsvvmProFileProcessor


class ProjectHandlers(metaclass=ExtendedType, mixin=True):
	@CommandHandler("project", help="Parse OSVVM project description.", description="Merge and/or transform unit testing results.")
	@LongValuedFlag("--regressionTCL", dest="regressionTCL", metaName='TCL file', optional=True, help="Regression file (TCL).")
	@LongValuedFlag("--render", dest="render", metaName='format', optional=True, help="Render unit testing results to <format>.")
	def HandleUnittest(self, args: Namespace) -> None:
		"""Handle program calls with command ``unittest``."""
		self._PrintHeadline()

		returnCode = 0
		if (args.regressionTCL is None):
			self.WriteError(f"Either option '--regressionTCL=<TCL file>' is missing.")
			returnCode = 3

		if returnCode != 0:
			self.Exit(returnCode)

		processor = OsvvmProFileProcessor()

		if args.regressionTCL is not None:
			self.WriteNormal(f"Reading regression TCL file ...")

			with Stopwatch() as sw:
				project = processor.LoadRegressionFile(Path(args.regressionTCL))

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
