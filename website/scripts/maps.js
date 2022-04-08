// MapBox token
mapboxgl.accessToken = 'pk.eyJ1IjoicHJhbmF2ZXNoIiwiYSI6ImNrcjc1Z2p0cDJocDIyb3J4emM2YWt1b2cifQ.npoMtNgcNZocxkIVTvWwkQ';

// Get the map from mapbox
var map = new mapboxgl.Map({
    container: 'map',
    maxZoom: 18,
    minZoom: 4,
    zoom: 11.5,
    center: [-95.4427, 29.69192],
    style: 'mapbox://styles/mapbox/streets-v10'
});

// Load water depht maps

//Adding raster image
map.on('load', function () {

    // Load all sources
    load_sources();
    // Add accessibility mesures_fire staion
    add_layer_access_to_fire_stations();
    // Add accessibility mesures hospitals
    add_layer_access_to_hospitals();
    // Add accessibility mesures_ dialysis centers
    add_layer_access_to_dialysis_centers();
    // Add outline to access maps
    add_layer_access_maps_outline();
    // Add inundation layer
    add_layer_inundation_map();
    // Add flooded roads
    add_layer_flooded_roads();
    // Load study area
    load_study_area_boundary();
    // Load locations of fire stations
    load_locations_of_fire_stations()
    // Location of hospitals
    load_locations_of_hospitals()
    // Location of dialysis centers
    load_locations_of_dialysis_centers()
    // Set initial visibility
    hide_layers(['Flooded roads', 'Accessibility Measures (Fire Stations)', 'outline', 'Accessibility Measures (Hospitals)', 'Accessibility Measures (Dialysis Centers)',
    'Location of fire stations', 'Location of Hospitals', 'Location of Dialysis Centers']);
    // Load legend

});


// Add all sources
function load_sources() {
    // Source: Add Flood depth raster data
    map.addSource('radar', {
        'type': 'image',
        'url': 'data/flood_depth_raster.png',
        'coordinates': [
            [-95.7167853758765119, 29.7957042639456091],
            [-95.2351955788307976, 29.7957042639456091],
            [-95.2351955788307976, 29.5831271579661497],
            [-95.7167853758765119, 29.5831271579661497]
        ]
    });

    // Source: Add road condition
    map.addSource('flooded_roads', { type: 'geojson', data: 'data/flooded_roads.geojson' }),

    // Source: Add accessibility measures data
    map.addSource('mobility', { type: 'geojson', data: 'data/mobility.geojson' })


};

// Add inundation layer
function add_layer_inundation_map() {

    // Map Layer: Add inundation depth map to a layer
    map.addLayer({ id: 'Inundation Depth', 'type': 'raster', 'source': 'radar', 'paint': { 'raster-fade-duration': 0 } });

};


// Load study area
function load_study_area_boundary() {
    // Add the study area boundary to the source
    map.addSource('study_area_boundary', { type: 'geojson', data: 'data/Brays_Watershed_EPSG4326.geojson' }),

    // Add the source to the layers as an outline
    map.addLayer({
        'id': 'Study area',
        'type': 'line',
        'source': 'study_area_boundary',
        'paint': {
            'line-width': 1,
            'line-color': 'black',
            // 'line-'

        }
    });
};

// Load fire stations
function load_locations_of_fire_stations() {
    // Add the study area boundary to the source
    map.addSource('locations_fire_stations', { type: 'geojson', data: 'data/Fire_Stations_Brays_Buffer_2miles_EPSG4326.geojson' }),

    // Add the source to the layers as an outline
    map.addLayer({
        'id': 'Location of fire stations',
        'type': 'symbol',
        'source': 'locations_fire_stations',
        'layout':{
            'icon-image': 'fire-station-15',
            'icon-allow-overlap': true,
          },
    });
};

// Load fire stations
function load_locations_of_hospitals() {
    // Add the study area boundary to the source
    map.addSource('locations_hospitals', { type: 'geojson', data: 'data/Hospitals_Brays_Buffer_2miles_EPSG4326.geojson' }),

    // Add the source to the layers as an outline
    map.addLayer({
        'id': 'Location of Hospitals',
        'type': 'symbol',
        'source': 'locations_hospitals',
        'layout':{
            'icon-image': 'hospital-15',
            'icon-allow-overlap': true,
          },
    });
};

// Load Dialysis centers
function load_locations_of_dialysis_centers() {
    // Add the study area boundary to the source
    map.addSource('locations_dialysis_centers', { type: 'geojson', data: 'data/Dialysis_Centers_Brays_Buffer_2miles_EPSG4326.geojson' }),

    // Add the source to the layers as an outline
    map.addLayer({
        'id': 'Location of Dialysis Centers',
        'type': 'symbol',
        'source': 'locations_dialysis_centers',
        'layout':{
            'icon-image': 'pharmacy-15',
            'icon-allow-overlap': true,
          },
    });
};

