"""
Utility functions for the anomaly detector to preprocess the dataset.
"""

import csv
from datetime import datetime

import numpy as np
from sklearn import preprocessing

import common_function
import constant

"""
IDs of the columns of the data, ordered as the input data rows.
"""
_COLUMNS = (constant.FEATURE_SQUARE_ID, constant.FEATURE_TIME_INTERVAL, constant.FEATURE_COUNTRY_CODE, constant.FEATURE_SMS_IN, constant.FEATURE_SMS_OUT, constant.FEATURE_CALL_IN, constant.FEATURE_CALL_OUT, constant.FEATURE_INTERNET_TRAFFIC)

"""
The scaler for the feature scaling.
"""
_SCALER = None

"""
A constant that controls how many outliers we will drop.
"""
_OUTLIER_CONTROL = 1.75


def read_files(files, squares):
    """Reades the given files and collect the data for the specified squares.

    Args:
        files: Paths to the files. It must be an iterable on strings.
        squares: The squares to read. It must be a collection of ints.

    Returns:
        The list of the read rows, where each item is a dictinary, where the keys are specified in the _COLUMNS constant.
    """
    data = []
    for file in files:
        # FIXME a hack to fasten the file reader
        with open(file) as tsv_file:
            tsv_reader = csv.DictReader(tsv_file, delimiter='\t', fieldnames=_COLUMNS)
            last_read_square_id = -1
            counter = -1
            for row in tsv_reader:
                if last_read_square_id != int(row[constant.FEATURE_SQUARE_ID]):  # assume that the values for a square are groupped together
                    counter += 1
                    if counter < len(squares):
                        last_read_square_id = int(row[constant.FEATURE_SQUARE_ID])
                    else:
                        break
                data.append(row)
        # this should be the implementation, but it requires much more time to run. I can optimize this a little
        # with open(file) as tsv_file:
        #     print('Reading ' + file)
        #     tsv_reader = csv.DictReader(tsvFile, delimiter='\t', fieldnames=_COLUMNS)
        #     for row in tsv_reader:
        #         for square in squares:
        #             if int(row[constant.FEATURE_SQUARE_ID]) == square:
        #                 data.append(row)
    return data


def get_value_from_row(row, value_id):
    """Returns the values for the given ID from the given row.

    If the value is missing from the row, it returns 0.

    Args:
        row: The row as a dictionary of the features.
        value_id: The ID of the value to get as a string.

    Returns:
        The value for the given ID as a float.
    """
    value = float(row[value_id]) if row[value_id] else 0.
    return value


def group_data_by_time_interval(data):
    """Group the given data by the timestamps.

    It summarises the values for each property for the same timestamp, except the country code. Instead of the country
    code, it calculates the activities for the foreign countries.

    Args:
        data: The data as a list of dictionaries, where the keys are the FEATURE_* constants.

    Returns:
        The grouped data as a dictinary, where the keys are the timestamps and the values are the properties for a timestamp as a dictinary. The latter's keys are the following globals: constant.FEATURE_SMS_IN, constant.FEATURE_SMS_OUT, constant.FEATURE_CALL_IN, constant.FEATURE_CALL_OUT, constant.FEATURE_INTERNET_TRAFFIC, constant.FEATURE_FOREIGN.
    """
    grouped_data = {}
    for row in data:
        time_interval = row[constant.FEATURE_TIME_INTERVAL]
        if time_interval in grouped_data:
            for prop in grouped_data[time_interval]:
                grouped_data[time_interval][prop] += get_value_from_row(row, prop)
        else:
            grouped_data[time_interval] = {
                constant.FEATURE_SMS_IN: get_value_from_row(row, constant.FEATURE_SMS_IN),
                constant.FEATURE_SMS_OUT: get_value_from_row(row, constant.FEATURE_SMS_OUT),
                constant.FEATURE_CALL_IN: get_value_from_row(row, constant.FEATURE_CALL_IN),
                constant.FEATURE_CALL_OUT: get_value_from_row(row, constant.FEATURE_CALL_OUT),
                constant.FEATURE_INTERNET_TRAFFIC: get_value_from_row(row, constant.FEATURE_INTERNET_TRAFFIC),
            }
    return grouped_data


