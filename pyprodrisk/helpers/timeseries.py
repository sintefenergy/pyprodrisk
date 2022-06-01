import pandas as pd
import numpy as np

def remove_consecutive_duplicates(df):
    """
    Compress timeseries by only keeping the first row of consecutive duplicates. This is done by comparing a copied
    DataFrame/Series that has been shifted by one, with the original, and only keeping the rows in which at least one
    one column value is different from the previous row. The first row will always be kept
    """
    if isinstance(df, pd.DataFrame):
        df = df.loc[(df.shift() != df).any(1)]
    else:
        df = df.loc[df.shift() != df]
    return df

