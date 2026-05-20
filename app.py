import json
import math
import pandas as pd

from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# APP INITIALIZATION
# =========================================================

app = Dash(__name__)
server = app.server

# =========================================================
# LOAD BIHAR BOUNDARY
# =========================================================

with open("bihar_boundary.geojson", "r", encoding="utf-8") as f:
    bihar_geojson = json.load(f)

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

        if "name" in col:
            column_mapping[col] = "Name"

        elif "district" in col:
            column_mapping[col] = "District"

        elif "lat" in col:
            column_mapping[col] = "Latitude"

        elif "lon" in col:
            column_mapping[col] = "Longitude"

    df = df.rename(columns=column_mapping)

    required_cols = ["Name", "District", "Latitude", "Longitude"]

    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    df["Name"] = df["Name"].fillna("Unknown")
    df["District"] = df["District"].fillna("Unknown")

    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

    df = df.dropna(subset=["Latitude", "Longitude"])

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

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

# =========================================================
# INITIAL MAP
# =========================================================

def create_base_map():

    fig = go.Figure()

    # Cold Storage
    fig.add_trace(
        go.Scattermapbox(
            lat=cold_df["Latitude"],
            lon=cold_df["Longitude"],
            mode="markers",
            marker=dict(size=10, color="blue"),
            text=cold_df["Name"],
            name="Cold Storage"
        )
    )

    # Railway
    fig.add_trace(
        go.Scattermapbox(
            lat=rail_df["Latitude"],
            lon=rail_df["Longitude"],
            mode="markers",
            marker=dict(size=12, color="red"),
            text=rail_df["Name"],
            name="Railway Station"
        )
    )

    # Airports
    fig.add_trace(
        go.Scattermapbox(
            lat=airport_df["Latitude"],
            lon=airport_df["Longitude"],
            mode="markers",
            marker=dict(size=11, color="green"),
            text=airport_df["Name"],
            name="Airport"
        )
    )

    # Mandis
    fig.add_trace(
        go.Scattermapbox(
            lat=mandi_df["Latitude"],
            lon=mandi_df["Longitude"],
            mode="markers",
            marker=dict(size=9, color="orange"),
            text=mandi_df["Name"],
            name="Mandis"
        )
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=6,
        mapbox_center={"lat": 25.7, "lon": 85.3},
        height=700,
        margin={"r":0,"t":0,"l":0,"b":0},
        legend=dict(
            bgcolor="white",
            bordercolor="black",
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
# DISTRICT CHART
# =========================================================

district_chart = px.bar(
    cold_df.groupby("District").size().reset_index(name="Cold Storages"),
    x="District",
    y="Cold Storages",
    title="District Wise Cold Storages"
)

# =========================================================
# APP LAYOUT
# =========================================================

app.layout = html.Div([

    # HEADER
    html.Div([

        html.H1(
            "Bihar GIS Dashboard",
            style={
                "textAlign": "center",
                "color": "white",
                "padding": "20px"
            }
        )

    ], style={
        "backgroundColor": "#0d47a1"
    }),

    # KPI CARDS
    html.Div([

        html.Div([
            html.H3(total_cold),
            html.P("Cold Storages")
        ], className="card"),

        html.Div([
            html.H3(total_rail),
            html.P("Railway Stations")
        ], className="card"),

        html.Div([
            html.H3(total_airport),
            html.P("Airports")
        ], className="card"),

        html.Div([
            html.H3(total_mandi),
            html.P("Mandis")
        ], className="card"),

    ], style={
        "display": "flex",
        "justifyContent": "space-around",
        "padding": "20px"
    }),

    # CONTROL PANEL
    html.Div([

        html.Div([

            html.H3("Railway Station Buffer"),

            dcc.Dropdown(
                id="rail-dropdown",
                options=[
                    {
                        "label": i,
                        "value": i
                    }
                    for i in sorted(rail_df["Name"].unique())
                ],
                placeholder="Select Railway Station",
                searchable=True
            ),

            html.Br(),

            dcc.Dropdown(
                id="buffer-dropdown",
                options=[
                    {"label": "5 KM", "value": 5},
                    {"label": "10 KM", "value": 10},
                    {"label": "25 KM", "value": 25},
                    {"label": "50 KM", "value": 50},
                ],
                value=10
            )

        ], style={
            "width": "30%",
            "padding": "20px",
            "backgroundColor": "white",
            "borderRadius": "10px",
            "boxShadow": "0px 0px 10px lightgray"
        })

    ], style={
        "padding": "20px"
    }),

    # MAP
    html.Div([

        dcc.Graph(
            id="gis-map",
            figure=create_base_map()
        )

    ], style={
        "padding": "20px"
    }),

    # CHART
    html.Div([

        dcc.Graph(
            figure=district_chart
        )

    ], style={
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
    Output("gis-map", "figure"),
    [
        Input("rail-dropdown", "value"),
        Input("buffer-dropdown", "value")
    ]
)

def update_map(selected_station, buffer_km):

    fig = create_base_map()

    if selected_station is None:
        return fig

    station = rail_df[rail_df["Name"] == selected_station]

    if station.empty:
        return fig

    station_lat = station.iloc[0]["Latitude"]
    station_lon = station.iloc[0]["Longitude"]

    # Highlight selected railway station
    fig.add_trace(
        go.Scattermapbox(
            lat=[station_lat],
            lon=[station_lon],
            mode="markers",
            marker=dict(size=20, color="yellow"),
            text=[selected_station],
            name="Selected Station"
        )
    )

    # Find nearby cold storages
    nearby = []

    for _, row in cold_df.iterrows():

        dist = haversine(
            station_lat,
            station_lon,
            row["Latitude"],
            row["Longitude"]
        )

        if dist <= buffer_km:
            nearby.append(row)

    if len(nearby) > 0:

        nearby_df = pd.DataFrame(nearby)

        fig.add_trace(
            go.Scattermapbox(
                lat=nearby_df["Latitude"],
                lon=nearby_df["Longitude"],
                mode="markers",
                marker=dict(size=14, color="cyan"),
                text=nearby_df["Name"],
                name="Nearby Cold Storages"
            )
        )

    fig.update_layout(
        mapbox_zoom=7,
        mapbox_center={
            "lat": station_lat,
            "lon": station_lon
        }
    )

    return fig

# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":
    app.run_server(debug=False)
