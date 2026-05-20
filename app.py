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

        if "station" in col_lower:
            column_mapping[col] = "Name"

        elif "name" in col_lower:
            column_mapping[col] = "Name"

        elif "district" in col_lower:
            column_mapping[col] = "District"

        elif "capacity" in col_lower:
            column_mapping[col] = "Capacity"

        elif "lat" in col_lower:
            column_mapping[col] = "Latitude"

        elif "lon" in col_lower:
            column_mapping[col] = "Longitude"

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

    df["Latitude"] = pd.to_numeric(
        df["Latitude"],
        errors="coerce"
    )

    df["Longitude"] = pd.to_numeric(
        df["Longitude"],
        errors="coerce"
    )

    df["Capacity"] = pd.to_numeric(
        df["Capacity"],
        errors="coerce"
    ).fillna(0)

    df = df.dropna(
        subset=["Latitude", "Longitude"]
    )

    return df

cold_df = standardize_columns(cold_df)
rail_df = standardize_columns(rail_df)
airport_df = standardize_columns(airport_df)
mandi_df = standardize_columns(mandi_df)

# =========================================================
# HAVERSINE DISTANCE
# =========================================================

def haversine(lat1, lon1, lat2, lon2):

    R = 6371

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c

# =========================================================
# CREATE BASE MAP
# =========================================================

def create_base_map():

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
            z=[1] * len(
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
                size=10,
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
                size=12,
                color="#D32F2F"
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
                color="#2E7D32"
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
                size=9,
                color="#F57C00"
            ),
            text=mandi_df["Name"],
            name="Mandis"
        )

    )

    # =====================================================
    # MAP LAYOUT
    # =====================================================

    fig.update_layout(

        mapbox_style="carto-positron",

        mapbox=dict(
            center=dict(
                lat=25.7,
                lon=85.3
            ),
            zoom=6
        ),

        height=800,

        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),

        legend=dict(
            bgcolor="white",
            bordercolor="lightgray",
            borderwidth=1
        )
    )

    return fig

# =========================================================
# KPI VALUES
# =========================================================

total_cold = len(cold_df)
total_rail = len(rail_df)
total_airport = len(airport_df)
total_mandi = len(mandi_df)

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

    color="Cold Storages"
)

district_chart.update_layout(
    height=450
)

# =========================================================
# APP LAYOUT
# =========================================================

app.layout = dbc.Container(

    fluid=True,

    children=[

        # =================================================
        # HEADER
        # =================================================

        dbc.Row([

            dbc.Col([

                html.Div([

                    html.H1(
                        "BIHAR GIS INFRASTRUCTURE DASHBOARD",
                        style={
                            "color": "white",
                            "fontWeight": "bold",
                            "textAlign": "center",
                            "padding": "15px"
                        }
                    )

                ], style={
                    "background":
                    "linear-gradient(to right, #0D47A1, #1565C0)",
                    "borderRadius": "10px",
                    "marginBottom": "20px"
                })

            ])

        ]),

        # =================================================
        # KPI CARDS
        # =================================================

        dbc.Row([

            dbc.Col([

                dbc.Card([

                    dbc.CardBody([

                        html.H2(total_cold),
                        html.H5("Cold Storages")

                    ])

                ], className="shadow")

            ], md=3),

            dbc.Col([

                dbc.Card([

                    dbc.CardBody([

                        html.H2(total_rail),
                        html.H5("Railway Stations")

                    ])

                ], className="shadow")

            ], md=3),

            dbc.Col([

                dbc.Card([

                    dbc.CardBody([

                        html.H2(total_airport),
                        html.H5("Airports")

                    ])

                ], className="shadow")

            ], md=3),

            dbc.Col([

                dbc.Card([

                    dbc.CardBody([

                        html.H2(total_mandi),
                        html.H5("Mandis")

                    ])

                ], className="shadow")

            ], md=3)

        ], className="mb-4"),

        # =================================================
        # MAIN CONTENT
        # =================================================

        dbc.Row([

            # =============================================
            # SIDEBAR
            # =============================================

            dbc.Col([

                dbc.Card([

                    dbc.CardBody([

                        html.H3(
                            "Railway Buffer Analysis"
                        ),

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
                            "Select District"
                        ),

                        html.Br(),

                        html.Div(
                            id="summary-box"
                        )

                    ])

                ], className="shadow")

            ], md=3),

            # =============================================
            # MAP
            # =============================================

            dbc.Col([

                dbc.Card([

                    dbc.CardBody([

                        dcc.Graph(
                            id="gis-map",
                            figure=create_base_map(),
                            style={
                                "height": "800px"
                            }
                        )

                    ])

                ], className="shadow")

            ], md=9)

        ]),

        html.Br(),

        # =================================================
        # TABLE
        # =================================================

        dbc.Row([

            dbc.Col([

                dbc.Card([

                    dbc.CardHeader(

                        html.H4(
                            "Nearby Cold Storages"
                        )

                    ),

                    dbc.CardBody([

                        dash_table.DataTable(

                            id="nearby-table",

                            columns=[

                                {
                                    "name": "District",
                                    "id": "District"
                                },

                                {
                                    "name": "Cold Storage",
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

                            style_cell={
                                "textAlign": "center",
                                "padding": "10px"
                            },

                            style_header={
                                "backgroundColor": "#1565C0",
                                "color": "white",
                                "fontWeight": "bold"
                            }
                        )

                    ])

                ], className="shadow")

            ])

        ]),

        html.Br(),

        # =================================================
        # CHART
        # =================================================

        dbc.Row([

            dbc.Col([

                dbc.Card([

                    dbc.CardBody([

                        dcc.Graph(
                            figure=district_chart
                        )

                    ])

                ], className="shadow")

            ])

        ])

    ],

    style={
        "backgroundColor": "#F4F6F9",
        "padding": "20px"
    }

)

# =========================================================
# CALLBACK
# =========================================================

@app.callback(

    [
        Output("gis-map", "figure"),
        Output("nearby-table", "data"),
        Output("summary-box", "children")
    ],

    [
        Input("rail-dropdown", "value"),
        Input("buffer-dropdown", "value"),
        Input("district-dropdown", "value")
    ]

)

def update_dashboard(

    selected_station,
    buffer_km,
    selected_district

):

    fig = create_base_map()

    nearby_records = []

    summary = "No Railway Station Selected"

    # =====================================================
    # DISTRICT FILTER
    # =====================================================

    if selected_district:

        district_filtered = cold_df[
            cold_df["District"]
            == selected_district
        ]

        fig.add_trace(

            go.Scattermapbox(

                lat=district_filtered["Latitude"],
                lon=district_filtered["Longitude"],

                mode="markers",

                marker=dict(
                    size=14,
                    color="yellow"
                ),

                text=district_filtered["Name"],

                name="District Filter"

            )

        )

    # =====================================================
    # BUFFER ANALYSIS
    # =====================================================

    if selected_station:

        station = rail_df[
            rail_df["Name"]
            == selected_station
        ]

        if not station.empty:

            station_lat = station.iloc[0]["Latitude"]
            station_lon = station.iloc[0]["Longitude"]

            # =============================================
            # SELECTED STATION
            # =============================================

            fig.add_trace(

                go.Scattermapbox(

                    lat=[station_lat],
                    lon=[station_lon],

                    mode="markers",

                    marker=dict(
                        size=20,
                        color="red"
                    ),

                    text=[selected_station],

                    name="Selected Station"

                )

            )

            # =============================================
            # BUFFER CIRCLE
            # =============================================

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
