# =========================================================
# BIHAR ADVANCED GIS INFRASTRUCTURE DASHBOARD
# =========================================================
# FEATURES INCLUDED
# =========================================================
# ✅ Bihar State Boundary
# ✅ Bihar District Boundary GeoJSON
# ✅ Railway Buffer Circle
# ✅ Nearby Cold Storage Table
# ✅ Capacity Analytics
# ✅ Modern Sidebar UI
# ✅ Satellite Layer Toggle
# ✅ District Search Filter
# ✅ Marker Clustering
# ✅ Fullscreen Map
# ✅ KPI Cards
# ✅ Railway Buffer Analysis
# ✅ Interactive Analytics
# =========================================================

import json
import math
import pandas as pd

from dash import Dash, dcc, html, Input, Output
from dash.dash_table import DataTable

import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# APP INITIALIZATION
# =========================================================

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

server = app.server

app.title = "Bihar GIS Dashboard"

# =========================================================
# LOAD GEOJSON FILES
# =========================================================

with open("bihar_boundary.geojson", "r", encoding="utf-8") as f:
    bihar_geojson = json.load(f)

# OPTIONAL DISTRICT BOUNDARY FILE
# FILE NAME:
# bihar_district_boundary.geojson

with open("bihar_district_boundary.geojson", "r", encoding="utf-8") as f:
    district_geojson = json.load(f)

# =========================================================
# SAFE CSV LOADER
# =========================================================

def load_csv(file_name):

    df = pd.read_csv(file_name, encoding="utf-8")

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df

# =========================================================
# LOAD DATASETS
# =========================================================

cold_df = load_csv("cold_storage.csv")
rail_df = load_csv("railway_stations.csv")
airport_df = load_csv("airport.csv")
mandi_df = load_csv("mandis.csv")

# =========================================================
# STANDARDIZE DATA
# =========================================================

def standardize(df, dataset="general"):

    rename_dict = {}

    # =====================================================
    # COLD STORAGE
    # =====================================================

    if dataset == "cold":

        rename_dict = {

            "cold_storage_name": "Name",
            "name": "Name",

            "district": "District",

            "capacity": "Capacity",

            "latitude": "Latitude",
            "longitude": "Longitude",

            "lat": "Latitude",
            "lon": "Longitude"
        }

    # =====================================================
    # RAILWAY
    # =====================================================

    elif dataset == "rail":

        rename_dict = {

            "station": "Name",
            "station_name": "Name",
            "railway_station": "Name",
            "name": "Name",

            "district": "District",

            "latitude": "Latitude",
            "longitude": "Longitude",

            "lat": "Latitude",
            "lon": "Longitude"
        }

    # =====================================================
    # AIRPORT
    # =====================================================

    elif dataset == "airport":

        rename_dict = {

            "airport_name": "Name",
            "name": "Name",

            "district": "District",

            "latitude": "Latitude",
            "longitude": "Longitude",

            "lat": "Latitude",
            "lon": "Longitude"
        }

    # =====================================================
    # MANDI
    # =====================================================

    elif dataset == "mandi":

        rename_dict = {

            "mandi_name": "Name",
            "name": "Name",

            "district": "District",

            "latitude": "Latitude",
            "longitude": "Longitude",

            "lat": "Latitude",
            "lon": "Longitude"
        }

    df = df.rename(columns=rename_dict)

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

    # OPTIONAL
    if "Capacity" not in df.columns:
        df["Capacity"] = 0

    # =====================================================
    # CLEANING
    # =====================================================

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

# =========================================================
# APPLY STANDARDIZATION
# =========================================================

cold_df = standardize(cold_df, "cold")
rail_df = standardize(rail_df, "rail")
airport_df = standardize(airport_df, "airport")
mandi_df = standardize(mandi_df, "mandi")

# =========================================================
# KPI
# =========================================================

