# =========================================================
# BIHAR GIS INFRASTRUCTURE DASHBOARD
# ENTERPRISE LEAFLET GIS VERSION
# =========================================================

import json
import math
import pandas as pd

from dash import Dash, html, dcc, Input, Output
from dash import dash_table

import dash_bootstrap_components as dbc

import dash_leaflet as dl
import dash_leaflet.express as dlx

# =========================================================
# APP INITIALIZATION
# =========================================================

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY]
)

server = app.server

# =========================================================
# LOAD GEOJSON
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
# LOAD CSV DATA
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

        col_lower = col.lower()

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
        # LATITUDE
        # =================================================

        elif "lat" in col_lower:
            column_mapping[col] = "Latitude"

        # =================================================
        # LONGITUDE
        # =================================================

        elif "lon" in col_lower:
            column_mapping[col] = "Longitude"

        # =================================================
        # CAPACITY
        # =================================================

        elif (
            "capacity" in col_lower
            or "cap" in col_lower
            or "storage" in col_lower
        ):

            column_mapping[col] = "Capacity"

    # =====================================================
    # RENAME
    # =====================================================

    df = df.rename(columns=column_mapping)

    # =====================================================
    # REQUIRED COLS
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
    # CAPACITY
    # =====================================================

    if "Capacity" not in df.columns:
        df["Capacity"] = 0

    # =====================================================
    # CLEANING
    # =====================================================

    df["Name"] = df["Name"].fillna("Unknown")

    df["District"] = df["District"].fillna("Unknown")

    # =====================================================
    # NUMERIC
    # =====================================================

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

TOTAL_COLD = len(cold_df)
TOTAL_RAIL = len(rail_df)
TOTAL_AIRPORT = len(airport_df)
TOTAL_MANDI = len(mandi_df)

# =========================================================
# HAVERSINE DISTANCE
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
# CREATE MARKERS
# =========================================================

def create_markers():

    markers = []

    # =====================================================
    # COLD STORAGE
    # =====================================================

    for _, row in cold_df.iterrows():

        popup = dbc.Card(

            [

                dbc.CardBody(

                    [

                        html.H5(
                            "Cold Storage"
                        ),

                        html.P(
                            f"District: {row['District']}"
                        ),

                        html.P(
                            f"Name: {row['Name']}"
                        ),

                        html.P(
                            f"Capacity: {row['Capacity']}"
                        ),

                        html.P(
                            f"Latitude: {row['Latitude']}"
                        ),

                        html.P(
                            f"Longitude: {row['Longitude']}"
                        ),

                        dbc.Button(
                            "Navigate",
                            color="primary",
                            size="sm"
                        )

                    ]

                )

            ],

            style={
                "width": "220px"
            }

        )

        markers.append(

            dl.CircleMarker(

                center=[
                    row["Latitude"],
                    row["Longitude"]
                ],

                radius=7,

                color="white",

                fillColor="blue",

                fillOpacity=0.9,

                children=[

                    dl.Popup(
                        popup
                    )

                ]

            )

        )

    # =====================================================
    # RAILWAY
    # =====================================================

    for _, row in rail_df.iterrows():

        markers.append(

            dl.CircleMarker(

                center=[
                    row["Latitude"],
                    row["Longitude"]
                ],

                radius=8,

                color="white",

                fillColor="red",

                fillOpacity=0.9,

                children=[

                    dl.Popup(

                        html.Div(

                            [

                                html.H5(
                                    "Railway Station"
                                ),

                                html.P(
                                    row["Name"]
                                ),

                                html.P(
                                    row["District"]
                                )

                            ]

                        )

                    )

                ]

            )

        )

    # =====================================================
    # AIRPORT
    # =====================================================

    for _, row in airport_df.iterrows():

        markers.append(

            dl.CircleMarker(

                center=[
                    row["Latitude"],
                    row["Longitude"]
                ],

                radius=8,

                color="white",

                fillColor="green",

                fillOpacity=0.9,

                children=[

                    dl.Popup(

                        html.Div(

                            [

                                html.H5(
                                    "Airport"
                                ),

                                html.P(
                                    row["Name"]
                                )

                            ]

                        )

                    )

                ]

            )

        )

    # =====================================================
    # MANDIS
    # =====================================================

    for _, row in mandi_df.iterrows():

        markers.append(

            dl.CircleMarker(

                center=[
                    row["Latitude"],
                    row["Longitude"]
                ],

                radius=8,

                color="white",

                fillColor="orange",

                fillOpacity=0.9,

                children=[

                    dl.Popup(

                        html.Div(

                            [

                                html.H5(
                                    "Mandi"
                                ),

                                html.P(
                                    row["Name"]
                                )

                            ]

                        )

                    )

                ]

            )

        )

    return markers

# =========================================================
# DISTRICT DROPDOWN
# =========================================================

district_options = [

    {

        "label": i,
        "value": i

    }

    for i in sorted(
        cold_df["District"]
        .dropna()
        .unique()
    )

]

# =========================================================
# RAILWAY DROPDOWN
# =========================================================

