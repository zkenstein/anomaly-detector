# Amit az algoritmus megvalósít:
# Egy négyzetet tud elemezni és annak indexét paraméterként kapja. Összeállít egy átlagos novemberi napot az adott négyzeten. Egy görbe, amit egy regresszor hoz létre, lesz az átlagos nap.
# - Végigmegy a training data összes napjának adott négyzetén és minden timestampre csinál egy targetet (nevezzük activitynek). Úgy hozza létre a activityt, hogy veszi az SMS in/out és call in/out adatok (tehát 4 különböző, de összehasonlítható) átlagát.
# - Kirajzolja ezeket az értékeket.

# TODO Hogyan kéne még fejleszteni a tranininget:
# - Kiszűrni a training databól az outlinerket, hisz egy átlagos napot akarunk megkapni.
# - A munkanapot és a hétvégét különválasztani.
# - A country code segítségével csinálni egy új feature-t.
# - Ahelyett, hogy az összes feature-t aggregáljuk (és lesz belőle az activity), minden feature-t külön kéne kezelni.
# - PCA-t használni.

from argparse import ArgumentParser
from os import walk
from os.path import join
from csv import DictReader
from time import time
from datetime import datetime
import matplotlib.pyplot as plot
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from scipy.interpolate import splrep
from scipy.interpolate import splev

# parse the arguments
parser = ArgumentParser(description='The machine learning algorithm for the anomaly detector.')
parser.add_argument('--training', help='Path to the root directory of the training dataset.', required=True)
parser.add_argument('--testing', help='Path to the root directory of the testing dataset.', required=True)
parser.add_argument('-s','--square', type=int, help='The square to analyze.', required=True)
args = vars(parser.parse_args())
trainingFilesRoot = args['training']
testingFilesRoot = args['testing']
square = args['square']

# preprocess the dataset under the given root and return the features and the targets
def preprocessDataset(datasetRoot, isTesting=False):
    startTime = time()

    # collect the dataset's files
    datasetFiles = []
    for (dirPath, dirNames, fileNames) in walk(datasetRoot):
        datasetFiles.extend([join(dirPath, fileName) for fileName in fileNames])

    # walk through the dataset's files and read the data for the given square
    fieldNames=('square_id', 'time_interval', 'country_code', 'sms_in', 'sms_out', 'call_in', 'call_out', 'internet_traffic')
    rawData = []
    for datasetFile in datasetFiles:
        with open(datasetFile) as tsvFile:
            tsvReader = DictReader(tsvFile, delimiter='\t', fieldnames=fieldNames)
            for row in tsvReader:
                if int(row['square_id']) == square:
                    rawData.append(row)
                elif int(row['square_id']) > square: # assume that the square id is increasing in each file
                    break

    # drop country code and the internet traffic and aggregate the rest
    cleanData = {}
    for row in rawData:
        if row['time_interval'] in cleanData:
            for key in cleanData[row['time_interval']]:
                cleanData[row['time_interval']][key] += float(row[key]) if row[key] != '' else float(0)
        else:
            cleanData[row['time_interval']] = {
                'sms_in' : float(row['sms_in']) if row['sms_in'] != '' else float(0),
                'sms_out' : float(row['sms_out']) if row['sms_out'] != '' else float(0),
                'call_in' : float(row['call_in']) if row['call_in'] != '' else float(0),
                'call_out' : float(row['call_out']) if row['call_out'] != '' else float(0),
                'internet_traffic' : float(row['internet_traffic']) if row['internet_traffic'] != '' else float(0)
            }

    # collect the features and the targets
    features = np.array([])
    targets = None
    for timestamp, properties in cleanData.items():
        date = datetime.fromtimestamp(float(timestamp) / 1000.0)
        minutes = 60 * date.hour + date.minute
        if isTesting:
            minutes += 24 * 60 * (date.day - 1)
        features = np.append(features, minutes)
        newTargetsRow = [properties['sms_in'], properties['sms_out'], properties['call_in'], properties['call_out'], properties['internet_traffic']]
        if targets is None:
            targets = np.array(newTargetsRow)
        else:
            targets = np.vstack([targets, newTargetsRow])

    # scale the targets into (0,1)
    targets = MinMaxScaler().fit_transform(targets)

    # reduce the targets to 1, by calculate the average of each row
    reducedTargets = np.array([])
    for row in targets:
        reducedTargets = np.append(reducedTargets, np.average(row))
    targets = reducedTargets

    # sort the arrays by the timestamp
    order = np.argsort(features)
    features = np.array(features)[order]
    targets = np.array(targets)[order]

    features = features.reshape(-1, 1) # required by sklearn

    print('Time for preprocess a dataset: ', round(time() - startTime, 3), ' sec')
    return targets, features

# preprocess the training dataset
targetsForTraining, featuresForTraining = preprocessDataset(trainingFilesRoot)
print('Targets for training: ', targetsForTraining)
print('Features for training: ', featuresForTraining)

# preprocess the testing dataset
targetsForTesting, featuresForTesting = preprocessDataset(testingFilesRoot, isTesting=True)
print('Targets for testing: ', targetsForTesting)
print('Features for testing: ', featuresForTesting)

# create a interpolation polynomial based on the given features and targets
def createInterpolationPolynomial(features, targets):
    startTime = time()
    interpolationPolynomial = splrep(features, targets, k=3)
    xnew = np.linspace(np.amin(features), np.amax(features), 144, endpoint=True)
    ynew = splev(xnew, interpolationPolynomial)
    print('Create interpolation polynomial time: ', round(time() - startTime, 3), ' sec')
    return xnew, ynew

# create the interpolation polynomial based on the training data
trainingInterpolationPolynomialX, trainingInterpolationPolynomialY = createInterpolationPolynomial(featuresForTraining, targetsForTraining)

# draw the day's data into the plot and show it
def drawDayIntoThePlotAndShow(day, dayFeatures, dayTargets):
    plot.scatter(featuresForTraining, targetsForTraining, color='gray', label='training data')
    plot.plot(trainingInterpolationPolynomialX, trainingInterpolationPolynomialY, color='blue', label='trained interpolation polynomial')

    plot.scatter(dayFeatures, dayTargets, color='black', label='current day data')
    currentDayInterpolationPolynomialX, currentDayInterpolationPolynomialY = createInterpolationPolynomial(dayFeatures, dayTargets)
    plot.plot(currentDayInterpolationPolynomialX, currentDayInterpolationPolynomialY, color='red', label='current day interpolation polynomial')

    plot.xlabel('time in minutes')
    plot.ylabel('activity')
    plot.title('The Average Day in November vs day ' + str(day) + ' in December')
    plot.legend()
    plot.show()

# walk through each day in the testing dataset and draw the regression line
currentDayFeatures = None
currentDayTargets = None
currentDay = 0
for index, minutes in enumerate(featuresForTesting):
    day = int(int(minutes[0]) / int(24 * 60) + 1)
    if currentDay < day: # if we collected all data for a day (assume that the minutes are in ascending order)
        if currentDay > 0: # skip day zero
            currentDayFeatures = currentDayFeatures.reshape(-1, 1) # required by sklearn
            drawDayIntoThePlotAndShow(currentDay, currentDayFeatures, currentDayTargets)
        # prepare for the new day
        currentDay = day
        currentDayFeatures = np.array([])
        currentDayTargets = np.array([])
    # collect the day's data
    currentDayFeatures = np.append(currentDayFeatures, minutes[0] - (day - 1) * 24 * 60)
    currentDayTargets = np.append(currentDayTargets, targetsForTesting[index])
