"""Code for generating result"""
from PIL import Image
import numpy as np
from geotiff import GeoTiff


def generate_png_file(path_to_tiff: str, color_map: dict, crs_code: int = 2278):
    # Read the geotiff file
    geo_tiff = GeoTiff(path_to_tiff, crs_code=crs_code)
    zarr_array = geo_tiff.read()
    _img = np.array(zarr_array)

    # Apply color map
    rgb_img = np.zeros((*_img.shape, 4), dtype=np.uint8)
    for key in color_map.keys():
        color_map[key] = [float(i) for i in color_map[key]]
        start, end, *_rgb = color_map[key]
        boolean_array = np.logical_and(_img > start, _img <= end)
        rgb_img[boolean_array] = _rgb

    # Convert array to image
    img = Image.fromarray(rgb_img, "RGBA")
    # Return image
    return img