rail_options = [

    {

        "label": i,
        "value": i

    }

    for i in sorted(
        rail_df["Name"]
        .dropna()
        .unique()
    )

]

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

                                "padding": "20px"

                            }

                        )

                    ],

                    style={

                        "backgroundColor": "#0D47A1",

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
                                    TOTAL_COLD,
                                    className="text-primary"
                                ),

                                html.H5(
                                    "Cold Storages"
                                )

                            ]

                        )

                    ),

                    md=3

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H2(
                                    TOTAL_RAIL,
                                    className="text-danger"
                                ),

                                html.H5(
                                    "Railway Stations"
                                )

                            ]

                        )

                    ),

                    md=3

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H2(
                                    TOTAL_AIRPORT,
                                    className="text-success"
                                ),

                                html.H5(
                                    "Airports"
                                )

                            ]

                        )

                    ),

                    md=3

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H2(
                                    TOTAL_MANDI,
                                    className="text-warning"
                                ),

                                html.H5(
                                    "Mandis"
                                )

                            ]

                        )

                    ),

                    md=3

                )

            ],

            className="mt-4"

        ),

        # =================================================
        # MAIN SECTION
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

                                    html.H3(
                                        "Railway Station Buffer"
                                    ),

                                    html.Br(),

                                    # =====================
                                    # RAILWAY DROPDOWN
                                    # =====================

                                    dcc.Dropdown(

                                        id="rail-dropdown",

                                        options=rail_options,

                                        value="Patna Junction",

                                        placeholder=
                                        "Select Railway Station"

                                    ),

                                    html.Br(),

                                    # =====================
                                    # BUFFER DROPDOWN
                                    # =====================

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

                                        value=5

                                    ),

                                    html.Br(),

                                    # =====================
                                    # DISTRICT SEARCH
                                    # =====================

                                    dcc.Dropdown(

                                        id="district-dropdown",

                                        options=district_options,

                                        placeholder=
                                        "Search District"

                                    ),

                                    html.Br(),

                                    html.Div(
                                        id="summary-box"
                                    )

                                ]

                            )

                        )

                    ],

                    md=3

                ),

                # =============================================
                # MAP
                # =============================================

                dbc.Col(

                    [

                        dl.Map(

                            [

                                # =====================
                                # BASE LAYERS
                                # =====================

                                dl.LayersControl(

                                    [

                                        dl.BaseLayer(

                                            dl.TileLayer(),

                                            name="OpenStreetMap",

                                            checked=True

                                        ),

                                        dl.BaseLayer(

                                            dl.TileLayer(

                                                url=
                                                "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
                                            ),

                                            name="Terrain"

                                        ),

                                        dl.BaseLayer(

                                            dl.TileLayer(

                                                url=
                                                "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                                            ),

                                            name="Dark Mode"

                                        )

                                    ]

                                ),

                                # =====================
                                # DISTRICT BOUNDARY
                                # =====================

                                dl.GeoJSON(

                                    data=district_geojson,

                                    options={

                                        "style": {

                                            "color": "black",

                                            "weight": 2,

                                            "fillOpacity": 0

                                        }

                                    }

                                ),

                                # =====================
                                # FULLSCREEN CONTROL
                                # =====================

                                dl.FullScreenControl(),

                                # =====================
                                # SCALE CONTROL
                                # =====================

                                dl.ScaleControl(),

                                # =====================
                                # MARKERS
                                # =====================

                                dl.LayerGroup(

                                    id="marker-layer",

                                    children=create_markers()

                                ),

                                # =====================
                                # BUFFER CIRCLE
                                # =====================

                                dl.LayerGroup(
                                    id="buffer-layer"
                                )

                            ],

                            center=[25.7, 85.3],

                            zoom=7,

                            style={
                                "width": "100%",
                                "height": "850px"
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

                                        "padding": "10px",

                                        "textAlign": "left"

                                    }

                                )

                            ]

                        )

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

        Output("buffer-layer", "children"),

        Output("cold-table", "data"),

        Output("summary-box", "children")

    ],

    [

        Input("rail-dropdown", "value"),

        Input("buffer-dropdown", "value"),

        Input("district-dropdown", "value")

    ]

)

def update_buffer(

    selected_station,

    buffer_km,

    selected_district

):

    # =====================================================
    # GET STATION
    # =====================================================

    station = rail_df[
        rail_df["Name"] == selected_station
    ]

    if station.empty:

        return [], [], "No station found"

    station_lat = station.iloc[0]["Latitude"]

    station_lon = station.iloc[0]["Longitude"]

    # =====================================================
    # FILTER DISTRICT
    # =====================================================

    filtered_df = cold_df.copy()

    if selected_district:

        filtered_df = filtered_df[

            filtered_df["District"]
            == selected_district

        ]

    # =====================================================
    # FIND NEARBY STORAGE
    # =====================================================

    nearby_rows = []

    nearby_markers = []

    total_capacity = 0

    for _, row in filtered_df.iterrows():

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

                    "Distance": round(
                        dist,
                        2
                    )

                }

            )

            total_capacity += row["Capacity"]

            nearby_markers.append(

                dl.CircleMarker(

                    center=[
                        row["Latitude"],
                        row["Longitude"]
                    ],

                    radius=10,

                    color="cyan",

                    fillColor="cyan",

                    fillOpacity=0.9

                )

            )

    # =====================================================
    # BUFFER CIRCLE
    # =====================================================

    buffer_circle = dl.Circle(

        center=[
            station_lat,
            station_lon
        ],

        radius=buffer_km * 1000,

        color="green",

        fillColor="green",

        fillOpacity=0.15

    )

    # =====================================================
    # SELECTED STATION MARKER
    # =====================================================

    station_marker = dl.Marker(

        position=[
            station_lat,
            station_lon
        ],

        children=[

            dl.Popup(

                html.Div(

                    [

                        html.H4(
                            selected_station
                        ),

                        html.P(
                            f"Buffer: {buffer_km} KM"
                        )

                    ]

                )

            )

        ]

    )

    # =====================================================
    # SUMMARY
    # =====================================================

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

    return (

        [

            buffer_circle,

            station_marker

        ] + nearby_markers,

        nearby_rows,

        summary

    )

# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run_server(

        debug=False,

        host="0.0.0.0",

        port=10000

    )