// Add flooded roads
function add_layer_flooded_roads() {

    map.addLayer({
        'id': 'Flooded roads',
        'type': 'line',
        'source': 'flooded_roads',
        'paint': {
            'line-width': 1,
            'line-color': 'red'
        }
    });

};


function add_layer_access_maps_outline() {
    // Add a black outline around the polygon.
    map.addLayer({
        'id': 'outline',
        'type': 'line',
        'source': 'mobility',
        'layout': {},
        'paint': {
            'line-color': '#000',
            'line-width': 1,
            'line-opacity': 0.1
        }
    });

};

function add_layer_access_to_fire_stations() {

    //https://coolors.co/palettes/popular
    map.addLayer({
        'id': 'Accessibility Measures (Fire Stations)',
        'type': 'fill',
        'source': 'mobility', // reference the data source
        'layout': {},
        'paint': {
            'fill-color': [
                'interpolate',
                ['linear'],
                ['get', 'CL_Fire_stations_max_water_depth_over_roads_Projected_mean'],
                0.0, '#ffffff', 0.1, '#f2f0f7', 0.3, '#dadaeb', 0.5, '#bcbddc', 0.7, '#9e9ac8', 0.8, '#807dba', 0.9, '#6a51a3', 1.0, '#4a1486'],
            'fill-opacity': 0.7
        }
    });
// https://stackoverflow.com/questions/18189201/is-there-a-color-code-for-transparent-in-html/18189313
};

//  0.0, '#1b7837', 0.1, '#5aae61', 0.3, '#d9f0d3', 0.5, '#fc9272', 0.7, '#fb6a4a', 0.8, '#ef3b2c', 0.9, '#cb181d', 1.0, '#99000d'],
function add_layer_access_to_hospitals() {

    //https://coolors.co/palettes/popular
    map.addLayer({
        'id': 'Accessibility Measures (Hospitals)',
        'type': 'fill',
        'source': 'mobility', // reference the data source
        'layout': {},
        'paint': {
            'fill-color': [
                'interpolate',
                ['linear'],
                ['get', 'CL_Hospitals_max_water_depth_over_roads_Projected_mean'],
                0.0, '#ffffff', 0.1, '#fee5d9', 0.3, '#fcbba1', 0.5, '#fc9272', 0.7, '#fb6a4a', 0.8, '#ef3b2c', 0.9, '#cb181d', 1.0, '#99000d'],
            'fill-opacity': 0.7
        }
    });

};

function add_layer_access_to_dialysis_centers() {

    //https://coolors.co/palettes/popular
    map.addLayer({
        'id': 'Accessibility Measures (Dialysis Centers)',
        'type': 'fill',
        'source': 'mobility', // reference the data source
        'layout': {},
        'paint': {
            'fill-color': [
                'interpolate',
                ['linear'],
                ['get', 'CL_Dialysis_centers_max_water_depth_over_roads_Projected_mean'],
                0.0, '#ffffff', 0.1, '#eff3ff', 0.3, '#c6dbef', 0.5, '#9ecae1', 0.7, '#6baed6', 0.8, '#4292c6', 0.9, '#2171b5', 1.0, '#084594'],
            'fill-opacity': 0.7
        }
    });

};
// add_layer_access_to_dialysis_centers
// CL_Dialysis_centers_max_Depth (26SEP2020 08 00 00)_mean

// 'CL_Hospitals_max_Depth (26SEP2020 08 00 00)_mean'
// ['get', 'CL_Dialysis_centers_max_Depth (26SEP2020 08 00 00)_mean'],

function hide_layers(list_of_layers) {

    for (i = 0; i < list_of_layers.length; i++) {
        // alert("at show layer")
        var layer = list_of_layers[i];
        map.setLayoutProperty(layer, 'visibility', 'none')
    };
};

function show_layers(list_of_layers) {
    // alert("at show layer")
    for (i = 0; i < list_of_layers.length; i++) {
        var layer = list_of_layers[i];
        map.setLayoutProperty(layer, 'visibility', 'visible')
    };
};


// function add_water_depth_legend() {

//     // Add title
//     // legend.appendChild("<h2>US population density</h2>")

//     var layers = ['0-0.1 ft', '0.1-0.2 ft', '0.2-0.5 ft', '0.5-1.0 ft', '1.0-1.5 ft', '1.5-2.0 ft', '2.0-4.0 ft', '4+ ft'];
//     var colors = ['#F7FBFF', '#DEEBF7', '#C6DBEF', '#9ECAE1', '#6BAED6', '#4292C6', '#2171b5', '#084594'];

//     for (i = 0; i < layers.length; i++) {
//         var layer = layers[i];
//         var color = colors[i];
//         var item = document.createElement('div');
//         var key = document.createElement('span');
//         key.className = 'legend-key';
//         key.style.backgroundColor = color;

//         var value = document.createElement('span');
//         value.innerHTML = layer;
//         item.appendChild(key);
//         item.appendChild(value);
//         legend.appendChild(item);
//     };
// }