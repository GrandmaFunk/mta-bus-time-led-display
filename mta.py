from adafruit_datetime import datetime
from os import getenv

def get_arrivals(network, stop_id, line_id):

    # Set parameters for the API call
    params = {
        'key': getenv('MTA_API_KEY'),
        'MonitoringRef': stop_id,
        'OperatorRef': 'MTA',
        'LineRef': line_id,
        'MaximumStopVisits': '2'
    }

    # Create endpoint URL
    query_string = "&".join(f"{key}={value}" for key, value in params.items())
    url = f'http://bustime.mta.info/api/siri/stop-monitoring.json?{query_string}'

    # Make the API call
    data = network.fetch_data(url, json_path=(['Siri'],))

    # Create empty list to store bus info
    buses = []

    # Parse json
    try:
        data = data['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']
    except KeyError:
        return buses

    if len(data) > 0:
        for journey in data:

            # Get the number of minutes away
            # If 'ExpectedArrivalTime' does not exist, use 'AimedArrivalTime'
            try:
                arrival = journey['MonitoredVehicleJourney']['MonitoredCall']['ExpectedArrivalTime']
            except KeyError:
                arrival = journey['MonitoredVehicleJourney']['MonitoredCall']['AimedArrivalTime']

            arrival = datetime.fromisoformat(arrival).replace(tzinfo=None)

            current_time = datetime.now()
            time_difference = arrival - current_time
            eta_minutes = time_difference.total_seconds() / 60

            # Get the distance away (This is unused for now. It can be presented in both miles or stops)
            distance = journey['MonitoredVehicleJourney']['MonitoredCall']['Extensions']['Distances']['PresentableDistance']
            distance_list = distance.split(' ')
            distance_display = ''
            if len(distance_list) == 1:
                distance_display = distance_list[0][:4]
            else:
                if distance_list[0] == '<':
                    distance_display += '<'
                    distance_display += str(distance_list[1])
                else:
                    distance_display += str(distance_list[0])

                if distance_list[-2] == 'stops' or distance_list[-2] == 'stop':
                    distance_display += ' stp'
                elif distance_list[-2] == 'miles' or distance_list[-2] == 'mile':
                    distance_display += 'mi'
            
            # Get number of stops away
            stops_away = journey['MonitoredVehicleJourney']['MonitoredCall']['Extensions']['Distances']['StopsFromCall']

            try:
                if stops_away <= 1:
                    stops_away = str(stops_away) + 'stop'
                else:
                    stops_away = str(stops_away) + 'stops'
            except ValueError as e:
                print(f'ValueError for stops_away = {stops_away}')
                stops_away = str(stops_away) + 'stps'

            buses.append({'eta_minutes': str(round(eta_minutes)) + 'min', 'distance': distance_display, 'stops_away': stops_away})
    return buses

