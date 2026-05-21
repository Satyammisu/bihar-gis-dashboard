import os
import json
import math
import pandas as pd
import plotly.express as px

from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output

import dash_bootstrap_components as dbc

import dash_leaflet as dl
import dash_leaflet.express as dlx

# =========================================================
# APP INITIALIZATION
# =========================================================

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

server = app.server

# =========================================================
# LOAD CSV
# =========================================================

def load_csv(file_name):

    if not os.path.exists(file_name):

        print(f"Missing file: {file_name}")

        return pd.DataFrame()

    df = pd.read_csv(file_name)

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
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

        # ==========================================
        # NAME
        # ==========================================

        if (
            "station" in col_lower
            or "name" in col_lower
        ):

            column_mapping[col] = "Name"

        # ==========================================
        # DISTRICT
        # ==========================================

        elif "district" in col_lower:

            column_mapping[col] = "District"

        # ==========================================
        # LATITUDE
        # ==========================================

        elif "lat" in col_lower:

            column_mapping[col] = "Latitude"

        # ==========================================
        # LONGITUDE
        # ==========================================

        elif "lon" in col_lower:

            column_mapping[col] = "Longitude"

        # ==========================================
        # CAPACITY
        # ==========================================

        elif (
            "capacity" in col_lower
            or "cap" in col_lower
            or "mt" in col_lower
            or "ton" in col_lower
            or "storage" in col_lower
        ):

            column_mapping[col] = "Capacity"

    df = df.rename(columns=column_mapping)

    required_cols = [
        "Name",
        "District",
        "Latitude",
        "Longitude"
    ]

    for col in required_cols:

        if col not in df.columns:
            df[col] = None

    if "Capacity" not in df.columns:
        df["Capacity"] = 0

    df["Name"] = df["Name"].fillna("Unknown")

    df["District"] = df["District"].fillna("Unknown")

    # ==========================================
    # CLEAN NUMBERS
    # ==========================================

    df["Latitude"] = pd.to_numeric(
        df["Latitude"],
        errors="coerce"
    )

    df["Longitude"] = pd.to_numeric(
        df["Longitude"],
        errors="coerce"
    )

    df["Capacity"] = (
        df["Capacity"]
        .astype(str)
        .str.replace(",", "")
        .str.replace("MT", "")
        .str.replace("mt", "")
        .str.strip()
    )

    df["Capacity"] = pd.to_numeric(
        df["Capacity"],
        errors="coerce"
    ).fillna(0)

    df = df.dropna(
        subset=["Latitude", "Longitude"]
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
# LOAD BIHAR DISTRICT BOUNDARY
# =========================================================

district_geojson = {}

if os.path.exists("bihar_district_boundary.geojson"):

    with open(
        "bihar_district_boundary.geojson",
        "r",
        encoding="utf-8"
    ) as f:

        district_geojson = json.load(f)

# =========================================================
# HAVERSINE DISTANCE
# =========================================================

def haversine(lat1, lon1, lat2, lon2):

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
# KPI VALUES
# =========================================================

TOTAL_COLD = len(cold_df)
TOTAL_RAIL = len(rail_df)
TOTAL_AIRPORT = len(airport_df)
TOTAL_MANDI = len(mandi_df)

# =========================================================
# DROPDOWN OPTIONS
# =========================================================

rail_options = [
    {
        "label": row["Name"],
        "value": row["Name"]
    }
    for _, row in rail_df.iterrows()
]

district_options = [
    {
        "label": d,
        "value": d
    }
    for d in sorted(
        cold_df["District"].dropna().unique()
    )
]

# =========================================================
# CREATE MARKERS
# =========================================================

def create_markers():

    markers = []

    # ==========================================
    # COLD STORAGE
    # ==========================================

    for _, row in cold_df.iterrows():

        popup = dbc.Card(

            [

                dbc.CardBody(

                    [

                        html.H5(
                            "Cold Storage",
                            style={
                                "fontWeight": "bold",
                                "color": "#0D47A1"
                            }
                        ),

                        html.Hr(),

                        html.P(
                            f"District: {row['District']}"
                        ),

                        html.P(
                            f"Name: {row['Name']}"
                        ),

                        html.P(
                            f"Capacity: {row['Capacity']} MT"
                        ),

                        html.P(
                            f"Latitude: {row['Latitude']}"
                        ),

                        html.P(
                            f"Longitude: {row['Longitude']}"
                        ),

                        html.Br(),

                        html.A(

                            dbc.Button(

                                "Navigate",

                                color="primary",

                                style={
                                    "width": "100%"
                                }

                            ),

                            href=f"https://www.google.com/maps?q={row['Latitude']},{row['Longitude']}",

                            target="_blank"

                        )

                    ]

                )

            ],

            style={
                "width": "250px"
            }

        )

        markers.append(

            dl.CircleMarker(

                center=(
                    row["Latitude"],
                    row["Longitude"]
                ),

                radius=7,

                color="white",

                weight=1,

                fillColor="blue",

                fillOpacity=1,

                children=[
                    dl.Popup(popup)
                ]

            )

        )

    # ==========================================
    # RAILWAY
    # ==========================================

    for _, row in rail_df.iterrows():

        markers.append(

            dl.CircleMarker(

                center=(
                    row["Latitude"],
                    row["Longitude"]
                ),

                radius=7,

                color="white",

                weight=1,

                fillColor="red",

                fillOpacity=1,

                children=[
                    dl.Tooltip(row["Name"])
                ]

            )

        )

    # ==========================================
    # AIRPORT
    # ==========================================

    for _, row in airport_df.iterrows():

        markers.append(

            dl.CircleMarker(

                center=(
                    row["Latitude"],
                    row["Longitude"]
                ),

                radius=7,

                color="white",

                weight=1,

                fillColor="green",

                fillOpacity=1,

                children=[
                    dl.Tooltip(row["Name"])
                ]

            )

        )

    # ==========================================
    # MANDI
    # ==========================================

    for _, row in mandi_df.iterrows():

        markers.append(

            dl.CircleMarker(

                center=(
                    row["Latitude"],
                    row["Longitude"]
                ),

                radius=7,

                color="white",

                weight=1,

                fillColor="orange",

                fillOpacity=1,

                children=[
                    dl.Tooltip(row["Name"])
                ]

            )

        )

    return markers

# =========================================================
# MAP
# =========================================================

base_map = dl.Map(

    center=[25.6, 85.1],

    zoom=7,

    children=[

        dl.LayersControl(

            [

                dl.BaseLayer(

                    dl.TileLayer(),

                    name="OpenStreetMap",

                    checked=True

                ),

                dl.BaseLayer(

                    dl.TileLayer(

                        url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
                    ),

                    name="Topographic"

                )

            ]

        ),

        dl.GeoJSON(

            data=district_geojson,

            options=dict(
                style=dict(
                    color="black",
                    weight=2,
                    fillOpacity=0
                )
            )

        ),

        dl.LayerGroup(
            create_markers(),
            id="marker-layer"
        ),

        dl.LayerGroup(
            id="buffer-layer"
        )

    ],

    style={
        "width": "100%",
        "height": "800px"
    }

)

# =========================================================
# APP LAYOUT
# =========================================================

app.layout = dbc.Container(

    [

        # ==========================================
        # HEADER
        # ==========================================

        dbc.Row(

            [

                dbc.Col(

                    html.Div(

                        [

                            html.H1(

                                "BIHAR GIS INFRASTRUCTURE DASHBOARD",

                                style={

                                    "textAlign": "center",

                                    "color": "white",

                                    "fontWeight": "bold",

                                    "padding": "20px"

                                }

                            )

                        ],

                        style={

                            "backgroundColor": "#0D47A1",

                            "borderRadius": "10px"

                        }

                    )

                )

            ],

            className="mt-3 mb-4"

        ),

        # ==========================================
        # KPI CARDS
        # ==========================================

        dbc.Row(

            [

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H1(
                                    TOTAL_COLD,
                                    style={"color": "#1D3557"}
                                ),

                                html.H4(
                                    "Cold Storages"
                                )

                            ]

                        )

                    ),

                    width=3

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H1(
                                    TOTAL_RAIL,
                                    style={"color": "#E74C3C"}
                                ),

                                html.H4(
                                    "Railway Stations"
                                )

                            ]

                        )

                    ),

                    width=3

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H1(
                                    TOTAL_AIRPORT,
                                    style={"color": "#1ABC9C"}
                                ),

                                html.H4(
                                    "Airports"
                                )

                            ]

                        )

                    ),

                    width=3

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H1(
                                    TOTAL_MANDI,
                                    style={"color": "#F39C12"}
                                ),

                                html.H4(
                                    "Mandis"
                                )

                            ]

                        )

                    ),

                    width=3

                )

            ],

            className="mb-4"

        ),

        # ==========================================
        # SIDEBAR + MAP
        # ==========================================

        dbc.Row(

            [

                # ==================================
                # SIDEBAR
                # ==================================

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H2(
                                    "Railway Station Buffer"
                                ),

                                html.Br(),

                                dcc.Dropdown(

                                    id="station-dropdown",

                                    options=rail_options,

                                    value="Patna Junction",

                                    clearable=False

                                ),

                                html.Br(),

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

                                    value=10,

                                    clearable=False

                                ),

                                html.Br(),

                                dcc.Dropdown(

                                    id="district-dropdown",

                                    options=district_options,

                                    value="Patna"

                                ),

                                html.Hr(),

                                html.H4(
                                    id="selected-station"
                                ),

                                html.H5(
                                    id="buffer-distance"
                                ),

                                html.H5(
                                    id="cold-count"
                                ),

                                html.H5(
                                    id="capacity-total"
                                )

                            ]

                        )

                    ),

                    width=3

                ),

                # ==================================
                # MAP
                # ==================================

                dbc.Col(

                    base_map,

                    width=9

                )

            ],

            className="mb-4"

        ),

        # ==========================================
        # TABLE
        # ==========================================

        dbc.Row(

            [

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H2(
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
                                            "name": "Cold Storage Name",
                                            "id": "Name"
                                        },

                                        {
                                            "name": "Capacity",
                                            "id": "Capacity"
                                        },

                                        {
                                            "name": "Distance (KM)",
                                            "id": "Distance"
                                        },

                                        {
                                            "name": "Latitude",
                                            "id": "Latitude"
                                        },

                                        {
                                            "name": "Longitude",
                                            "id": "Longitude"
                                        }

                                    ],

                                    data=[],

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

                                        "padding": "10px",

                                        "fontFamily": "monospace"

                                    }

                                )

                            ]

                        )

                    )

                )

            ],

            className="mb-4"

        ),

        # ==========================================
        # DISTRICT CHART
        # ==========================================

        dbc.Row(

            [

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H4(
                                    "District Wise Cold Storages"
                                ),

                                dcc.Graph(

                                    figure=px.bar(

                                        cold_df.groupby(
                                            "District"
                                        ).size().reset_index(
                                            name="Cold Storages"
                                        ),

                                        x="District",

                                        y="Cold Storages",

                                        color="Cold Storages",

                                        title="District Wise Cold Storages",

                                        height=500

                                    )

                                )

                            ]

                        )

                    )

                )

            ],

            className="mb-5"

        )

    ],

    fluid=True,

    style={
        "backgroundColor": "#ECECEC"
    }

)

