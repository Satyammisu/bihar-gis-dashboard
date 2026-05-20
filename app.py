import pandas as pd
import json
from math import radians, cos, sin, sqrt, atan2

from dash import Dash, dcc, html, dash_table, Input, Output
import plotly.express as px
import dash_leaflet as dl

# ============================================
# CREATE DASH APP
# ============================================

app = Dash(__name__)
server = app.server

# ============================================
# LOAD BIHAR BOUNDARY
# ============================================

with open("bihar_boundary.geojson", "r", encoding="utf-8") as f:
    bihar_boundary = json.load(f)

# ============================================
# LOAD CSV FILES
# ============================================

cold_df = pd.read_csv("cold_storage.csv")
rail_df = pd.read_csv("railway_stations.csv")
airport_df = pd.read_csv("airport.csv")
mandi_df = pd.read_csv("mandis.csv")

# ============================================
# RENAME COLUMNS
# ============================================

cold_df.rename(columns={
    'Cold Storage_Name': 'Name',
    'Capacity and UOM': 'Capacity'
}, inplace=True)

# ============================================
# SAFE COLUMN HANDLING - COLD STORAGE
# ============================================

if 'Name' not in cold_df.columns:
    cold_df['Name'] = 'Cold Storage'
else:
    cold_df['Name'] = cold_df['Name'].fillna('Cold Storage')

if 'District' not in cold_df.columns:
    cold_df['District'] = 'Unknown'
else:
    cold_df['District'] = cold_df['District'].fillna('Unknown')

if 'Capacity' not in cold_df.columns:
    cold_df['Capacity'] = 'N/A'
else:
    cold_df['Capacity'] = cold_df['Capacity'].fillna('N/A')

if 'Latitude' not in cold_df.columns:
    cold_df['Latitude'] = 0

if 'Longitude' not in cold_df.columns:
    cold_df['Longitude'] = 0

# ============================================
# SAFE COLUMN HANDLING - RAILWAY
# ============================================

rail_df.columns = rail_df.columns.str.strip()

if 'Station' not in rail_df.columns:
    if len(rail_df.columns) > 0:
        rail_df.rename(columns={rail_df.columns[0]: 'Station'}, inplace=True)
    else:
        rail_df['Station'] = 'Unknown Station'

if 'Latitude' not in rail_df.columns:
    rail_df['Latitude'] = 0

if 'Longitude' not in rail_df.columns:
    rail_df['Longitude'] = 0

rail_df['Station'] = rail_df['Station'].fillna('Unknown Station')

# ============================================
# SAFE COLUMN HANDLING - AIRPORT
# ============================================

airport_df.columns = airport_df.columns.str.strip()

if 'Name' not in airport_df.columns:
    if len(airport_df.columns) > 0:
        airport_df.rename(columns={airport_df.columns[0]: 'Name'}, inplace=True)
    else:
        airport_df['Name'] = 'Airport'

if 'Latitude' not in airport_df.columns:
    airport_df['Latitude'] = 0

if 'Longitude' not in airport_df.columns:
    airport_df['Longitude'] = 0

airport_df['Name'] = airport_df['Name'].fillna('Airport')

# ============================================
# SAFE COLUMN HANDLING - MANDI
# ============================================

mandi_df.columns = mandi_df.columns.str.strip()

if 'Name' not in mandi_df.columns:
    if len(mandi_df.columns) > 0:
        mandi_df.rename(columns={mandi_df.columns[0]: 'Name'}, inplace=True)
    else:
        mandi_df['Name'] = 'Mandi'

if 'Latitude' not in mandi_df.columns:
    mandi_df['Latitude'] = 0

if 'Longitude' not in mandi_df.columns:
    mandi_df['Longitude'] = 0

mandi_df['Name'] = mandi_df['Name'].fillna('Mandi')

# ============================================
# DISTRICT WISE CHART
# ============================================

district_count = cold_df.groupby("District").size().reset_index(name="Cold Storages")

fig = px.bar(
    district_count,
    x="District",
    y="Cold Storages",
    title="District Wise Cold Storages"
)

# ============================================
# HAVERSINE DISTANCE FUNCTION
# ============================================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

# ============================================
# MAP MARKERS
# ============================================

cold_markers = [
    dl.CircleMarker(
        center=[row["Latitude"], row["Longitude"]],
        radius=6,
        color="blue",
        children=[
            dl.Tooltip(
                f"{row['Name']} | {row['District']}"
            )
        ]
    )
    for _, row in cold_df.iterrows()
]

rail_markers = [
    dl.CircleMarker(
        center=[row["Latitude"], row["Longitude"]],
        radius=6,
        color="red",
        children=[
            dl.Tooltip(row["Station"])
        ]
    )
    for _, row in rail_df.iterrows()
]

