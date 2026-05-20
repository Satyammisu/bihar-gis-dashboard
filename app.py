import pandas as pd
import json
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

# =====================================================
# LOAD BIHAR BOUNDARY GEOJSON
# =====================================================

with open("bihar_boundary.geojson", "r", encoding="utf-8") as f:
    bihar_geojson = json.load(f)

# =====================================================
# SAFE CSV LOADER
# =====================================================

def load_csv(file_name):

    df = pd.read_csv(file_name, encoding="utf-8")

    # normalize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df

# =====================================================
# LOAD ALL DATASETS
# =====================================================

cold_df = load_csv("cold_storage.csv")
rail_df = load_csv("railway_stations.csv")
airport_df = load_csv("airport.csv")
mandi_df = load_csv("mandis.csv")

# =====================================================
# STANDARDIZE COLUMNS
# =====================================================

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

# =====================================================
# CLEAN DATA
# =====================================================

cold_df = standardize_columns(cold_df)
rail_df = standardize_columns(rail_df)
airport_df = standardize_columns(airport_df)
mandi_df = standardize_columns(mandi_df)

# =====================================================
# VERIFY DATA
# =====================================================

print("Cold Storage Columns:", cold_df.columns)
print("Railway Columns:", rail_df.columns)
print("Airport Columns:", airport_df.columns)
print("Mandi Columns:", mandi_df.columns)

print("Railway Records:", len(rail_df))
print("Cold Storage Records:", len(cold_df))

# =====================================================
# CREATE DASH APP
# =====================================================

app = Dash(__name__)
server = app.server

# =====================================================
# INITIAL MAP
# =====================================================

fig = go.Figure()

# Bihar boundary
fig.add_trace(
    go.Choroplethmapbox(
        geojson=bihar_geojson,
        locations=[0],
        z=[1],
        colorscale=[[0, "lightgrey"], [1, "lightgrey"]],
        showscale=False,
        marker_opacity=0.2,
        marker_line_width=1
    )
)

# Cold storage markers
fig.add_trace(
    go.Scattermapbox(
        lat=cold_df["Latitude"],
        lon=cold_df["Longitude"],
        mode="markers",
        marker=go.scattermapbox.Marker(
            size=8,
            color="blue"
        ),
        text=cold_df["Name"],
        name="Cold Storage"
    )
)

# Railway station markers
fig.add_trace(
    go.Scattermapbox(
        lat=rail_df["Latitude"],
        lon=rail_df["Longitude"],
        mode="markers",
        marker=go.scattermapbox.Marker(
            size=9,
            color="red"
        ),
        text=rail_df["Name"],
        name="Railway Station"
    )
)

# Airport markers
fig.add_trace(
    go.Scattermapbox(
        lat=airport_df["Latitude"],
        lon=airport_df["Longitude"],
        mode="markers",
        marker=go.scattermapbox.Marker(
            size=10,
            color="green"
        ),
        text=airport_df["Name"],
        name="Airport"
    )
)

# Mandi markers
fig.add_trace(
    go.Scattermapbox(
        lat=mandi_df["Latitude"],
        lon=mandi_df["Longitude"],
        mode="markers",
        marker=go.scattermapbox.Marker(
            size=7,
            color="orange"
        ),
        text=mandi_df["Name"],
        name="Mandis"
    )
)

# Map Layout
fig.update_layout(
    mapbox_style="open-street-map",
    mapbox_zoom=6,
    mapbox_center={"lat": 25.6, "lon": 85.1},
    margin={"r":0,"t":0,"l":0,"b":0},
    height=700
)

# =====================================================
# DISTRICT CHART
# =====================================================

district_chart = px.bar(
    cold_df.groupby("District").size().reset_index(name="Cold Storages"),
    x="District",
    y="Cold Storages",
    title="District Wise Cold Storages"
)

# =====================================================
# APP LAYOUT
# =====================================================

app.layout = html.Div([

    html.H1(
        "Bihar GIS Dashboard",
        style={
            "textAlign": "center",
            "color": "#003366"
        }
    ),

    html.Div([

        html.Div([

            html.H2("Railway Station Buffer"),

            dcc.Dropdown(
                id="station-dropdown",
                options=[
                    {
                        "label": name,
                        "value": name
                    }
                    for name in sorted(rail_df["Name"].unique())
                ],
                placeholder="Select Railway Station"
            ),

            dcc.Dropdown(
                id="buffer-distance",
                options=[
                    {"label": "5 KM", "value": 5},
                    {"label": "10 KM", "value": 10},
                    {"label": "20 KM", "value": 20},
                    {"label": "50 KM", "value": 50},
                ],
                value=5
            ),

            html.Br(),

            html.Button(
                "Generate Buffer",
                id="generate-button",
                n_clicks=0,
                style={
                    "backgroundColor": "#007BFF",
                    "color": "white",
                    "padding": "12px",
                    "border": "none",
                    "width": "100%",
                    "fontSize": "18px"
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
            "padding": "20px",
            "display": "inline-block",
            "verticalAlign": "top"
        }),

        html.Div([

            dcc.Graph(
                id="map",
                figure=fig
            )

        ],
        style={
            "width": "68%",
            "display": "inline-block"
        })

    ])

])

# =====================================================
# BUFFER CALLBACK
# =====================================================

@app.callback(
    Output("map", "figure"),
    Input("generate-button", "n_clicks"),
    Input("station-dropdown", "value"),
    Input("buffer-distance", "value")
)

def update_map(n_clicks, selected_station, buffer_distance):

    updated_fig = go.Figure(fig)

    if selected_station:

        station_row = rail_df[
            rail_df["Name"] == selected_station
        ]

        if not station_row.empty:

            lat = station_row.iloc[0]["Latitude"]
            lon = station_row.iloc[0]["Longitude"]

            updated_fig.add_trace(
                go.Scattermapbox(
                    lat=[lat],
                    lon=[lon],
                    mode="markers",
                    marker=go.scattermapbox.Marker(
                        size=25,
                        color="yellow"
                    ),
                    text=[selected_station],
                    name="Selected Station"
                )
            )

            updated_fig.update_layout(
                mapbox_center={
                    "lat": lat,
                    "lon": lon
                },
                mapbox_zoom=8
            )

    return updated_fig

# =====================================================
# RUN SERVER
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)
