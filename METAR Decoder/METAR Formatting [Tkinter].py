'''
Maksim Stadler
May 2019

This program will scrape METARs from www.aviationweather.gov.
The specific page of a specific location's data will be determined by entering a city name.
The program will convert the city name to its 4-letter code with a look up table.
The raw METAR text is parsed and will be formattedsimilarly to how the website does so itself.

Code for generating searchable dropdown menu adapted from https://gist.github.com/uroshekic/11078820
'''

# import required libraries
from tkinter import *
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

# create lists from lokup dictionaries for index selection
stationList = list(stationLUT[ICAOColumn])
autoList = [item[3:] for item in list(stationLUT[stationColumn])]
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

# set default url, city, and label text
url = 'https://www.aviationweather.gov/adds/metars?station_ids=CYSN&std_' \
      'trans=translated&chk_metars=on&hoursStr=past+3+hours'
city = 'ST. CATHARINES A'
defaultData = '''WEATHER REPORT
Conditions at:
Temperature:
Dewpoint:
Pressure (altimeter):
Winds:
                         
Visibility:
Ceiling:
Clouds:
Weather:'''

# set colour variables
grey1 = '#222222'
grey2 = '#333333'
grey3 = '#444444'
grey4 = '#555555'
text1 = '#aaaaaa'
outline = '#7777777'


# noinspection PyShadowingNames
def reportPull(url):
    # pull html code from webpage
    metarHTML = requests.get(url)

    # isolate report text only
    metar = bs4.BeautifulSoup(metarHTML.text, 'lxml').select('strong')[1].getText().split()
    return metar


# parse through METAR text and extract variables according to naming order and conventions
def getReport(metar):
    # prepare certain keys in metar data
    metarDict['windGust'] = 0
    metarDict['station'] = metar[0]
    metarDict['weather'] = []
    metarDict['windDir'] = []
    metarDict['sky'] = []
    # iterate through codes to determine placement and decode
    for code in metar:
        if 'Z' in code:
            metarDict['date'] = code[2:-1] + ' UTC ' + code[:2] + ' ' + monthDict[today.month] + ' ' + str(today.year)
        elif 'KT' in code:
            for dirKey in directionDict:
                if directionDict[dirKey][0] <= int(code[:3]) <= directionDict[dirKey][1]:
                    metarDict['windDir'].append(dirKey)
            if not metarDict['windDir']:
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
    return metarDict