def split_data_for_timestamps_and_features(data):
    """Split the data for timestamps and features.

    Args:
        data: The data as a dictinary, where the keys are the timestamps and the values are the features for a timestamp as a dictionary.

    Returns:
        A tuple, with the following items.
        - 1.: The timestamps as a numpy array of strings.
        - 2.: The features as a numpy array of numpy arrays (a matrix), where each column represents a feature.
    """
    timestamps = np.array([])
    features = None
    for timestamp, properties in data.items():
        timestamps = np.append(timestamps, timestamp)
        new_row = [properties[constant.FEATURE_SMS_IN], properties[constant.FEATURE_SMS_OUT], properties[constant.FEATURE_CALL_IN], properties[constant.FEATURE_CALL_OUT], properties[constant.FEATURE_INTERNET_TRAFFIC]]
        features = common_function.add_row_to_matrix(features, new_row)
    return timestamps, features


def split_data_for_weekdays_and_weekends(timestamps, features):
    """Split the data for weekdays and weekends.

    Args:
        timestamps: The timestamps as a numpy array of strings.
        features: The features as a numpy array of numpy arrays (a matrix), where each column represents a feature.

    Returns:
        A tuple, where the first element corresponds for the weekdays and the second for the weekends. Each element is a list, with the following items.
        - 1.: The timestamps as a numpy array of strings. (as given)
        - 2.: The features as a numpy array of numpy arrays (a matrix), where each column represents a feature. (as given)
    """
    weekday_timestamps = np.array([])
    weekend_timestamps = np.array([])
    weekday_features = None
    weekend_features = None
    for index, timestamp in enumerate(timestamps):
        date = datetime.fromtimestamp(float(timestamp) / 1000.)
        if date.weekday() < 5:
            weekday_timestamps = np.append(weekday_timestamps, timestamp)
            weekday_features = common_function.add_row_to_matrix(weekday_features, features[index])
        else:
            weekend_timestamps = np.append(weekend_timestamps, timestamp)
            weekend_features = common_function.add_row_to_matrix(weekend_features, features[index])
    return {constant.TIMESTAMPS: weekday_timestamps, constant.FEATURES: weekday_features}, {constant.TIMESTAMPS: weekend_timestamps, constant.FEATURES: weekend_features}


def scale_features(features):
    """Scale the features with a min-max scaler. It is saving the firstly created scaler and use it as a transformer every time.

    Args:
        features: The features as a numpy array of numpy arrays (a matrix), where each column represents a feature.

    Returns:
        The scaled features.
    """
    global _SCALER
    if _SCALER is None:
        _SCALER = preprocessing.MinMaxScaler().fit(features)
    return _SCALER.transform(features)


def translate_matrix_to_mean_vector(matrix):
    """Translate each row in the matrix to their mean values.

    Args:
        features: The features as a numpy array of numpy arrays (a matrix), where each column represents a feature.

    Returns:
        - 1.: The vector of the mean values.
    """
    mean_vector = np.array([])
    for row in matrix:
        mean_vector = np.append(mean_vector, np.mean(row))
    return mean_vector