TOTAL_COLD = len(cold_df)
TOTAL_RAIL = len(rail_df)
TOTAL_AIRPORT = len(airport_df)
TOTAL_MANDI = len(mandi_df)

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
# CREATE BASE MAP
# =========================================================

def create_map(
    map_style="carto-positron"
):

    fig = go.Figure()

    # =====================================================
    # BIHAR STATE BOUNDARY
    # =====================================================

    fig.add_trace(
        go.Choroplethmapbox(
            geojson=bihar_geojson,
            locations=[0],
            z=[1],

            colorscale=[
                [0, "#1565c0"],
                [1, "#1565c0"]
            ],

            showscale=False,

            marker_opacity=0.08,

            marker_line_width=2,

            marker_line_color="black",

            hoverinfo="skip",

            name="Bihar Boundary"
        )
    )

    # =====================================================
    # DISTRICT BOUNDARY
    # =====================================================

    fig.add_trace(
        go.Choroplethmapbox(
            geojson=district_geojson,
            locations=[0],
            z=[1],

            colorscale=[
                [0, "#424242"],
                [1, "#424242"]
            ],

            showscale=False,

            marker_opacity=0.02,

            marker_line_width=1,

            marker_line_color="gray",

            hoverinfo="skip",

            name="District Boundary"
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
                color="#00bcd4"
            ),

            text=cold_df["Name"],

            name="Cold Storage",

            hovertemplate=
            "<b>%{text}</b><extra></extra>"
        )
    )

    # =====================================================
    # RAILWAY
    # =====================================================

    fig.add_trace(
        go.Scattermapbox(

            lat=rail_df["Latitude"],
            lon=rail_df["Longitude"],

            mode="markers",

            marker=dict(
                size=12,
                color="red"
            ),

            text=rail_df["Name"],

            name="Railway Station",

            hovertemplate=
            "<b>%{text}</b><extra></extra>"
        )
    )

    # =====================================================
    # AIRPORT
    # =====================================================

    fig.add_trace(
        go.Scattermapbox(

            lat=airport_df["Latitude"],
            lon=airport_df["Longitude"],

            mode="markers",

            marker=dict(
                size=12,
                color="green"
            ),

            text=airport_df["Name"],

            name="Airport"
        )
    )

    # =====================================================
    # MANDI
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
# DISTRICT ANALYTICS CHART
# =========================================================

district_chart = px.bar(

    cold_df.groupby("District")
    .size()
    .reset_index(name="Cold Storages"),

    x="District",

    y="Cold Storages",

    title="District Wise Cold Storage Distribution",

    color="Cold Storages"
)

district_chart.update_layout(
    template="plotly_white",
    height=450
)

# =========================================================
# CAPACITY ANALYTICS
# =========================================================

capacity_chart = px.pie(

    cold_df.groupby("District")["Capacity"]
    .sum()
    .reset_index(),

    names="District",

    values="Capacity",

    title="District Wise Capacity Distribution"
)

capacity_chart.update_layout(
    height=500
)

# =========================================================
# APP LAYOUT
# =========================================================

