'''
Maksim Stadler
April 2019

This program will scrape METARs from www.aviationweather.gov.
The specific page of a specific location's data will be determined by entering a city name.
The program will convert the city name to its 4-letter code with a look up table.
The raw METAR text is parsed and will be formattedsimilarly to how the website does so itself.
'''

# import requests
import pandas as pd
import datetime
import requests
import math
import bs4

# set some variables
today = datetime.datetime.now()
kTOmph = 1.15077944702935
kTOms = 0.514444444
mTOkm = 1.609344
stationColumn = 'STATION'
ICAOColumn = 'ICAO'
codeColumn = 'Code'
weatherColumn = 'Weather'
layerColumn = 'Layer'
metarDict = {}
monthDict = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
             5: 'May', 6: 'June', 7: 'July', 8: 'August',
             9: 'September', 10: 'October', 11: 'November', 12: 'December'}
# create lookup dictionary of canadian cities and their codes only only
stationLUT = pd.read_csv('station_lut.csv')
weatherLUT = pd.read_csv('weather_lut.csv')
cloudLUT = pd.read_csv('cloud_lut.csv')
stationList = list(stationLUT[ICAOColumn])
weatherList = list(weatherLUT[codeColumn])
cloudList = list(cloudLUT[codeColumn])
directionDict = {'NNE': [12, 33],
                 'NE': [34, 56],
                 'ENE': [57, 78],
                 'E': [79, 101],
                 'ESE': [102, 123],
                 'SE': [124, 146],
                 'SSE': [147, 168],
                 'S': [169, 191],
                 'SSW': [192, 213],
                 'SW': [214, 236],
                 'WSW': [237, 258],
                 'W': [259, 281],
                 'WNW': [282, 303],
                 'NW': [304, 326],
                 'NNW': [327, 348]}
url = 'https://www.aviationweather.gov/adds/metars?station_ids=CYSN&std_' \
      'trans=translated&chk_metars=on&hoursStr=past+3+hours'

# set user mode to True/False
# userMode = False

# check if user mode is on
# if userMode:
#     ask user for city name
#     cityName = input('Enter the name of a canadian city: ').upper()
#     convert city name to code
#     cityCode = cityDict[cityName]
#     generate URL variable with that city's data
#     url='https://www.aviationweather.gov/adds/metars?station_ids=' + cityCode + '&std_trans=translated&chk_metars=on'

# check if user mode is off
#     set URL variable
#     url = 'https://www.aviationweather.gov/adds/metars?station_ids=
#     CYSN&std_trans=translated&chk_metars=on&hoursStr=past+3+hours'
#     set city name variable
#     cityName = 'ST. CATHERINES'

# pull html code from webpage
metarHTML = requests.get(url)

# isolate report text only
metar = bs4.BeautifulSoup(metarHTML.text, 'lxml').select('strong')[1].getText().split()
# print(metar)

# prepare certain keys in metar data
metarDict['windGust'] = 0
metarDict['station'] = metar[0]
metarDict['weather'] = []
metarDict['windDir'] = []
metarDict['sky'] = []

# parse through METAR text and extract variables according to naming order and conventions
for code in metar:
    if 'Z' in code:
        metarDict['date'] = code[2:-1] + ' UTC ' + code[:2] + ' ' + monthDict[today.month] + ' ' + str(today.year)
    elif 'KT' in code:
        for dirKey in directionDict:
            if directionDict[dirKey][0] <= int(code[:3]) <= directionDict[dirKey][1]:
                metarDict['windDir'].append(dirKey)
        if not metarDict['windDir']:
            # noinspection PyTypeChecker
            metarDict['windDir'].append('calm')
        metarDict['windDir'].append(int(code[:3]))
        metarDict['windSpeed'] = int(code[3:5])
        if 'G' in code:
            metarDict['windGust'] = int(code[code.index('G') + 1:code.index('KT')])
    elif 'SM' in code:
        metarDict['visibility'] = int(code[:code.index('S')])
    elif code[0] in weatherList:
        metarDict['weather'].append(weatherLUT[weatherColumn][weatherList.index(code[0])] + ' ' +
                                    weatherLUT[weatherColumn][weatherList.index(code[1:])])
    elif code in weatherList:
        if not metarDict['weather']:
            metarDict['weather'].append('Moderate ' + weatherLUT[weatherColumn][weatherList.index(code)])
        else:
            metarDict['weather'].append(weatherLUT[weatherColumn][weatherList.index(code)])
    elif code[:3] in cloudList:
        metarDict['sky'].append(code)
    elif code[2:3] == '/':
        metarDict['temperature'] = [float(code[:code.index('/')]), float(code[:code.index('/')]) * 9 / 5 + 32]
        metarDict['dewpoint'] = [float(code[code.index('/') + 1:].replace('M', '-')),
                                 float(code[code.index('/') + 1:].replace('M', '-')) * 9 / 5 + 32,
                                 int(-(metarDict['temperature'][1] - (float(
                                     code[code.index('/') + 1:].replace('M', '-')) * 9 / 5 + 32)) * 10 / 3 + 100)]
    elif code[0] == 'A' and len(code) == 5:
        metarDict['pressure'] = int(code[1:]) / 100

