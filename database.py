import logging
import pymongo
import pandas as pd
import expiringdict
import utils


client = pymongo.MongoClient()
logger = logging.Logger(__name__)
utils.setup_logger(logger, 'database.log')
RESULT_CACHE_EXPIRATION = 15             # seconds

def upsert_forecast_data(df_daily_forecast, df_hourly_forecast):
    """
    Update MongoDB database `daily_forecast`,  and collection `daily_forecast` with the given `df_daily_forecast`
    Update MongoDB database `hourly_forecast`,  and collection `hourly_forecast` with the given `df_hourly_forecast`
    """
    db = client.get_database("weather")
    collection_daily = db.get_collection("daily_weather_forecast")
    collection_hourly = db.get_collection("hourly_weather_forecast")

    update_count_daily = 0
    for record in df_daily_forecast.to_dict('records'):
        result = collection_daily.replace_one(
            filter={'city': record['city'], 'datetime': record['datetime']},    # locate the document if exists
            replacement=record,                         # latest document
            upsert=True)                                # update if exists, insert if not
        if result.matched_count > 0:
            update_count_daily += 1
    logger.info("Daily forecat weather: rows={}, update={}, ".format(df_daily_forecast.shape[0], update_count_daily) +
                "insert={}".format(df_daily_forecast.shape[0]-update_count_daily))

    update_count_hourly = 0
    for record in df_hourly_forecast.to_dict('records'):
        result1 = collection_hourly.replace_one(
            filter={'city': record['city'], 'datetime': record['datetime']},    # locate the document if exists
            replacement=record,                         # latest document
            upsert=True)                                # update if exists, insert if not
        if result1.matched_count > 0:
            update_count_hourly += 1

        if record['current']:
            result2 = collection_hourly.replace_one(
                filter={'current': True},                    # locate the document if exists
                replacement=record,                         # latest document
                upsert=True)                                # update if exists, insert if not
            if result2.matched_count > 0 and result1.matched_count <= 0:
                update_count_hourly += 1
    logger.info("Hourly forecast weather: rows={}, update={}, ".format(df_hourly_forecast.shape[0], update_count_hourly) +
                "insert={}".format(df_hourly_forecast.shape[0]-update_count_hourly))


def fetch_forecast_data():
    db = client.get_database("weather")
    collection_daily = db.get_collection("daily_weather_forecast")
    collection_hourly = db.get_collection("hourly_weather_forecast")
    ret_daily = list(collection_daily.find())
    ret_hourly = list(collection_hourly.find())
    logger.info('Daily weather: ' + str(len(ret_daily)) + ' documents read from the db')
    logger.info('Hourly weather: ' + str(len(ret_hourly)) + ' documents read from the db')
    return ret_daily, ret_hourly

_fetch_forecast_data_as_df_cache = expiringdict.ExpiringDict(max_len=1,
                                                       max_age_seconds=RESULT_CACHE_EXPIRATION)


def fetch_forecast_data_as_df(allow_cached=False):
    """Converts list of dicts returned by `fetch_all_bpa` to DataFrame with ID removed
    Actual job is done in `_worker`. When `allow_cached`, attempt to retrieve timed cached from
    `_fetch_all_bpa_as_df_cache`; ignore cache and call `_work` if cache expires or `allow_cached`
    is False.
    """
    def _work():
        daily_forecast_data, hourly_forecast_data = fetch_forecast_data()
        if len(daily_forecast_data) == 0 or len(hourly_forecast_data) == 0:
            return None
        df_daily_forecast = pd.DataFrame.from_records(daily_forecast_data)
        df_daily_forecast.drop('_id', axis=1, inplace=True)

        df_hourly_forecast = pd.DataFrame.from_records(hourly_forecast_data)
        df_hourly_forecast.drop('_id', axis=1, inplace=True)

        return (df_daily_forecast, df_hourly_forecast)

    if allow_cached:
        try:
            return _fetch_forecast_data_as_df_cache['cache']
        except KeyError:
            pass
    ret = _work()
    _fetch_forecast_data_as_df_cache['cache'] = ret
    return ret

if __name__ == '__main__':
    print(fetch_forecast_data_as_df()[0])
    print('--------------------')
    print(fetch_forecast_data_as_df()[1])