import time
import requests
import yaml
from enum import Enum


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
    printRequests = False
    def __init__(self, type: RequestType, id = None, endpoint = "https://api-v3.mbta.com/"):
        self.api = endpoint
        self.payload = {}
        self.headers = {'Accept-Encoding': 'gzip'}

        try:
            with open('keys.yaml', 'r') as file:
                keys = yaml.safe_load(file)
                self.headers['X-Api-Key'] = keys['MBTA_API_KEY']
        except FileNotFoundError:
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

        if ApiRequestBuilder.printRequests:
            print(f"{ApiRequestBuilder.ratelimit - ApiRequestBuilder.ratelimit_remaining}/{ApiRequestBuilder.ratelimit} requests in current limit period.")
        if response.status_code == 429:
            print(f"Requested past rate limit. Sleeping for {ApiRequestBuilder.ratelimit_reset - time.time()} seconds.")
            time.sleep(ApiRequestBuilder.ratelimit_reset - time.time())
            return self.get()
        return response