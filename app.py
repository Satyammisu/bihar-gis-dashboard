from flask import Flask, render_template_string
import pandas as pd
import json
import math
import os

app = Flask(__name__)

# =========================================================
# LOAD CSV FILES
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

cold_storage_file = os.path.join(BASE_DIR, "cold_storage.csv")
railway_file = os.path.join(BASE_DIR, "railway_stations.csv")
airport_file = os.path.join(BASE_DIR, "airport.csv")
mandi_file = os.path.join(BASE_DIR, "mandis.csv")

# =========================================================
# READ CSV DATA
# =========================================================

cold_df = pd.read_csv(cold_storage_file)
railway_df = pd.read_csv(railway_file)
airport_df = pd.read_csv(airport_file)
mandi_df = pd.read_csv(mandi_file)

# =========================================================
# CLEAN COLUMN NAMES
# =========================================================

cold_df.columns = cold_df.columns.str.strip()
railway_df.columns = railway_df.columns.str.strip()
airport_df.columns = airport_df.columns.str.strip()
mandi_df.columns = mandi_df.columns.str.strip()

# =========================================================
# REQUIRED COLUMN FIXES
# =========================================================

cold_df.rename(columns={
    'district': 'District',
    'name': 'Name',
    'capacity': 'Capacity',
    'latitude': 'Latitude',
    'longitude': 'Longitude'
}, inplace=True)

railway_df.rename(columns={
    'station_name': 'Station_Name',
    'latitude': 'Latitude',
    'longitude': 'Longitude'
}, inplace=True)

airport_df.rename(columns={
    'airport_name': 'Airport_Name',
    'latitude': 'Latitude',
    'longitude': 'Longitude'
}, inplace=True)

mandi_df.rename(columns={
    'mandi_name': 'Mandi_Name',
    'latitude': 'Latitude',
    'longitude': 'Longitude'
}, inplace=True)

# =========================================================
# FILL MISSING VALUES
# =========================================================

cold_df['District'] = cold_df.get('District', 'Unknown').fillna('Unknown')
cold_df['Name'] = cold_df.get('Name', 'Cold Storage').fillna('Cold Storage')
cold_df['Capacity'] = cold_df.get('Capacity', 'N/A').fillna('N/A')

railway_df['Station_Name'] = railway_df.get(
    'Station_Name',
    'Railway Station'
).fillna('Railway Station')

# =========================================================
# CONVERT LAT LONG
# =========================================================

cold_df['Latitude'] = pd.to_numeric(cold_df['Latitude'], errors='coerce')
cold_df['Longitude'] = pd.to_numeric(cold_df['Longitude'], errors='coerce')

railway_df['Latitude'] = pd.to_numeric(
    railway_df['Latitude'],
    errors='coerce'
)

railway_df['Longitude'] = pd.to_numeric(
    railway_df['Longitude'],
    errors='coerce'
)

airport_df['Latitude'] = pd.to_numeric(
    airport_df['Latitude'],
    errors='coerce'
)

airport_df['Longitude'] = pd.to_numeric(
    airport_df['Longitude'],
    errors='coerce'
)

mandi_df['Latitude'] = pd.to_numeric(
    mandi_df['Latitude'],
    errors='coerce'
)

mandi_df['Longitude'] = pd.to_numeric(
    mandi_df['Longitude'],
    errors='coerce'
)

# =========================================================
# REMOVE INVALID COORDINATES
# =========================================================

cold_df = cold_df.dropna(subset=['Latitude', 'Longitude'])
railway_df = railway_df.dropna(subset=['Latitude', 'Longitude'])
airport_df = airport_df.dropna(subset=['Latitude', 'Longitude'])
mandi_df = mandi_df.dropna(subset=['Latitude', 'Longitude'])

# =========================================================
# DISTRICT WISE SUMMARY
# =========================================================

district_summary = cold_df.groupby('District').size().reset_index(name='Count')

district_labels = district_summary['District'].tolist()
district_values = district_summary['Count'].tolist()

# =========================================================
# HAVERSINE DISTANCE
# =========================================================

def haversine(lat1, lon1, lat2, lon2):

    R = 6371

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 2)

# =========================================================
# RAILWAY BUFFER CALCULATION
# =========================================================

buffer_station = railway_df.iloc[0]

station_lat = buffer_station['Latitude']
station_lon = buffer_station['Longitude']

cold_df['Distance'] = cold_df.apply(
    lambda row: haversine(
        station_lat,
        station_lon,
        row['Latitude'],
        row['Longitude']
    ),
    axis=1
)

# =========================================================
# HTML TEMPLATE
# =========================================================

