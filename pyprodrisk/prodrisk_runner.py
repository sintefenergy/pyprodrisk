import os
import sys
import pandas as pd
import numpy as np
import re

from .prodrisk_core.model_builder import ModelBuilderType
from .helpers.time import get_api_datetime, get_api_timestring

def _camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

# This check can be used to stops infinite recursion in some debuggers when stepping into __init__. Debuggers can call
# __dir__ before/during the initialization, and if any class attributes are referred to in both __dir__ and __getattr__
# the call to dir will invoke __getattr__, which in turn will call itself indefinitely
def is_private_attr(attr):
    return attr[0] == '_'


class ProdriskSession(object):

    # Class for handling a Prodrisk session through the python API.

    def __init__(self, license_path='', silent=True, log_file='', solver_path='', suppress_log=False, log_gets=True):

        self._n_scenarios = 1
        self._license_path = license_path
        self._silent_console = silent
        self._silent_log = suppress_log
        self._keep_working_directory = False

        if license_path:
            os.environ['LTM_LICENSE_CONTROL_SYSTEM'] = 'TRUE'
            os.environ['LTM_LICENSE_FILE'] = 'LTM_License.dat' #TODO: cleverly search for LTM_Lice*.dat 
            os.environ['LTM_LICENSE_PATH'] = license_path
            
        # Insert either the solver_path or the LTM_LICENSE_PATH to sys.path to find prodrisk_pybind.pyd
        
        if solver_path:
            solver_path = os.path.abspath(solver_path)
            sys.path.insert(1, solver_path)
        else:
            sys.path.insert(1, os.environ['LTM_LICENSE_PATH'])

        import prodrisk_pybind as pb

        self._session_id = "session_" + pd.Timestamp("now").strftime("%Y-%m-%d-%H-%M-%S")

        # ProdriskSess(<session_id>, <silentConsoleOutput>, <filePath>)
        self._pb_api = pb.ProdriskCore(self.session_id, self._silent_console)
        self._pb_api.KeepWorkingDirectory(self._keep_working_directory)  # The Prodrisk directory for the current session will be kept. The folder is found under prodrisk.prodrisk_path

        self.model = ModelBuilderType(self._pb_api, ignores=['setting'])
        self._model = ModelBuilderType(self._pb_api)
        self._setting = self._model.setting.add_object('setting')

        # default settings
        self._settings = {_camel_to_snake(atr): atr for atr in dir(self._setting) if atr[0] != '_'}

        self.prodrisk_path = "C:/PRODRISK/ltm_core_bin/"
        self.mpi_path = "C:/Program Files/Microsoft MPI/Bin"
        self.use_coin_osi = True

    def __dir__(self):
        return [atr for atr in super().__dir__() if atr[0] != '_'] + list(self._settings.keys())

    def __getattr__(self, atr_name):
        # Recursion guard
        if is_private_attr(atr_name):
            return
        if atr_name in self._settings.keys():
            return getattr(self._setting, self._settings[atr_name])
        raise AttributeError(f"{type(self)} has no attribute named '{atr_name}'")

    def __setattr__(self, atr_name, value):
        if self._settings and atr_name in self._settings.keys():
            getattr(self, atr_name).set(value)
            return
        super().__setattr__(atr_name, value)

    @property
    def session_id(self):
        return self._session_id

    @property
    def keep_working_directory(self):
        return self._keep_working_directory

    @keep_working_directory.setter
    def keep_working_directory(self, keep):
        self._pb_api.KeepWorkingDirectory(keep)
        self._keep_working_directory = keep

    @property
    def license_path(self):
        return self._license_path

    # n_scenarios --------

    @property
    def n_scenarios(self):
        return self._n_scenarios

    @n_scenarios.setter
    def n_scenarios(self, n: int):
        assert n > 0, "n_scenarios must be positive"
        self._n_scenarios = n

    # optimization period --------

    @property
    def start_time(self):
        return self._start_time
    
    @property
    def end_time(self):
        return self._end_time
    
    @property
    def n_weeks(self):
        return self._n_weeks

    def set_optimization_period(self, start_time: pd.Timestamp, n_weeks: int = 52):
        """
            Parameters
            ----------
            start_time: [pandas.Timestamp] start of optimization period
            n_weeks: [integer] number of weeks in optimization period
        """
        self._start_time = start_time
        self._n_weeks = n_weeks
        self._end_time = start_time + pd.Timedelta(f"{n_weeks}W")
        self._fmt_start_time = get_api_timestring(self._start_time)
        self._fmt_end_time = get_api_timestring(self._end_time)
        self._pb_api.SetOptimizationPeriod(
            self._fmt_start_time,
            self._fmt_end_time,
        )

    def run(self):

        # OPTIMIZE #
        # prodr.optimize()
        status = self._pb_api.GenerateProdriskFiles()
        if status is True:
            status = self._pb_api.RunProdrisk()
            if status is False:
                print("An error occured during the ProdRisk optimization/simulation. Please check the log for details.")
        else:
            print("An error occured, and the ProdRisk optimization/simulation was not run. Please check the log for details.")

        return status
