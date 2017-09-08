# allen2quicknii

Command line script for downloading series from the Allen data portal into QuickNII-compatible package.

This script has been tested with in-situ hybridization datasets and connectivity (block-face) datasets. It creates images and ancillary files (xml) compatible with QuickNII mouse. It only works with ABA template at 25 micrometers isotropic voxel.

## Dependencies
`requests` : part of (Ana)conda, or can be installed with `pip install requests`

## Usage
In conda

    python ants2quicknii.py <series identifier>
    python ants2quicknii.py --get-orig <series identifier>
    python ants2quicknii.py --target-dir /data/AMBA/datsets/ <series identifier>

In iPython

    run ants2quicknii.py <series identifier>
    run ants2quicknii.py --get-orig <series identifier>
    run ants2quicknii.py --target-dir /data/AMBA/datsets/ <series identifier>

## Arguments

`--get-orig` if added, the original size images are downloaded. This mights take a lot of time (~5 minutes per file)
                      "This might take a lot of time")

`--target-dir TARGET_DIR` the images and associated files are saved in TARGET_DIR folder

Note: full resolution images are provided in JPEG format, putting them into Navigator may involve additional hurdles.

## Details description
- creates a folder for the series
- indicates when encountering unknown reference space. AMBA is #9 (tested, working so far), and #10 may work too (not tested).
- creates a complete QuickNII series, with downscaled images and accompanying "<series identifier>.xml" file, using registration data from Allen portal
