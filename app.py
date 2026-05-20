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
# LOAD BIHAR DISTRICT BOUNDARY
# =========================================================

with open("data/bihar_district_boundary.geojson", "r", encoding="utf-8") as f:
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
# LOAD DATA
# =========================================================

cold_df = load_csv("data/cold_storage.csv")
rail_df = load_csv("data/railway_stations.csv")
airport_df = load_csv("data/airport.csv")
mandi_df = load_csv("data/mandis.csv")

# =========================================================
# STANDARDIZE COLUMNS
# =========================================================

def standardize_columns(df):

    column_mapping = {}

    for col in df.columns:

        if "station" in col:
            column_mapping[col] = "Name"

        elif "name" in col:
            column_mapping[col] = "Name"

        elif "district" in col:
            column_mapping[col] = "District"

        elif "capacity" in col:
            column_mapping[col] = "Capacity"

        elif "lat" in col:
            column_mapping[col] = "Latitude"

        elif "lon" in col:
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

    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df["Capacity"] = pd.to_numeric(df["Capacity"], errors="coerce").fillna(0)

    df = df.dropna(subset=["Latitude", "Longitude"])

    return df

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
# CREATE MODERN MAP
# =========================================================

def create_map():

    fig = go.Figure()

    # =====================================================
    # BIHAR DISTRICT BOUNDARY
    # =====================================================

    fig.add_trace(
        go.Choroplethmapbox(
            geojson=district_geojson,
            locations=[i for i in range(len(district_geojson["features"]))],
            z=[1] * len(district_geojson["features"]),
            colorscale=[[0, "#dfefff"], [1, "#dfefff"]],
            showscale=False,
            marker_line_width=1,
            marker_line_color="black",
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
                color="#1e88e5"
            ),
            text=cold_df["Name"],
            name="Cold Storage"
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
                size=11,
                color="#e53935"
            ),
            text=rail_df["Name"],
            name="Railway Station"
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
                size=11,
                color="#43a047"
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
                color="#fb8c00"
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

        mapbox_zoom=6.4,

        mapbox_center={
            "lat": 25.7,
            "lon": 85.3
        },

        margin={
            "r": 0,
            "t": 0,
            "l": 0,
            "b": 0
        },

        height=800,

        legend=dict(
            bgcolor="white",
            bordercolor="lightgray",
            borderwidth=1
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

    color="Cold Storages",

    title="District Wise Cold Storages"
)

district_chart.update_layout(
    template="plotly_white",
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
            "BIHAR GIS INFRASTRUCTURE DASHBOARD",
            style={
                "color": "white",
                "textAlign": "center",
                "padding": "20px",
                "fontWeight": "bold",
                "letterSpacing": "2px"
            }
        )

    ], style={
        "background": "linear-gradient(to right, #0d47a1, #1565c0)"
    }),

    # =====================================================
    # KPI SECTION
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
    # MAIN SECTION
    # =====================================================

    html.Div([

        # =================================================
        # SIDEBAR
        # =================================================

        html.Div([

            html.H2(
                "Railway Buffer Analysis",
                style={
                    "marginBottom": "20px",
                    "color": "#0d47a1"
                }
            ),

            html.Label("Select Railway Station"),

            dcc.Dropdown(
                id="rail-dropdown",

                options=[
                    {
                        "label": str(i),
                        "value": str(i)
                    }
                    for i in sorted(rail_df["Name"].dropna().unique())
                ],

                placeholder="Choose Railway Station",

                searchable=True,

                style={
                    "marginBottom": "20px"
                }
            ),

            html.Label("Select Buffer Distance"),

            dcc.Dropdown(
                id="buffer-dropdown",

                options=[
                    {"label": "5 KM", "value": 5},
                    {"label": "10 KM", "value": 10},
                    {"label": "25 KM", "value": 25},
                    {"label": "50 KM", "value": 50}
                ],

                value=10,

                style={
                    "marginBottom": "20px"
                }
            ),

            html.Label("Search District"),

            dcc.Dropdown(
                id="district-dropdown",

                options=[
                    {
                        "label": i,
                        "value": i
                    }
                    for i in sorted(cold_df["District"].unique())
                ],

                placeholder="Select District",

                searchable=True
            ),

            html.Br(),

            html.Div(
                id="summary-box"
            )

        ], style={

            "width": "25%",
            "backgroundColor": "white",
            "padding": "25px",
            "borderRadius": "15px",
            "boxShadow": "0px 0px 15px rgba(0,0,0,0.1)",
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
            "width": "75%"
        })

    ], style={
        "display": "flex",
        "padding": "20px",
        "gap": "20px"
    }),

    # =====================================================
    # ANALYTICS
    # =====================================================

    html.Div([

        dcc.Graph(
            figure=district_chart
        )

    ], style={
        "padding": "20px"
    }),

    # =====================================================
    # TABLE SECTION
    # =====================================================

    html.Div([

        html.H2(
            "Nearby Cold Storages",
            style={
                "paddingBottom": "15px",
                "color": "#0d47a1"
            }
        ),

        dash_table.DataTable(

            id="cold-table",

            columns=[
                {"name": "District", "id": "District"},
                {"name": "Cold Storage", "id": "Name"},
                {"name": "Capacity", "id": "Capacity"},
                {"name": "Latitude", "id": "Latitude"},
                {"name": "Longitude", "id": "Longitude"},
                {"name": "Distance (KM)", "id": "Distance"}
            ],

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
                "textAlign": "center",
                "padding": "10px"
            }
        )

    ], style={
        "padding": "20px"
    })

], style={
    "backgroundColor": "#f4f7fc",
    "fontFamily": "Arial"
})

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
        Input("district-dropdown", "value")
    ]
)

def update_dashboard(selected_station, buffer_km, selected_district):

    fig = create_map()

    filtered_cold = cold_df.copy()

    if selected_district:

        filtered_cold = filtered_cold[
            filtered_cold["District"] == selected_district
        ]

    nearby_df = pd.DataFrame()

    if selected_station:

        station = rail_df[
            rail_df["Name"] == selected_station
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
                        color="yellow"
                    ),

                    text=[selected_station],

                    name="Selected Station"
                )
            )

            nearby_rows = []

            for _, row in filtered_cold.iterrows():

                distance = haversine(
                    station_lat,
                    station_lon,
                    row["Latitude"],
                    row["Longitude"]
                )

                if distance <= buffer_km:

                    row["Distance"] = round(distance, 2)

                    nearby_rows.append(row)

            if len(nearby_rows) > 0:

                nearby_df = pd.DataFrame(nearby_rows)

                # =========================================
                # BUFFER COLD STORAGE
                # =========================================

                fig.add_trace(
                    go.Scattermapbox(

                        lat=nearby_df["Latitude"],
                        lon=nearby_df["Longitude"],

                        mode="markers",

                        marker=dict(
                            size=14,
                            color="cyan"
                        ),

                        text=nearby_df["Name"],

                        name="Nearby Cold Storages"
                    )
                )

            fig.update_layout(

                mapbox_zoom=8,

                mapbox_center={
                    "lat": station_lat,
                    "lon": station_lon
                }
            )

    summary = html.Div([

        html.H3(
            f"Nearby Cold Storages : {len(nearby_df)}",
            style={"color": "#1565c0"}
        ),

        html.H4(
            f"Total Capacity : {nearby_df['Capacity'].sum():,.0f}"
            if not nearby_df.empty
            else "Total Capacity : 0"
        )

    ])

    return (
        fig,
        nearby_df.to_dict("records"),
        summary
    )

# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run_server(
        host="0.0.0.0",
        port=8050,
        debug=False
    )