# Example

# Weather Report
# Conditions at:	    CYSN (ST. CATHARINES A, ON, CA) observed 1800 UTC 20 April 2019
# Temperature:	        7.0°C (45°F)
# Dewpoint:	            7.0°C (45°F) [RH = 100%]
# Pressure (altimeter):	29.62 inches Hg (1003.1 mb)
# [Sea-level pressure:  1003.4 mb]
# Winds:	            from the ENE (70 degrees) at 17 MPH (15 knots; 7.7 m/s)
#                       gusting to 29 MPH (25 knots; 12.9 m/s)
# Visibility:	        15 miles (24 km)
# Ceiling:	            900 feet AGL
# Clouds:	            overcast cloud deck at 900 feet AGL
# Weather:	            no significant weather observed at this time

# Note:
# - Both columns are left justified
# - Values must align after longest label (dot leaders?)
# - Values listed in same order as METAR text

# print line-by-line recreation of METAR conditions from aviationweather.gov
print('Weather Report')
print(*metar)
print('Conditions at:           {} ({}) observed {}'.format(metarDict['station'],
                                                            stationLUT.loc[stationList.index(metarDict['station'])][0],
                                                            metarDict['date']))
print('Temperature:             {}°C ({}°F)'.format(metarDict['temperature'][0], metarDict['temperature'][1]))
print('Dewpoint:                {}°C ({}°F) [RH = {}%]'.format(metarDict['dewpoint'][0],
                                                               metarDict['dewpoint'][1],
                                                               metarDict['dewpoint'][2]))
print('Pressure (altimeter):    {} inches Hg'.format(metarDict['pressure']))
if 'calm' in metarDict['windDir']:
    print('Winds:                   calm')
else:
    print('Winds:                   From the {0} ({1} degrees) at {3} MPH ({2} knots; {4} m/s)'.format(
        metarDict['windDir'][0],
        metarDict['windDir'][1],
        metarDict['windSpeed'],
        math.ceil(metarDict['windSpeed'] * kTOmph),
        round(metarDict['windSpeed'] * kTOms, 1)))
if metarDict['windGust'] != 0:
    print('                         Gusting to {1} MPH ({0} knots; {2} m/s)'.format(metarDict['windGust'], math.ceil(
        metarDict['windGust'] * kTOmph), round(metarDict['windGust'] * kTOms, 1)))
print('Visibility:              {} miles ({} km)'.format(metarDict['visibility'],
                                                         int(metarDict['visibility'] * mTOkm)))
if metarDict['sky'] == ['SKC']:
    print('Clouds:                  Sky is clear')
if metarDict['sky'] != ['SKC']:
    print('Ceiling:                 {} feet AGL'.format(int(metarDict['sky'][0][3:]) * 100))
    print('Clouds:                  {} clouds at {} feet AGL'.format(
        cloudLUT[layerColumn][cloudList.index(metarDict['sky'][0][:3])], int(metarDict['sky'][0][3:]) * 100))
    if len(metarDict['sky']) > 1:
        for layer in metarDict['sky'][1:]:
            print('                         {} clouds at {} feet AGL'.format(
                cloudLUT[layerColumn][cloudList.index(layer[:3])], int(layer[3:]) * 100))
if metarDict['weather']:
    print('Weather:                 ', end='')
    for condition in metarDict['weather'][:-1]:
        print('{}'.format(condition), end=', ')
    print(metarDict['weather'][-1])
if not metarDict['weather']:
    print('Weather:                 No significant weather observed at this time')
