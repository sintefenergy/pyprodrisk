import numpy as np
import pandas as pd

from ..helpers.time import get_api_datetime, get_api_timestring

def get_attribute_value(api, object_name, object_type, attribute_name, datatype, dataframe=True):
    value = None
    if datatype == 'int':
        value = api.GetIntValue(object_type, object_name, attribute_name)
        if value <= -2**15+1: # largest possible INT_MIN (init value in API core)
            value = None      # i.e. attribute has not been set
    elif datatype == 'int_array':
        value = list(api.GetIntArray(object_type, object_name, attribute_name))
        if len(value) == 0:
            value = None
    elif datatype == 'double':
        value = api.GetDoubleValue(object_type, object_name, attribute_name)
        if value <= -1e37: # largest possible -DBL_MAX (init value in API core)
            value = None
    elif datatype == 'double_array':
        value = list(api.GetDoubleArray(object_type, object_name, attribute_name))
        if len(value) == 0:
            value = None
    elif datatype == 'string':
        value = api.GetStringValue(object_type, object_name, attribute_name)
    elif datatype == 'xy':
        ref = api.GetXyCurveReference(object_type, object_name, attribute_name)
        x = np.fromiter(api.GetXyCurveX(object_type, object_name, attribute_name), float)
        y = np.fromiter(api.GetXyCurveY(object_type, object_name, attribute_name), float)
        if x.size == 0:
            value = None
        else:
            if dataframe:
                value = pd.Series(y, index=x, name=ref)
            else:
                xy = [[x, y] for x, y in zip(x, y)]
                value = dict(ref=ref, xy=xy)
    elif datatype == 'xy_array':
        refs = np.fromiter(api.GetXyCurveArrayReferences(object_type, object_name, attribute_name), float)
        n = np.fromiter(api.GetXyCurveArrayNPoints(object_type, object_name, attribute_name), int)
        x = np.fromiter(api.GetXyCurveArrayX(object_type, object_name, attribute_name), float)
        y = np.fromiter(api.GetXyCurveArrayY(object_type, object_name, attribute_name), float)
        value = []
        offset = 0
        if n.size == 0:
            value = None
        else:
            if dataframe:
                for n_items, ref in zip(n, refs):
                    df = pd.Series(y[offset:offset + n_items], index=x[offset:offset + n_items], name=ref)
                    value.append(df)
                    offset += n_items
            else:
                for n_items, ref in zip(n, refs):
                    xy = [[x[i], y[i]] for i in range(offset, offset + n_items)]
                    v = dict(ref=ref, xy=xy)
                    value.append(v)
                    offset += n_items
    elif datatype == 'xyt':
        start = get_api_datetime(api.GetStartTime())
        end = get_api_datetime(api.GetEndTime())
        value = get_xyt_attribute(api, object_name, object_type, attribute_name, start, end, dataframe)
    elif datatype == 'txy' or datatype == 'txy_stochastic':
        start_time = api.GetTxySeriesStartTime(object_type, object_name, attribute_name)
        if start_time:
            start_time = get_api_datetime(start_time)
            t = api.GetTxySeriesT(object_type, object_name, attribute_name)
            y = api.GetTxySeriesY(object_type, object_name, attribute_name)
            time_unit = api.GetTimeUnit()
            # value = get_timestamp_indexed_series(start_time, time_unit, t, y, column_name=attribute_name)
            # Placeholder code. PyProdRisk should probably return a timestamp indexed Txy like PyShop does
            if not isinstance(t, np.ndarray):
                t = np.fromiter(t, int)
            if not isinstance(y, np.ndarray):
                y = np.fromiter(y, float)
            assert time_unit == 'hour', 'unexpected time unit encountered'
            delta = pd.Timedelta(hours=1)
            t = start_time + t * delta
            if y.size > t.size:  # Stochastic
                value = pd.DataFrame(data=y, index=t)
            else:
                #value = pd.Series(data=y.flatten(), index=t, name=column_name)
                value = pd.Series(data=y.flatten(), index=t, name=attribute_name)

    else:
        value = None
    return value


