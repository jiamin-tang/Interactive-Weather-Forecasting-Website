import logging
import pymongo
import pandas as pd
#import expiringdict
import utils

from data_acquire import process_location, process_date_historical, load_historical_data, load_forecast_data

client = pymongo.MongoClient()
logger = logging.Logger(__name__)
utils.setup_logger(logger, 'database.log')
#RESULT_CACHE_EXPIRATION = 10             # seconds

def upsert_historical(df_day, df_hourly):
    """
    Update MongoDB database `daily_weather`,  and collection `daily_weather` with the given `df_day`
    Update MongoDB database `hourly_weather`,  and collection `hourly_weather` with the given `df_hourly`
    """
    db = client.get_database("weather")
    collection_daily = db.get_collection("daily_weather")
    collection_hourly = db.get_collection("hourly_weather")

    update_count_daily = 0
    for record in df_day.to_dict('records'):
        result = collection_daily.replace_one(
            filter={'city': record['city'], 'datetime': record['datetime']},    # locate the document if exists
            replacement=record,                         # latest document
            upsert=True)                                # update if exists, insert if not
        if result.matched_count > 0:
            update_count_daily += 1
    logger.info("Daily weather: rows={}, update={}, ".format(df_day.shape[0], update_count_daily) +
                "insert={}".format(df_day.shape[0]-update_count_daily))

    update_count_hourly = 0
    for record in df_hourly.to_dict('records'):
        result = collection_hourly.replace_one(
            filter={'city': record['city'], 'datetime': record['datetime']},    # locate the document if exists
            replacement=record,                         # latest document
            upsert=True)                                # update if exists, insert if not
        if result.matched_count > 0:
            update_count_hourly += 1
    logger.info("Hourly weather: rows={}, update={}, ".format(df_hourly.shape[0], update_count_hourly) +
                "insert={}".format(df_hourly.shape[0]-update_count_hourly))


def fetch_historical_data():
    db = client.get_database("weather")
    collection_daily = db.get_collection("daily_weather")
    collection_hourly = db.get_collection("hourly_weather")
    ret_daily = list(collection_daily.find())
    ret_hourly = list(collection_hourly.find())
    logger.info('Daily weather: ' + str(len(ret_daily)) + ' documents read from the db')
    logger.info('Hourly weather: ' + str(len(ret_hourly)) + ' documents read from the db')
    return ret_daily, ret_hourly


def fetch_historical_data_as_df():
    data_daily, data_hourly = fetch_historical_data()
    if len(data_daily) == 0 or len(data_hourly) == 0:
        return None, None
    df_daily = pd.DataFrame.from_records(data_daily)
    df_daily.drop('_id', axis=1, inplace=True)

    df_hourly = pd.DataFrame.from_records(data_hourly)
    df_hourly.drop('_id', axis=1, inplace=True)

    return df_daily, df_hourly


def upsert_forecast_data(df_daily_forecast, df_hourly_forecast):
    """
    Update MongoDB database `daily_forecast`,  and collection `daily_forecast` with the given `df_daily_forecast`
    Update MongoDB database `hourly_forecast`,  and collection `hourly_forecast` with the given `df_hourly_forecast`
    """
    db = client.get_database("weather")
    collection_daily = db.get_collection("daily_forecast")
    collection_hourly = db.get_collection("hourly_forecast")

    update_count_daily = 0
    for record in df_day.to_dict('records'):
        result = collection_daily.replace_one(
            filter={'city': record['city'], 'datetime': record['datetime']},    # locate the document if exists
            replacement=record,                         # latest document
            upsert=True)                                # update if exists, insert if not
        if result.matched_count > 0:
            update_count_daily += 1
    logger.info("Daily forecat weather: rows={}, update={}, ".format(df_daily_forecast.shape[0], update_count_daily) +
                "insert={}".format(df_daily_forecast.shape[0]-update_count_daily))

    update_count_hourly = 0
    for record in df_hourly.to_dict('records'):
        result = collection_hourly.replace_one(
            filter={'city': record['city'], 'datetime': record['datetime']},    # locate the document if exists
            replacement=record,                         # latest document
            upsert=True)                                # update if exists, insert if not
        if result.matched_count > 0:
            update_count_hourly += 1
    logger.info("Hourly forecast weather: rows={}, update={}, ".format(df_hourly_forecast.shape[0], update_count_hourly) +
                "insert={}".format(df_hourly_forecast.shape[0]-update_count_hourly))


def fetch_forecast_data():
    db = client.get_database("weather")
    collection_daily = db.get_collection("daily_forecast")
    collection_hourly = db.get_collection("hourly_forecast)
    ret_daily = list(collection_daily.find())
    ret_hourly = list(collection_hourly.find())
    logger.info('Daily weather: ' + str(len(ret_daily)) + ' documents read from the db')
    logger.info('Hourly weather: ' + str(len(ret_hourly)) + ' documents read from the db')
    return ret_daily, ret_hourly


def fetch_forecast_data_as_df():
    forecast_daily, forecast_hourly = fetch_forecast_data()
    if len(data_daily) == 0 or len(data_hourly) == 0:
        return None, None
    df_daily_forecast = pd.DataFrame.from_records(forecast_daily)
    df_daily_forecast.drop('_id', axis=1, inplace=True)

    df_hourly_forecast = pd.DataFrame.from_records(forecast_hourly)
    df_hourly_forecast.drop('_id', axis=1, inplace=True)

    return df_daily_forecast, df_hourly_forecast

if __name__ == '__main__':
    location = 'providence'
    dates = process_date_historical(2019, 2, 27, 2019, 3, 5)
    df_day, df_hourly = load_historical_data(location, dates)
    upsert_historical(df_day, df_hourly)
    df_day, df_hourly = fetch_historical_data_as_df()
    print(df_day.head())
    print(df_hourly.head())