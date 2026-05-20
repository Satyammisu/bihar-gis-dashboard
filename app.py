from flask import Flask, render_template_string
import json
import os
import math

app = Flask(__name__)

# =========================================================
# LOAD GEOJSON
# =========================================================

def load_geojson(filename):
    path = os.path.join(os.path.dirname(__file__), filename)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    return {"type": "FeatureCollection", "features": []}


cold_storage = load_geojson("cold_storage.geojson")
railway_station = load_geojson("railway_station.geojson")
airport = load_geojson("airport.geojson")
mandis = load_geojson("mandis.geojson")
bihar_boundary = load_geojson("bihar_boundary.geojson")


# =========================================================
# HAVERSINE DISTANCE
# =========================================================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371

    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)

    a = (
        math.sin(dLat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dLon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 2)


# =========================================================
# FIELD EXTRACTION
# =========================================================

def get_field(props, possible_fields):

    for field in possible_fields:
        if field in props and props[field] not in [None, "", "NULL"]:
            return props[field]

    return "N/A"


# =========================================================
# PREPARE COLD STORAGE TABLE
# =========================================================

cold_storage_table = []

district_counts = {}

for feature in cold_storage["features"]:

    props = feature.get("properties", {})
    coords = feature.get("geometry", {}).get("coordinates", [0, 0])

    lon = coords[0]
    lat = coords[1]

    district = get_field(props, [
        "district",
        "District",
        "DISTRICT",
        "district_name"
    ])

    name = get_field(props, [
        "name",
        "Name",
        "cold_storage",
        "Cold_Storage",
        "storage_name"
    ])

    capacity = get_field(props, [
        "capacity",
        "Capacity",
        "CAPACITY",
        "capacity_mt"
    ])

    nearest_distance = "N/A"

    if railway_station["features"]:

        min_distance = 999999

        for rs in railway_station["features"]:

            rs_coords = rs.get("geometry", {}).get("coordinates", [0, 0])

            rs_lon = rs_coords[0]
            rs_lat = rs_coords[1]

            distance = haversine(lat, lon, rs_lat, rs_lon)

            if distance < min_distance:
                min_distance = distance

        nearest_distance = round(min_distance, 2)

    cold_storage_table.append({
        "district": district,
        "name": name,
        "capacity": capacity,
        "distance": nearest_distance,
        "lat": lat,
        "lon": lon
    })

    district_counts[district] = district_counts.get(district, 0) + 1


# =========================================================
# RAILWAY DROPDOWN
# =========================================================

railway_dropdown = []

for feature in railway_station["features"]:

    props = feature.get("properties", {})

    station_name = get_field(props, [
        "name",
        "Name",
        "station",
        "Station",
        "station_name"
    ])

    railway_dropdown.append(station_name)


# =========================================================
# HTML TEMPLATE
# =========================================================

HTML = """

<!DOCTYPE html>
<html>

<head>

<title>Bihar GIS Dashboard</title>

<meta charset="utf-8"/>

<link rel="stylesheet"
href="https://unpkg.com/leaflet/dist/leaflet.css"/>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>

body{
margin:0;
padding:0;
font-family:Arial;
background:#f4f4f4;
}

.container{
display:flex;
height:100vh;
}

.sidebar{
width:35%;
overflow-y:auto;
padding:20px;
background:white;
}

.map-container{
width:65%;
}

#map{
height:100vh;
width:100%;
}

.card{
background:white;
padding:20px;
margin-bottom:20px;
border-radius:10px;
box-shadow:0 2px 10px rgba(0,0,0,0.1);
}

.title{
background:#0d47a1;
color:white;
padding:20px;
border-radius:10px;
font-size:36px;
font-weight:bold;
margin-bottom:20px;
}

.summary-box{
background:linear-gradient(to right,#1565c0,#1e88e5);
color:white;
padding:15px;
margin-bottom:10px;
border-radius:8px;
font-size:22px;
font-weight:bold;
}

select,button{
width:100%;
padding:14px;
margin-top:10px;
border-radius:8px;
border:1px solid #ccc;
font-size:18px;
}

button{
background:#1565c0;
color:white;
border:none;
font-weight:bold;
cursor:pointer;
}

table{
width:100%;
border-collapse:collapse;
font-size:14px;
}

th{
background:#0d47a1;
color:white;
padding:10px;
}

td{
padding:8px;
border:1px solid #ccc;
}

</style>

</head>

<body>

<div class="container">

<div class="sidebar">

<div class="title">
Bihar GIS Dashboard
</div>

<div class="card">

<h2>Summary</h2>

<div class="summary-box">
Cold Storages: {{ cold_count }}
</div>

<div class="summary-box">
Railway Stations: {{ railway_count }}
</div>

<div class="summary-box">
Airports: {{ airport_count }}
</div>

<div class="summary-box">
Mandis: {{ mandi_count }}
</div>

</div>

<div class="card">

<h2>Railway Station Buffer</h2>

<select>

{% for station in railway_dropdown %}

<option>{{ station }}</option>

{% endfor %}

</select>

<select>
<option>5 KM</option>
<option>10 KM</option>
<option>20 KM</option>
</select>

<button>Generate Buffer</button>

</div>

<div class="card">

<h2>District Wise Cold Storages</h2>

<canvas id="chart"></canvas>

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

{% for row in cold_storage_table %}

<tr>

<td>{{ row.district }}</td>
<td>{{ row.name }}</td>
<td>{{ row.capacity }}</td>
<td>{{ row.distance }}</td>
<td>{{ row.lat }}</td>
<td>{{ row.lon }}</td>

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
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
).addTo(map);

var boundary = {{ boundary|safe }};

L.geoJSON(boundary,{
style:{
color:"black",
weight:3,
fill:false
}
}).addTo(map);

var cold = {{ cold_storage|safe }};

L.geoJSON(cold,{

pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:6,
fillColor:"red",
color:"white",
weight:1,
fillOpacity:1
});

},

onEachFeature:function(feature,layer){

var props = feature.properties;

layer.bindPopup(
"<b>Cold Storage</b><br>" +
JSON.stringify(props)
);

}

}).addTo(map);

var railway = {{ railway_station|safe }};

L.geoJSON(railway,{

pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:6,
fillColor:"blue",
color:"white",
weight:1,
fillOpacity:1
});

},

onEachFeature:function(feature,layer){

layer.bindPopup(
"<b>Railway Station</b><br>" +
JSON.stringify(feature.properties)
);

}

}).addTo(map);

var airport = {{ airport|safe }};

L.geoJSON(airport,{
pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:6,
fillColor:"green",
color:"white",
weight:1,
fillOpacity:1
});

}
}).addTo(map);

var mandi = {{ mandis|safe }};

L.geoJSON(mandi,{
pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:6,
fillColor:"orange",
color:"white",
weight:1,
fillOpacity:1
});

}
}).addTo(map);

var chart = new Chart(
document.getElementById("chart"),
{
type:"bar",
data:{
labels: {{ district_labels|safe }},
datasets:[{
label:"Cold Storages",
data: {{ district_values|safe }},
backgroundColor:"#42a5f5"
}]
}
}
);

</script>

</body>
</html>

"""


# =========================================================
# ROUTE
# =========================================================

@app.route("/")

def home():

    return render_template_string(

        HTML,

        cold_count=len(cold_storage["features"]),
        railway_count=len(railway_station["features"]),
        airport_count=len(airport["features"]),
        mandi_count=len(mandis["features"]),

        cold_storage=json.dumps(cold_storage),
        railway_station=json.dumps(railway_station),
        airport=json.dumps(airport),
        mandis=json.dumps(mandis),
        boundary=json.dumps(bihar_boundary),

        cold_storage_table=cold_storage_table,

        railway_dropdown=railway_dropdown,

        district_labels=json.dumps(list(district_counts.keys())),
        district_values=json.dumps(list(district_counts.values()))
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
