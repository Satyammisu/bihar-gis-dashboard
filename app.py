import json
import math
import pandas as pd

from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# APP INITIALIZATION
# =========================================================

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY]
)

server = app.server

# =========================================================
# LOAD BIHAR DISTRICT BOUNDARY
# =========================================================

with open(
    "bihar_district_boundary.geojson",
    "r",
    encoding="utf-8"
) as f:

    district_geojson = json.load(f)

# =========================================================
# SAFE CSV LOADER
# =========================================================

def load_csv(file_name):

    df = pd.read_csv(
        file_name,
        encoding="utf-8"
    )

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df

# =========================================================
# LOAD DATA
# =========================================================

cold_df = load_csv("cold_storage.csv")
rail_df = load_csv("railway_stations.csv")
airport_df = load_csv("airport.csv")
mandi_df = load_csv("mandis.csv")

# =========================================================
# STANDARDIZE COLUMNS
# =========================================================

def standardize_columns(df):

    column_mapping = {}

    for col in df.columns:

        col_lower = col.lower().strip()

        # =================================================
        # NAME
        # =================================================

        if "station" in col_lower:
            column_mapping[col] = "Name"

        elif "name" in col_lower:
            column_mapping[col] = "Name"

        # =================================================
        # DISTRICT
        # =================================================

        elif "district" in col_lower:
            column_mapping[col] = "District"

        # =================================================
        # CAPACITY
        # =================================================

        elif (
            "capacity" in col_lower
            or "cap" in col_lower
            or "storage" in col_lower
        ):
            column_mapping[col] = "Capacity"

        # =================================================
        # LATITUDE
        # =================================================

        elif "lat" in col_lower:
            column_mapping[col] = "Latitude"

        # =================================================
        # LONGITUDE
        # =================================================

        elif "lon" in col_lower:
            column_mapping[col] = "Longitude"

    # =====================================================
    # RENAME
    # =====================================================

    df = df.rename(columns=column_mapping)

    # =====================================================
    # REQUIRED COLUMNS
    # =====================================================

    required_cols = [
        "Name",
        "District",
        "Latitude",
        "Longitude"
    ]

    for col in required_cols:

        if col not in df.columns:
            df[col] = None

    # =====================================================
    # CAPACITY COLUMN
    # =====================================================

    if "Capacity" not in df.columns:
        df["Capacity"] = 0

    # =====================================================
    # CLEAN DATA
    # =====================================================

    df["Name"] = df["Name"].fillna("Unknown")
    df["District"] = df["District"].fillna("Unknown")

    # =====================================================
    # LATITUDE
    # =====================================================

    df["Latitude"] = pd.to_numeric(
        df["Latitude"],
        errors="coerce"
    )

    # =====================================================
    # LONGITUDE
    # =====================================================

    df["Longitude"] = pd.to_numeric(
        df["Longitude"],
        errors="coerce"
    )

    # =====================================================
    # CAPACITY CLEANING
    # =====================================================

    df["Capacity"] = (
        df["Capacity"]
        .astype(str)
        .str.replace(",", "")
    )

    df["Capacity"] = pd.to_numeric(
        df["Capacity"],
        errors="coerce"
    ).fillna(0)

    # =====================================================
    # REMOVE INVALID COORDINATES
    # =====================================================

    df = df.dropna(
        subset=[
            "Latitude",
            "Longitude"
        ]
    )

    return df

# =========================================================
# APPLY STANDARDIZATION
# =========================================================

cold_df = standardize_columns(cold_df)
rail_df = standardize_columns(rail_df)
airport_df = standardize_columns(airport_df)
mandi_df = standardize_columns(mandi_df)

# =========================================================
# KPI VALUES
# =========================================================

total_cold = len(cold_df)
total_rail = len(rail_df)
total_airport = len(airport_df)
total_mandi = len(mandi_df)

# =========================================================
# HAVERSINE FUNCTION
# =========================================================

