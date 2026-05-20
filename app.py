from flask import Flask, render_template_string
import json
import os
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)

# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = BASE_DIR

# =========================================================
# LOAD GEOJSON
# =========================================================

def load_geojson(filename):
    filepath = os.path.join(DATA_DIR, filename)

    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    return {"type": "FeatureCollection", "features": []}

# =========================================================
# LOAD DATA
# =========================================================

cold_storage = load_geojson("cold_storage.geojson")
railway_station = load_geojson("railway_station.geojson")
airport = load_geojson("airport.geojson")
mandis = load_geojson("mandis.geojson")
bihar_boundary = load_geojson("bihar_boundary.geojson")

# =========================================================
# HAVERSINE DISTANCE
# =========================================================

def haversine(lat1, lon1, lat2, lon2):

    lon1, lat1, lon2, lat2 = map(
        radians,
        [lon1, lat1, lon2, lat2]
    )

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2

    c = 2 * asin(sqrt(a))

    r = 6371

    return round(c * r, 2)

# =========================================================
# DISTRICT SUMMARY
# =========================================================

district_counts = {}

for feature in cold_storage.get("features", []):

    props = feature.get("properties", {})

    district = props.get("district", "Unknown")

    district_counts[district] = district_counts.get(district, 0) + 1

district_labels = list(district_counts.keys())
district_values = list(district_counts.values())

# =========================================================
# HTML TEMPLATE
# =========================================================

