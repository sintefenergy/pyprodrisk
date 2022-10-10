# pyprodrisk
Status:

[![CI](https://github.com/sintef-energy/pyprodrisk/actions/workflows/pytest.yml/badge.svg)](https://github.com/sintef-energy/pyprodrisk/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/sintef-energy/pyprodrisk/branch/main/graph/badge.svg?token=FYASF5O90D)](https://codecov.io/gh/sintef-energy/pyprodrisk/branch/main/)

The nicest python interface to ProdRisk!

ProdRisk is a modeling tool for medium-term hydro operation planning developed by SINTEF Energy Research in Trondheim, Norway. ProdRisk is used for both scientific and commerical purposes, please visit the [ProdRisk home page](https://www.sintef.no/en/software/prodrisk/) for further information and inquiries regarding access and use.

The pyprodrisk package is an open source python wrapper for ProdRisk, and requires the proper ProdRisk binaries to function (see step 2).

## 1 Installing pyprodrisk
The pyprodrisk package can be installed using pip, the package installer for python. Please visit the [pip home page](https://pip.pypa.io/en/stable/) for installation and any pip related issues. You can install the official pyprodrisk release through the terminal command:

`pip install pyprodrisk`

You can also clone this repository and install the latest development version. To do this, open a terminal in the cloned pyProdRisk directory and give the command:

`pip install .`

You should now see pyprodrisk appear in the list of installed python modules when typing:

`pip list`

## 2 Download the desired ProdRisk binaries for your system 

> NOTE: You may not distribute the cplex library as it requires end user license

The ProdRisk core and API are separate from the pyprodrisk package, and must be downloaded separately. The latest ProdRisk binaries are found on the [ProdRisk Portal](https://prodrisk.sintef.energy/files/). Access to the portal must be granted by SINTEF Energy Research.

The following binaries are required for pyprodrisk to run:

Windows:
- A ltm_core_bin folder containing the prodrisk and genpris binaries, and cplex2010.dll (only needed if you have a HPO license).
- The ProdRisk API binary prodrisk_pybind.pyd

Linux:
- A ltm_core_bin folder containing the prodrisk- and genpris binaries, and cplex2010.dll (only needed if you have a HPO license).
- The ProdRisk API binary prodrisk_pybind.so

The solver specific binary is listed as cplex2010 here, but will change as new CPLEX versions become available.

It is also possible to use the OSI coin solver with ProdRisk, by setting the attribute use_coin_osi=True on a ProdRisk session object. 

## 3 Environment and license file

To use a license file to access your ProdRisk license, the environment variable `LTM_LICENSE_CONTROL_SYSTEM` should be set to TRUE (note: all capical letters!).

The ProdRisk license file, `LTM_License.dat`, must always be located in the directory specified by the environment variable `LTM_LICENSE_PATH`. 
The `LTM_LICENSE_PATH` can be added as a persistent environment variable in the regular ways, or it can be set by pyprodrisk on a session basis. 
If the keyword argument `license_path` is specified when creating an instance of the ProdriskSession class (see step 4), the environment variables 
`LTM_LICENSE_CONTROL_SYSTEM` is set to TRUE, and `LTM_LICENSE_PATH` and is overridden in the local environment of the executing process. 
If ProdRisk complains about not finding the license file, it is likely an issue with the LTM_LICENSE_PATH and/or LTM_LICENSE_CONTROL_SYSTEM are not being correctly specified.

The `LTM_LICENSE_PATH` is also the default place pyprodrisk will look for the ProdRisk API binary prodrisk_pybind mentioned in step 2. 
If the binaries are placed elsewhere, the keyword argument `solver_path` must be used when a ProdriskSession instance is created to ensure the correct binaries are loaded. 

The setting attribute prodrisk_path should be set on a ProdriskSession to the directory where the ltm_core_bin (prodrisk and genpris binaries) mentioned in step 2 is installed, e.g. prodrisk.prodrisk_path = "/path/to/ltm_core_bin/"

Note that libcplex2010.so also may be placed in the '/lib' directory when running pyprodrisk in a Linux environment.

## 4 Running ProdRisk

Now that pyprodrisk is installed, the ProdRisk binaries are downloaded, and the license file and binary paths are located, it is possible to run ProdRisk in python using pyProdRisk:

    import pyprodrisk as pys
    
    prodrisk = pys.ProdriskSession(license_path="C:/License/File/Path", solver_path="C:/ProdRisk/versions/10.3.0")
    prodrisk.prodrisk_path = "C:/ProdRisk/versions/10.3.0/ltm_core_bin/"
    
    #If you have a HPO license you may use the cplex solver:
    prodrisk.use_coin_osi = False
	
    #Set time resolution
    #Build topolgy
    #Add temporal input
    #Run model
    #Retreive results

Please visit the ProdRisk Portal for a detailed [tutorial](https://prodrisk.sintef.energy/documentation/tutorials/pyprodrisk/) and several [examples](https://prodrisk.sintef.energy/documentation/examples/) using pyprodrisk.
