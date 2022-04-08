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


# pth_raster = r"C:\Dev\OpenSafe-Mobility\Model\Model_02_Aug_2021\OpenSafe\WSE (26SEP2020 08 00 00).Terrain_10ft.Resampled_Projected.tif"
# pth_shapefile_points = r"C:\Dev\OpenSafe-Mobility\inputs\USGS_Gage_Location_in_WGS1984\USGS_Gage_Location_in_WGS1984.shp"

#%%
# df = extract_raster_value_with_buffer(pth_raster=pth_raster, pth_shapefile_points=pth_shapefile_points)
# # Read the point shapefile
# sjer_plots_points = gpd.read_file(shp_filename)
# # Create a buffered polygon layer from your plot location points
# sjer_plots_poly = sjer_plots_points.copy()
# # Buffer each point using a 20 meter circle radius and replace the point geometry with the new buffered geometry
# sjer_plots_poly["geometry"] = sjer_plots_points.geometry.buffer(.0001)
# # If the dir does not exist, create it
# output_path = os.path.join(r"C:\Dev\OpenSafe-Mobility\Results", "outputs")
# if not os.path.isdir(output_path):
#     os.mkdir(output_path)
# # Export the buffered point layer as a shapefile to use in zonal stats
# plot_buffer_path = os.path.join(output_path,
#                                 "plot_buffer.shp")
#
# sjer_plots_poly.to_file(plot_buffer_path)
# #
# sjer_chm_data = rxr.open_rasterio(src_filename, masked=True).squeeze()
# # Extract zonal stats
# sjer_tree_heights = rs.zonal_stats(plot_buffer_path,
#                                    sjer_chm_data.values,
#                                    nodata=-999,
#                                    affine=sjer_chm_data.rio.transform(),
#                                    geojson_out=True,
#                                    copy_properties=True,
#                                    stats="count min mean max median")
#
# # %%
# columns = ['STAID', 'STANAME', 'max']
# # %%
# # Turn extracted data into a pandas geodataframe
# sjer_lidar_height_df = gpd.GeoDataFrame.from_features(sjer_tree_heights)
# sjer_lidar_height_df.to_csv(r"C:\Dev\OpenSafe-Mobility\Results\Result.csv")
# print(sjer_lidar_height_df)
# print("Test")
