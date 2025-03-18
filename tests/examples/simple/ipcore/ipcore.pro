set version [GetVHDLVersion]

SetVHDLVersion 2019

library ip
analyze ipcore.vhdl

SetVHDLVersion $version
