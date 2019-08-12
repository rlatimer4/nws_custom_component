# nws_custom_component
National Weather Service custom component for Home Assistant

This should be placed in your configuration folder:

For HA .87 and lower
```
<config directory>/custom_components/sensor/nws_alerts.py
```
For HA .88 and higher (rename nws_alerts.py to sensor.py)
```
<config directory>/custom_components/nws_alerts/sensor.py
```
For HA .92 and higher (add a empty file named __init__.py to the folder nws_alerts)
```
<config directory>/custom_components/nws_alerts/__init__.py
```

Sensor state now reflects the highest severity level of the alerts, ranging from 0-4 (unkown to extreme).

To create an sensor instance add to your sensor definitions:
```
- platform: nws_alerts
  zone_id: 'PAC049'
```
or comma separated values

```
- platform: nws_alerts
  zone_id: 'PAC049,WVC031'
```

Optionally, you may also choose which statuses to monitor with the configuration option below.  
By default all status types will be tracked.
```
  status_types:
    - actual
    - test
    - draft
    - exercise
    - system
```