def haversine(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(math.radians(lat1))
        *
        math.cos(math.radians(lat2))
        *
        math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c

# =========================================================
# CREATE MAP
# =========================================================

def create_map(map_style):

    fig = go.Figure()

    # =====================================================
    # DISTRICT BOUNDARY
    # =====================================================

    fig.add_trace(

        go.Choroplethmapbox(

            geojson=district_geojson,

            locations=[
                feature["properties"].get(
                    "district",
                    str(i)
                )

                for i, feature in enumerate(
                    district_geojson["features"]
                )
            ],

            z=[
                1
            ] * len(
                district_geojson["features"]
            ),

            colorscale=[
                [0, "rgba(0,0,0,0)"],
                [1, "rgba(0,0,0,0)"]
            ],

            marker_line_width=1,

            marker_line_color="black",

            showscale=False,

            hoverinfo="skip"

        )

    )

    # =====================================================
    # COLD STORAGE
    # =====================================================

    fig.add_trace(

        go.Scattermapbox(

            lat=cold_df["Latitude"],

            lon=cold_df["Longitude"],

            mode="markers",

            marker=dict(
                size=9,
                color="#1976D2"
            ),

            text=cold_df["Name"],

            name="Cold Storage"

        )

    )

    # =====================================================
    # RAILWAY STATIONS
    # =====================================================

    fig.add_trace(

        go.Scattermapbox(

            lat=rail_df["Latitude"],

            lon=rail_df["Longitude"],

            mode="markers",

            marker=dict(
                size=11,
                color="red"
            ),

            text=rail_df["Name"],

            name="Railway Station"

        )

    )

    # =====================================================
    # AIRPORTS
    # =====================================================

    fig.add_trace(

        go.Scattermapbox(

            lat=airport_df["Latitude"],

            lon=airport_df["Longitude"],

            mode="markers",

            marker=dict(
                size=13,
                color="green"
            ),

            text=airport_df["Name"],

            name="Airport"

        )

    )

    # =====================================================
    # MANDIS
    # =====================================================

    fig.add_trace(

        go.Scattermapbox(

            lat=mandi_df["Latitude"],

            lon=mandi_df["Longitude"],

            mode="markers",

            marker=dict(
                size=10,
                color="orange"
            ),

            text=mandi_df["Name"],

            name="Mandis"

        )

    )

    # =====================================================
    # MAP LAYOUT
    # =====================================================

    fig.update_layout(

        mapbox_style=map_style,

        mapbox_zoom=6,

        mapbox_center={

            "lat": 25.7,
            "lon": 85.3

        },

        height=800,

        margin={
            "r": 0,
            "t": 0,
            "l": 0,
            "b": 0
        },

        legend=dict(
            bgcolor="white"
        )

    )

    return fig

# =========================================================
# DISTRICT ANALYTICS
# =========================================================

district_chart = px.bar(

    cold_df.groupby("District")
    .size()
    .reset_index(name="Cold Storages"),

    x="District",

    y="Cold Storages",

    title="District Wise Cold Storages",

    color="Cold Storages",

    template="plotly_white"

)

district_chart.update_layout(
    height=450
)

# =========================================================
# APP LAYOUT
# =========================================================

app.layout = dbc.Container(

    [

        # =================================================
        # HEADER
        # =================================================

        dbc.Row(

            dbc.Col(

                html.Div(

                    [

                        html.H1(

                            "BIHAR GIS INFRASTRUCTURE DASHBOARD",

                            style={

                                "textAlign": "center",

                                "color": "white",

                                "fontWeight": "bold",

                                "padding": "15px"

                            }

                        )

                    ],

                    style={

                        "background": "#0D47A1",

                        "borderRadius": "10px",

                        "marginTop": "10px"

                    }

                )

            )

        ),

        # =================================================
        # KPI CARDS
        # =================================================

        dbc.Row(

            [

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H2(
                                    total_cold,
                                    className="text-primary"
                                ),

                                html.H5(
                                    "Cold Storages"
                                )

                            ]

                        ),

                        className="shadow-sm"

                    ),

                    md=3

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H2(
                                    total_rail,
                                    className="text-danger"
                                ),

                                html.H5(
                                    "Railway Stations"
                                )

                            ]

                        ),

                        className="shadow-sm"

                    ),

                    md=3

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H2(
                                    total_airport,
                                    className="text-success"
                                ),

                                html.H5(
                                    "Airports"
                                )

                            ]

                        ),

                        className="shadow-sm"

                    ),

                    md=3

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H2(
                                    total_mandi,
                                    className="text-warning"
                                ),

                                html.H5(
                                    "Mandis"
                                )

                            ]

                        ),

                        className="shadow-sm"

                    ),

                    md=3

                )

            ],

            className="mt-4"

        ),

        # =================================================
        # SIDEBAR + MAP
        # =================================================

        dbc.Row(

            [

                # =============================================
                # SIDEBAR
                # =============================================

                dbc.Col(

                    [

                        dbc.Card(

                            dbc.CardBody(

                                [

                                    html.H4(

                                        "Railway Buffer Analysis",

                                        className="mb-4"

                                    ),

                                    # =====================
                                    # RAILWAY DROPDOWN
                                    # =====================

                                    html.Label(
                                        "Select Railway Station"
                                    ),

                                    dcc.Dropdown(

                                        id="rail-dropdown",

                                        options=[

                                            {

                                                "label": i,

                                                "value": i

                                            }

                                            for i in sorted(
                                                rail_df["Name"]
                                                .dropna()
                                                .unique()
                                            )

                                        ],

                                        placeholder=
                                        "Choose Railway Station",

                                        searchable=True

                                    ),

                                    html.Br(),

                                    # =====================
                                    # BUFFER DROPDOWN
                                    # =====================

                                    html.Label(
                                        "Buffer Distance"
                                    ),

                                    dcc.Dropdown(

                                        id="buffer-dropdown",

                                        options=[

                                            {
                                                "label": "5 KM",
                                                "value": 5
                                            },

                                            {
                                                "label": "10 KM",
                                                "value": 10
                                            },

                                            {
                                                "label": "25 KM",
                                                "value": 25
                                            },

                                            {
                                                "label": "50 KM",
                                                "value": 50
                                            }

                                        ],

                                        value=10

                                    ),

                                    html.Br(),

                                    # =====================
                                    # DISTRICT DROPDOWN
                                    # =====================

                                    html.Label(
                                        "Search District"
                                    ),

                                    dcc.Dropdown(

                                        id="district-dropdown",

                                        options=[

                                            {

                                                "label": i,

                                                "value": i

                                            }

                                            for i in sorted(
                                                cold_df["District"]
                                                .dropna()
                                                .unique()
                                            )

                                        ],

                                        placeholder=
                                        "Choose District"

                                    ),

                                    html.Br(),

                                    # =====================
                                    # MAP STYLE
                                    # =====================

                                    html.Label(
                                        "Map Style"
                                    ),

                                    dcc.Dropdown(

                                        id="map-style",

                                        options=[

                                            {
                                                "label": "Street Map",
                                                "value": "carto-positron"
                                            },

                                            {
                                                "label": "Satellite",
                                                "value": "satellite-streets"
                                            },

                                            {
                                                "label": "Dark Mode",
                                                "value": "carto-darkmatter"
                                            },

                                            {
                                                "label": "OpenStreetMap",
                                                "value": "open-street-map"
                                            }

                                        ],

                                        value="carto-positron",

                                        clearable=False

                                    ),

                                    html.Hr(),

                                    html.Div(
                                        id="summary-box"
                                    )

                                ]

                            ),

                            className="shadow"

                        )

                    ],

                    md=3

                ),

                # =============================================
                # MAP
                # =============================================

                dbc.Col(

                    [

                        dcc.Graph(

                            id="gis-map",

                            figure=create_map(
                                "carto-positron"
                            ),

                            config={
                                "displayModeBar": True
                            }

                        )

                    ],

                    md=9

                )

            ],

            className="mt-4"

        ),

        # =================================================
        # TABLE
        # =================================================

        dbc.Row(

            [

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H4(
                                    "Nearby Cold Storage Details"
                                ),

                                dash_table.DataTable(

                                    id="cold-table",

                                    columns=[

                                        {
                                            "name": "District",
                                            "id": "District"
                                        },

                                        {
                                            "name":
                                            "Cold Storage Name",

                                            "id": "Name"
                                        },

                                        {
                                            "name": "Capacity",
                                            "id": "Capacity"
                                        },

                                        {
                                            "name": "Latitude",
                                            "id": "Latitude"
                                        },

                                        {
                                            "name": "Longitude",
                                            "id": "Longitude"
                                        },

                                        {
                                            "name": "Distance (KM)",
                                            "id": "Distance"
                                        }

                                    ],

                                    data=[],

                                    page_size=10,

                                    style_table={
                                        "overflowX": "auto"
                                    },

                                    style_header={

                                        "backgroundColor": "#0D47A1",

                                        "color": "white",

                                        "fontWeight": "bold"

                                    },

                                    style_cell={

                                        "textAlign": "left",

                                        "padding": "10px"

                                    }

                                )

                            ]

                        ),

                        className="shadow"

                    )

                )

            ],

            className="mt-4"

        ),

        # =================================================
        # ANALYTICS CHART
        # =================================================

        dbc.Row(

            [

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                dcc.Graph(
                                    figure=district_chart
                                )

                            ]

                        ),

                        className="shadow"

                    )

                )

            ],

            className="mt-4 mb-5"

        )

    ],

    fluid=True,

    style={
        "backgroundColor": "#F4F6F9"
    }

)