HTML = """

<!DOCTYPE html>
<html>

<head>

<title>Bihar GIS Dashboard</title>

<meta charset="utf-8"/>

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link rel="stylesheet"
href="https://unpkg.com/leaflet/dist/leaflet.css"/>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>

body{
margin:0;
padding:0;
font-family:Arial;
background:#f4f7fb;
}

.container{
display:flex;
height:100vh;
}

.sidebar{
width:30%;
overflow-y:auto;
padding:15px;
background:white;
}

.map-container{
width:70%;
}

#map{
height:100vh;
width:100%;
}

.card{
background:white;
padding:15px;
border-radius:10px;
margin-bottom:15px;
box-shadow:0px 2px 5px rgba(0,0,0,0.1);
}

h1{
background:#0b4dbb;
color:white;
padding:20px;
border-radius:10px;
font-size:36px;
}

.summary-box{
background:linear-gradient(to right,#0b4dbb,#1f78ff);
padding:15px;
color:white;
border-radius:10px;
margin-bottom:10px;
font-size:24px;
font-weight:bold;
}

select,button{
width:100%;
padding:12px;
margin-top:10px;
font-size:16px;
border-radius:6px;
border:1px solid #ccc;
}

button{
background:#1565c0;
color:white;
border:none;
cursor:pointer;
font-weight:bold;
}

button:hover{
background:#0d47a1;
}

table{
width:100%;
border-collapse:collapse;
font-size:12px;
}

table th{
background:#0b4dbb;
color:white;
padding:8px;
}

table td{
padding:8px;
border:1px solid #ddd;
}

.legend{
background:white;
padding:10px;
line-height:25px;
color:#333;
}

.legend i{
width:18px;
height:18px;
float:left;
margin-right:8px;
opacity:0.9;
}

</style>

</head>

<body>

<div class="container">

<div class="sidebar">

<h1>Bihar GIS Dashboard</h1>

<div class="card">

<h2>Summary</h2>

<div class="summary-box">
Cold Storages: {{cold_count}}
</div>

<div class="summary-box">
Railway Stations: {{rail_count}}
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

<select id="stationSelect">

<option value="">Select Railway Station</option>

{% for station in station_names %}

<option value="{{station}}">
{{station}}
</option>

{% endfor %}

</select>

<select id="bufferDistance">

<option value="5">5 KM</option>
<option value="10">10 KM</option>
<option value="20">20 KM</option>

</select>

<button onclick="generateBuffer()">
Generate Buffer
</button>

</div>

<div class="card">

<h2>District Wise Cold Storages</h2>

<canvas id="districtChart"></canvas>

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

{% for row in table_data %}

<tr>

<td>{{row.district}}</td>
<td>{{row.name}}</td>
<td>{{row.capacity}}</td>
<td>{{row.distance}}</td>
<td>{{row.lat}}</td>
<td>{{row.lon}}</td>

</tr>

{% endfor %}

</table>

</div>

</div>

<div class="map-container">

<div id="map"></div>

</div>

</div>

<script>

var map = L.map('map').setView([25.6,85.1],7);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
{
maxZoom:19
}
).addTo(map);

var coldData = {{cold_storage|safe}};
var railData = {{railway_station|safe}};
var airportData = {{airport|safe}};
var mandiData = {{mandis|safe}};
var boundaryData = {{bihar_boundary|safe}};

L.geoJSON(boundaryData,{
style:{
color:'black',
weight:2,
fillOpacity:0
}
}).addTo(map);

var coldLayer = L.geoJSON(coldData,{

pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:6,
fillColor:'red',
color:'white',
weight:1,
fillOpacity:1
});

},

onEachFeature:function(feature,layer){

var p = feature.properties;

layer.bindPopup(
"<b>Cold Storage</b><br>"+
"District: "+(p.district || 'N/A')+"<br>"+
"Capacity: "+(p.capacity || 'N/A')
);

}

}).addTo(map);

var railLayer = L.geoJSON(railData,{

pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:6,
fillColor:'blue',
color:'white',
weight:1,
fillOpacity:1
});

},

onEachFeature:function(feature,layer){

var p = feature.properties;

layer.bindPopup(
"<b>Railway Station</b><br>"+
(p.name || 'N/A')
);

}

}).addTo(map);

var airportLayer = L.geoJSON(airportData,{
pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:6,
fillColor:'green',
color:'white',
weight:1,
fillOpacity:1
});

}
}).addTo(map);

var mandiLayer = L.geoJSON(mandiData,{
pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:6,
fillColor:'orange',
color:'white',
weight:1,
fillOpacity:1
});

}
}).addTo(map);

function generateBuffer(){

var stationName =
document.getElementById("stationSelect").value;

var distance =
document.getElementById("bufferDistance").value;

railData.features.forEach(function(feature){

if(feature.properties.name == stationName){

var lat =
feature.geometry.coordinates[1];

var lon =
feature.geometry.coordinates[0];

L.circle([lat,lon],{
radius:distance*1000,
color:'green',
fillOpacity:0.1
}).addTo(map);

map.setView([lat,lon],10);

}

});

}

var ctx =
document.getElementById('districtChart');

new Chart(ctx,{
type:'bar',
data:{
labels: {{district_labels|safe}},
datasets:[{
label:'Cold Storages',
data: {{district_values|safe}},
backgroundColor:'#1565c0'
}]
}
});

</script>

</body>
</html>

"""

# =========================================================
# TABLE DATA
# =========================================================

table_data = []

for feature in cold_storage.get("features", [])[:50]:

    props = feature.get("properties", {})

    coords = feature.get("geometry", {}).get("coordinates", [0,0])

    lon = coords[0]
    lat = coords[1]

    table_data.append({
        "district": props.get("district", "N/A"),
        "name": props.get("name", "Cold Storage"),
        "capacity": props.get("capacity", "N/A"),
        "distance": "N/A",
        "lat": lat,
        "lon": lon
    })

# =========================================================
# HOME ROUTE
# =========================================================

@app.route("/")

def home():

    station_names = []

    for feature in railway_station.get("features", []):

        props = feature.get("properties", {})

        name = props.get("name")

        if name:
            station_names.append(name)

    return render_template_string(

        HTML,

        cold_count=len(cold_storage.get("features", [])),
        rail_count=len(railway_station.get("features", [])),
        airport_count=len(airport.get("features", [])),
        mandi_count=len(mandis.get("features", [])),

        station_names=station_names,

        district_labels=district_labels,
        district_values=district_values,

        table_data=table_data,

        cold_storage=json.dumps(cold_storage),
        railway_station=json.dumps(railway_station),
        airport=json.dumps(airport),
        mandis=json.dumps(mandis),
        bihar_boundary=json.dumps(bihar_boundary)

    )

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