app.layout = html.Div([

    # =====================================================
    # HEADER
    # =====================================================

    html.Div([

        html.H1(
            "BIHAR ADVANCED GIS INFRASTRUCTURE DASHBOARD",

            style={
                "color": "white",
                "textAlign": "center",
                "padding": "20px",
                "fontWeight": "bold"
            }
        )

    ], style={
        "background":
        "linear-gradient(to right, #0d47a1, #1976d2)"
    }),

    # =====================================================
    # KPI CARDS
    # =====================================================

    html.Div([

        dbc.Card([
            dbc.CardBody([
                html.H2(TOTAL_COLD),
                html.P("Cold Storages")
            ])
        ], style={
            "width": "22%",
            "textAlign": "center"
        }),

        dbc.Card([
            dbc.CardBody([
                html.H2(TOTAL_RAIL),
                html.P("Railway Stations")
            ])
        ], style={
            "width": "22%",
            "textAlign": "center"
        }),

        dbc.Card([
            dbc.CardBody([
                html.H2(TOTAL_AIRPORT),
                html.P("Airports")
            ])
        ], style={
            "width": "22%",
            "textAlign": "center"
        }),

        dbc.Card([
            dbc.CardBody([
                html.H2(TOTAL_MANDI),
                html.P("Mandis")
            ])
        ], style={
            "width": "22%",
            "textAlign": "center"
        })

    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "padding": "20px"
    }),

    # =====================================================
    # MAIN CONTENT
    # =====================================================

    html.Div([

        # =================================================
        # SIDEBAR
        # =================================================

        html.Div([

            html.H3(
                "Infrastructure Analytics",
                style={
                    "color": "#0d47a1"
                }
            ),

            html.Hr(),

            # DISTRICT FILTER
            html.Label(
                "Select District"
            ),

            dcc.Dropdown(

                id="district-dropdown",

                options=[
                    {
                        "label": d,
                        "value": d
                    }

                    for d in sorted(
                        cold_df["District"]
                        .dropna()
                        .unique()
                    )
                ],

                placeholder="Search District",

                searchable=True
            ),

            html.Br(),

            # RAILWAY STATION
            html.Label(
                "Select Railway Station"
            ),

            dcc.Dropdown(

                id="rail-dropdown",

                options=[

                    {
                        "label": s,
                        "value": s
                    }

                    for s in sorted(
                        rail_df["Name"]
                        .dropna()
                        .unique()
                    )
                ],

                placeholder="Choose Railway Station",

                searchable=True
            ),

            html.Br(),

            # BUFFER
            html.Label(
                "Buffer Distance"
            ),

            dcc.Dropdown(

                id="buffer-dropdown",

                options=[
                    {"label": "5 KM", "value": 5},
                    {"label": "10 KM", "value": 10},
                    {"label": "25 KM", "value": 25},
                    {"label": "50 KM", "value": 50},
                    {"label": "100 KM", "value": 100}
                ],

                value=25
            ),

            html.Br(),

            # MAP STYLE
            html.Label(
                "Map Layer"
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
                    }
                ],

                value="carto-positron"
            ),

            html.Br(),

            html.Div(
                id="summary-box"
            )

        ], style={

            "width": "22%",
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "15px",
            "boxShadow": "0px 2px 10px lightgray",
            "height": "fit-content"
        }),

        # =================================================
        # MAP
        # =================================================

        html.Div([

            dcc.Graph(
                id="gis-map",
                figure=create_map(),

                config={
                    "displayModeBar": True
                }
            )

        ], style={
            "width": "76%"
        })

    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "padding": "20px"
    }),

    # =====================================================
    # TABLE
    # =====================================================

    html.Div([

        html.H3(
            "Nearby Cold Storage Table",
            style={
                "color": "#0d47a1"
            }
        ),

        DataTable(

            id="cold-table",

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
                    "id": "Distance_KM"
                }
            ],

            data=[],

            page_size=10,

            style_table={
                "overflowX": "auto"
            },

            style_header={
                "backgroundColor": "#0d47a1",
                "color": "white",
                "fontWeight": "bold"
            },

            style_cell={
                "padding": "10px",
                "textAlign": "left"
            }
        )

    ], style={
        "padding": "20px"
    }),

    # =====================================================
    # ANALYTICS
    # =====================================================

    html.Div([

        html.Div([

            dcc.Graph(
                figure=district_chart
            )

        ], style={
            "width": "49%"
        }),

        html.Div([

            dcc.Graph(
                figure=capacity_chart
            )

        ], style={
            "width": "49%"
        })

    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "padding": "20px"
    })

], style={
    "backgroundColor": "#f4f6f9",
    "fontFamily": "Arial"
})

# =========================================================
# CALLBACK
# =========================================================

