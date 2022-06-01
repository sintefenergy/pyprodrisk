import pandas as pd
import numpy as np

from pyprodrisk.prodrisk_core.prodrisk_api import get_attribute_value, get_time_resolution, set_attribute


class ProdriskApiMock:
    mock_dict = {
        'GetIntValue': 11,
        'GetIntArray': [11, 22],
        'GetDoubleValue': 1.1,
        'GetDoubleArray': [1.1, 2.2],
        'GetStringValue': 'abc',
        'GetStringArray': ['abc', 'def'],
        'GetXyCurveX': [0, 1],
        'GetXyCurveY': [0.0, 1.1],
        'GetSyCurveS': ['s1', 's2'],
        'GetSyCurveY': [0.0, 1.1],
        'GetXyCurveReference': 0.0,
        'GetXyCurveArrayReferences': [0.0, 10.0],
        'GetXyCurveArrayNPoints': [2, 3],
        'GetXyCurveArrayX': [0, 1, 0, 1, 2],
        'GetXyCurveArrayY': [0.0, 1.1, 0.0, 1.1, 2.2],
        'GetTimeUnit': 'minute',
        'GetTxySeriesStartTime': '202201010000',
        'GetTxySeriesT': [0, 15, 30, 45, 60, 120],
        'GetTxySeriesY': [0.0, 1.1, 2.2, 3.3, 4.4, 5.5],
        'GetTimeZone': '',
        'GetStartTime': '202201010000',
        'GetEndTime': '202201010300',
        'GetTimeResolutionT': [0, 60],
        'GetTimeResolutionY': [15, 60]
    }

    def __getattr__(self, command: str):
        def dummy_func(*args):
            if command.startswith('Get'):
                return self.mock_dict[command]
            elif command.startswith('Set'):
                self.mock_dict[command] = args
        return dummy_func

    def __getitem__(self, command):
        return self.mock_dict[command]


class TestGetAttribute:
    prodrisk_api = ProdriskApiMock()

    def test_get_int(self):
        assert get_attribute_value(self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'int') == self.prodrisk_api['GetIntValue']

    def test_get_int_array(self):
        assert(
            get_attribute_value(
                self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'int_array'
            ) == self.prodrisk_api['GetIntArray']
        )

    def test_get_double(self):
        assert(
            get_attribute_value(
                self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'double'
            ) == self.prodrisk_api['GetDoubleValue']
        )

    def test_get_double_array(self):
        assert(
            get_attribute_value(
                self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'double_array'
            ) == self.prodrisk_api['GetDoubleArray']
        )

    def test_get_string(self):
        assert(
            get_attribute_value(
                self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'string'
            ) == self.prodrisk_api['GetStringValue']
        )

    def test_get_string_array(self):
        assert(
            get_attribute_value(
                self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'string_array'
            ) == self.prodrisk_api['GetStringArray']
        )

    def test_get_xy(self):
        value = get_attribute_value(self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'xy')
        assert (value.index == self.prodrisk_api['GetXyCurveX']).all()
        assert (value.values == self.prodrisk_api['GetXyCurveY']).all()
        assert value.name == self.prodrisk_api['GetXyCurveReference']

    def test_get_sy(self):
        value = get_attribute_value(self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'sy')
        assert (value.index == self.prodrisk_api['GetSyCurveS']).all()
        assert (value.values == self.prodrisk_api['GetSyCurveY']).all()

    def test_get_xy_array(self):
        value = get_attribute_value(self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'xy_array')
        for i, n in enumerate(self.prodrisk_api['GetXyCurveArrayNPoints']):
            n_sum = sum(self.prodrisk_api['GetXyCurveArrayNPoints'][0:i])
            assert (value[i].index == self.prodrisk_api['GetXyCurveArrayX'][n_sum:n_sum + n]).all()
            assert (value[i].values == self.prodrisk_api['GetXyCurveArrayY'][n_sum:n_sum + n]).all()
            assert value[i].name == self.prodrisk_api['GetXyCurveArrayReferences'][i]

    def test_get_txy(self):
        value = get_attribute_value(self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'txy')
        if self.prodrisk_api['GetTimeUnit'] == 'hour':
            starttime = pd.Timestamp(self.prodrisk_api['GetTxySeriesStartTime'])
            assert (value.index == [starttime + pd.Timedelta(hours=t) for t in self.prodrisk_api['GetTxySeriesT']]).all()
            assert (value.values == self.prodrisk_api['GetTxySeriesY']).all()