airport_markers = [
    dl.CircleMarker(
        center=[row["Latitude"], row["Longitude"]],
        radius=8,
        color="green",
        children=[
            dl.Tooltip(row["Name"])
        ]
    )
    for _, row in airport_df.iterrows()
]

mandi_markers = [
    dl.CircleMarker(
        center=[row["Latitude"], row["Longitude"]],
        radius=5,
        color="orange",
        children=[
            dl.Tooltip(row["Name"])
        ]
    )
    for _, row in mandi_df.iterrows()
]

# ============================================
# APP LAYOUT
# ============================================

app.layout = html.Div([

    html.H1(
        "Bihar GIS Dashboard",
        style={
            "textAlign": "center",
            "color": "darkblue"
        }
    ),

    html.Div([

        html.Div([
            html.H2(f"Cold Storages: {len(cold_df)}"),
            html.H2(f"Railway Stations: {len(rail_df)}"),
            html.H2(f"Airports: {len(airport_df)}"),
            html.H2(f"Mandis: {len(mandi_df)}")
        ],
        style={
            "width": "30%",
            "display": "inline-block",
            "verticalAlign": "top",
            "padding": "10px"
        }),

        html.Div([

            html.H2("Railway Station Buffer"),

            dcc.Dropdown(
                id="rail-dropdown",
                options=[
                    {
                        "label": row["Station"],
                        "value": row["Station"]
                    }
                    for _, row in rail_df.iterrows()
                ],
                placeholder="Select Railway Station"
            ),

            dcc.Dropdown(
                id="buffer-dropdown",
                options=[
                    {"label": "5 KM", "value": 5},
                    {"label": "10 KM", "value": 10},
                    {"label": "20 KM", "value": 20},
                    {"label": "50 KM", "value": 50}
                ],
                value=5
            ),

            html.Br(),

            html.Button(
                "Generate Buffer",
                id="buffer-btn",
                n_clicks=0,
                style={
                    "backgroundColor": "blue",
                    "color": "white",
                    "padding": "10px",
                    "border": "none"
                }
            ),

            html.Br(),
            html.Br(),

            dcc.Graph(figure=fig),

            html.H2("Cold Storage Details"),

            dash_table.DataTable(
                id="cold-table",
                columns=[
                    {"name": i, "id": i}
                    for i in cold_df.columns
                ],
                data=cold_df.to_dict("records"),
                page_size=10,
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "padding": "5px"
                },
                style_header={
                    "backgroundColor": "darkblue",
                    "color": "white",
                    "fontWeight": "bold"
                }
            )

        ],
        style={
            "width": "35%",
            "display": "inline-block",
            "verticalAlign": "top",
            "padding": "10px"
        }),

        html.Div([

            dl.Map(
                center=[25.6, 85.1],
                zoom=7,
                children=[

                    dl.TileLayer(),

                    dl.GeoJSON(
                        data=bihar_boundary,
                        options={
                            "style": {
                                "color": "black",
                                "weight": 2,
                                "fillOpacity": 0
                            }
                        }
                    ),

                    dl.LayerGroup(cold_markers),
                    dl.LayerGroup(rail_markers),
                    dl.LayerGroup(airport_markers),
                    dl.LayerGroup(mandi_markers),

                    dl.LayerGroup(id="buffer-layer")

                ],
                style={
                    "width": "100%",
                    "height": "900px"
                }
            )

        ],
        style={
            "width": "30%",
            "display": "inline-block",
            "verticalAlign": "top"
        })

    ])

])

# ============================================
# BUFFER CALLBACK
# ============================================

@app.callback(
    Output("buffer-layer", "children"),
    Input("buffer-btn", "n_clicks"),
    Input("rail-dropdown", "value"),
    Input("buffer-dropdown", "value")
)
def generate_buffer(n_clicks, station, buffer_km):

    if station is None:
        return []

    selected = rail_df[rail_df["Station"] == station]

    if selected.empty:
        return []

    lat = selected.iloc[0]["Latitude"]
    lon = selected.iloc[0]["Longitude"]

    nearby = []

    for _, row in cold_df.iterrows():

        distance = haversine(
            lat,
            lon,
            row["Latitude"],
            row["Longitude"]
        )

        if distance <= buffer_km:

            nearby.append(
                dl.CircleMarker(
                    center=[
                        row["Latitude"],
                        row["Longitude"]
                    ],
                    radius=10,
                    color="yellow",
                    children=[
                        dl.Tooltip(
                            f"{row['Name']} ({distance:.2f} KM)"
                        )
                    ]
                )
            )

    return [

        dl.Circle(
            center=[lat, lon],
            radius=buffer_km * 1000,
            color="red",
            fillOpacity=0.1
        )

    ] + nearby

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    app.run_server(
        debug=False,
        host="0.0.0.0",
        port=8050
    )
