"""Handles DSS generation from pandas"""
import pandas as pd
import os
from pydsstools.core import TimeSeriesContainer
from pydsstools.heclib.dss import HecDss


def remove_file_if_existing(file_name: str) -> None:
    """
    Remove a file if it exists in the directory
    :param file_name: Name of the file. Full path should be provided
    :type file_name: str
    :return: None
    :rtype:
    """
    # Remove old file
    try:
        os.remove(file_name)
    except OSError:
        pass


def generate_dss_from_pandas(dataframe: pd.DataFrame, config: dict) -> None:
    """
    Generate and write a DSS time series file form pandas dataframe. Removes any existing dss files with the same
    name :param dataframe: Pandas dataframe with column labels as the 'path name' in DSS; Each column should ideally
    contain the time series related to that item. :type dataframe: pd.DataFrame :param config: The config dict used
    in this project :type config: dict :return: Saves the file to folder. :rtype:
    """
    # Reading config files
    # Name of the dss file
    name_dss_file = config.radar.dss_file.name_dss_file
    # Remove existing files
    remove_file_if_existing(name_dss_file)
    # Define start time of the series
    start_time = config.radar.dss_file.start_time
    # path_name_dss string
    query_string = config.radar.dss_file.path_name_dss
    # ID to replace in path_name string
    basin_id = config.radar.dss_file.ID_to_replace
    # Units
    units = config.radar.dss_file.units
    # Type of unit
    _type = config.radar.dss_file.type
    # Interval to use, this should be multiplied with the path_name time stamp
    interval = config.radar.dss_file.interval

    for basin in dataframe.columns:
        # Create a pathname for the string
        pathname = query_string.replace(basin_id, basin)
        # Initiate time series
        tsc = TimeSeriesContainer()
        # Set the pathname
        tsc.pathname = pathname
        # Set start time
        tsc.startDateTime = start_time
        # Set the number of values
        tsc.numberValues = len(dataframe[basin])
        # Set units
        tsc.units = units
        # set type
        tsc.type = _type
        # set interval
        tsc.interval = interval
        # get values
        tsc.values = list(dataframe[basin])
        # Open the dss file
        fid = HecDss.Open(name_dss_file)
        # Delete pathname; i.e., delete any existing items to overwrite it
        fid.deletePathname(tsc.pathname)
        # Write the values
        fid.put_ts(tsc)
        # Read the data to commit it
        fid.read_ts(pathname)
        # Close the connection
        fid.close()
