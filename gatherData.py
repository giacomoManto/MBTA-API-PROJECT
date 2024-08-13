from enum import Enum
import requests
import os
import yaml
import polyline
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

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

totalRequests = 0
class ApiRequestBuilder:

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
        global totalRequests
        totalRequests += 1
        return requests.get(self.api, params=self.payload, headers=self.headers)


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

routeData = {'Name': [], 'Shapes': [], 'Color': []}
for route in routes.json()['data']:
    routeData['Name'].append(f"{route['id']}")
    routeData['Color'].append(route['attributes']['color'])
    shapes = ApiRequestBuilder(RequestType.shapes).filter("route", route['id']).get()
    curShapes = []
    for shape in shapes.json()['data']:
        data = {'id': shape['id'], "Lat": [], "Long":[]}
        for lat, lon in polyline.decode(shape['attributes']['polyline']):
            data['Lat'].append(float(lat))
            data['Long'].append(float(lon))
        curShapes.append(data)
    routeData['Shapes'].append(curShapes)
    
fig = go.Figure(go.Scattergeo())

for pos in range(len(routeData['Name'])):
    name = routeData['Name'][pos]
    color = f"#{routeData['Color'][pos]}"
    shapes = routeData['Shapes'][pos]
    for shape in shapes:
        fig.add_scattermapbox(lat=shape['Lat'], lon=shape['Long'], name=f"{name}-{shape['id']}",
                              marker=dict(
                                    color=color,
                              ),
                              mode='lines')

fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()
print(totalRequests)

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