# =========================================================
# CALLBACK
# =========================================================

@app.callback(

    [

        Output("buffer-layer", "children"),

        Output("selected-station", "children"),

        Output("buffer-distance", "children"),

        Output("cold-count", "children"),

        Output("capacity-total", "children"),

        Output("cold-table", "data")

    ],

    [

        Input("station-dropdown", "value"),

        Input("buffer-dropdown", "value")

    ]

)

def update_buffer(selected_station, buffer_km):

    if selected_station is None:

        return [], "", "", "", "", []

    station = rail_df[
        rail_df["Name"] == selected_station
    ]

    if station.empty:

        return [], "", "", "", "", []

    station_lat = station.iloc[0]["Latitude"]
    station_lon = station.iloc[0]["Longitude"]

    nearby_rows = []

    nearby_markers = []

    total_capacity = 0

    # ==========================================
    # BUFFER CIRCLE
    # ==========================================

    circle = dl.Circle(

        center=(station_lat, station_lon),

        radius=buffer_km * 1000,

        color="green",

        fillColor="lightgreen",

        fillOpacity=0.3

    )

    # ==========================================
    # SELECTED STATION
    # ==========================================

    station_marker = dl.Marker(

        position=(station_lat, station_lon),

        children=[
            dl.Tooltip(selected_station)
        ]

    )

    # ==========================================
    # NEARBY COLD STORAGE
    # ==========================================

    for _, row in cold_df.iterrows():

        dist = haversine(

            station_lat,
            station_lon,

            row["Latitude"],
            row["Longitude"]

        )

        if dist <= buffer_km:

            total_capacity += row["Capacity"]

            nearby_rows.append(

                {

                    "District": row["District"],

                    "Name": row["Name"],

                    "Capacity": row["Capacity"],

                    "Distance": round(dist, 2),

                    "Latitude": row["Latitude"],

                    "Longitude": row["Longitude"]

                }

            )

            nearby_markers.append(

                dl.CircleMarker(

                    center=(
                        row["Latitude"],
                        row["Longitude"]
                    ),

                    radius=10,

                    color="cyan",

                    fillColor="cyan",

                    fillOpacity=0.8,

                    children=[

                        dl.Tooltip(

                            f"{row['Name']} | {round(dist,2)} KM"

                        )

                    ]

                )

            )

    layers = [

        circle,

        station_marker

    ] + nearby_markers

    return (

        layers,

        f"Selected: {selected_station}",

        f"Buffer Distance: {buffer_km} KM",

        f"Nearby Cold Storages: {len(nearby_rows)}",

        f"Total Capacity: {round(total_capacity,2)}",

        nearby_rows

    )

# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":

    app.run_server(

        host="0.0.0.0",

        port=8050,

        debug=False

    )
