import pandas as pd
import logging
import requests
import datetime
import string
import time
import sched

import utils
from database import upsert_forecast_data

logger = logging.Logger(__name__)
utils.setup_logger(logger, 'data.log')


LOCATION = 'New+York'
DOWNLOAD_PERIOD = 15         # second


def process_location(city, state):
    return ('{},{}'.format(city, state)).replace(' ', '+').lower()


def process_date_historical(date_year, date_month, date_day, enddate_year, enddate_month, enddate_day):
    '''
    return list of dates --- yyyy-MM-dd
    '''
    startdate = datetime.datetime(year = date_year, month = date_month, day = date_day)
    enddate = datetime.datetime(year = enddate_year, month = enddate_month, day = enddate_day)

    start_timestamp = startdate.timestamp()
    end_timestamp = enddate.timestamp()

    if (start_timestamp > end_timestamp):
        raise ValueError ('Start date must not be later than end date!')

    curr_timestamp = start_timestamp

    dates = [] 
    while True:
        curr_datetime = datetime.datetime.fromtimestamp(curr_timestamp)
        curr_date_str = curr_datetime.strftime('%Y-%m-%d')
        dates.append(curr_date_str)
        if curr_timestamp == end_timestamp:
            break
        curr_timestamp += 60*60*24
        
    return dates



def load_historical_data(location, dates):
    '''
    dates: list of date --- yyyy-MM-dd
    return: df_day
            df_hourly
    '''
    interval = 1
    url = 'http://api.worldweatheronline.com/premium/v1/past-weather.ashx'
    key = '8fefb61db8a241c4b7524155190612'
    fm = 'json'

    days_data = []
    days_hourly_data = []

    for day in dates:
        paras = dict()
        paras['key'] = key
        paras['format'] = fm
        paras['q'] = location
        paras['date'] = day
        paras['tp'] = interval
        
        r = requests.get(url, paras)
        r.raise_for_status()                             ### try and except? ### 

        city = r.json()['data']['request'][0]['query']
        result = r.json()['data']['weather'][0]
        
        #################### day data ####################
        day_data = []
        day_data.append(city)

        day_data.append(pd.to_datetime(day, format='%Y-%m-%d'))
        day_data.append(result['astronomy'][0]['sunrise'])
        day_data.append(result['astronomy'][0]['sunset'])
        day_data.append(result['astronomy'][0]['moonrise'])
        day_data.append(result['astronomy'][0]['moonset'])
        day_data.append(result['astronomy'][0]['moon_phase'])
        day_data.append(result['astronomy'][0]['moon_illumination'])
        day_data.append(result['maxtempC'])
        day_data.append(result['maxtempF'])
        day_data.append(result['mintempC'])
        day_data.append(result['mintempF'])
        day_data.append(result['avgtempC'])
        day_data.append(result['avgtempF'])
        day_data.append(result['totalSnow_cm'])
        day_data.append(result['sunHour'])
        day_data.append(result['uvIndex'])
        
        days_data.append(day_data)
        
        #################### hourly data ####################
        result_hourly = result['hourly']
        for hour in range(len(result_hourly)):
            result_hour = result_hourly[hour]
            hourly_data = []
            hourly_data.append(city)
            date_time = '{}-{}'.format(day, hour)
            hourly_data.append(pd.to_datetime(date_time, format='%Y-%m-%d-%H'))
            hourly_data.append(result_hour['tempC'])
            hourly_data.append(result_hour['tempF'])
            hourly_data.append(result_hour['windspeedMiles'])
            hourly_data.append(result_hour['windspeedKmph'])
            hourly_data.append(result_hour['winddirDegree'])
            hourly_data.append(result_hour['winddir16Point'])
            hourly_data.append(result_hour['weatherDesc'][0]['value'])
            hourly_data.append(result_hour['precipMM'])
            hourly_data.append(result_hour['precipInches'])
            hourly_data.append(result_hour['humidity'])
            hourly_data.append(result_hour['visibility'])
            hourly_data.append(result_hour['visibilityMiles'])
            hourly_data.append(result_hour['cloudcover'])
            hourly_data.append(result_hour['uvIndex'])
            days_hourly_data.append(hourly_data)

    df_day = pd.DataFrame(days_data, columns = ['city', 'datetime', 'sunrise', 'sunset', 'moonrise', 'moonset', 'moon_phase', 'moon_illumination',
                                                'maxtempC', 'maxtempF', 'mintempC', 'mintempF', 'avgtempC', 'avgtempF', 'totalSnow_cm',
                                                'sunHour', 'uvIndex'])
    df_hourly = pd.DataFrame(days_hourly_data, columns = ['city', 'datetime', 'tempC', 'tempF', 'windspeedMiles', 'windspeedKmph', 
                                                        'winddirDegree', 'winddir16Point', 'weatherDesc', 'precipMM', 
                                                        'precipInches', 'humidity', 'visibility', 'visibilityMiles', 'cloudcover', 'uvIndex'])
    return df_day, df_hourly



