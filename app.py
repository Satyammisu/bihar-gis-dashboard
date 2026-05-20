from flask import Flask, render_template_string
import json
import os

app = Flask(__name__)

# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# =========================================================
# LOAD GEOJSON
# =========================================================

def load_geojson(filename):

    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):

        return {
            "type": "FeatureCollection",
            "features": []
        }

    with open(path, "r", encoding="utf-8") as f:

        return json.load(f)

# =========================================================
# LOAD FILES
# =========================================================

bihar_boundary = load_geojson("bihar_boundary.geojson")
cold_storage = load_geojson("cold_storage.geojson")
railway_station = load_geojson("railway_station.geojson")
airport = load_geojson("airport.geojson")
mandis = load_geojson("mandis.geojson")

# =========================================================
# SUMMARY COUNTS
# =========================================================

cold_count = len(cold_storage["features"])
rail_count = len(railway_station["features"])
airport_count = len(airport["features"])
mandi_count = len(mandis["features"])

# =========================================================
# DISTRICT COUNTS
# =========================================================

district_counts = {}

for f in cold_storage["features"]:

    props = f.get("properties", {})

    district = (
        props.get("District")
        or props.get("district")
        or props.get("DISTRICT")
        or props.get("dist_name")
        or "Unknown"
    )

    district_counts[district] = district_counts.get(district, 0) + 1

# =========================================================
# RAILWAY DROPDOWN LIST
# =========================================================

railway_list = []

for f in railway_station["features"]:

    props = f.get("properties", {})

    name = (
        props.get("Name")
        or props.get("name")
        or props.get("Station")
        or props.get("station")
        or props.get("Railway")
        or "Railway Station"
    )

    lat = f["geometry"]["coordinates"][1]
    lon = f["geometry"]["coordinates"][0]

    railway_list.append({
        "name": name,
        "lat": lat,
        "lon": lon
    })

# =========================================================
# HTML TEMPLATE
# =========================================================