# noinspection PyShadowingNames,PyListCreation,PyUnusedLocal
def formatText(metarDict, metar):
    # print line-by-line recreation of METAR conditions from aviationweather.gov
    global weatherSection
    finalReport = []
    finalReport.append('WEATHER REPORT')
    # finalReport.append(' '.join(metar))
    finalReport.append('Conditions at:           {} ({}) observed {}'.format(metarDict['station'],
                                                                             stationLUT.loc[stationList.index(
                                                                                 metarDict['station'])][
                                                                                 0],
                                                                             metarDict['date']))
    finalReport.append(
        'Temperature:             {}°C ({}°F)'.format(metarDict['temperature'][0], metarDict['temperature'][1]))
    finalReport.append('Dewpoint:                {}°C ({}°F) [RH = {}%]'.format(metarDict['dewpoint'][0],
                                                                                metarDict['dewpoint'][1],
                                                                                metarDict['dewpoint'][2]))
    finalReport.append('Pressure (altimeter):    {} inches Hg'.format(metarDict['pressure']))
    if 'calm' in metarDict['windDir']:
        finalReport.append('Winds:                   calm')
    else:
        finalReport.append('Winds:                   From the {0} ({1} degrees) at {3} MPH ({2} knots; {4} m/s)'.format(
            metarDict['windDir'][0],
            metarDict['windDir'][1],
            metarDict['windSpeed'],
            math.ceil(metarDict['windSpeed'] * kTOmph),
            round(metarDict['windSpeed'] * kTOms, 1)))
    if metarDict['windGust'] != 0:
        finalReport.append(
            '                         Gusting to {1} MPH ({0} knots; {2} m/s)'.format(metarDict['windGust'], math.ceil(
                metarDict['windGust'] * kTOmph), round(metarDict['windGust'] * kTOms, 1)))
    finalReport.append('Visibility:              {} miles ({} km)'.format(metarDict['visibility'],
                                                                          int(metarDict['visibility'] * mTOkm)))
    if metarDict['sky'] == ['SKC']:
        finalReport.append('Clouds:                  Sky is clear')
    if metarDict['sky'] != ['SKC']:
        finalReport.append('Ceiling:                 {} feet AGL'.format(int(metarDict['sky'][0][3:]) * 100))
        finalReport.append('Clouds:                  {} clouds at {} feet AGL'.format(
            cloudLUT[layerColumn][cloudList.index(metarDict['sky'][0][:3])], int(metarDict['sky'][0][3:]) * 100))
        if len(metarDict['sky']) > 1:
            for layer in metarDict['sky'][1:]:
                finalReport.append('                         {} clouds at {} feet AGL'.format(
                    cloudLUT[layerColumn][cloudList.index(layer[:3])], int(layer[3:]) * 100))
    if metarDict['weather']:
        weatherSection = 'Weather:                 '
        for condition in metarDict['weather'][:-1]:
            weatherSection += '{}, '.format(condition)
        weatherSection += metarDict['weather'][-1]
    if not metarDict['weather']:
        weatherSection = 'Weather:                 No significant weather observed at this time'
    finalReport.append(weatherSection)
    return finalReport


# build search bar class for easy station selection
# code is slightly adapted from code from uroskekic's repository
# noinspection PyAttributeOutsideInit,PyUnusedLocal
class METAR(Entry):
    def __init__(self, autocompleteList, *args, **kwargs):

        self.listboxLength = kwargs.pop('listboxLength', 8)

        if 'matchesFunction' in kwargs:
            self.matchesFunction = kwargs['matchesFunction']
            del kwargs['matchesFunction']
        else:
            def matches(fieldValue, acListEntry):
                pattern = re.compile('.*' + re.escape(fieldValue) + '.*', re.IGNORECASE)
                return re.match(pattern, acListEntry)

            self.matchesFunction = matches

        Entry.__init__(self, *args, **kwargs, borderwidth=2, bg=grey2, fg=text1, selectbackground=grey1,
                       selectforeground=text1, font=('Verdana', 10), selectborderwidth=0, insertbackground=text1,
                       relief='solid')
        self.focus()

        # tell search bar to use items from the list of stations for comparison
        self.autocompleteList = autocompleteList

        # set initial string variable to be replaced by index of user selected item from station list
        self.var = self['textvariable']
        if self.var == '':
            self.var = self['textvariable'] = StringVar()

        # bind keys to list selection events
        self.var.trace('w', self.changed)
        self.bind('<Return>', self.selection)
        self.bind('<Button-1>', self.selection)
        self.bind('<Up>', self.moveUp)
        self.bind('<Down>', self.moveDown)
        self.listboxUp = False

    def changed(self, name, index, mode):
        if self.var.get() == '':
            if self.listboxUp:
                self.listbox.destroy()
                self.listboxUp = False
        else:
            words = self.comparison()
            if words:
                if not self.listboxUp:
                    self.listbox = Listbox(mainFrame, height=self.listboxLength, bg=grey2, fg=text1,
                                           font=('Verdana', 10),
                                           selectbackground=grey1, selectforeground=text1, relief='flat')
                    self.listbox.config(highlightbackground=grey2)
                    self.listbox.bind("<Button-1>", self.selection)
                    self.listbox.bind("<Right>", self.selection)
                    self.listbox.place(relx=0.003, rely=0.2, relwidth=0.489)
                    self.listboxUp = True

                self.listbox.delete(0, END)
                for w in words:
                    self.listbox.insert(END, w)
            else:
                if self.listboxUp:
                    self.listbox.destroy()
                    self.listboxUp = False

    # close dropdown list and set stirng varable on click/enter event
    def selection(self, event):
        if self.listboxUp:
            self.var.set(self.listbox.get(ACTIVE))
            self.listbox.destroy()
            self.listboxUp = False
            self.icursor(END)
            global city
            city = self.var.get()

    # move list selection up when up arrow pressed
    def moveUp(self, event):
        if self.listboxUp:
            if self.listbox.curselection() == ():
                index = '0'
            else:
                index = self.listbox.curselection()[0]

            if index != '0':
                self.listbox.selection_clear(first=index)
                index = str(int(index) - 1)

                self.listbox.see(index)  # Scroll!
                self.listbox.selection_set(first=index)
                self.listbox.activate(index)

    # move list selection down when down arrow pressed
    def moveDown(self, event):
        if self.listboxUp:
            if self.listbox.curselection() == ():
                index = '0'
            else:
                index = self.listbox.curselection()[0]

            if index != END:
                self.listbox.selection_clear(first=index)
                index = str(int(index) + 1)

                self.listbox.see(index)  # Scroll!
                self.listbox.selection_set(first=index)
                self.listbox.activate(index)

    # limit station list items to those beginning with substrings matching user search input
    def comparison(self):
        return [w for w in self.autocompleteList if self.matchesFunction(self.var.get(), w)]


