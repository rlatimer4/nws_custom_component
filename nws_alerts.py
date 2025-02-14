'''
---------------------------------------------------------
NWS Alerts
---------------------------------------------------------
VERSION: 0.0.3
Forum: https://community.home-assistant.io/t/severe-weather-alerts-from-the-us-national-weather-service/71853

API Documentation
---------------------------------------------------------
https://www.weather.gov/documentation/services-web-api
https://forecast-v3.weather.gov/documentation
---------------------------------------------------------
'''

import requests
import logging
import voluptuous as vol
from datetime import timedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, ATTR_ATTRIBUTION
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle


API_ENDPOINT = 'https://api.weather.gov'
USER_AGENT = 'Home Assistant'
DEFAULT_ICON = 'mdi:alert'
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)
_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = 'NWS Alerts'
CONF_ZONE_ID = 'zone_id'
CONF_STATUS_TYPES = 'status_types'

DEFAULT_STATUS_TYPES = [
    'actual',
    'exercise',
    'system',
    'test',
    'draft'
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ZONE_ID): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_STATUS_TYPES, default=DEFAULT_STATUS_TYPES): 
        vol.All(cv.ensure_list, [vol.In(DEFAULT_STATUS_TYPES)])
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    name = config.get(CONF_NAME)
    zone_id = config.get(CONF_ZONE_ID)
    status_types = config[CONF_STATUS_TYPES]
    add_devices([NWSAlertSensor(name, zone_id, status_types)])

class NWSAlertSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, name, zone_id, status_types):
        """Initialize the sensor."""
        self._name = name
        self._icon = DEFAULT_ICON
        self._state = 0
        self._event = None
        self._severity = None
        self._display_desc = None
        self._spoken_desc = None
        self._zone_id = zone_id.replace(' ', '')
        self._status_types = status_types
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state message."""
        attributes = {"title": self._event,
                      "severity": self._severity,
                      "display_desc": self._display_desc,
                      "spoken_desc": self._spoken_desc
                      }

        return attributes

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        values = self.get_state()
        self._state = values['state']
        self._event = values['event']
        self._severity = values['severity']
        self._display_desc = values['display_desc']
        self._spoken_desc = values['spoken_desc']

    def get_state(self):
        values = {'state': 0,
                  'event': None,
                  'severity': None,
                  'display_desc': None,
                  'spoken_desc': None
                  }

        headers = {'User-Agent': USER_AGENT,
                   'Accept': 'application/ld+json'
                   }

        url = '%s/alerts/active/count' % API_ENDPOINT
        r = requests.get(url, headers=headers)
        _LOGGER.debug("getting state, %s", url)
        if r.status_code == 200:
            if 'zones' in r.json():
                for zone in self._zone_id.split(','):
                    if zone in r.json()['zones']:
                        values = self.get_alerts()
                        break

        return values

    def get_alerts(self):
        values = {'state': 0,
                  'event': None,
                  'severity': None,
                  'display_desc': None,
                  'spoken_desc': None
                  }

        headers = {'User-Agent': USER_AGENT,
                   'Accept': 'application/geo+json'
                   }
        url = '%s/alerts/active?zone=%s' % (API_ENDPOINT, self._zone_id)
        r = requests.get(url, headers=headers)
        _LOGGER.debug("getting alert, %s", url)
        if r.status_code == 200:
            events = []
            headlines = []
            severity = []
            severity_level = 0
            display_desc = ''
            spoken_desc = ''
            features = r.json()['features']
            for alert in features:
                status = alert['properties']['status']
                if status.lower() in self._status_types:
                    event = alert['properties']['event']
                    if 'NWSheadline' in alert['properties']['parameters']:
                        headline = alert['properties']['parameters']['NWSheadline'][0]
                    else:
                        headline = event
                    new_severity = alert['properties']['severity']
                    new_severity = new_severity.capitalize()
                    description = alert['properties']['description']
                    instruction = alert['properties']['instruction']
                    
                    if event in events:
                        continue
                    
                    if new_severity == 'Unknown':
                        new_severity_level = 0
                    elif new_severity == 'Minor':
                        new_severity_level = 1
                    elif new_severity == 'Moderate':
                        new_severity_level = 2
                    elif new_severity == 'Severe':
                        new_severity_level = 3
                    elif new_severity == 'Extreme':
                        new_severity_level = 4
                    
                    if new_severity_level > severity_level:
                        severity_level = new_severity_level
                    

                    
                    events.append(event)
                    headlines.append(headline)
                    severity.append(new_severity)
                    
                    if display_desc != '':
                        display_desc += '\n\n'
                    
                    display_desc += '%s\n%s\n%s\n%s' % (event, headline, description, instruction)
                else:
                    continue

            if headlines:
                num_headlines = len(headlines)
                i = 0
                for headline in headlines:
                    i += 1
                    if spoken_desc != '':
                        if i == num_headlines:
                            spoken_desc += ' and a '
                        else:
                            spoken_desc += ', a '

                    spoken_desc += headline

            if len(events) > 0:
                event_str = ''
                for item in events:
                    if event_str != '':
                        event_str += ' - '
                    event_str += item
                
#                values['state'] = len(events)
                values['state'] = severity_level
                values['severity'] = severity
                values['event'] = event_str
                values['display_desc'] = display_desc
                values['spoken_desc'] = spoken_desc

        return values

