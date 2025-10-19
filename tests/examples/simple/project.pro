include ipcore

library lib1
analyze lib1_file1.vhdl [ConstraintFile lib1_file1.xdc [ScopeToCell foo/bar/spam/ham/egg]]
analyze lib1_file2.vhdl [ConstraintFile lib1_file2.xdc [ScopeToRef file2]]

library lib2
analyze lib2_file1.vhdl [ConstraintFile lib2_file1-1.xdc] [ConstraintFile lib2_file1-2.xdc]