HTML = """

<!DOCTYPE html>
<html>
<head>

<title>Bihar GIS Dashboard</title>

<meta charset="utf-8" />

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link rel="stylesheet"
href="https://unpkg.com/leaflet/dist/leaflet.css"/>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

<style>

body{
margin:0;
padding:0;
font-family:Arial;
background:#f4f6f9;
}

.container{
display:flex;
height:100vh;
}

.sidebar{
width:38%;
overflow-y:auto;
padding:20px;
background:white;
}

.map{
width:62%;
height:100vh;
}

.card{
background:white;
padding:15px;
margin-bottom:20px;
border-radius:10px;
box-shadow:0 2px 5px rgba(0,0,0,0.2);
}

.summary-box{
background:linear-gradient(90deg,#0f4cdd,#1d6cff);
color:white;
padding:15px;
margin-bottom:10px;
border-radius:8px;
font-size:22px;
font-weight:bold;
}

table{
width:100%;
border-collapse:collapse;
font-size:14px;
}

table th{
background:#0f4cdd;
color:white;
padding:10px;
}

table td{
padding:8px;
border:1px solid #ccc;
}

select{
width:100%;
padding:10px;
margin-bottom:10px;
}

button{
width:100%;
padding:12px;
background:#0f4cdd;
color:white;
border:none;
border-radius:5px;
font-size:16px;
cursor:pointer;
}

</style>

</head>

<body>

<div class="container">

<div class="sidebar">

<div class="card">

<h1>Bihar GIS Dashboard</h1>

<div class="summary-box">
Cold Storages: {{cold_count}}
</div>

<div class="summary-box">
Railway Stations: {{railway_count}}
</div>

<div class="summary-box">
Airports: {{airport_count}}
</div>

<div class="summary-box">
Mandis: {{mandi_count}}
</div>

</div>

<div class="card">

<h2>Railway Station Buffer</h2>

<select>

{% for station in railway_names %}

<option>{{station}}</option>

{% endfor %}

</select>

<select>
<option>5 KM</option>
<option>10 KM</option>
<option>20 KM</option>
<option>50 KM</option>
</select>

<button>Generate Buffer</button>

</div>

<div class="card">

<h2>District Wise Cold Storages</h2>

<div id="chart"></div>

</div>

<div class="card">

<h2>Cold Storage Details</h2>

<table>

<tr>
<th>District</th>
<th>Name</th>
<th>Capacity</th>
<th>Distance</th>
<th>Latitude</th>
<th>Longitude</th>
</tr>

{% for row in cold_rows %}

<tr>

<td>{{row.District}}</td>
<td>{{row.Name}}</td>
<td>{{row.Capacity}}</td>
<td>{{row.Distance}}</td>
<td>{{row.Latitude}}</td>
<td>{{row.Longitude}}</td>

</tr>

{% endfor %}

</table>

</div>

</div>

<div id="map" class="map"></div>

</div>

<script>

var map = L.map('map').setView([25.5,85.3],7);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
{
maxZoom:19
}
).addTo(map);

var cold = {{cold_json | safe}};
var railway = {{railway_json | safe}};
var airport = {{airport_json | safe}};
var mandi = {{mandi_json | safe}};

cold.forEach(function(d){

L.circleMarker(
[d.Latitude,d.Longitude],
{
radius:6,
color:'red'
}
)
.addTo(map)
.bindPopup(
"<b>"+d.Name+"</b><br>"
+"District: "+d.District+"<br>"
+"Capacity: "+d.Capacity
);

});

railway.forEach(function(d){

L.circleMarker(
[d.Latitude,d.Longitude],
{
radius:6,
color:'blue'
}
)
.addTo(map)
.bindPopup(d.Station_Name);

});

airport.forEach(function(d){

L.circleMarker(
[d.Latitude,d.Longitude],
{
radius:6,
color:'green'
}
)
.addTo(map)
.bindPopup(d.Airport_Name);

});

mandi.forEach(function(d){

L.circleMarker(
[d.Latitude,d.Longitude],
{
radius:6,
color:'orange'
}
)
.addTo(map)
.bindPopup(d.Mandi_Name);

});

Plotly.newPlot(
'chart',
[
{
x: {{district_labels | safe}},
y: {{district_values | safe}},
type:'bar'
}
]
);

</script>

</body>
</html>

"""

# =========================================================
# HOME ROUTE
# =========================================================

@app.route("/")

def home():

    return render_template_string(
        HTML,

        cold_count=len(cold_df),
        railway_count=len(railway_df),
        airport_count=len(airport_df),
        mandi_count=len(mandi_df),

        railway_names=railway_df['Station_Name'].tolist(),

        district_labels=json.dumps(district_labels),
        district_values=json.dumps(district_values),

        cold_rows=cold_df.head(100).to_dict(orient='records'),

        cold_json=cold_df.to_json(orient='records'),
        railway_json=railway_df.to_json(orient='records'),
        airport_json=airport_df.to_json(orient='records'),
        mandi_json=mandi_df.to_json(orient='records')
    )

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