def get_xyt_attribute(api, object_name, object_type, attribute_name, start, end, dataframe=True):
    # Get time delta from time unit
    unit = api.GetTimeUnit()
    delta = pd.Timedelta(minutes=1)
    resolution = api.GetTimeResolutionY()[0]
    if unit == 'hour':
        delta = pd.Timedelta(hours=1)
    elif unit == 'second':
        delta = pd.Timedelta(seconds=1)
        print('WARNING: Xyt series are not supported when the time unit is set to "second". '
              'This will likely not work as intended')

    # Identify the indices that should be extracted from the xyt series
    shop_start_time = get_api_datetime(api.GetStartTime())
    shop_end_time = get_api_datetime(api.GetEndTime())
    min_time_index = int((start - shop_start_time)/(resolution*delta))
    max_time_index = int((end - shop_start_time)/(resolution*delta))

    # Handle illegal bounds
    min_time_index = max(min_time_index, 0)

    # The time optimization is defined with an excluded end bound, while xyt retrieval operates with an included end
    # This means that the largest time index for xyt is that of the optimization end time - 1
    max_possible_index = int((shop_end_time - shop_start_time)/(resolution * delta)) - 1
    max_time_index = min(max_time_index, max_possible_index)

    # This is only needed if it is possible to have missing time steps in the XyT curve, otherwise it can be
    # replaced by a simple range
    xyt_time_indices = api.GetXyTCurveTimes(object_type, object_name, attribute_name)
    time_list = []
    for xyt_time_index in xyt_time_indices:
        if min_time_index <= xyt_time_index <= max_time_index:
            time_list.append(shop_start_time + xyt_time_index*delta*resolution)

    x = np.fromiter(api.GetXyTCurveX(object_type, object_name, attribute_name,
                                          get_api_timestring(start), get_api_timestring(end)), float)
    y = np.fromiter(api.GetXyTCurveY(object_type, object_name, attribute_name,
                                          get_api_timestring(start), get_api_timestring(end)), float)
    n = np.fromiter(api.GetXyTCurveN(object_type, object_name, attribute_name,
                                          get_api_timestring(start), get_api_timestring(end)), int)
    value = []
    offset = 0
    if n.size == 0:
        value = None
    else:
        if dataframe:
            for n_items, time in zip(n, time_list):
                df = pd.Series(y[offset:offset + n_items], index=x[offset:offset + n_items], name=time)
                value.append(df)
                offset += n_items
        else:
            for n_items, time in zip(n, time_list):
                xy = [[x[i], y[i]] for i in range(offset, offset + n_items)]
                v = dict(time=time, xy=xy)
                value.append(v)
                offset += n_items
    return value


def get_attribute_info(api, object_type, attribute_name, key=''):
    if key:
        return api.GetAttributeInfo(object_type, attribute_name, key)
    else:
        return {key: api.GetAttributeInfo(object_type, attribute_name, key) for key in api.GetValidAttributeInfoKeys()}


def get_object_info(api, object_type, key=''):
    if key:
        return api.GetObjectInfo(object_type, key)
    else:
        return {key: api.GetObjectInfo(object_type, key) for key in api.GetValidObjectInfoKeys()}


def set_attribute(api, object_name, object_type, attribute_name, datatype, value):
    ##Set a attribute in the SHOP core.
    #datatype = get_attribute_info(api, object_type, attribute_name, 'datatype')
    if datatype == 'int':
        api.SetIntValue(object_type, object_name, attribute_name, int(value))
    elif datatype == 'int_array':
        try:
            iter(value)
        except TypeError:
            value = np.array([value],dtype=int)
        api.SetIntArray(object_type, object_name, attribute_name, value)
    elif datatype == 'double':
        api.SetDoubleValue(object_type, object_name, attribute_name, value)
    elif datatype == 'double_array':
        try:
            iter(value)
        except TypeError:
            value = np.array([value],dtype=float)
        api.SetDoubleArray(object_type, object_name, attribute_name, value)
    elif datatype == 'string':
        api.SetStringValue(object_type, object_name, attribute_name, value)
    elif datatype == 'xy':
        if isinstance(value, pd.Series):
            api.SetXyCurve(object_type, object_name, attribute_name, value.name, value.index.values,
                                value.values)
        else:
            x = [x[0] for x in value['xy']]
            y = [x[1] for x in value['xy']]
            api.SetXyCurve(object_type, object_name, attribute_name, value['ref'], x, y)
    elif datatype == 'xy_array':
        if len(value) == 0:
            return
        ref = np.array([])
        x = np.array([])
        y = np.array([])
        n = np.array([])
        if isinstance(value[0], pd.DataFrame):
            for df in value:
                ref = np.append(ref, float(df.columns[0]))
                n = np.append(n, df.size)
                x = np.append(x, df.index.values)
                y = np.append(y, df.iloc[:,0].values)
        elif isinstance(value[0], pd.Series):
            for ser in value:
                ref = np.append(ref, float(ser.name))
                n = np.append(n, ser.size)
                x = np.append(x, ser.index.values)
                y = np.append(y, ser.values)
        else:
            for xy in value:
                ref = np.append(ref, xy['ref'])
                n = np.append(n, len(xy['xy']))
                x = np.append(x, [x[0] for x in xy['xy']])
                y = np.append(y, [x[1] for x in xy['xy']])
        api.SetXyCurveArray(object_type, object_name, attribute_name, ref, n, x, y)

    elif datatype == 'xyt':
        return

    elif datatype == 'txy' or datatype == 'txy_stochastic':
        
        assert type(value) == pd.DataFrame or type(value) == pd.Series, 'expected pandas.DataFrame or pandas.Series'

        value = pd.DataFrame(value)

        txy_start_time = api.GetStartTime()

        start_timestamp = get_api_datetime(txy_start_time)
        diff_time = value.index - start_timestamp
        int_hours = diff_time.seconds // 3600  # time differences < 1h are cut off!
        float_hours = diff_time.seconds / 3600.
        assert max(float_hours - int_hours) < 1./3600, 'all time intervals must be given in full hours'
        int_hours = int_hours + diff_time.days * 24
        if len(int_hours)>1:
            assert min(int_hours.to_numpy()[1:]-int_hours.to_numpy()[:len(int_hours)-1])>0, 'non-positive time interval in TXY series'

        api.SetTxySeries(
            object_type,
            object_name,
            attribute_name,
            txy_start_time,
            int_hours.to_numpy(), #value.index.astype(int),
            np.asfortranarray(value.values),
        )