class TestSetAttribute:
    prodrisk_api = ProdriskApiMock()

    def test_set_xy(self):
        xy_val = pd.Series(
            self.prodrisk_api['GetXyCurveY'], index=self.prodrisk_api['GetXyCurveX'], name=self.prodrisk_api['GetXyCurveReference']
        )
        set_attribute(self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'xy', xy_val)
        res = self.prodrisk_api['SetXyCurve']
        assert res[3] == self.prodrisk_api['GetXyCurveReference']
        assert (res[4] == self.prodrisk_api['GetXyCurveX']).all()
        assert (res[5] == self.prodrisk_api['GetXyCurveY']).all()

    def test_set_sy(self):
        sy_val = pd.Series(
            self.prodrisk_api['GetSyCurveY'], index=self.prodrisk_api['GetSyCurveS']
        )
        set_attribute(self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'sy', sy_val)
        res = self.prodrisk_api['SetSyCurve']
        assert res[3] == self.prodrisk_api['GetSyCurveS']
        assert (res[4] == self.prodrisk_api['GetSyCurveY']).all()

    def test_set_xy_array(self):
        xy_array_val = []
        for i, n in enumerate(self.prodrisk_api['GetXyCurveArrayNPoints']):
            n_sum = sum(self.prodrisk_api['GetXyCurveArrayNPoints'][0:i])
            xy_array_val.append(
                pd.Series(
                    self.prodrisk_api['GetXyCurveArrayY'][n_sum:n_sum + n],
                    index=self.prodrisk_api['GetXyCurveArrayX'][n_sum:n_sum + n],
                    name=self.prodrisk_api['GetXyCurveArrayReferences'][i]
                )
            )
        set_attribute(self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'xy_array', xy_array_val)
        res = self.prodrisk_api['SetXyCurveArray']
        assert (res[3] == self.prodrisk_api['GetXyCurveArrayReferences']).all()
        assert (res[4] == self.prodrisk_api['GetXyCurveArrayNPoints']).all()
        assert (res[5] == self.prodrisk_api['GetXyCurveArrayX']).all()
        assert (res[6] == self.prodrisk_api['GetXyCurveArrayY']).all()

    def test_set_txy(self):
        starttime = pd.Timestamp(self.prodrisk_api['GetStartTime'])
        txy_val = pd.Series(
            self.prodrisk_api['GetTxySeriesY'],
            index=[starttime + pd.Timedelta(minutes=t) for t in self.prodrisk_api['GetTxySeriesT']]
        )
        set_attribute(self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'txy', txy_val)
        res = self.prodrisk_api['SetTxySeries']
        assert res[3].startswith(self.prodrisk_api['GetStartTime'])
        assert (res[4] == self.prodrisk_api['GetTxySeriesT']).all()
        assert (res[5] == self.prodrisk_api['GetTxySeriesY']).all()

    def test_set_constant_txy(self):
        set_attribute(self.prodrisk_api, 'obj_name', 'obj_type', 'attr_name', 'txy', 1.1)
        res = self.prodrisk_api['SetTxySeries']
        assert res[3].startswith(self.prodrisk_api['GetStartTime'])
        assert (res[4] == self.prodrisk_api['GetTxySeriesT']).all()
        assert (np.abs(res[5] - 1.1) < 1e-15).all()


class TestTime:
    prodrisk_api = ProdriskApiMock()

    def test_get_time_resolution(self):
        timeres = get_time_resolution(self.prodrisk_api)
        assert timeres['starttime'] == pd.Timestamp(self.prodrisk_api['GetStartTime'])
        assert timeres['endtime'] == pd.Timestamp(self.prodrisk_api['GetEndTime'])
        assert timeres['timeunit'] == self.prodrisk_api['GetTimeUnit']
