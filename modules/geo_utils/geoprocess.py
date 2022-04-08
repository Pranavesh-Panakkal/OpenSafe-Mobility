from osgeo import gdal
import geopandas as gpd
import rasterstats as rs
import rioxarray as rxr
import os


def reproject_raster(
    source_file_location: str,
    destination_file_location: str,
    destination_crs: str = "EPSG:4326",
    source_crs: str = "EPSG:2278",
):
    input_raster = gdal.Open(source_file_location)
    warp = gdal.Warp(
        destination_file_location,
        input_raster,
        dstSRS=destination_crs,
        srcSRS=source_crs,
    )
    warp = None  # Closes the files


def extract_raster_value_with_buffer(
    pth_raster: str, pth_shapefile_points: str, buffer: float = 0.0001
):
    # Read the point shapefile
    points_ = gpd.read_file(pth_shapefile_points)
    # Create a buffered polygon
    buffered_points = points_.copy()
    buffered_points["geometry"] = points_.geometry.buffer(buffer)
    # Create a temp file
    output_path = os.getcwd() + "\\temp"
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    # Save the file
    pth_shapefile_buffered = os.path.join(output_path, "plot_buffer.shp")
    buffered_points.to_file(pth_shapefile_buffered)
    # Use rasterio to read the file
    raster_data = rxr.open_rasterio(pth_raster, masked=True).squeeze()
    # Extract raster stat data
    zonal_stat = rs.zonal_stats(
        pth_shapefile_buffered,
        raster_data.values,
        nodata=-999,
        affine=raster_data.rio.transform(),
        geojson_out=True,
        copy_properties=True,
        stats="min mean max",
    )
    #
    zonal_df = gpd.GeoDataFrame.from_features(zonal_stat)
    return zonal_df

