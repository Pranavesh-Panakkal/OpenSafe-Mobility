# Title     :
# Created by: Pranavesh Panakkal
# Created on: 9/5/2021
# Version   :
# Notes     :
""""""
from climata.usgs import DailyValueIO, InstantValueIO
import geopandas as gpd
import json
import io
import numpy as np
import pandas as pd
from bokeh.io import output_file, show, output_notebook, export_png
from bokeh.models import (
    ColumnDataSource,
    GeoJSONDataSource,
    LinearColorMapper,
    ColorBar,
)
from bokeh.plotting import figure
from bokeh.palettes import brewer
from bokeh.tile_providers import CARTODBPOSITRON, get_provider

# Add hover tool
from bokeh.models.tools import HoverTool
from jinja2 import Template
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.browser import view
from bokeh.plotting import figure, output_file, save
from pytz import utc, timezone
from datetime import datetime
from bokeh.models import Span, Label
from modules.plot_utils.validation_plot_template import get_jinga_template


def spatial_dist_rainfall(
    pth_geojson, item_to_plot, data, col_name_to_use_as_key, config
):
    # Read shapefile using Geopandas
    gdf = gpd.read_file(pth_geojson)
    # resetting index to make sure that we can merge data on the key
    _cases = data.columns.to_list()
    data.reset_index(inplace=True)
    data = data.rename(columns={"index": col_name_to_use_as_key})
    # Merge values on the left, this will address any data mismatch
    gdf = gdf.merge(data, on=col_name_to_use_as_key, how="left")
    # Now reorder geopandas
    columns = gdf.columns.tolist()
    columns.append(columns.pop(columns.index("geometry")))
    gdf = gdf.reindex(columns, axis=1)
    gdf.columns = [str(item) for item in gdf.columns.tolist()]
    # Replace nan with zeros
    # gdf["rain"] = np.random.rand(gdf.shape[0])
    json_data = json.dumps(json.loads(gdf.to_json()))
    geosource = GeoJSONDataSource(geojson=json_data)
    # Define the palled
    palette = brewer["Blues"][8]
    palette = palette[::-1]
    # vals = gdf[item_to_plot]
    # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    color_mapper = LinearColorMapper(
        palette=palette, low=0, high=10, nan_color="#d9d9d9"
    )
    # Define custom tick labels for color bar.
    tick_labels = {
        "0": "0 in",
        "2": "2 in",
        "4": "4 in",
        "6": "6 in",
        "8": "8 in",
        "10": "10 in",
    }

    color_bar = ColorBar(
        color_mapper=color_mapper,
        label_standoff=8,
        width=500,
        height=20,
        location=(0, 0),
        orientation="horizontal",
        major_label_overrides=tick_labels,
    )
    tools = "reset, pan, box_select, zoom_in, zoom_out,save"

    p = figure(
        title="",
        plot_height=config.website.validation_dashboard.figure_labels.figure_1.fig_height,
        sizing_mode="scale_width",
        plot_width=config.website.validation_dashboard.figure_labels.figure_1.fig_width,
        toolbar_location="right",
        tools=tools,
    )
    # p = figure(title="Cumulative rainfall distribution in the most recent 3-hr", plot_height=600,
    #            plot_width=1000, toolbar_location='right', tools=tools)

    p.patches(
        "xs",
        "ys",
        source=geosource,
        fill_alpha=0.8,
        line_width=0.5,
        line_color="black",
        fill_color={"field": str(item_to_plot), "transform": color_mapper},
    )

    _cases.sort()
    # Dict of tooltips
    tool_tip = [
        (f"Rain in the last {item} min", f"@{str(item)}" + "{0.00}") for item in _cases
    ]

    # hover = HoverTool(tooltips=[('Rain in last 3 hour', f"@{str(item_to_plot)}")])
    hover = HoverTool(tooltips=tool_tip)

    # Specify figure layout.
    p.add_layout(color_bar, "below")

    # Styling the color map
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    # Outline around the image
    # p.outline_line_color = None
    # Turn off tick labels
    p.axis.major_label_text_font_size = "0pt"
    # Turn off tick marks
    p.axis.major_tick_line_color = None  # turn off major ticks
    p.axis[0].ticker.num_minor_ticks = 0  # turn off minor ticks
    p.axis[1].ticker.num_minor_ticks = 0
    p.axis.visible = False

    tile_provider = get_provider(CARTODBPOSITRON)
    p.add_tile(tile_provider)
    p.add_tools(hover)
    return p