HTML = """

<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">

<title>Bihar Government GIS Dashboard</title>

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link rel="stylesheet"
href="https://unpkg.com/leaflet/dist/leaflet.css"/>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>

body{
    margin:0;
    padding:0;
    font-family:Arial,sans-serif;
}

#container{
    display:flex;
    height:100vh;
}

#sidebar{
    width:420px;
    overflow-y:auto;
    background:#eef3f8;
    padding:15px;
    box-shadow:0 0 10px rgba(0,0,0,0.2);
}

#map{
    flex:1;
}

.header{
    background:#0d47a1;
    color:white;
    padding:15px;
    border-radius:10px;
    margin-bottom:20px;
    text-align:center;
}

.card{
    background:white;
    border-radius:14px;
    border:1px solid #dce3ea;
    padding:15px;
    margin-bottom:20px;
    box-shadow:0 2px 8px rgba(0,0,0,0.1);
}

.card h2{
    margin-top:0;
    color:#0d47a1;
}

.summary-box{
    background:#1565c0;
    color:white;
    padding:12px;
    border-radius:8px;
    margin-bottom:10px;
    font-size:20px;
    font-weight:bold;
}

select{
    width:100%;
    padding:12px;
    margin-bottom:10px;
    border-radius:5px;
    border:1px solid #ccc;
}

button{
    width:100%;
    padding:12px;
    border:none;
    background:#1565c0;
    color:white;
    border-radius:5px;
    cursor:pointer;
    font-size:16px;
    font-weight:bold;
}

button:hover{
    background:#0d47a1;
}

.table-container{
    max-height:350px;
    overflow:auto;
}

table{
    width:100%;
    border-collapse:collapse;
}

table th{
    background:#0d47a1;
    color:white;
    padding:8px;
    font-size:13px;
    position:sticky;
    top:0;
}

table td{
    border:1px solid #ddd;
    padding:6px;
    font-size:12px;
}

.popup-btn{
    width:100%;
    background:#1565c0;
    color:white;
    border:none;
    padding:10px;
    border-radius:5px;
    cursor:pointer;
}

.legend{
    background:white;
    padding:10px;
    border-radius:6px;
    line-height:25px;
}

.legend span{
    width:15px;
    height:15px;
    display:inline-block;
    border-radius:50%;
    margin-right:5px;
}

</style>

</head>

<body>

<div id="container">

<div id="sidebar">

<div class="header">

<h1>Bihar GIS Dashboard</h1>

</div>

<div class="card">

<h2>Summary</h2>

<div class="summary-box">
Cold Storages: {{ cold_count }}
</div>

<div class="summary-box">
Railway Stations: {{ rail_count }}
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

<select id="stationSelect">

<option value="">
Select Railway Station
</option>

</select>

<select id="bufferDistance">

<option value="5">5 KM</option>
<option value="10">10 KM</option>
<option value="20">20 KM</option>
<option value="50">50 KM</option>

</select>

<button onclick="generateBuffer()">
Generate Buffer
</button>

</div>

<div class="card">

<h2>District Wise Cold Storages</h2>

<div style="height:350px;">
<canvas id="districtChart"></canvas>
</div>

</div>

<div class="card">

<h2>Cold Storage Details</h2>

<div class="table-container">

<table>

<thead>

<tr>

<th>District</th>
<th>Name</th>
<th>Capacity</th>
<th>Distance</th>
<th>Latitude</th>
<th>Longitude</th>

</tr>

</thead>

<tbody id="coldTable"></tbody>

</table>

</div>

</div>

</div>

<div id="map"></div>

</div>

<script>

// =======================================================
// MAP
// =======================================================

var map = L.map('map').setView([25.6,85.1],7);

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
{
maxZoom:19
}
).addTo(map);

// =======================================================
// BIHAR BOUNDARY
// =======================================================

var biharBoundary = {{ bihar_boundary|safe }};

L.geoJSON(biharBoundary,{
style:{
color:'black',
weight:3,
fillOpacity:0
}
}).addTo(map);

// =======================================================
// DISTANCE CALCULATION
// =======================================================

function calculateDistance(lat1, lon1, lat2, lon2) {

    var R = 6371;

    var dLat = (lat2-lat1) * Math.PI / 180;
    var dLon = (lon2-lon1) * Math.PI / 180;

    var a =
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1*Math.PI/180) *
        Math.cos(lat2*Math.PI/180) *
        Math.sin(dLon/2) *
        Math.sin(dLon/2);

    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return (R * c).toFixed(2);

}

// =======================================================
// COLD STORAGE
// =======================================================

var coldStorageData = {{ cold_storage|safe }};

var coldLayer = L.geoJSON(coldStorageData,{

pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:7,
fillColor:'blue',
color:'white',
weight:1,
fillOpacity:1
});

},

onEachFeature:function(feature,layer){

var p = feature.properties || {};

var district =
p.District ||
p.district ||
p.DISTRICT ||
p.dist_name ||
"N/A";

var name =
p.Name ||
p.name ||
p.NAME ||
p.storage_name ||
p.Storage_Name ||
p.cold_storage ||
p.ColdStorage ||
p.cold_name ||
"Cold Storage";

var capacity =
p.Capacity ||
p.capacity ||
p.CAPACITY ||
p.Capacity_MT ||
p.capacity_mt ||
p.Storage_Capacity ||
p.storage_capacity ||
p.cap_mt ||
p.cap ||
"N/A";

var lat = feature.geometry.coordinates[1];
var lon = feature.geometry.coordinates[0];

var distance = "N/A";

if(window.selectedRailway){

distance = calculateDistance(
lat,
lon,
window.selectedRailway.lat,
window.selectedRailway.lon
) + " KM";

}

layer.bindTooltip(
"<b>" + name + "</b>",
{
sticky:true,
direction:'top',
opacity:1
}
);

layer.bindPopup(

"<b>Cold Storage</b><br><br>" +

"<b>District:</b> " + district + "<br>" +

"<b>Name:</b> " + name + "<br>" +

"<b>Capacity:</b> " + capacity + "<br>" +

"<b>Distance:</b> " + distance + "<br>" +

"<b>Latitude:</b> " + lat + "<br>" +

"<b>Longitude:</b> " + lon + "<br><br>" +

"<button class='popup-btn' onclick=\\"window.open('https://www.google.com/maps/search/?api=1&query=" +

lat + "," + lon +

"','_blank')\\">Navigate</button>"

);

}

}).addTo(map);

// =======================================================
// RAILWAY STATION
// =======================================================

var railwayData = {{ railway_station|safe }};

var railwayLayer = L.geoJSON(railwayData,{

pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:7,
fillColor:'red',
color:'white',
weight:1,
fillOpacity:1
});

},

onEachFeature:function(feature,layer){

var p = feature.properties || {};

var name =
p.Name ||
p.name ||
p.Station ||
p.station ||
p.Railway ||
"Railway Station";

var lat = feature.geometry.coordinates[1];
var lon = feature.geometry.coordinates[0];

layer.bindTooltip(
"<b>" + name + "</b>",
{
sticky:true,
direction:'top',
opacity:1
}
);

layer.bindPopup(

"<b>Railway Station</b><br><br>" +

"<b>Name:</b> " + name + "<br>" +

"<b>Latitude:</b> " + lat + "<br>" +

"<b>Longitude:</b> " + lon + "<br><br>" +

"<button class='popup-btn' onclick=\\"window.open('https://www.google.com/maps/search/?api=1&query=" +

lat + "," + lon +

"','_blank')\\">Navigate</button>"

);

}

}).addTo(map);

// =======================================================
// AIRPORT
// =======================================================

var airportData = {{ airport|safe }};

L.geoJSON(airportData,{

pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:7,
fillColor:'green',
color:'white',
weight:1,
fillOpacity:1
});

}

}).addTo(map);

// =======================================================
// MANDI
// =======================================================

var mandiData = {{ mandis|safe }};

L.geoJSON(mandiData,{

pointToLayer:function(feature,latlng){

return L.circleMarker(latlng,{
radius:7,
fillColor:'orange',
color:'white',
weight:1,
fillOpacity:1
});

}

}).addTo(map);

// =======================================================
// RAILWAY DROPDOWN
// =======================================================

var railwayList = {{ railway_list|safe }};

var select = document.getElementById("stationSelect");

railwayList.forEach(function(item,index){

var option = document.createElement("option");

option.value = index;
option.text = item.name;

select.appendChild(option);

});

// =======================================================
// BUFFER
// =======================================================

var bufferCircle;

function generateBuffer(){

var index =
document.getElementById("stationSelect").value;

if(index === ""){
alert("Please select railway station");
return;
}

var distance =
parseInt(document.getElementById("bufferDistance").value);

var item = railwayList[index];

window.selectedRailway = item;

if(bufferCircle){
map.removeLayer(bufferCircle);
}

bufferCircle = L.circle(
[item.lat,item.lon],
{
radius:distance*1000,
color:'green',
fillOpacity:0.1
}
).addTo(map);

map.setView([item.lat,item.lon],10);

// ================================================
// UPDATE TABLE DISTANCE
// ================================================

updateTable();

}

// =======================================================
// TABLE
// =======================================================

function updateTable(){

var tbody = document.getElementById("coldTable");

tbody.innerHTML = "";

coldStorageData.features.forEach(function(f){

var p = f.properties || {};

var district =
p.District ||
p.district ||
p.DISTRICT ||
p.dist_name ||
"N/A";

var name =
p.Name ||
p.name ||
p.NAME ||
p.storage_name ||
p.Storage_Name ||
p.cold_storage ||
p.ColdStorage ||
p.cold_name ||
"Cold Storage";

var capacity =
p.Capacity ||
p.capacity ||
p.CAPACITY ||
p.Capacity_MT ||
p.capacity_mt ||
p.Storage_Capacity ||
p.storage_capacity ||
p.cap_mt ||
p.cap ||
"N/A";

var lat = f.geometry.coordinates[1];
var lon = f.geometry.coordinates[0];

var distance = "N/A";

if(window.selectedRailway){

distance = calculateDistance(
lat,
lon,
window.selectedRailway.lat,
window.selectedRailway.lon
) + " KM";

}

tbody.innerHTML +=

"<tr>" +

"<td>" + district + "</td>" +

"<td>" + name + "</td>" +

"<td>" + capacity + "</td>" +

"<td>" + distance + "</td>" +

"<td>" + lat + "</td>" +

"<td>" + lon + "</td>" +

"</tr>";

});

}

updateTable();

// =======================================================
// CHART
// =======================================================

var districtData = {{ district_counts|safe }};

var labels = Object.keys(districtData);
var values = Object.values(districtData);

new Chart(document.getElementById("districtChart"),{

type:'bar',

data:{
labels:labels,
datasets:[{
label:'Cold Storages',
data:values,
backgroundColor:'#1565c0'
}]
},

options:{
responsive:true,
maintainAspectRatio:false,
plugins:{
legend:{
display:false
}
}
}

});

// =======================================================
// LEGEND
// =======================================================

var legend = L.control({position:'bottomright'});

legend.onAdd = function(){

var div = L.DomUtil.create('div','legend');

div.innerHTML =

'<b>Legend</b><br>' +

'<span style="background:blue"></span> Cold Storage<br>' +

'<span style="background:red"></span> Railway Station<br>' +

'<span style="background:green"></span> Airport<br>' +

'<span style="background:orange"></span> Mandi';

return div;

};

legend.addTo(map);

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

        cold_count=cold_count,
        rail_count=rail_count,
        airport_count=airport_count,
        mandi_count=mandi_count,

        district_counts=json.dumps(district_counts),

        bihar_boundary=json.dumps(bihar_boundary),
        cold_storage=json.dumps(cold_storage),
        railway_station=json.dumps(railway_station),
        airport=json.dumps(airport),
        mandis=json.dumps(mandis),

        railway_list=json.dumps(railway_list)

    )

# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )