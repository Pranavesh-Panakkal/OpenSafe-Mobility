import datetime
import os
import pandas as pd
import numpy as np

import logging

logger = logging.getLogger(__name__)


def round_down_time_to_the_nearest_time_delta(
    dt=None, dateDelta=datetime.timedelta(minutes=5)
):
    """Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
            Stijn Nevens 2014 - Changed to use only datetime objects as variables
            https://stackoverflow.com/questions/3463930
    """
    round_to = dateDelta.total_seconds()

    if dt is None:
        dt = datetime.datetime.now()

    seconds = (dt - dt.min).seconds
    # // is a floor division, not a comment on following line:
    rounding = (seconds + round_to / 2) // round_to * round_to
    _dt = dt + datetime.timedelta(0, rounding - seconds, -dt.microsecond)
    _dt = _dt if _dt < dt else _dt - dateDelta
    return _dt


def format_time(current_time):
    return current_time.strftime("%Y%m%d%H%M%S")


def collcect_a_file(ssh_client, file_path, local_file_path):
    """Copy the file from remote server to the local server"""
    try:
        ftp_client = ssh_client.open_sftp()
        logger.info(f"collecting {file_path}")
        ftp_client.get(file_path, local_file_path)
        ftp_client.close()
    except IOError:
        logger.info("Failed to collect")
        return False

    return True


def append_last_time_step(label, _source_time_delta):
    # Get the time stamp from file name
    time = datetime.strptime(label[19:-4], "%Y%m%d%H%M%S")
    _new_time = time - _source_time_delta
    # Convert to file name
    _new_file = f"KHGX_LII_basin_UTC_{format_time(_new_time)}.csv"
    return _new_file


def sum_consecutive_rows(
    df: pd.DataFrame,
    number_of_columns_to_sum: int = 4,
    length_of_the_record_to_filter: int = 1,
) -> pd.DataFrame:
    """
    Generate rolling sum of pandas columns. Adds 'number_of_columns_to_sum' number of columns at a time to generate a
    new column. Raises an exception if the number of columns time the lenght of record is les than the number of record.
    In such cases, the analysis will stop
    :param df: The dataframe with rainfall records
    :type df: pd.DataFrame
    :param number_of_columns_to_sum: Number of columns to add together
    :type number_of_columns_to_sum: int
    :param length_of_the_record_to_filter: Length of record needed. The input record should have Len of record X number
    of columns. Else, the code will raise an error and stop working. Columns are added from the higher to lower index.
    :type length_of_the_record_to_filter: int
    :return: a pandas dataframe with columns added together
    :rtype: pd.DataFrame
    """
    # Ensuring that the number of records is greater than the length of record x columns to sum
    assert len(df.columns) >= number_of_columns_to_sum * length_of_the_record_to_filter
    # Drop all columns other than last length of record x columns to sum
    _df = df.drop(
        df.columns[
            0 : len(df.columns)
            - length_of_the_record_to_filter * number_of_columns_to_sum
        ],
        axis=1,
    ).copy()
    # Adding the columns together; this code will add 'number_of_columns_to_sum' together; a prefix is added at the end
    _df_scenarios = (
        _df.groupby(
            (np.arange(len(_df.columns)) // number_of_columns_to_sum) + 1, axis=1
        )
        .sum()
        .add_prefix("s")
    )
    # Return the new dataframe with added columns
    return _df_scenarios


def remove_empty_files(rootdir: str) -> None:
    """
    Get a list of empty files. This is required as sometimes the CSV files for DSS creation are empty.
    :param rootdir: location to check for empty files
    :type rootdir: str
    :return:
    :rtype:
    """
    # https: // stackoverflow.com / questions / 29451686 / how - to - remove - all - empty - files - within -
    # folder - and -its - sub - folders
    for root, dirs, files in os.walk(rootdir):
        for d in ["RECYCLER", "RECYCLED"]:
            if d in dirs:
                dirs.remove(d)

        for f in files:
            fullname = os.path.join(root, f)
            try:
                if os.path.getsize(fullname) == 0:
                    os.remove(fullname)
            except WindowsError:
                continue


def slice_list_and_provide_all_elements(
    list_to_filter: list, item_to_match, inclusive: bool = True
):
    """
    This code will find the last index of an item in the list and then get all element before that list
    :param list_to_filter:
    :type list_to_filter:
    :param item_to_match:
    :type item_to_match:
    :return:
    :rtype:
    """
    # Find all index of items matching the filter
    indexes = [
        index
        for index in range(len(list_to_filter))
        if list_to_filter[index] == item_to_match
    ]

    # if no match, return the list
    if len(indexes) < 1:
        return list_to_filter

    if inclusive:
        last_index = indexes[-1] + 1
    else:
        last_index = indexes[-1]

    return list_to_filter[:last_index]


def get_before_and_after_indexes_for_a_list_item(list_to_filter, item_to_match):
    list_ = []

    indexes = [
        index
        for index in range(len(list_to_filter))
        if list_to_filter[index] == item_to_match
    ]

    before_index = indexes[-1] - 1
    after_index = indexes[-1] + 1

    if before_index < 0:
        pass
    else:
        list_.append(list_to_filter[before_index])

    if after_index > len(list_to_filter) - 1:
        pass
    else:
        list_.append(list_to_filter[after_index])

    return list_