# =========================================================
# CALLBACK
# =========================================================

@app.callback(

    [

        Output("gis-map", "figure"),

        Output("cold-table", "data"),

        Output("summary-box", "children")

    ],

    [

        Input("rail-dropdown", "value"),

        Input("buffer-dropdown", "value"),

        Input("district-dropdown", "value"),

        Input("map-style", "value")

    ]

)

def update_map(

    selected_station,

    buffer_km,

    selected_district,

    map_style

):

    fig = create_map(map_style)

    filtered_cold_df = cold_df.copy()

    # =====================================================
    # DISTRICT FILTER
    # =====================================================

    if selected_district:

        filtered_cold_df = filtered_cold_df[

            filtered_cold_df["District"]
            == selected_district

        ]

    # =====================================================
    # NO STATION SELECTED
    # =====================================================

    if selected_station is None:

        return (

            fig,

            [],

            html.Div(

                [

                    html.H5(
                        "No Railway Station Selected"
                    )

                ]

            )

        )

    # =====================================================
    # GET STATION
    # =====================================================

    station = rail_df[
        rail_df["Name"] == selected_station
    ]

    if station.empty:

        return fig, [], "No station found"

    station_lat = station.iloc[0]["Latitude"]

    station_lon = station.iloc[0]["Longitude"]

    # =====================================================
    # HIGHLIGHT SELECTED STATION
    # =====================================================

    fig.add_trace(

        go.Scattermapbox(

            lat=[station_lat],

            lon=[station_lon],

            mode="markers",

            marker=dict(
                size=18,
                color="yellow"
            ),

            text=[selected_station],

            name="Selected Station"

        )

    )

    # =====================================================
    # BUFFER CIRCLE
    # =====================================================

    theta = [

        i * (360 / 100)

        for i in range(101)

    ]

    circle_lat = []
    circle_lon = []

    for angle in theta:

        dx = (
            buffer_km / 111
        ) * math.cos(
            math.radians(angle)
        )

        dy = (
            buffer_km / 111
        ) * math.sin(
            math.radians(angle)
        )

        circle_lat.append(
            station_lat + dy
        )

        circle_lon.append(
            station_lon + dx
        )

    fig.add_trace(

        go.Scattermapbox(

            lat=circle_lat,

            lon=circle_lon,

            mode="lines",

            fill="toself",

            fillcolor="rgba(255,0,0,0.15)",

            line=dict(
                color="red",
                width=2
            ),

            name=f"{buffer_km} KM Buffer"

        )

    )

    # =====================================================
    # FIND NEARBY COLD STORAGE
    # =====================================================

    nearby_rows = []

    nearby_lat = []

    nearby_lon = []

    nearby_name = []

    for _, row in filtered_cold_df.iterrows():

        dist = haversine(

            station_lat,

            station_lon,

            row["Latitude"],

            row["Longitude"]

        )

        if dist <= buffer_km:

            nearby_rows.append(

                {

                    "District": row["District"],

                    "Name": row["Name"],

                    "Capacity": row["Capacity"],

                    "Latitude": round(
                        row["Latitude"],
                        4
                    ),

                    "Longitude": round(
                        row["Longitude"],
                        4
                    ),

                    "Distance": round(
                        dist,
                        2
                    )

                }

            )

            nearby_lat.append(
                row["Latitude"]
            )

            nearby_lon.append(
                row["Longitude"]
            )

            nearby_name.append(
                row["Name"]
            )

    # =====================================================
    # PLOT NEARBY STORAGE
    # =====================================================

    if len(nearby_lat) > 0:

        fig.add_trace(

            go.Scattermapbox(

                lat=nearby_lat,

                lon=nearby_lon,

                mode="markers",

                marker=dict(
                    size=14,
                    color="cyan"
                ),

                text=nearby_name,

                name="Nearby Cold Storage"

            )

        )

    # =====================================================
    # MAP CENTER
    # =====================================================

    fig.update_layout(

        mapbox_zoom=7,

        mapbox_center={

            "lat": station_lat,

            "lon": station_lon

        }

    )

    # =====================================================
    # SUMMARY
    # =====================================================

    total_capacity = sum(

        row["Capacity"]

        for row in nearby_rows

    )

    summary = html.Div(

        [

            html.H5(
                f"Selected: {selected_station}"
            ),

            html.P(
                f"Buffer Distance: {buffer_km} KM"
            ),

            html.P(
                f"Nearby Cold Storages: {len(nearby_rows)}"
            ),

            html.P(
                f"Total Capacity: {total_capacity}"
            )

        ]

    )

    return fig, nearby_rows, summary

# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run_server(

        debug=False,

        host="0.0.0.0",

        port=10000

    )
