# Title     : Temp file for items related to raster processing
# Created by: Pranavesh Panakkal
# Created on: 8/22/2021
# Version   :
# Notes     :
""""""
import rioxarray as rxr


def subtract_two_raster(
    raster_to_subtract_from: str, subtracting_raster: str, file_path_to_save: str
) -> None:
    """
    Subtract two rasters
    :param raster_to_subtract_from: A of A-B raster operation
    :type raster_to_subtract_from: str
    :param subtracting_raster: B of A-B raster operation
    :type subtracting_raster: str
    :param file_path_to_save: Path to save the final raster
    :type file_path_to_save: str
    :return: None
    :rtype: None
    """
    _main_raster = rxr.open_rasterio(raster_to_subtract_from, masked=True).squeeze()
    _second_raster = rxr.open_rasterio(subtracting_raster, masked=True).squeeze()
    _difference = _main_raster - _second_raster
    _difference.rio.to_raster(file_path_to_save)
