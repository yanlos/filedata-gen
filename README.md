# filedata-gen
generates file systems and databases

File system generator - creates a folder on your chosen workspace (directory) containing a certain amount of sub folders (folder_depth) with the following parameters:
# directory:        directory for folder to be created
# size:             format with number space and size (B is exact # of bytes). ex: 512 B, 1 KB, 22 MB, 42 GB, 1 TB
# number_files:     number of randomly sized files
# compression_rate: percent that is not random characters (is white space)
# type_data:        can generate OS random bytes or ASCII characters: "bytes" or "ascii"
# folder_depth:     layers of folders in the directory before getting to data files
