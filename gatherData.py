from enum import Enum
import requests
import os
import yaml
import polyline
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time

class RequestType(Enum):
    alerts = 'alerts'
    facilities = 'facilities'
    lines = 'lines'
    live_facilities = 'live_facilities'
    predictions = 'predictions'
    routes = 'routes'
    route_patterns = 'route_patterns'
    schedules = 'schedules'
    shapes = 'shapes'
    stops = 'stops'
    trips = 'trips'
    vehicles = 'vehicles'


class ApiRequestBuilder:
    ratelimit = 20
    ratelimit_remaining = ratelimit
    ratelimit_reset = time.time() + 60
    def __init__(self, type: RequestType, id = None, endpoint = "https://api-v3.mbta.com/"):
        self.api = endpoint
        self.payload = {}
        self.headers = {'Accept-Encoding': 'gzip'}

        try:
            with open('keys.yaml', 'r') as file:
                keys = yaml.safe_load(file)
                self.headers['X-Api-Key'] = keys['MBTA_API_KEY']
        except:
            pass

        # Add type to api
        self.api += (type.value)

        # Add id if request type accepts it
        if id is not None and type is not RequestType.predictions and type is not RequestType.schedules:
            self.api += f"/{(str(id))}"

    def addApiKey(self, key) -> 'ApiRequestBuilder':
        self.payload['X-Api-Key'] = key
        return self

    def include(self, *relationships: str) -> 'ApiRequestBuilder':
        if 'include' in self.payload:
            self.payload['include'] += (f",{",".join(relationships)}")
        else:
            self.payload['include'] = ",".join(relationships)
        return self
    
    def filter(self, key, *filt) -> 'ApiRequestBuilder':
        if f"filter[{key}]" in self.payload:
            self.payload[f"filter[{key}]"] += (f",{",".join(filt)}")
        else:
            self.payload[f"filter[{key}]"] = ",".join(filt)
        return self
    
    def get(self) -> requests.Response:
        if ApiRequestBuilder.ratelimit_remaining <= 0 and time.time() < ApiRequestBuilder.ratelimit_reset:
            while time.time() < ApiRequestBuilder.ratelimit_reset:
                print(f"Rate limit hit. Sleeping for {ApiRequestBuilder.ratelimit_reset - time.time()} seconds.")
                time.sleep(1)
        
        response = requests.get(self.api, params=self.payload, headers=self.headers)
        ApiRequestBuilder.ratelimit = int(response.headers['x-ratelimit-limit'])
        ApiRequestBuilder.ratelimit_remaining = int(response.headers['x-ratelimit-remaining'])
        ApiRequestBuilder.ratelimit_reset = int(response.headers['x-ratelimit-reset'])

        if ApiRequestBuilder.ratelimit_remaining % 10 == 0:
            print(f"{ApiRequestBuilder.ratelimit - ApiRequestBuilder.ratelimit_remaining} requests in current limit period.")
        if response.status_code == 429:
            print(f"Requested past rate limit. Sleeping for {ApiRequestBuilder.ratelimit_reset - time.time()} seconds.")
            time.sleep(ApiRequestBuilder.ratelimit_reset - time.time())
            return self.get()
        return response


# def routes(id = None):
#     if id is not None:
#         return f"{API_URL}/routes/{id}"
#     return f"{API_URL}/routes"

# def shapes(id = None):
#     if id is not None:
#         return f"{API_URL}/shapes/{id}"
#     return f"{API_URL}/shapes"
# request = f"{API_URL}/routes?filter[type]="
# response = requests.get(request)
# data = response.json()
# for route in data['data']:
#     print(f"{route['attributes']['long_name']} | {route['attributes']['short_name']} | {route['id']}")

# request = f"{API_URL}/predictions?filter[route]=Red&include=vehicle,route"
# response = requests.get(request)
# data = response.json()
print("MEOW")
routes = ApiRequestBuilder(RequestType.routes).filter("type", "0", "1").get()
print(routes.url)

routeData = {}
for route in routes.json()['data']:
    routeData[route['id']] = {'color': route['attributes']['color'], 'shapes': {}}
    shapes = ApiRequestBuilder(RequestType.shapes).filter("route", route['id']).get()
    curShapes = {}
    for shape in shapes.json()['data']:
        data = {"Lat": [], "Long":[]}
        for lat, lon in polyline.decode(shape['attributes']['polyline']):
            data['Lat'].append(float(lat))
            data['Long'].append(float(lon))
            pass
        routeData[route['id']]['shapes'][shape['id']] = data
    vehicles = ApiRequestBuilder(RequestType.vehicles).filter("route", route['id']).get()
    routeData[route['id']]['vehicles'] = {}
    for vehicle in vehicles.json()['data']:
        routeData[route['id']]['vehicles'][vehicle['id']] = {'long': vehicle['attributes']['longitude'], 'lat': vehicle['attributes']['latitude']}

fig = go.Figure(go.Scattergeo())

for route in routeData:
    name = route
    color = f"#{routeData[route]['color']}"
    shapes = routeData[route]['shapes']
    # for shape in shapes:
    #     fig.add_scattermapbox(lat=shapes[shape]['Lat'], lon=shapes[shape]['Long'], name=f"{name}-{shape}",
    #                           marker=dict(
    #                                 color=color,
    #                           ),
    #                           mode='lines')
    for vehicle in routeData[route]['vehicles']:
        fig.add_scattermapbox(lat=[routeData[route]['vehicles'][vehicle]['lat']],
                              lon=[routeData[route]['vehicles'][vehicle]['long']],
                              name=f"{vehicle}",
                              marker=dict(
                                    color=color,
                              ),
                              mode='markers')

fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()

# fig = px.scatter_mapbox(df, 
#                         lat="Lat", 
#                         lon="Long", 
#                         hover_name="Address", 
#                         hover_data=["Address", "Listed"],
#                         color="Listed",
#                         color_continuous_scale=color_scale,
#                         size="Listed",
#                         zoom=8, 
#                         height=800,
#                         width=800)

# fig.update_layout(mapbox_style="open-street-map")
# fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
# fig.show()
