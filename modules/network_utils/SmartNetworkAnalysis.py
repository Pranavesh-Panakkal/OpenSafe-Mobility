"""Class for smart network analysis
Details
-------
Author: Pranavesh Panakkal
Release: r0.12_16_20

Changelog:
- 12_16_20:
    - Create a deep copy of the analysis everytime a loop is done to perform initial distance calculation
    - Modified the _scenario_analysis function to add links with no data when building the network.
       Initially only wd less than thershold was added and this neglected links without any flood data.
    - identify_flooded_roads modified to consider the list of scenarios in the file

"""
from modules.geo_utils.SmartGeoProcess import (
    GeoDataLines,
    GeoDataPolygons,
    GeoDataPoints,
)
from shapely.geometry import Point, MultiPoint, LineString
from shapely.ops import nearest_points
import pandas as pd
import geopandas as gpd
import networkx as nx
import copy
import os
from itertools import product
from functools import partial
from loky import get_reusable_executor
from tqdm import tqdm
import numpy as np

import logging

log = logging.getLogger(__name__)


class NetworkAnalysis:
    def __init__(self, path_network=None, crs="epsg:26915"):
        self.path_network = path_network
        self.crs = crs
        self.destination_nodes = {}

    def add_start_end_nodes_to_gdf(self, gdf=None, explode_data=False):
        """Explode might be required if the data contains multiline_string"""
        # This function adds start and end nodes to geodataframe

        if gdf is None:
            gdf = self.GeoData.gdf
        # Explode might be required if the data contains multiline_string
        if explode_data:
            gdf = gdf.explode()

        gdf["start_node"] = None
        gdf["end_node"] = None

        for index, row in gdf.iterrows():
            coords = [(coords) for coords in list(row["geometry"].coords)]
            start_node, end_node = [coords[i] for i in (0, -1)]
            gdf.at[index, "start_node"] = start_node
            gdf.at[index, "end_node"] = end_node

        self.GeoData.gdf = gdf

    def get_network_from_geodata(self, path_network=None, crs=None):
        """Read geodata for the network"""

        if path_network is None:
            path_network = self.path_network
        if crs is None:
            crs = self.crs

        # Initiate a network reader, Our network model now inherits the GeoDataLines class
        self.GeoData = GeoDataLines(path_geodata=path_network, crs=crs)
        # load data to file;
        self.GeoData.read_geodata()

    def get_unique_nodes_in_the_graph(self, gdf=None):
        """Generate unique nodes in the graph"""
        if gdf is None:
            gdf = self.GeoData.gdf

        # Returns unique list of nodes and the count of unique nodes
        lst_of_nodes = pd.concat([gdf["start_node"], gdf["end_node"]], axis=0)
        lst_of_nodes.drop_duplicates(inplace=True)
        df = pd.DataFrame()
        df["nodes"] = lst_of_nodes

        # Save the list of nodes and node results
        self.nodes = lst_of_nodes
        self.node_results = df

        # return df
        return df

    def fit(self):
        """

        :return:
        :rtype:
        """
        self.get_network_from_geodata()  # <--This reads the network data
        self.add_start_end_nodes_to_gdf()  # <-- Adds 'end_node', 'start_node' to gdf
        self.get_unique_nodes_in_the_graph()  # <-- Finds unique nodes and generated  self.nodes (lst_of_nodes) and (self.node_results) a df

    def give_nearest_point_to_given_point_nodeList(self, origin_X_Y, node_list):
        # get the list of nodes
        # set multipoint
        destinations = MultiPoint([(x) for x in node_list])
        # Set origin
        origin__ = Point(origin_X_Y)
        # caluclate the nearest neighbour
        nearest_geoms = nearest_points(origin__, destinations)
        # the result will contain two point geometry first is our origin, next is our desti.
        return (nearest_geoms[1].x, nearest_geoms[1].y)

    def get_the_nearest_node_for_points(
        self, gdf, network_nodes=None, label_facility=None
    ):
        """Get the nearest node for each facility; Include label_facility for including the facility for analysis"""

        # If no nodes are given, take out nodes
        if network_nodes is None:
            network_nodes = self.nodes
        # Loop through nodes
        gdf["nearest_network_node"] = None
        for index, row in gdf.iterrows():
            coords = [(coords) for coords in list(row["geometry"].coords)]
            gdf.at[
                index, "nearest_network_node"
            ] = self.give_nearest_point_to_given_point_nodeList(
                Point(coords), network_nodes
            )

        if label_facility is not None:
            self.destination_nodes[label_facility] = set(gdf["nearest_network_node"])

        return gdf

    def get_initial_distance(
        self,
        facility_labels="All",
        lbl_of_weight="length",
        inaccessibility_code=999,
        model_flow_direction=False,
        start_node_label=None,
        end_node_label=None,
    ):

        _net_gdf = self.GeoData.gdf

        _facility_nodes_dict = copy.deepcopy(self.destination_nodes)
        # Limit only the facility interested
        if not facility_labels == "All":
            # Convert item to list if they are string
            facility_labels = (
                facility_labels
                if isinstance(facility_labels, list)
                else [facility_labels]
            )
            # Filter the list to only include select case
            _facility_nodes_dict = {
                k: v for k, v in _facility_nodes_dict.items() if k in facility_labels
            }

        # adding nodes to the graph
        if model_flow_direction is False:
            # creating a network
            G = nx.Graph()
            for index, row in _net_gdf.iterrows():
                G.add_edge(
                    row["start_node"], row["end_node"], weight=row[lbl_of_weight]
                )
        elif all([model_flow_direction, end_node_label, end_node_label]):
            # Model directed graph
            G = nx.DiGraph()
            for index, row in _net_gdf.iterrows():
                G.add_edge(
                    row[start_node_label],
                    row[end_node_label],
                    weight=row[lbl_of_weight],
                )

        # Loop through each facility
        for facility, nodes in _facility_nodes_dict.items():
            # Create a new deep copy of the network which contains all nodes
            # This is done not to disturb the original node. The 'aux_node' depends on the facility
            _g = copy.deepcopy(G)
            # For each facility perform the analysis
            _g.add_node("aux_node")
            # Loop through nodes and add them to the master node
            for items in nodes:
                try:
                    _g.add_edge(items, "aux_node", weight=0)
                except:  # sometimes point of intersts like hosp locations may be flooded
                    pass
            # Add a column to save results
            self.node_results[f"Initial_dist_{facility}"] = None

            for index, row in self.node_results.iterrows():
                lenVal = inaccessibility_code  # float("inf")
                try:
                    lenVal = nx.shortest_path_length(
                        _g, source=row["nodes"], target="aux_node", weight="weight"
                    )
                except nx.NetworkXNoPath:
                    lenVal = inaccessibility_code  # float("inf")
                except:
                    lenVal = inaccessibility_code  # float("inf") # error code for nodes not present in the mofified network. Flooded nodes

                row[f"Initial_dist_{facility}"] = lenVal

        # Save the dataframe as a) geodataframe and b) as dataframe
        self.gdf_results = self._df_to_gdf(self.node_results)
        return self.node_results

    def _df_to_gdf(self, df_results):
        # Converting panda dataframe into geometry
        geometry = [Point(xy) for xy in df_results.nodes]
        return gpd.GeoDataFrame(df_results, crs=self.crs, geometry=geometry)

    def batch_extract_raster(self, list_of_raster_path, buffer=10):
        # Generate a line file from self.geoData.gdf
        self.GeoData.batch_estimate_raster_stat(
            list_of_raster_path=list_of_raster_path, buffer=buffer, attach_to_file=True
        )
        # Store raster paths
        facility_labels = (
            list_of_raster_path
            if isinstance(list_of_raster_path, list)
            else [list_of_raster_path]
        )
        self.list_scenarios = [
            f"max_{os.path.basename(x).split('.')[0]}" for x in facility_labels
        ]

    def perform_scenaio_analysis(
        self,
        scenaio_field_in_df=None,
        facility_labels="All",
        link_removal_threshold=0.6,
        lbl_of_weight="length",
        inaccessibilityCode=1e5,
        attach_to_file=True,
        model_flow_direction=False,
        start_node_label=None,
        end_node_label=None,
    ):

        # Provide list of scenario to work on
        if scenaio_field_in_df is None:
            scenaio_field_in_df = self.list_scenarios
        scenaio_field_in_df = list(scenaio_field_in_df)
        # Get the list of facility nodes
        _facility_nodes_dict = copy.deepcopy(self.destination_nodes)
        # Limit only the facility interested
        if not facility_labels == "All":
            # Convert item to list if they are string
            facility_labels = (
                facility_labels
                if isinstance(facility_labels, list)
                else [facility_labels]
            )
            # Filter the list to only include select case
            _facility_nodes_dict = {
                k: v for k, v in _facility_nodes_dict.items() if k in facility_labels
            }

        # Create a partial function for passing buffer and making the process concurrent
        func_ = partial(
            self._scenario_analysis,
            link_removal_threshold=link_removal_threshold,
            lbl_of_weight=lbl_of_weight,
            inaccessibilityCode=inaccessibilityCode,
        )

        # func_((scenaio_field_in_df[0], list(_facility_nodes_dict.keys())[0]))
        with get_reusable_executor() as executor:
            results = list(
                tqdm(
                    executor.map(
                        func_, product(scenaio_field_in_df, _facility_nodes_dict)
                    ),
                    total=len(scenaio_field_in_df * len(_facility_nodes_dict)),
                    desc="Performing scenario analysis",
                )
            )

        combined_df = pd.concat(results, axis=1)

        # If attached is true
        if attach_to_file:
            # _combined = pd.concat([self.gdf, combined_df], axis=1)
            _combined = pd.concat(
                [
                    self.node_results.reset_index(drop=True),
                    combined_df.reset_index(drop=True),
                ],
                axis=1,
            )
            self.node_results = _combined
            self.gdf_results = self._df_to_gdf(self.node_results)
            return _combined

        return combined_df

    def batch_identify_flooded_road_from_roadway_elevation(
        self,
        string_for_shortlisting_scenario=None,
        wading_height=2,
        col_name_for_elevation_in_network="min_ele",
        suffix="ft",
        factor_link_elevation_data=3.28084,
    ):

        if string_for_shortlisting_scenario:
            scenarios = [
                sce
                for sce in self.list_scenarios
                if string_for_shortlisting_scenario in sce
            ]

        for sce in tqdm(scenarios):
            self.identify_flooded_roads_elevation(
                sce,
                wading_height=wading_height,
                new_field_label=None,
                col_name_for_elevation_in_network=col_name_for_elevation_in_network,
                suffix=suffix,
                factor_link_elevation_data=factor_link_elevation_data,
            )

    def batch_identify_flooded_road(
        self,
        string_for_shortlisting_scenario=None,
        wading_height=2,
        suffix="ft",
        factor_link_elevation_data=3.28084,
    ):

        if string_for_shortlisting_scenario:
            scenarios = [
                sce
                for sce in self.list_scenarios
                if string_for_shortlisting_scenario in sce
            ]

        for sce in tqdm(scenarios):
            self.identify_flooded_roads(
                sce, wading_height=wading_height, new_field_label=None, suffix=suffix
            )

    def identify_flooded_roads_elevation(
        self,
        scenaio_field_in_df,
        wading_height=2,
        new_field_label=None,
        suffix=None,
        col_name_for_elevation_in_network="max_elev",
        factor_link_elevation_data=1,
    ):
        """
        Identify flooded roads using wading height. If the water depht is greater than the wading height the road
        is considered flooded
        :param scenaio_field_in_df: Label of field in the database
        :type scenaio_field_in_df:
        :param wading_height: Wading height, unit same as CRS
        :type wading_height: float
        :return: None
        :rtype:
        """
        if new_field_label is None:
            new_field_label = f"{scenaio_field_in_df}_{wading_height}"

        if suffix:
            new_field_label = f"{new_field_label}_{suffix}"

        self.GeoData.gdf[new_field_label] = None

        for index, row in self.GeoData.gdf.iterrows():
            if np.isfinite(
                row[scenaio_field_in_df]
            ):  # <-- If data is available for that link
                # Estimate elevation, +ve for flooded case
                _elev_diff = (
                    row[scenaio_field_in_df]
                    - row[col_name_for_elevation_in_network]
                    * factor_link_elevation_data
                )
                # Tag roads
                if _elev_diff >= wading_height:
                    self.GeoData.gdf.at[index, new_field_label] = 1  # <-- Flooded tag
                elif _elev_diff < wading_height:
                    self.GeoData.gdf.at[index, new_field_label] = 0  # <-- No flood tag

    def identify_flooded_roads(
        self,
        scenaio_field_in_df=None,
        wading_height=2,
        new_field_label=None,
        suffix=None,
        encode_no_data_as=None,
    ):
        """
        Identify flooded roads using wading height. If the water depht is greater than the wading height the road
        is considered flooded
        :param scenaio_field_in_df: Label of field in the database
        :type scenaio_field_in_df:
        :param wading_height: Wading height, unit same as CRS
        :type wading_height: float
        :return: None
        :rtype:
        """
        if scenaio_field_in_df is None:
            scenaio_field_in_df = self.list_scenarios

        if not isinstance(scenaio_field_in_df, list):
            scenaio_field_in_df = [scenaio_field_in_df]

        if new_field_label is None:
            new_field_label = [f"{x}_{wading_height}" for x in scenaio_field_in_df]

        if suffix:
            new_field_label = [f"{x}_{suffix}" for x in new_field_label]

        for _scenaio_field_in_df, _label in zip(scenaio_field_in_df, new_field_label):

            self.GeoData.gdf[_label] = encode_no_data_as

            for index, row in self.GeoData.gdf.iterrows():
                if np.isfinite(
                    row[_scenaio_field_in_df]
                ):  # <-- If data is available for that link
                    if row[_scenaio_field_in_df] >= wading_height:
                        self.GeoData.gdf.at[index, _label] = 1  # <-- Flooded tag
                    elif row[_scenaio_field_in_df] < wading_height:
                        self.GeoData.gdf.at[index, _label] = 0  # <-- No flood tag

    def _scenario_analysis(
        self,
        parms,
        link_removal_threshold,
        lbl_of_weight,
        inaccessibilityCode,
        model_flow_direction=False,
        start_node_label=None,
        end_node_label=None,
    ):

        scenaio_field_in_df, facility_node_list = parms
        # creating a network
        G = nx.Graph()
        # Bring in the network
        gdf_network = copy.deepcopy(self.GeoData.gdf)
        df_results = copy.deepcopy(self.node_results)
        # adding only the unaffected nodes to the graph

        for index, row in gdf_network.iterrows():
            # analyze only if the condition is satisfied
            if not (row[scenaio_field_in_df] > link_removal_threshold):
                G.add_edge(
                    row["start_node"], row["end_node"], weight=row[lbl_of_weight]
                )

        # Getting information on the nearest road node for each critical facility
        nodesOfInterest = self.destination_nodes[
            facility_node_list
        ]  # <--Get nodes for the facility

        # adding auxillary nodes
        for items in nodesOfInterest:
            try:
                G.add_edge(
                    items, "aux_node", weight=0
                )  # sometimes point of interests like hosp locs. may be flooded
            except:
                pass

        # Initilize the field
        new_field_name = f"{scenaio_field_in_df}_{facility_node_list}"
        df_results[new_field_name] = None

        for index, row in df_results.iterrows():
            lenVal = inaccessibilityCode  # float("inf")
            try:
                lenVal = nx.shortest_path_length(
                    G, source=row["nodes"], target="aux_node", weight="weight"
                )
            except nx.NetworkXNoPath:
                lenVal = inaccessibilityCode  # float("inf")
            except:
                lenVal = inaccessibilityCode  # float("inf") # error code for nodes not present in the mofified network. Flooded nodes

            df_results.at[index, new_field_name] = lenVal

        return df_results[new_field_name]

    def estimate_CL_ratio(self):
        list_facilities = list(self.destination_nodes.keys())
        for facility in list_facilities:
            for scenario in self.list_scenarios:
                self.node_results[f"CL_{facility}_{scenario}"] = 1 - (
                    (self.node_results[f"Initial_dist_{facility}"] + 1e-15)
                    / (self.node_results[f"{scenario}_{facility}"] + 1e-15)
                )
        # Update node results

        self.node_results = self.node_results

        # Update gdf
        self.gdf_results = self._df_to_gdf(self.node_results)

    def summarize_results_at_polygons(
        self, path_polygon, summary_statistics=["mean", "std", "max", "min"]
    ):
        census_block = GeoDataPolygons(path_geodata=path_polygon, crs=self.crs)
        census_block.read_geodata()
        census_block.clip(mask=self.GeoData.gdf, buffer_dist=1, update_geometry=True)
        # Get node results
        node_results = self._df_to_gdf(self.node_results)
        self.summary_gdf = census_block.summarize_points_at_polygons(
            points=node_results, summary_statistics=summary_statistics
        )

    def save_results(
        self,
        config=None,
        accessibility_measures=True,
        road_network_csv=True,
        critical_facility=False,
        road_network_geoData=False,
        results_aggregated_at_polygons=False,
    ):
        if accessibility_measures:
            self.gdf_results = self._df_to_gdf(self.node_results)
            self.gdf_results.drop(columns="nodes", inplace=True)
            log.info("Writing files: Accessibility Measures...")
            self.GeoData.save_geodata(
                polygon=self.gdf_results,
                filename="Node_results",
                path_to_save=config.analysis_results.temporary_files.temp_storage_for_analysis,
            )
        if road_network_geoData:
            log.info("Writing files: Network with road condition...")
            data_without_nodes = self.GeoData.gdf
            data_without_nodes = self.GeoData._make_geometry_the_last_column(
                data_without_nodes
            )
            data_without_nodes.drop(columns=["start_node", "end_node"], inplace=True)
            self.GeoData.save_geodata(
                polygon=data_without_nodes,
                filename="Network_Condition_results",
                path_to_save=config.analysis_results.temporary_files.temp_storage_for_analysis,
            )
        if results_aggregated_at_polygons:
            log.info("Writing files: Aggregating results with road condition...")
            self.GeoData.save_geodata(
                polygon=self.summary_gdf,
                filename="Geo_summary_results",
                path_to_save=config.analysis_results.temporary_files.temp_storage_for_analysis,
            )
            # self.GeoData.save_geodata(polygon=self.summary_gdf, filename="Geo_summary_results")
        if road_network_csv:
            pd.DataFrame(self.GeoData.gdf).to_csv(
                f"{config.analysis_results.temporary_files.temp_storage_for_analysis}/Network_Condition_results.csv"
            )

        log.info("Analysis Completed!")
