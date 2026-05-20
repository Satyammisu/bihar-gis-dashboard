# ============================================
# BIHAR GIS DASHBOARD - FINAL FULL app.py
# ============================================

import pandas as pd
import dash
from dash import Dash, dcc, html, dash_table, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import os

# ============================================
# INITIALIZE DASH APP
# ============================================

app = Dash(__name__)
server = app.server

# ============================================
# LOAD CSV FILES
# ============================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

cold_storage_file = os.path.join(BASE_DIR, "cold_storage.csv")
railway_file = os.path.join(BASE_DIR, "railway_stations.csv")
airport_file = os.path.join(BASE_DIR, "airport.csv")
mandi_file = os.path.join(BASE_DIR, "mandis.csv")

# ============================================
# READ CSV FILES
# ============================================

cold_df = pd.read_csv(cold_storage_file)
rail_df = pd.read_csv(railway_file)
airport_df = pd.read_csv(airport_file)
mandi_df = pd.read_csv(mandi_file)

# ============================================
# CLEAN COLUMN NAMES
# ============================================

cold_df.columns = cold_df.columns.str.strip().str.lower()
rail_df.columns = rail_df.columns.str.strip().str.lower()
airport_df.columns = airport_df.columns.str.strip().str.lower()
mandi_df.columns = mandi_df.columns.str.strip().str.lower()

# ============================================
# RENAME COLUMNS
# ============================================

cold_df.rename(columns={
    "name": "Name",
    "district": "District",
    "latitude": "Latitude",
    "longitude": "Longitude"
}, inplace=True)

rail_df.rename(columns={
    "station_name": "Name",
    "name": "Name",
    "district": "District",
    "latitude": "Latitude",
    "longitude": "Longitude"
}, inplace=True)

airport_df.rename(columns={
    "airport_name": "Name",
    "name": "Name",
    "district": "District",
    "latitude": "Latitude",
    "longitude": "Longitude"
}, inplace=True)

mandi_df.rename(columns={
    "mandi_name": "Name",
    "name": "Name",
    "district": "District",
    "latitude": "Latitude",
    "longitude": "Longitude"
}, inplace=True)

# ============================================
# HANDLE MISSING COLUMNS
# ============================================

required_cols = ["Name", "District", "Latitude", "Longitude"]

for df in [cold_df, rail_df, airport_df, mandi_df]:
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

# ============================================
# REMOVE NULL LAT LONG
# ============================================

cold_df = cold_df.dropna(subset=["Latitude", "Longitude"])
rail_df = rail_df.dropna(subset=["Latitude", "Longitude"])
airport_df = airport_df.dropna(subset=["Latitude", "Longitude"])
mandi_df = mandi_df.dropna(subset=["Latitude", "Longitude"])

# ============================================
# CONVERT LAT LONG TO NUMERIC
# ============================================

for df in [cold_df, rail_df, airport_df, mandi_df]:
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

# ============================================
# REMOVE INVALID COORDINATES
# ============================================

cold_df = cold_df.dropna(subset=["Latitude", "Longitude"])
rail_df = rail_df.dropna(subset=["Latitude", "Longitude"])
airport_df = airport_df.dropna(subset=["Latitude", "Longitude"])
mandi_df = mandi_df.dropna(subset=["Latitude", "Longitude"])

# ============================================
# CREATE MAP
# ============================================

fig = go.Figure()

# ============================================
# ADD COLD STORAGE MARKERS
# ============================================

fig.add_trace(go.Scattermapbox(
    lat=cold_df["Latitude"],
    lon=cold_df["Longitude"],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=10,
        color='blue'
    ),
    text=cold_df["Name"],
    name="Cold Storage"
))

# ============================================
# ADD RAILWAY STATION MARKERS
# ============================================

fig.add_trace(go.Scattermapbox(
    lat=rail_df["Latitude"],
    lon=rail_df["Longitude"],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=10,
        color='red'
    ),
    text=rail_df["Name"],
    name="Railway Stations"
))

# ============================================
# ADD AIRPORT MARKERS
# ============================================

fig.add_trace(go.Scattermapbox(
    lat=airport_df["Latitude"],
    lon=airport_df["Longitude"],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=10,
        color='green'
    ),
    text=airport_df["Name"],
    name="Airports"
))

# ============================================
# ADD MANDI MARKERS
# ============================================

fig.add_trace(go.Scattermapbox(
    lat=mandi_df["Latitude"],
    lon=mandi_df["Longitude"],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=10,
        color='orange'
    ),
    text=mandi_df["Name"],
    name="Mandis"
))

# ============================================
# MAP LAYOUT
# ============================================

fig.update_layout(
    mapbox_style="open-street-map",
    mapbox_zoom=5,
    mapbox_center={"lat": 25.5, "lon": 85.3},
    margin={"r":0,"t":0,"l":0,"b":0},
    height=700
)

# ============================================
# DISTRICT WISE COLD STORAGE CHART
# ============================================

district_chart = px.bar(
    cold_df.groupby("District").size().reset_index(name="Cold Storages"),
    x="District",
    y="Cold Storages",
    title="District Wise Cold Storages"
)

# ============================================
# APP LAYOUT
# ============================================

app.layout = html.Div([

    html.H1(
        "Bihar GIS Dashboard",
        style={
            "textAlign": "center",
            "marginBottom": "20px"
        }
    ),

    html.Div([

        html.Div([

            html.H2("Railway Station Buffer"),

            dcc.Dropdown(
                id='rail-dropdown',
                options=[
                    {"label": i, "value": i}
                    for i in rail_df["Name"].dropna().unique()
                ],
                placeholder="Select Railway Station"
            ),

            html.Br(),

            dcc.Dropdown(
                id='buffer-distance',
                options=[
                    {"label": "5 KM", "value": 5},
                    {"label": "10 KM", "value": 10},
                    {"label": "20 KM", "value": 20}
                ],
                value=5
            ),

            html.Br(),

            html.Button(
                "Generate Buffer",
                id='buffer-btn',
                n_clicks=0,
                style={
                    "backgroundColor": "#007BFF",
                    "color": "white",
                    "border": "none",
                    "padding": "12px",
                    "width": "100%",
                    "borderRadius": "5px",
                    "fontWeight": "bold"
                }
            ),

            html.Br(),
            html.Br(),

            dcc.Graph(
                figure=district_chart
            )

        ],
        style={
            "width": "30%",
            "display": "inline-block",
            "verticalAlign": "top",
            "padding": "20px"
        }),

        html.Div([

            dcc.Graph(
                id='map',
                figure=fig
            )

        ],
        style={
            "width": "68%",
            "display": "inline-block"
        })

    ])

])

# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