def generate_validation_plots_before_run(
    pth_geojson,
    item_to_plot,
    data,
    pth_validation_html,
    col_name_to_use_as_key,
    config,
    df_criteria,
    df_time_series,
):
    TEMPLATE = get_jinga_template(config)
    # Generate the map
    map_rainfall = spatial_dist_rainfall(
        pth_geojson=pth_geojson,
        item_to_plot=item_to_plot,
        data=data,
        col_name_to_use_as_key=col_name_to_use_as_key,
        config=config,
    )
    # Generate the rainfall distribution
    rainfall_dist = rainfall_distribution(df_time_series, config=config)

    # Generate the threshold
    threshold_criteria = create_criteria_plot(df_criteria=df_criteria, config=config)

    # Generate comparison
    gage_1 = plot_gages_usgs(
        USGS_Gage_ID="08074810",
        discription="Brays Bayou at Gessner Dr",
        risk_stage=[54.0, 57.0, 58.0, 59.0],
        config=config,
    )

    # gage_2 = plot_gages_usgs(USGS_Gage_ID='08075110',
    #                          discription="Brays Bayou at MLK Jr Blvd",
    #                          risk_stage=[])

    gage_3 = plot_gages_usgs(
        USGS_Gage_ID="08075000",
        discription="Brays Bayou at Houston",
        risk_stage=[38.0, 41.0, 42.0, 43.0],
        config=config,
    )

    resources = INLINE.render()

    script, div = components(
        {
            "map": map_rainfall,
            "trigger_criteria": threshold_criteria,
            "rainfall_time_series": rainfall_dist,
            "gage_1": gage_1,
            "gage_3": gage_3,
        }
    )

    html = TEMPLATE.render(resources=resources, plot_script=script, plot_div=div)

    with io.open(pth_validation_html, mode="w", encoding="utf-8") as f:
        f.write(html)

    # view(pth_validation_html)


def utc_datetime_to_cst(date_time):
    """
    Converts UTC date time to CST

    :param date_time: date time
    :return: date time in CST
    https://stackoverflow.com/questions/59139859/convert-utc-to-cst
    """
    # Load current date as UTC
    utc_now = utc.localize(date_time)
    eastern = timezone("America/Chicago")

    # Return as CST
    return utc_now.astimezone(eastern)


def convert_label_to_numerical_format(value_in_min):
    if value_in_min < 60:
        return f"{value_in_min}-min"
    elif value_in_min < 1440:
        return f"{value_in_min / 60}-hr"
    else:
        return f"{value_in_min / 1440}-day"


