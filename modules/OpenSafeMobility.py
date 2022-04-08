# Title     : OpenSafe Mobility Class
# Objective : The main class of OpenSafe Mobility
# Created by: Pranavesh Panakkal
# Created on: 4/6/2022
# Version   :
# Dev log   :
""""""
import logging
import time
import paramiko

from datetime import timedelta, datetime
from functools import partial
from itertools import compress
from shutil import copyfile

from modules.geo_utils.SmartGeoProcess import GeoDataPoints
from modules.network_utils.SmartNetworkAnalysis import NetworkAnalysis
from modules.file_management.file_processing import (
    create_a_folder_if_it_doesnt_exist,
    list_all_files_with_an_extension,
)
from modules.file_management.file_processing import remove_all_contents_of_a_folder
from modules.file_management.file_processing import remove_folder_if_exist
from modules.radar.radar_data import (
    remove_empty_files,
    round_down_time_to_the_nearest_time_delta,
    format_time,
)
from modules.radar.radar_data import (
    collcect_a_file,
    slice_list_and_provide_all_elements,
)
from modules.radar.radar_data import (
    get_before_and_after_indexes_for_a_list_item,
    sum_consecutive_rows,
)
from modules.hec_ras.ras import kill_a_process
from modules.rascontrol import rascontrol
from modules.radar.dss import generate_dss_from_pandas
from modules.geo_utils.raster_processing import subtract_two_raster
from modules.geo_utils.geoprocess import reproject_raster
from modules.image_utils.image_processing import generate_png_file
from modules.plot_utils.generate_validation_plots import (
    generate_validation_plots_before_run,
    utc_datetime_to_cst,
)
from modules.publish.publish import sync_aws

import pandas as pd
import numpy as np
import geopandas as gpd

log = logging.getLogger(__name__)


