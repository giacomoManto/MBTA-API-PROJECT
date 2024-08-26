import os
import yaml
import polyline
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from ApiRequestBuilder import ApiRequestBuilder
from ApiRequestBuilder import RequestType

ApiRequestBuilder.printRequests = True
routes = ApiRequestBuilder(RequestType.routes).filter("type", "0", "1").get()

routes = {}
route_patterns = {}
trips = {}
shapes = {}
predictions = {}
stops = {}
vehicles = {}
data = ApiRequestBuilder(RequestType.routes).include('route_patterns').filter('type', '0', '1').get().json()
for route in data['data']:
    routes[route['id']] = route
    tripsAll = ApiRequestBuilder(RequestType.trips).filter("route", route['id']).include("shape", "predictions", "stops", "vehicle").get().json()
    for include in tripsAll['included']:
        if include['type'] == "shape":
            shapes[include['id']] = include
        elif include['type'] == "prediction":
            predictions[include['id']] = include
        elif include['type'] == "stop":
            stops[include['id']] = include
        elif include['type'] == 'vehicle':
            vehicles[include['id']] = include
    for trip in tripsAll['data']:
        trips[trip['id']] = trip
            

for include in data['included']:
    if include['type'] == 'route_pattern':
        route_patterns[include['id']] = include


fig = go.Figure(go.Scattergeo())

drawnShapes = {}
drawnStops = []
drawnVehicles = []

for trip in list(trips.values()):
    if len(trip['relationships']['predictions']['data']) == 0:
        continue
    if trip['relationships']['vehicle'] == None or  trip['relationships']['vehicle']['data'] == None:
        continue
    routeid = trip['relationships']['route']['data']['id']
    vehicleid = trip['relationships']['vehicle']['data']['id']
    color = f"#{routes[routeid]['attributes']['color']}"
    try:
        shapeid = trip['relationships']['shape']['data']['id']
        if shapeid not in drawnShapes:
            shape = shapes[shapeid]
            lats, lons = zip(*polyline.decode(shape['attributes']['polyline']))
            drawnShapes[shapeid] = (lats, lons)
            fig.add_scattermapbox(lat=lats, lon=lons, name=trip['relationships']['route_pattern']['data']['id'],
                                legendgroup=f"{routeid}",
                                legendgrouptitle_text=f"{routeid}",
                                marker=dict(
                                        color=color,
                                        symbol='star'
                                ),
                                mode='lines')
    except TypeError:
        pass
    vehicle = vehicles[vehicleid]
    fig.add_scattermapbox(lat=[vehicle['attributes']['latitude']], lon=[vehicle['attributes']['longitude']], name=f"{vehicleid}",
                        legendgroup=f"{routeid}",
                        marker=dict(
                            color=color,
                            size=10,
                        ),
                        mode='markers')
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()