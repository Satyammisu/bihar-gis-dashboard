import json
import math
import pandas as pd

from dash import Dash, dcc, html, Input, Output, dash_table
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

def standardize_columns(df, dataset_type):

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    if dataset_type == "cold":

        mapping = {
            "cold_storage_name": "Name",
            "name": "Name",
            "district": "District",
            "capacity": "Capacity",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "lat": "Latitude",
            "lon": "Longitude"
        }

    elif dataset_type == "rail":

        mapping = {
            "station_name": "Name",
            "railway_station": "Name",
            "name": "Name",
            "district": "District",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "lat": "Latitude",
            "lon": "Longitude"
        }

    elif dataset_type == "airport":

        mapping = {
            "airport_name": "Name",
            "name": "Name",
            "district": "District",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "lat": "Latitude",
            "lon": "Longitude"
        }

    else:

        mapping = {
            "mandi_name": "Name",
            "name": "Name",
            "district": "District",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "lat": "Latitude",
            "lon": "Longitude"
        }

    df = df.rename(columns=mapping)

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

    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df["Capacity"] = pd.to_numeric(df["Capacity"], errors="coerce").fillna(0)

    df = df.dropna(subset=["Latitude", "Longitude"])

    return df

# =========================================================
# CLEAN DATA
# =========================================================

cold_df = standardize_columns(cold_df, "cold")
rail_df = standardize_columns(rail_df, "rail")
airport_df = standardize_columns(airport_df, "airport")
mandi_df = standardize_columns(mandi_df, "mandi")

# =========================================================
# REMOVE UNKNOWN STATIONS
# =========================================================

rail_df = rail_df[rail_df["Name"] != "Unknown"]

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
# CREATE MAP
# =========================================================

def create_base_map():

    fig = go.Figure()

    # Cold Storages
    fig.add_trace(
        go.Scattermapbox(
            lat=cold_df["Latitude"],
            lon=cold_df["Longitude"],
            mode="markers",
            marker=dict(
                size=10,
                color="#1976d2"
            ),
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
            marker=dict(
                size=12,
                color="#d32f2f"
            ),
            text=rail_df["Name"],
            name="Railway Station"
        )
    )

    # Airport
    fig.add_trace(
        go.Scattermapbox(
            lat=airport_df["Latitude"],
            lon=airport_df["Longitude"],
            mode="markers",
            marker=dict(
                size=11,
                color="#388e3c"
            ),
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
            marker=dict(
                size=9,
                color="#f57c00"
            ),
            text=mandi_df["Name"],
            name="Mandis"
        )
    )

    fig.update_layout(

        mapbox_style="open-street-map",

        mapbox=dict(
            center=dict(
                lat=25.7,
                lon=85.3
            ),
            zoom=6
        ),

        height=750,

        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),

        legend=dict(
            bgcolor="white",
            bordercolor="gray",
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
    title="District Wise Cold Storages",
    color="Cold Storages"
)

district_chart.update_layout(
    height=450
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
            "BIHAR GIS INFRASTRUCTURE DASHBOARD",
            style={
                "color": "white",
                "textAlign": "center",
                "padding": "20px",
                "fontWeight": "bold"
            }
        )

    ], style={
        "backgroundColor": "#0d47a1"
    }),

    # =====================================================
    # KPI CARDS
    # =====================================================

    html.Div([

        html.Div([
            html.H2(total_cold),
            html.P("Cold Storages")
        ], className="kpi-card"),

        html.Div([
            html.H2(total_rail),
            html.P("Railway Stations")
        ], className="kpi-card"),

        html.Div([
            html.H2(total_airport),
            html.P("Airports")
        ], className="kpi-card"),

        html.Div([
            html.H2(total_mandi),
            html.P("Mandis")
        ], className="kpi-card"),

    ], style={
        "display": "flex",
        "justifyContent": "space-around",
        "padding": "20px",
        "gap": "20px"
    }),

    # =====================================================
    # FILTER PANEL
    # =====================================================

    html.Div([

        html.Div([

            html.H3(
                "Railway Station Buffer Analysis",
                style={
                    "marginBottom": "20px"
                }
            ),

            html.Label("Select Railway Station"),

            dcc.Dropdown(
                id="rail-dropdown",

                options=[
                    {
                        "label": i,
                        "value": i
                    }
                    for i in sorted(
                        rail_df["Name"].dropna().unique()
                    )
                ],

                placeholder="Choose Railway Station",

                searchable=True,

                style={
                    "marginBottom": "20px"
                }
            ),

            html.Label("Select Buffer Radius"),

            dcc.Dropdown(
                id="buffer-dropdown",

                options=[
                    {"label": "5 KM", "value": 5},
                    {"label": "10 KM", "value": 10},
                    {"label": "25 KM", "value": 25},
                    {"label": "50 KM", "value": 50},
                ],

                value=10,

                style={
                    "marginBottom": "20px"
                }
            ),

            html.Div(
                id="summary-box",
                style={
                    "padding": "15px",
                    "backgroundColor": "#f5f5f5",
                    "borderRadius": "10px",
                    "marginTop": "20px"
                }
            )

        ], style={
            "width": "25%",
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "15px",
            "boxShadow": "0px 0px 10px rgba(0,0,0,0.1)"
        }),

        # =================================================
        # MAP
        # =================================================

        html.Div([

            dcc.Graph(
                id="gis-map",
                figure=create_base_map()
            )

        ], style={
            "width": "74%"
        })

    ], style={
        "display": "flex",
        "gap": "20px",
        "padding": "20px"
    }),

    # =====================================================
    # DISTRICT CHART
    # =====================================================

    html.Div([

        dcc.Graph(
            figure=district_chart
        )

    ], style={
        "padding": "20px"
    }),

    # =====================================================
    # TABLE
    # =====================================================

    html.Div([

        html.H2(
            "Nearby Cold Storages",
            style={
                "paddingBottom": "20px"
            }
        ),

        dash_table.DataTable(

            id="data-table",

            columns=[
                {"name": "District", "id": "District"},
                {"name": "Cold Storage Name", "id": "Name"},
                {"name": "Capacity", "id": "Capacity"},
                {"name": "Latitude", "id": "Latitude"},
                {"name": "Longitude", "id": "Longitude"},
                {"name": "Distance (KM)", "id": "Distance"}
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
                "textAlign": "center"
            },

            filter_action="native",
            sort_action="native",

            export_format="csv"
        )

    ], style={
        "padding": "20px",
        "backgroundColor": "white",
        "margin": "20px",
        "borderRadius": "15px",
        "boxShadow": "0px 0px 10px rgba(0,0,0,0.1)"
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
        Output("data-table", "data"),
        Output("summary-box", "children")
    ],

    [
        Input("rail-dropdown", "value"),
        Input("buffer-dropdown", "value")
    ]
)

def update_dashboard(selected_station, buffer_km):

    fig = create_base_map()

    if selected_station is None:

        return (
            fig,
            [],
            html.Div([
                html.H4("No Railway Station Selected")
            ])
        )

    station = rail_df[
        rail_df["Name"] == selected_station
    ]

    if station.empty:

        return (
            fig,
            [],
            html.Div([
                html.H4("Station Not Found")
            ])
        )

    station_lat = station.iloc[0]["Latitude"]
    station_lon = station.iloc[0]["Longitude"]

    # =====================================================
    # HIGHLIGHT STATION
    # =====================================================

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

    # =====================================================
    # FIND NEARBY COLD STORAGES
    # =====================================================

    nearby = []

    for _, row in cold_df.iterrows():

        dist = haversine(
            station_lat,
            station_lon,
            row["Latitude"],
            row["Longitude"]
        )

        if dist <= buffer_km:

            nearby.append({
                "District": row["District"],
                "Name": row["Name"],
                "Capacity": row["Capacity"],
                "Latitude": round(row["Latitude"], 5),
                "Longitude": round(row["Longitude"], 5),
                "Distance": round(dist, 2)
            })

    # =====================================================
    # PLOT NEARBY POINTS
    # =====================================================

    if len(nearby) > 0:

        nearby_df = pd.DataFrame(nearby)

        fig.add_trace(
            go.Scattermapbox(
                lat=nearby_df["Latitude"],
                lon=nearby_df["Longitude"],
                mode="markers",
                marker=dict(
                    size=15,
                    color="cyan"
                ),
                text=nearby_df["Name"],
                name="Nearby Cold Storages"
            )
        )

        total_capacity = nearby_df["Capacity"].sum()

        summary = html.Div([

            html.H4("Analysis Summary"),

            html.P(
                f"Selected Railway Station: {selected_station}"
            ),

            html.P(
                f"Buffer Radius: {buffer_km} KM"
            ),

            html.P(
                f"Nearby Cold Storages: {len(nearby_df)}"
            ),

            html.P(
                f"Total Capacity: {total_capacity}"
            )

        ])

    else:

        nearby_df = pd.DataFrame()

        summary = html.Div([

            html.H4("No Cold Storages Found"),
            html.P(
                f"No cold storages within {buffer_km} KM"
            )

        ])

    fig.update_layout(

        mapbox=dict(
            center=dict(
                lat=station_lat,
                lon=station_lon
            ),
            zoom=7
        )
    )

    return (
        fig,
        nearby_df.to_dict("records"),
        summary
    )

# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":
    app.run_server(debug=False)