class OpenSafeMobility:
    """
    The main class of OpenSafe Mobility
    """

    def __init__(self, config):
        # Store the config file for future use
        self.ssh_client = None
        self.config = config
        self.path_to_store_radar = None

        # Placeholders
        self.current_time_steps = None
        self.radar_available = None
        self.last_available_data_step = None
        self.list_of_relevant_files_to_current_run = None
        self.availability_status_of_relevant_files_to_current_run = None
        self.current_time_steps_on_disk = None
        self.df_radar = None
        self.df_criteria = None
        self.df_validation_dash_maps = None
        self.crs = None
        self.network = None

        # Initialize storage tasks
        self.initialize()

        # Log
        log.info("Initialized OpenSafe Mobility")

    def initialize(self) -> None:
        """
        Code to initialize the model
        :return: None
        """
        # Make directory in the storage config files if they are misssing.
        self.make_dir_if_missing()

    def make_dir_if_missing(self) -> bool:
        """
        Create folders if they do not exist.
        :return: bool
        """
        # Create files
        return all(
            [
                create_a_folder_if_it_doesnt_exist(_pth)
                for _pth in self.config.storage.folders_to_create.values()
            ]
        )

    def run(self) -> None:
        """
        Perform the analysis. This is the main method.
        :return:
        """
        # Perform initialization. This will create folder structure for storing radar data if it is missing.
        log.info("Staring a run")
        # Storing model start time to estimate the total run time
        start_time = time.time()
        # Remove last analysis results
        self.remove_old_files()
        # Preemptively avoid hec-ras locking error
        self.fix_potential_hec_ras_error()
        # Generate the DSS file
        self.get_rainfall_radar_data()
        # Create a panda dataframe and write the files to it
        self.read_files_to_pandas()
        # Handle missing data
        self.handle_missing_data()
        # Check model run condition
        if any(
            [
                self.check_threshold(),
                self.config.thresholds.run_model_even_if_no_flooding,
            ]
        ):
            # If either of this two conditions are met, the madel will run
            # Create a dss file from panda dataframe
            self.create_dss()
            # Run Analysis using HEC-RAS Controller
            self.run_hec_ras_model()
            log.info("HEC-RAS Model Complete")
            # Kill HEC-RAS
            self.kill_hec_ras()
            # Get water depth over DSM, this will be used to identify flooded roads
            self.subtract_dsm_from_wse()
            log.info("Water over structure raster created")
            # Reproject raster, flood depth raster
            reproject_raster(
                source_file_location=self.config.analysis_results.temporary_files.results_tiff,
                destination_file_location=self.config.analysis_results.temporary_files.results_tiff_projected,
                destination_crs=self.config.analysis_results.temporary_files.output_crs,
                source_crs=self.config.analysis_results.temporary_files.input_crs,
            )
            # Reproject water over roads raster
            reproject_raster(
                source_file_location=self.config.analysis_results.temporary_files.results_tiff_water_over_roads,
                destination_file_location=self.config.analysis_results.temporary_files.results_tiff_water_over_roads_projected,
                destination_crs=self.config.analysis_results.temporary_files.output_crs,
                source_crs=self.config.analysis_results.temporary_files.input_crs,
            )
            # Save water depth raster
            self.generate_water_depth_map()
            log.info("Generated water depth map")
            # # Initialize network analysis
            self.initiate_network()
            # Perform mobility analysis
            self.perform_mobility_analysis()
            # Plot flooded roads
            try:
                self.plot_flooded_roads()
            except FileNotFoundError:
                log.warning("Unable to plot flooded roads!")
            copyfile(
                src=f"{self.config.analysis_results.temporary_files.temp_storage_for_analysis}\Geo_summary_results.json",
                dst=self.config.analysis_results.final_results.accessibility_measures,
            )
        # Create validation plots
        self.create_validation_plots()
        # Save to html the the last run step of this code, this is then displayed on the website
        self.save_last_run_html()
        # Sync the files with aws
        sync_aws(self.config)
        # Convey runtime and final status
        log.info(
            f"Running completed at: {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        )
        log.info(f"Runtime: --- %{(time.time() - start_time) / 60} minutes --- ")

    def remove_old_files(self) -> None:
        """
        Remove old results. This step ensures that no old files are carried over to the new analysis
        :return: None
        :rtype: None
        """
        # Delete all files in the output folder for HEC RAS
        remove_all_contents_of_a_folder(
            folder_path=self.config.analysis_results.results_folder
        )

        # Collect all temp and final result files
        [
            remove_folder_if_exist(_files)
            for _files in self.config.analysis_results.final_results.values()
        ]
        [
            remove_folder_if_exist(_files)
            for _files in self.config.analysis_results.temporary_files.values()
        ]

        log.info("Removed old files")

    def fix_potential_hec_ras_error(self) -> None:
        """
        Functions to fix data lock error in HEC-RAS. Deleting and replacing with original files for overcome locks in
        windows.
        :return:
        """
        # list all files that should be replaced
        list_to_replace = (
            self.config.hec_ras.fix_hec_ras_automation_error.files_to_replace
        )
        # Replace those files
        for keys in list_to_replace.keys():
            copyfile(src=list_to_replace[keys]["from"], dst=list_to_replace[keys]["to"])

    def get_rainfall_radar_data(self) -> None:
        """
        All steps to create the dss file required for analysis
        :return: None
        :rtype: None
        """
        # Remove empty CSV files in the location of radar data
        remove_empty_files(
            rootdir=self.config.storage.folders_to_create.path_to_store_radar
        )

        # Initiate connection to the server
        if self.connect_to_remote_server_via_ssh():
            log.info("Connected to remote server for radar.")

        # Get the file names required
        self.get_radar_paths_for_current_run()

    def connect_to_remote_server_via_ssh(self) -> None:
        """
        Connect via ssh to the remote server
        :return: None
        :rtype: None
        """
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(
            hostname=self.config.radar.server.HOST_NAME,
            username=self.config.radar.server.USER_NAME,
            password=self.config.radar.server.PASSWORD,
        )

    def get_radar_paths_for_current_run(self) -> None:
        """
        Get the names of files required for current analysis. This function should be modified to suit new datasets.
        Some values might depend on the data source (e.g., naming convention of the files).
        :return:
        :rtype:
        """
        # Get the time delta
        _source_time_delta = timedelta(
            minutes=self.config.radar.radar_rainfall.time_resolution_of_the_incoming_data
        )

        # Get the current time step in UTC
        if self.config.radar.hindcast_model.active:
            now = round_down_time_to_the_nearest_time_delta(
                datetime.strptime(
                    self.config.radar.hindcast_model.time, "%Y-%m-%d  %I:%M%p"
                ),
                _source_time_delta,
            )
        else:
            now = round_down_time_to_the_nearest_time_delta(
                datetime.utcnow(), _source_time_delta
            )

        # Get the start time
        # Adding X more hours, we will later remove them while initializing the analysis.
        # This is done so that if the current file is not available, the model can still run
        start_time = now - timedelta(
            hours=self.config.radar.radar_rainfall.duration_hr
            + self.config.radar.radar_rainfall.additional_data_in_hrs,
            minutes=self.config.radar.radar_rainfall.duration_min,
        )

        # Time steps
        steps = int((now - start_time) / _source_time_delta)

        # Get all time intervals between start and end time
        list_of_times = [
            (start_time + x * _source_time_delta) for x in range(0, steps + 1)
        ]

        # Correctly formatted list of times
        list_of_times = [
            f"KHGX_LII_basin_UTC_{format_time(_time)}.csv" for _time in list_of_times
        ]

        # Find a list of all files with csv extension in the main folder
        _pth_store_radar = self.config.storage.folders_to_create.path_to_store_radar
        existing_files_partial = partial(
            list_all_files_with_an_extension, _pth_store_radar, ".csv"
        )

        # Get all existing files
        existing_files = existing_files_partial()

        # The files that we are currently lacking are
        # files_to_collect_from_server = list(set(list_of_times) - set(existing_files))
        files_to_collect_from_server = [
            i for i in list_of_times if i not in existing_files
        ]

        # Now we have to collect all this file and save it to the disk
        def server_file_path(_file_name):
            return f"PIRadarData/{_file_name}"

        def local_file_path(_file_name):
            return f"{_pth_store_radar}/{_file_name}"

        log.info(files_to_collect_from_server)
        status = [
            collcect_a_file(
                self.ssh_client, server_file_path(_pth), local_file_path(_pth)
            )
            for _pth in files_to_collect_from_server
        ]
        count_failed = len(status) - sum(status)
        if count_failed > 0:
            log.info(status)
            log.info(f"Failed to collect {len(status) - sum(status)} files")
            log.info(
                f"Following files failed: {list(compress(files_to_collect_from_server, [not elem for elem in status]))}"
            )

        # Remove empty CSV files in the location of radar data
        # We have to call this function again since the ssh call to server will save files without any data
        remove_empty_files(rootdir=_pth_store_radar)
        # List of files to concat
        # Get the new list of existing files
        existing_files_now = existing_files_partial()
        # Get the status of files in the list_of_times
        file_status = [
            True if i in existing_files_now else False for i in list_of_times
        ]
        # Filter only the available time steps
        files_to_combine = [i for i in list_of_times if i in existing_files_now]
        assert len(files_to_combine) > 0

        # Store the results
        self.current_time_steps_on_disk = files_to_combine
        self.last_available_data_step = files_to_combine[-1]
        self.list_of_relevant_files_to_current_run = (
            slice_list_and_provide_all_elements(
                list_to_filter=list_of_times,
                item_to_match=self.last_available_data_step,
            )
        )

    def read_files_to_pandas(self) -> None:
        """
        Read csv files to panda dataframe
        :return:
        """
        # List of all time steps
        csv_list = self.list_of_relevant_files_to_current_run
        list_on_drive = self.current_time_steps_on_disk
        diff = list(set(csv_list) - set(list_on_drive))

        # Renaming lambda function
        func_lambda = (
            lambda item: f"{self.config.storage.folders_to_create.path_to_store_radar}/{item}"
        )

        # Reaa all csv files on disk
        df = pd.concat(
            [
                pd.read_csv(func_lambda(item), names=[item[:-4]])
                for item in list_on_drive
            ],
            axis=1,
        )
        # For the files not on disk, create empty file
        for item in diff:
            df[item[:-4]] = np.nan
        # Reindex the items based on the initial list
        self.df_radar = df.reindex([item[:-4] for item in csv_list], axis=1)
        # self.df_radar.to_csv("datafrmae_lambda.csv")

    def handle_missing_data(self) -> None:
        """
        Functions to handle missing data in rainfall radar
        :return:
        """
        # Handling -1 data
        self.df_radar = self.df_radar.replace(
            self.config.radar.radar_rainfall.missing_data_tag,
            self.config.radar.radar_rainfall.replace_missing_tag_with,
        )
        # Now handle completely missing data
        # List of missing data
        missing_time_steps = [
            item
            for item in self.list_of_relevant_files_to_current_run
            if item not in set(self.current_time_steps_on_disk)
        ]

        log.info(
            f"Some values are missing {missing_time_steps}, attempting to fill them using : "
            f"{self.config.radar.radar_rainfall.handle_missing_by}"
        )

        for time_step in missing_time_steps:
            # Find the method to fill the values
            method = self.config.radar.radar_rainfall.handle_missing_by
            if method == "linear":
                # Find the step before and after the current step
                before_after_column_names = (
                    get_before_and_after_indexes_for_a_list_item(
                        list_to_filter=self.list_of_relevant_files_to_current_run,
                        item_to_match=time_step,
                    )
                )
                # Now select the columns and average them
                # remove the CSV tag from the list; when we created the table, we removed the .csv extension
                before_after_column_names = [
                    item[:-4] for item in before_after_column_names
                ]
                self.df_radar[time_step[:-4]] = self.df_radar[
                    before_after_column_names
                ].mean(axis=1)

            elif method[:4] == "fill":
                self.df_radar[time_step[:-4]] = float(method[5:])

    def check_threshold(self) -> None:
        """
        For a given rainfall duration and rainfall depth, check if the criterion is met.
        """
        # First read all thresholds
        criteria = self.config.thresholds.run_criteria
        # Looping through criteria
        df = pd.DataFrame(
            columns=[
                "Duration",
                "Limit",
                "Time steps",
                "Max of Observed Rainfall",
                "Avg of Observed Rainfall",
            ]
        )
        for keys in criteria:
            duration = criteria[keys]["duration_min"]
            threshold = criteria[keys]["threshold"]
            time_steps = int(
                duration
                // self.config.radar.radar_rainfall.time_resolution_of_the_incoming_data
            )

            # Finding the mean and max of all column values
            current_keys = self.list_of_relevant_files_to_current_run[
                -int(time_steps) :
            ]
            current_keys = [item[:-4] for item in current_keys]
            max_rainfall = (self.df_radar[current_keys].sum(axis=1)).max()
            mean_rainfall = (self.df_radar[current_keys].sum(axis=1)).mean()

            df = df.append(
                {
                    "Duration": duration,
                    "Limit": threshold,
                    "Time steps": time_steps,
                    "Max of Observed Rainfall": max_rainfall,
                    "Avg of Observed Rainfall": mean_rainfall,
                },
                ignore_index=True,
            )

        df["Trigger_Model_Run"] = np.where(
            df["Limit"] > df["Max of Observed Rainfall"], False, True
        )
        self.df_criteria = df

        # Send the status
        # Model is triggered if at least one criteria is true. ie. criteria is exceeded at least in one sub-watershed
        if True in set(df["Trigger_Model_Run"]):
            # Threshold exceeded, initiate model run
            log.info(
                "Rainfall threshold exceeded in at least one sub-watershed. Triggering model run"
            )
            return True
        else:
            log.info("Rainfall threshold is not exceeded")
            return False

    def create_dss(self) -> None:
        """
        Function to create the DSS file to model rainfall
        :return:
        """
        # Make sure that Panda dataframe is ready for dss
        number_of_columns_to_sum = self.config.radar.radar_rainfall.col_per_time_step
        # Read the number of rows to sum
        record_length = self.config.radar.radar_rainfall.record_length
        # Modify the record
        _df = sum_consecutive_rows(
            df=self.df_radar,
            number_of_columns_to_sum=number_of_columns_to_sum,
            length_of_the_record_to_filter=record_length,
        )
        # Transposing the data to make sub-basins as columns
        _df = _df.transpose()
        _df = _df[self.config.radar.radar_rainfall.rows_to_keep_in_the_record].copy()
        # # add a random value
        # numeric_cols = [col for col in _df if _df[col].dtype.kind != 'O']
        # _df[numeric_cols] += 1

        # Create the DSS file
        generate_dss_from_pandas(dataframe=_df, config=self.config)

    def run_hec_ras_model(self) -> None:
        """
        Code to run the Hec-Ras Model
        :return:
        """
        # Kill old Hec-Ras
        self.kill_hec_ras()
        # Run the analysis
        # Open ras-controller
        rc = rascontrol.RasController(
            version=self.config.hec_ras.ras_controller.version_string
        )
        # Open the project file
        rc.open_project(self.config.hec_ras.ras_controller.ras_file)
        # run the current plan
        rc.run_current_plan()

    def kill_hec_ras(self, process_name="Ras.exe") -> None:
        """
        Function to kill hec ras if it is already running
        :param process_name: The name of the process to kill
        :return:
        """
        if kill_a_process(process_name=process_name):
            log.info("Killed old Ras.exe")
        else:
            log.warning("Unable to kill Ras.exe")

    def subtract_dsm_from_wse(self) -> None:
        """
        Estimate depth by subtracting the water surface elevation model from the digital surface model
        :return:
        """
        # Get DSM data
        _dsm_file = self.config.spatial_network_data.input.flood_analysis.dsm
        # Get wse data
        _wse_file = self.config.analysis_results.temporary_files.results_WSE_tiff
        #
        _water_over_roads = (
            self.config.analysis_results.temporary_files.results_tiff_water_over_roads
        )
        # Subtract raster
        subtract_two_raster(
            raster_to_subtract_from=_wse_file,
            subtracting_raster=_dsm_file,
            file_path_to_save=_water_over_roads,
        )

    def generate_water_depth_map(self) -> None:
        """
        Generate water depth map for visualization
        :return:
        """
        img = generate_png_file(
            path_to_tiff=self.config.analysis_results.temporary_files.results_tiff_projected,
            color_map=self.config.website.map_legend,
        )

        img.save(self.config.analysis_results.final_results.flood_depth_png)

    def initiate_network(self) -> None:
        """
        Initiate network model
        :return:
        """
        # Get the crs
        self.crs = self.config.spatial_network_data.input.spatial_analysis.crs
        # Read the network
        self.network = NetworkAnalysis(
            path_network=self.config.spatial_network_data.input.network_analysis.path_network,
            crs=self.crs,
        )
        # Read the nodes, unique nodes, and generate network
        self.network.fit()
        # Register the critical facilities
        list_of_critical_facilities = (
            self.config.spatial_network_data.input.spatial_analysis.critical_facilities
        )
        # Loop through each critical facility
        critical_facilities = {}
        for key in list_of_critical_facilities.keys():
            critical_facilities[key] = GeoDataPoints(
                path_geodata=list_of_critical_facilities[key], crs=self.crs
            )
            critical_facilities[key].read_geodata()
            critical_facilities[key].gdf = self.network.get_the_nearest_node_for_points(
                gdf=critical_facilities[key].gdf, label_facility=key
            )

        # The key contains the names of facilities
        self.network.get_initial_distance()

    def perform_mobility_analysis(self) -> None:
        """
        Perform connectivity analysis
        :return:
        """
        self.network.batch_extract_raster(
            list_of_raster_path=self.config.analysis_results.temporary_files.results_tiff_water_over_roads_projected,
            buffer=self.config.spatial_network_data.input.spatial_analysis.buffer_for_flood_depth_extraction,
        )
        # Perform scenario analysis
        self.network.perform_scenaio_analysis(
            link_removal_threshold=self.config.spatial_network_data.input.network_analysis.link_removal_threshold
        )
        # Estimate CL ratio
        self.network.estimate_CL_ratio()
        # summarize results
        self.network.summarize_results_at_polygons(
            path_polygon=self.config.spatial_network_data.input.spatial_analysis.path_census_tract
        )
        # Identify flooded roads
        self.network.identify_flooded_roads(
            wading_height=self.config.spatial_network_data.input.network_analysis.link_removal_threshold,
            encode_no_data_as=0,
        )  # <-- This will make sure flooded roads are encoded as 1
        # Save results
        self.network.save_results(
            road_network_geoData=True,
            results_aggregated_at_polygons=True,
            config=self.config,
        )

    def plot_flooded_roads(self) -> None:
        """
        Plot flooded roads for visualization
        :return:
        """
        # Get the flood condition
        pth_road_condition = f"{self.config.analysis_results.temporary_files.temp_storage_for_analysis}/Network_Condition_results.json"

        # Select only flooded roads
        gdf_roads = gpd.read_file(filename=pth_road_condition)

        # Select flooded roads
        gdf_roads_flooded = gdf_roads[
            gdf_roads["max_water_depth_over_roads_Projected_2"] == 1
        ].copy()
        # gdf_roads_flooded.to_file("flooded_roads.geojson", driver='GeoJSON')

        if gdf_roads_flooded.shape[0] > 0:
            gdf_roads_flooded.to_file(
                self.config.analysis_results.final_results.road_condition,
                driver="GeoJSON",
            )
        else:
            # Paste an empty file results
            copyfile(
                src=self.config.hec_ras.fix_hec_ras_automation_error.empty_road_file,
                dst=self.config.analysis_results.final_results.road_condition,
            )

    def create_validation_plots(self) -> None:
        """
        Function to create validation plot for the website
        :return:
        """
        self.create_stats_for_rainfall_distribution()
        generate_validation_plots_before_run(
            pth_geojson=self.config.radar.dss_file.geodata_for_rainfall,
            item_to_plot=self.config.website.validation_dashboard.rainfall_distribution_map.time_intervals_in_minutes.main,
            data=self.df_validation_dash_maps,
            pth_validation_html=self.config.analysis_results.final_results.validation_dashboard,
            col_name_to_use_as_key=self.config.radar.dss_file.col_name_to_use_as_key,
            config=self.config,
            df_criteria=self.df_criteria,
            df_time_series=self.create_cumulative_rainfall_for_visualization(),
        )

    def create_stats_for_rainfall_distribution(self) -> None:
        """
        Statistics for rainfall distribution
        :return:
        """
        # Get the data
        _config_duration = (
            self.config.website.validation_dashboard.rainfall_distribution_map.time_intervals_in_minutes
        )
        # Get the main time interval
        main_duration = _config_duration["main"]
        # Get all intervals required
        all_durations = {main_duration} | set(_config_duration["tool_tips"])

        # Aggregate the time interval required
        # df = pd.DataFrame(columns=all_durations)
        # Sum the value
        def aggregate_values(time_interval):
            # Number of time steps to aggregate
            time_steps = int(
                time_interval
                // self.config.radar.radar_rainfall.time_resolution_of_the_incoming_data
            )
            # Get the keys
            current_keys = self.list_of_relevant_files_to_current_run[
                -int(time_steps) :
            ]
            # Remove .csv from keys
            current_keys = [item[:-4] for item in current_keys]
            # Sum rainfall
            return self.df_radar[current_keys].sum(axis=1).rename(time_interval)

        # Now append the results
        self.df_validation_dash_maps = pd.concat(
            [aggregate_values(case) for case in all_durations], axis=1
        )
        self.df_validation_dash_maps.drop(
            labels=self.config.radar.radar_rainfall.rows_to_remove_from_record,
            axis=0,
            inplace=True,
        )

    def create_cumulative_rainfall_for_visualization(self) -> None:
        """
        Estimate cumulative rainfall for visualization
        :return:
        """
        # Get the time series
        return self.df_radar.drop(
            labels=self.config.radar.radar_rainfall.rows_to_remove_from_record, axis=0
        )

    def save_last_run_html(self):
        """
        Save the last run html tag
        :return:
        """
        time_last_radar = utc_datetime_to_cst(
            datetime.strptime(self.last_available_data_step[-18:-4], "%Y%m%d%H%M%S")
        ).strftime("%H:%M, %m/%d/%y")

        with open(
            self.config.analysis_results.final_results.last_run_tag_website, "w+"
        ) as file:
            file.write(f"""<font size="2">Last run: {time_last_radar}</font>""")