# define inner search matching test
def matches(fieldValue, acListEntry):
    pattern = re.compile(re.escape(fieldValue) + '.*', re.IGNORECASE)
    return re.match(pattern, acListEntry)


# define function to update text box with desired weather data
def updateData():
    icao = stationList[autoList.index(city)]
    url = 'https://www.aviationweather.gov/adds/metars?station_ids=' + icao + \
          '&std_trans=translated&chk_metars=on&hoursStr=past+3+hours'
    print(url)
    metar = reportPull(url)
    metarDict = getReport(metar)
    conditionList = formatText(metarDict, metar)
    conditions = '{}'.format('\n'.join(conditionList))
    dataLabel.configure(text=conditions, justify='left', anchor='w')
    print(conditions)


# begin window construction
# set window variable as tk for simplicity
tk = Tk()

# set title, window size, etc.
tk.title('M.E.T.A.R. Decoder')
tk.iconbitmap(default='drizzle-2.vnd')
tk.geometry('700x300')
tk.resizable(False, False)
# tk.overrideredirect(True)

background = Label(tk, bg=grey2)
background.place(relwidth=1, relheight=1)

mainFrame = Frame(tk, bg=grey1, bd='5')
mainFrame.place(relx=0.5, rely=0.5, relwidth=0.96, relheight=0.97, anchor='c')

# create instruction label
instructionLabel = Label(mainFrame, text='ENTER/SELECT A CITY AND CLICK THE BUTTON TO CHECK THE WEATHER',
                         font=('Verdana', 10), bg=grey2, fg=text1, relief='solid')
instructionLabel.place(relx=0, rely=0, relwidth=1, relheight=0.1)

# place search box in bottom row
entry = METAR(autoList, mainFrame, listboxLength=10, matchesFunction=matches)
entry.place(relx=0, rely=0.12, relwidth=0.495, relheight=0.1)

# create button to update METAR data in text box
updateButton = Button(mainFrame, text='CHECK WEATHER', font=('Verdana', 10), command=updateData,
                      activebackground=grey1,
                      activeforeground=text1, bg=grey2, fg=text1, relief='solid')
updateButton.place(relx=0.505, rely=0.12, relwidth=0.495, relheight=0.1)

# create weather data display label
dataLabel = Label(mainFrame, text=defaultData, justify='left', anchor='w', font=('Courier', 10), bg=grey2, fg=text1,
                  borderwidth=2, relief='solid', padx=5)
dataLabel.place(relx=0, rely=0.24, relwidth=1, relheight=0.76)

# open window until closed
tk.mainloop()