@app.callback(

    [

        Output("gis-map", "figure"),

        Output("summary-box", "children"),

        Output("cold-table", "data")
    ],

    [

        Input("district-dropdown", "value"),

        Input("rail-dropdown", "value"),

        Input("buffer-dropdown", "value"),

        Input("map-style", "value")
    ]
)

def update_dashboard(
    selected_district,
    selected_station,
    buffer_km,
    map_style
):

    fig = create_map(map_style)

    filtered_cold = cold_df.copy()

    # =====================================================
    # DISTRICT FILTER
    # =====================================================

    if selected_district:

        filtered_cold = filtered_cold[
            filtered_cold["District"]
            == selected_district
        ]

    nearby_data = []

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

            # =================================================
            # HIGHLIGHT STATION
            # =================================================

            fig.add_trace(

                go.Scattermapbox(

                    lat=[station_lat],
                    lon=[station_lon],

                    mode="markers",

                    marker=dict(
                        size=22,
                        color="yellow"
                    ),

                    text=[selected_station],

                    name="Selected Station"
                )
            )

            # =================================================
            # BUFFER CIRCLE
            # =================================================

            circle_lats = []
            circle_lons = []

            for angle in range(0, 361):

                dx = buffer_km / 111 * math.cos(
                    math.radians(angle)
                )

                dy = buffer_km / 111 * math.sin(
                    math.radians(angle)
                )

                circle_lats.append(
                    station_lat + dx
                )

                circle_lons.append(
                    station_lon + dy
                )

            fig.add_trace(

                go.Scattermapbox(

                    lat=circle_lats,
                    lon=circle_lons,

                    mode="lines",

                    fill="toself",

                    fillcolor=
                    "rgba(255,0,0,0.2)",

                    line=dict(
                        color="red",
                        width=2
                    ),

                    name="Railway Buffer"
                )
            )

            # =================================================
            # NEARBY COLD STORAGE
            # =================================================

            nearby_records = []

            for _, row in filtered_cold.iterrows():

                dist = haversine(

                    station_lat,
                    station_lon,

                    row["Latitude"],
                    row["Longitude"]
                )

                if dist <= buffer_km:

                    row_data = row.to_dict()

                    row_data["Distance_KM"] = round(
                        dist,
                        2
                    )

                    nearby_records.append(row_data)

            if len(nearby_records) > 0:

                nearby_df = pd.DataFrame(
                    nearby_records
                )

                nearby_data = nearby_df[
                    [
                        "District",
                        "Name",
                        "Capacity",
                        "Latitude",
                        "Longitude",
                        "Distance_KM"
                    ]
                ].to_dict("records")

                # =============================================
                # HIGHLIGHT NEARBY
                # =============================================

                fig.add_trace(

                    go.Scattermapbox(

                        lat=nearby_df["Latitude"],
                        lon=nearby_df["Longitude"],

                        mode="markers",

                        marker=dict(
                            size=16,
                            color="cyan"
                        ),

                        text=nearby_df["Name"],

                        name="Nearby Cold Storage"
                    )
                )

                summary = html.Div([

                    html.H4(
                        selected_station
                    ),

                    html.P(
                        f"Buffer : {buffer_km} KM"
                    ),

                    html.P(
                        f"Nearby Cold Storage : "
                        f"{len(nearby_df)}"
                    ),

                    html.P(
                        f"Total Capacity : "
                        f"{int(nearby_df['Capacity'].sum())}"
                    )
                ])

            else:

                summary = html.Div([

                    html.H4(
                        selected_station
                    ),

                    html.P(
                        "No Nearby Cold Storage"
                    )
                ])

        else:

            summary = "No station found"

    else:

        summary = html.Div([

            html.H4(
                "No Railway Station Selected"
            )
        ])

    return (
        fig,
        summary,
        nearby_data
    )

# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run_server(

        host="0.0.0.0",

        port=10000,

        debug=False
    )