def preprocess_dataset(dataset_files, squares, is_training=False):
    """Preprocess the given dataset.

    1. Reads the files.
    2. Group by time interval.
    3. Split to timestamps and features.
    4. Split to weekdays and weekends.
    5. Scale.
    6. Select and convert the specified features.
    7. If it's a training dataset, convert timestamps to the passed minutes each day.
    8. Sort the arrays based on the timestamps.
    If the dataset is large, it will run for a while.

    Args:
        dataset_files: List of the paths of the dataset files.
        squares: The squares to read.
        is_training: Indicates if it's a training dataset or not. False by default.

    Returns:
        The processed dataset as a dictionary, with the following schema:
        {
            constant.WEEKDAYS: { constant.TIMESTAMPS: [ ... ], constant.FEATURES: [ ... ] },
            constant.WEEKENDS: { constant.TIMESTAMPS: [ ... ], constant.FEATURES: [ ... ] }
        }
    """
    data = read_files(dataset_files, squares)
    data = group_data_by_time_interval(data)
    timestamps, features = split_data_for_timestamps_and_features(data)
    weekdays, weekends = split_data_for_weekdays_and_weekends(timestamps, features)
    categories = {constant.WEEKDAYS: weekdays, constant.WEEKENDS: weekends}
    for _, category in categories.items():
        category[constant.FEATURES] = scale_features(category[constant.FEATURES])
        category[constant.FEATURES] = translate_matrix_to_mean_vector(category[constant.FEATURES])
        if is_training:
            category[constant.TIMESTAMPS] = common_function.get_minutes(category[constant.TIMESTAMPS])
        category[constant.TIMESTAMPS], category[constant.FEATURES] = common_function.sort_arrays_based_on_the_first(category[constant.TIMESTAMPS], category[constant.FEATURES])
    return categories


def drop_outliers(vector):
    """Drops the outliers from the given vector.

    It calculates each value's difference from the mean. It will drop a value, if the difference is greater than the _OUTLIER_CONTROL * standard deviation of the vector.

    Args:
        vector: The vector, as a numpy array of numbers.

    Returns:
        The vector without the outliers.
    """
    difference_from_mean = abs(vector - np.mean(vector))
    standard_deviation = np.std(vector)
    allowed_difference = _OUTLIER_CONTROL * standard_deviation
    return vector[difference_from_mean <= allowed_difference]


def features_mean_for_each_timestamps(data):
    """Calculates the mean of each feature for each timestamp.

    Also drops the outliers with the drop_outliers_from_vector function.

    Args:
        data: A dictionary with the following form: { constant.TIMESTAMPS: [ ... ], constant.FEATURES: [ ... ] }.

    Returns:
        The data with the the new mean feature matrix instead of the given.
    """
    features_mean = np.array([])
    current_timestamp = data[constant.TIMESTAMPS][0]
    current_values = np.array([])
    for index, _ in enumerate(data[constant.TIMESTAMPS]):
        current_values = np.append(current_values, data[constant.FEATURES][index])
        if index == len(data[constant.TIMESTAMPS]) - 1 or current_timestamp < data[constant.TIMESTAMPS][index + 1]:
            # add the mean value
            current_values = drop_outliers(current_values)
            features_mean = np.append(features_mean, np.average(current_values))
            # prepare for the next iteration
            if index != len(data[constant.TIMESTAMPS]) - 1:
                current_timestamp = data[constant.TIMESTAMPS][index + 1]
                current_values = np.array([])
    return features_mean


def group_data_by_day(data):
    """Group the given data by day.

    It assumes that the timestamps are in ascending order.

    Args:
        data: A dictionary with the following form: { constant.TIMESTAMPS: [ ... ], constant.FEATURES: [ ... ] }.

    Returns:
        An array, where each element is a dictionary with the following form: { constant.DAY: [ ... ], constant.TIMESTAMPS: [ ... ], constant.FEATURES: [ ... ] }.
    """
    days = np.array([])
    current_day = common_function.date_from_timestamp(data[constant.TIMESTAMPS][0]).day
    current_timestamps = np.array([])
    current_features = np.array([])
    for index, timestamp in enumerate(data[constant.TIMESTAMPS]):
        if index != len(data[constant.TIMESTAMPS]) - 1:
            next_day = common_function.date_from_timestamp(data[constant.TIMESTAMPS][index + 1]).day
        current_timestamps = np.append(current_timestamps, common_function.get_minute(timestamp))
        current_features = np.append(current_features, data[constant.FEATURES][index])
        if index == len(data[constant.TIMESTAMPS]) - 1 or current_day < next_day:
            # add the current day's data
            day_data = {constant.DAY: current_day, constant.TIMESTAMPS: current_timestamps, constant.FEATURES: current_features}
            days = np.append(days, day_data)
            # prepare for the next iteration
            if index != len(data[constant.TIMESTAMPS]) - 1:
                current_day = next_day
                current_timestamps = np.array([])
                current_features = np.array([])
    return days