def load_forecast_data(location, num_of_days=7, num_of_hours=24):
    '''
    dates: location
            num_of_days: Number of days of forecast
            num_0f_hours: number of hours of forecast
    return: df_daily_forecast
            df_hourly_forecast
    '''

    interval = 1
    url = 'http://api.worldweatheronline.com/premium/v1/weather.ashx'
    key = 'ddc7eb4778ba48e69e825031190612'
    fm = 'json'
    show_comments = 'no'
    show_local_time = 'yes'

    paras = dict()
    paras['key'] = key
    paras['format'] = fm
    paras['q'] = location
    paras['tp'] = interval
    paras['num_of_days'] = num_of_days
    paras['show_comments'] = show_comments
    paras['showlocaltime'] = show_local_time

    res = requests.get(url, paras)
    res.raise_for_status()

    res_hourly_data = []
    res_daily_data = []

    r = res.json()
    curr_time = r['data']['time_zone'][0]['localtime']
    curr_datetime = pd.to_datetime(curr_time, format='%Y-%m-%d %H:%M')
    curr_condition = r['data']['current_condition'][0]

    hour_count = 0
    need_hour_data = True

    hourly_data = []
    hourly_data.append(True)
    hourly_data.append(curr_datetime)
    hourly_data.append(curr_condition['temp_C'])
    hourly_data.append(curr_condition['temp_F'])
    hourly_data.append(curr_condition['precipMM'])
    hourly_data.append(curr_condition['uvIndex'])
    res_hourly_data.append(hourly_data)
    hour_count += 1

    for day in range(len(r['data']['weather'])):
        day_weather = r['data']['weather'][day]
        day_data = []
        day_data.append(pd.to_datetime(day_weather['date'], format='%Y-%m-%d'))
        day_data.append(day_weather['astronomy'][0]['sunrise'])
        day_data.append(day_weather['astronomy'][0]['sunset'])
        day_data.append(day_weather['astronomy'][0]['moonrise'])
        day_data.append(day_weather['astronomy'][0]['moonset'])
        day_data.append(day_weather['astronomy'][0]['moon_phase'])
        day_data.append(day_weather['astronomy'][0]['moon_illumination'])
        tempC = '{} ~ {}'.format(day_weather['mintempC'], day_weather['maxtempC'])
        tempF = '{} ~ {}'.format(day_weather['mintempF'], day_weather['maxtempF'])
        day_data.append(tempC)
        day_data.append(tempF)
        day_data.append(day_weather['sunHour'])
        day_data.append(day_weather['uvIndex'])
        res_daily_data.append(day_data)

        curr_hour = curr_datetime.hour
        if need_hour_data:
            result_hourly = day_weather['hourly']
            start = 0
            if day == 0:
                start = curr_hour+1
            for hour in range(start, len(result_hourly)):
                result_hour = result_hourly[hour]
                hourly_data = []
                hourly_data.append(False)
                date_time = '{}-{}'.format(day_weather['date'], hour)
                hourly_data.append(pd.to_datetime(date_time, format='%Y-%m-%d-%H'))
                hourly_data.append(result_hour['tempC'])
                hourly_data.append(result_hour['tempF'])
                hourly_data.append(result_hour['precipMM'])
                hourly_data.append(result_hour['uvIndex'])
                res_hourly_data.append(hourly_data)
                hour_count += 1
                if hour_count == num_of_hours:
                    need_hour_data = False
                    break

    df_daily_forecast = pd.DataFrame(res_daily_data, columns = ['datetime', 'sunrise', 'sunset', 'moonrise', 'moonset', 'moon_phase',
                                                                'moon_illumination', 'tempC', 'tempF', 'sunHour', 'uvIndex'])
    df_hourly_forecast = pd.DataFrame(res_hourly_data, columns = ['current', 'datetime', 'tempC', 'tempF', 'precipMM', 'uvIndex'])
    return df_daily_forecast, df_hourly_forecast


def update_forecast_once():
    df_daily_forecast, df_hourly_forecast = load_forecast_data(LOCATION)
    upsert_forecast_data(df_daily_forecast, df_hourly_forecast)



def main_loop(timeout=DOWNLOAD_PERIOD):
    scheduler = sched.scheduler(time.time, time.sleep)

    def _worker():
        try:
            update_forecast_once()
        except Exception as e:
            logger.warning("main loop worker ignores exception and continues: {}".format(e))
        scheduler.enter(timeout, 1, _worker)    # schedule the next event

    scheduler.enter(0, 1, _worker)              # start the first event
    scheduler.run(blocking=True)

if __name__ == '__main__':
    df_daily_forecast, df_hourly_forecast = load_forecast_data('providence')
    df_daily_forecast.to_csv('daily_weather.csv')
    #main_loop()