def rainfall_distribution(df_time_series, config):
    # Create x axis
    x = list(df_time_series.columns)
    # Now convert the columns to time
    # string_to_date_time_central = lambda st: utc_datetime_to_cst(datetime.strptime(st[-18:-4], '%Y%m%d%H%M%S'))
    string_to_date_time_central_cst = lambda st: utc_datetime_to_cst(
        datetime.strptime(st[-14:], "%Y%m%d%H%M%S")
    ).strftime("%Y:%m:%d:%H:%M")
    # x = [string_to_date_time_central_cst(item) for item in x]
    # y = df_time_series.sum(axis=0)

    _df_data = pd.DataFrame()
    _df_data["Time"] = [string_to_date_time_central_cst(item) for item in x]
    _df_data["Rain"] = df_time_series.mean(axis=0).reset_index().iloc[:, -1]
    # Here we have to take average rainfall instead of sum. We are not plotting cumulative rainfall
    # _df_data["Rain"] = df_time_series.sum(axis=0).reset_index().iloc[:, -1]

    # Create rolling time window
    list_times = config.website.validation_dashboard.rainfall_time_series_duration
    _time_resolution = config.radar.radar_rainfall.time_resolution_of_the_incoming_data
    # Get the sum windows
    column_labels = ["5-min"] + [
        convert_label_to_numerical_format(duration) for duration in list_times
    ]
    list_window_size = [1] + [
        int(duration // _time_resolution) for duration in list_times
    ]

    # Now do the cumulative sum
    df_new = pd.concat(
        [
            _df_data.rolling(period_length, min_periods=1).sum()
            # [_df_data.rolling(window=pd.api.indexers.FixedForwardWindowIndexer(window_size=period_length),
            #                   min_periods=1).sum()
            for period_length in list_window_size
        ],
        axis=1,
    )
    # df_new.columns = [period_length for period_length in list_window_size]
    # Rename the columns
    df_new.columns = column_labels
    # Add time
    df_new["Time"] = pd.to_datetime(_df_data["Time"], format="%Y:%m:%d:%H:%M")

    # Make time the index
    # df_new.set_index("Time", inplace=True)
    def nearest_value(value):
        if value < 3:
            return 3
        else:
            return value

    # Now plot the different window size
    palette = brewer["Paired"][nearest_value(len(column_labels))]
    # Find the closes value
    # palette = palette[::-1]

    source = ColumnDataSource(df_new)
    p = figure(
        x_axis_type="datetime",
        plot_height=config.website.validation_dashboard.figure_labels.figure_2.fig_height,
        plot_width=config.website.validation_dashboard.figure_labels.figure_2.fig_width,
        sizing_mode="scale_width",
    )
    # p.title.text = 'Click on legend entries to hide the corresponding lines'
    # Plot all cumulative values as lines

    for count, a_col in enumerate(column_labels):
        # p.line(x='Time', y=a_col, line_width=2, source=source, legend_label=column_labels[count])
        if a_col == "5-min":
            p.line(
                x="Time",
                y=a_col,
                line_width=2,
                source=source,
                legend_label=column_labels[count],
                color=palette[count],
            )
            # p.visible = True
        else:
            p.line(
                x="Time",
                y=a_col,
                line_width=2,
                source=source,
                legend_label=column_labels[count],
                color=palette[count],
            )
        # Mute the last one
        # p.muted = True

    p.yaxis.axis_label = "Cumulative Rainfall (inches)"
    p.legend.click_policy = "hide"
    p.legend.location = "left"

    tool_tip = [
        (f"{item} cumulative rainfall", "@{" + item + "}" + "{0.00}")
        for item in column_labels
    ]

    hover = HoverTool(tooltips=tool_tip, mode="mouse")

    p.add_tools(hover)

    return p


def create_criteria_plot(df_criteria, config):
    # Get the durations
    source = ColumnDataSource(df_criteria)

    x = df_criteria["Duration"]

    # Get the thresholds
    # threshold = df_criteria['Limit']

    # Draw the line
    # obs = df_criteria['Max of Observed Rainfall']
    # avg = df_criteria['Avg of Observed Rainfall']

    # create a new plot
    fig = figure(
        tools="pan,box_zoom,wheel_zoom,zoom_in,zoom_out,reset,save",
        title="Observed Rainfall",
        y_range=[-2, 20],
        x_range=[25, 7000],
        x_axis_label="Duration",
        y_axis_label="Precipitation depth (in)",
        plot_height=config.website.validation_dashboard.figure_labels.figure_3.fig_height,
        plot_width=config.website.validation_dashboard.figure_labels.figure_3.fig_width,
        sizing_mode="scale_width",
        x_axis_type="log",
    )

    fig.line(
        x="Duration",
        y="Limit",
        legend_label="5-year recurrence interval rainfall (NOAA Atlas-14)",
        line_width=2,
        line_color="red",
        source=source,
    )

    fig.circle(
        x="Duration",
        y="Max of Observed Rainfall",
        legend_label="Maximum observed rainfall in any sub-region of the study area",
        line_width=1,
        fill_color="white",
        size=8,
        source=source,
    )

    fig.circle(
        x="Duration",
        y="Avg of Observed Rainfall",
        legend_label="Average rainfall in the study area",
        line_width=1,
        fill_color="blue",
        size=8,
        source=source,
    )

    fig.xaxis.ticker = x

    fig.xaxis.major_label_overrides = {
        30: "30-min",
        60: "60-min",
        120: "2-hr",
        180: "3-hr",
        360: "6-hr",
        720: "12-hr",
        1440: "1-day",
        2880: "2-day",
        4320: "3-day",
        5760: "4-day",
    }

    fig.xaxis.major_label_orientation = "vertical"

    tool_tip = [
        ("5-year NOAA Atlas-14 threshold", "@Limit{0.00}"),
        ("Maximum observed rainfall", r"@{Max of Observed Rainfall}{0.00}"),
        ("Average rainfall", r"@{Avg of Observed Rainfall}{0.00}"),
    ]

    # hover = HoverTool(tooltips=[('Rain in last 3 hour', f"@{str(item_to_plot)}")])
    hover = HoverTool(tooltips=tool_tip)

    fig.add_tools(hover)

    return fig

    # output_file("Threshold.html")
    # save(fig)


class stream_gage_reading:
    def __init__(self, USGS_Gage_ID: str, duration_of_record: int = 10) -> None:
        self.station_id = USGS_Gage_ID
        self.record_length = duration_of_record
        self.param_id = (
            "00065"  # 00065 Gage height, 00060 Discharge; 00045 Precipitation
        )
        self.dates = None
        self.flow = None
        self.site = None

        self.get()

    def get(self):
        datelist = pd.date_range(
            end=pd.datetime.today(), periods=self.record_length
        ).tolist()
        data = InstantValueIO(
            start_date=datelist[0],
            end_date=datelist[-1],
            station=self.station_id,
            parameter=self.param_id,
        )
        for series in data:
            self.flow = [r[1] for r in series.data]
            self.dates = [r[0] for r in series.data]
            self.site = series.site_name

        return self.flow, self.dates


def plot_gages_usgs(
    USGS_Gage_ID: str = "08074810",
    discription="Brays Bayou at Gessner Dr",
    risk_stage=[54.0, 57.0, 58.0, 59.0],
    config=None,
):
    """Gage data"""
    gage = stream_gage_reading(USGS_Gage_ID=USGS_Gage_ID)

    p = figure(
        x_axis_type="datetime",
        plot_height=config.website.validation_dashboard.figure_labels.figure_4.fig_height,
        plot_width=config.website.validation_dashboard.figure_labels.figure_4.fig_width,
        y_range=[min(gage.flow) - 3, risk_stage[-1] + 3],
        x_axis_label="Time",
        y_axis_label="Gage height (feet)",
        sizing_mode="scale_width",
    )
    p.title.text = f"Gage: {USGS_Gage_ID} | {discription}"

    # Horizontal line
    if len(risk_stage) > 0:
        action_stage = Span(
            location=risk_stage[0],
            dimension="width",
            line_color="grey",
            line_dash="dashed",
            line_width=3,
        )
        action_stage_label = Label(
            x=min(gage.dates),
            y=risk_stage[0],
            text="Action stage",
            text_font_size="8pt",
        )
        p.add_layout(action_stage)
        p.add_layout(action_stage_label)

        minor_flood_stage = Span(
            location=risk_stage[1],
            dimension="width",
            line_color="orange",
            line_dash="dashed",
            line_width=3,
        )
        minor_flood_stage_label = Label(
            x=min(gage.dates),
            y=risk_stage[1],
            text="Minor flood stage",
            text_font_size="8pt",
        )
        p.add_layout(minor_flood_stage)
        p.add_layout(minor_flood_stage_label)

        moderate_flood_stage = Span(
            location=risk_stage[2],
            dimension="width",
            line_color="red",
            line_dash="dashed",
            line_width=3,
        )
        moderate_flood_stage_label = Label(
            x=min(gage.dates),
            y=risk_stage[2],
            text="Moderate flood stage",
            text_font_size="8pt",
        )
        p.add_layout(moderate_flood_stage)
        p.add_layout(moderate_flood_stage_label)

        major_flood_stage = Span(
            location=risk_stage[3], dimension="width", line_color="red", line_width=3
        )
        major_flood_stage_label = Label(
            x=min(gage.dates),
            y=risk_stage[3],
            text="Major flood stage",
            text_font_size="8pt",
        )
        p.add_layout(major_flood_stage)
        p.add_layout(major_flood_stage_label)

    df = pd.DataFrame(columns=["Time", "Gage"])
    df["Time"] = gage.dates
    df["Gage"] = gage.flow

    source = ColumnDataSource(df)
    p.line(x="Time", y="Gage", line_width=2, source=source)
    tool_tip = [("Gage height in feet", "@{Gage}{0.00}")]
    hover = HoverTool(tooltips=tool_tip, mode="mouse")
    p.add_tools(hover)
    return p
