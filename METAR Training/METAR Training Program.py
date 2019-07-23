'''
Makism Stadler
June 2019

This program will assign random METAR reports to a user and display the simplified, english. The user will then have to
rewrite the full METAR code string properly formatted according the official rules. It will be compared and scored,
and hints will be provided as options.

Frame swapping code adapted from https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
'''

# import required libraries
from tkinter import *
import pandas as pd
from math import *
import datetime
import requests
import random
import bs4

# set colour variables
grey1 = '#222222'
grey2 = '#333333'
grey3 = '#444444'
grey4 = '#555555'
text1 = '#aaaaaa'
text2 = '#777777'

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

# create lookup dictionary of canadian cities and their codes only
stationLUT = pd.read_csv('station_lut.csv')
weatherLUT = pd.read_csv('weather_lut.csv')
cloudLUT = pd.read_csv('cloud_lut.csv')

# create lists from lookup dictionaries for index selection
stationList = ['CYSN', 'CYTH', 'CYBL', 'CYDF', 'CYYZ']
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
hintList = ['Remember: Order matters.', 'Celcius, miles per hour, and inches are the units used in the codes.',
            'Don\'t forget to read up on weather and cloud codes', 'The first code is 4 letters.',
            'Click the hint button for random hints']
defaultDataFilled = '''
METAR Text:            CYSN 012225Z 28006KT 250V310 6SM -SHRA OVC100 15/13 A2974
Conditions At:         CYSN (ST. CATHARINES A, ON, CA) observed 2225 UTC 01 June 2019
Temperature:           15.0°C (59°F)
Dewpoint:              13.0°C (55°F) [RH = 88%]
Pressure (altimeter):  29.74 inches Hg (1007.2 mb)
Winds:                 from the W (280 degrees) at 7 MPH (6 knots; 3.1 m/s)
Visibility:            6 miles (10 km)
Ceiling:               10000 feet AGL
Clouds:                overcast cloud deck at 10000 feet AGL
Weather:               -SHRA  (light rain showers)'''

defaultDataEmpty = '''METAR Text:
Conditions At:
Temperature:
Dewpoint:
Pressure (altimeter):
Winds:
Visibility:
Ceiling:
Clouds:
Weather:'''

# simplify Tk()
tk = Tk


# noinspection PyShadowingNames
def reportPull(url):
    '''
    pull oy only METAR text from aviaitonweather.gov and split int olist of individual condition codes
    :param url: full URL of city's weather for past x hours
    :return: list of encoded conditions
    '''
    # pull html code from webpage
    metarHTML = requests.get(url)
    # isolate report text only
    global metar
    metar = bs4.BeautifulSoup(metarHTML.text, 'lxml').select('strong')[1].getText().split()
    return metar


# parse through METAR text and extract variables according to naming order and conventions
def getReport(metar):
    '''
    iterate through codes and decrypting them based on which condition they describe
    :param metar: list of encoded conditions
    :return: dictionary of weather conditionss and data/time
    '''
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
def formatText(metarDict):
    '''
    generate multiline string based on dictionary of weather condiitions
    :param metarDict: dictionary of conditions
    :return: multiline string of decoded conditions in english
    '''
    # create line-by-line recreation of METAR conditions from aviationweather.gov
    global weatherSection
    finalReport = []
    finalReport.append('WEATHER REPORT')
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
            ceil(metarDict['windSpeed'] * kTOmph),
            round(metarDict['windSpeed'] * kTOms, 1)))
    if metarDict['windGust'] != 0:
        finalReport.append(
            '                         Gusting to {1} MPH ({0} knots; {2} m/s)'.format(metarDict['windGust'], ceil(
                metarDict['windGust'] * kTOmph), round(metarDict['windGust'] * kTOms, 1)))
    finalReport.append('Visibility:              {} miles ({} km)'.format(metarDict['visibility'],
                                                                          int(metarDict['visibility'] * mTOkm)))
    if metarDict['sky'] == ['SKC']:
        finalReport.append('Clouds:                  Sky is clear')
    if metarDict['sky'] != ['SKC']:
        finalReport.append('Ceiling:                 {} feet AGL'.format(int(metarDict['sky'][-1][3:]) * 100))
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


# create application class
# noinspection PyMissingConstructor
class weatherApp(tk):
    def __init__(self, *args, **kwargs):
        tk.__init__(self, *args, **kwargs)

        # set window size and position on screen
        winWidth = 800
        winHeight = 400
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws / 2) - (winWidth / 2)
        y = (hs / 3) - (winHeight / 3)
        self.geometry('%dx%d+%d+%d' % (winWidth, winHeight, x, y))
        self.minsize(800, 400)

        # set window title, icon, etc.
        self.title('M.E.T.A.R. Testing')
        self.iconbitmap(default='drizzle-2.vnd')
        self.configure(background=grey2)

        # set area to parent frames
        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # list expected frames and define area to parent them
        self.frames = {}
        for F in (homePage, encodeTestPage, instructionPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("homePage")

    # define function to place desired frame on top layer
    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


# define homepage frame
class homePage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        # set background colour
        self.configure(background=grey1)

        # banner label
        banner = Label(self, bg=grey2)
        banner.place(x=-1, y=-1, relwidth=1, height=22)

        # button for homepage
        homeButton = Button(banner, text='Home', command=lambda: controller.show_frame("homePage"),
                            font=('Verdana', 10), activebackground=grey1, activeforeground=text1,
                            disabledforeground=text1, bg=grey1, fg=text1, relief='flat', borderwidth=0, state='d')
        homeButton.place(x=0, y=0, width=50, height=20)
        # button for encoding practice
        encodeTestButton = Button(banner, text='Encoding Practice',
                                  command=lambda: controller.show_frame("encodeTestPage"),
                                  font=('Verdana', 10), activebackground=grey1, activeforeground=text1,
                                  disabledforeground=text1, bg=grey2, fg=text1, relief='flat', borderwidth=0, state='n')
        encodeTestButton.place(x=50, y=0, width=130, height=20)
        # button/tab for encoding practice
        intructionsButton = Button(banner, text='Instructions',
                                   command=lambda: controller.show_frame("instructionPage"),
                                   font=('Verdana', 10), activebackground=grey1, activeforeground=text1,
                                   disabledforeground=text1, bg=grey2, fg=text1, relief='flat', borderwidth=0,
                                   state='n')
        intructionsButton.place(x=180, y=0, width=90, height=20)

        # homepage content
        homeLabel = Label(self, text='Test Your Skills In METARs In The Encoding Practice Page.',
                          font=('Verdana', 12), bg=grey3, fg=text1)
        homeLabel.place(relx=0.01, rely=0.025, y=20, relwidth=0.98, relheight=0.08)

        exampleReport = Label(self, text=defaultDataFilled, font=('courier', 11), justify='left', anchor='w', padx=8,
                              bg=grey3, fg=text1)
        exampleReport.place(relx=0.01, rely=0.125, y=20, relwidth=0.98, relheight=0.7)

        exampleLabel = Label(self, text='[Standard Decoded Report from St. Catharines on June 1, 2019 at 10:25 UTC]',
                             font=('Verdana', 12), bg=grey3, fg=text1)
        exampleLabel.place(relx=0.01, rely=0.845, y=20, relwidth=0.98, relheight=0.08)


# define encoding practice frame
class encodeTestPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        # set background colour
        self.configure(background=grey1)

        # banner label
        banner = Label(self, bg=grey2)
        banner.place(x=-1, y=-1, relwidth=1, height=22)

        # button for homepage
        homeButton = Button(banner, text='Home', command=lambda: controller.show_frame("homePage"),
                            font=('Verdana', 10), activebackground=grey1, activeforeground=text1,
                            disabledforeground=text1, bg=grey2, fg=text1, relief='flat', borderwidth=0, state='n')
        homeButton.place(x=0, y=0, width=50, height=20)
        # button for encoding practice
        encodeTestButton = Button(banner, text='Encoding Practice',
                                  command=lambda: controller.show_frame("encodeTestPage"),
                                  font=('Verdana', 10), activebackground=grey1, activeforeground=text1,
                                  disabledforeground=text1, bg=grey1, fg=text1, relief='flat', borderwidth=0, state='d')
        encodeTestButton.place(x=50, y=0, width=130, height=20)
        # button/tab for encoding practice
        intructionsButton = Button(banner, text='Instructions',
                                   command=lambda: controller.show_frame("instructionPage"),
                                   font=('Verdana', 10), activebackground=grey1, activeforeground=text1,
                                   disabledforeground=text1, bg=grey2, fg=text1, relief='flat', borderwidth=0,
                                   state='n')
        intructionsButton.place(x=180, y=0, width=90, height=20)

        # instructions label
        instructions = Label(self, text='Recreate the "METAR Text" based on the given information. '
                                        'Enter the code in the provided field.',
                             font=('Verdana', 11), bg=grey3, fg=text1)
        instructions.place(relx=0.01, rely=0.075, relwidth=0.98, relheight=0.07)

        # label to display decoded METAR
        decoded = Label(self, text=defaultDataEmpty[12:], font=('courier', 11), justify='left', anchor='nw',
                        padx=8, pady=5, bg=grey3, fg=text1)
        decoded.place(relx=0.17, rely=0.24, relwidth=0.82, relheight=0.65)

        # label for hints
        hintLabel = Label(self, text='[Hint]', font=('Verdana', 12),
                          bg=grey3, fg=text1, relief='flat', borderwidth=0, state='n')
        hintLabel.place(relx=0.01, rely=0.91, relwidth=0.98, relheight=0.07)

        # set entry box string variable
        submission = StringVar()

        # entry field for code to be scored
        metarEntry = Entry(self, textvariable=submission, font=('Courier', 11), borderwidth=0,
                           selectborderwidth=0, insertbackground=text1, selectbackground=grey1, selectforeground=text1,
                           disabledbackground=grey2, bg=grey2, fg=text1, relief='solid', state='d')
        metarEntry.place(x=110, relx=0.17, rely=0.165, width=-110, relwidth=0.82, relheight=0.055)

        # label to label METAR Text entry box
        metarTextLabel = Label(self, text='METAR Text:', font=('Courier', 11), justify='left', anchor='w',
                               padx=8, bg=grey3, fg=text1)
        metarTextLabel.place(relx=0.17, rely=0.165, width=110, relheight=0.055)

        # button to get random METAR data
        startButton = Button(self, text='Start Test', font=('Verdana', 10),
                             command=lambda: startTest([scoreButton, clearButton, hintButton], [startButton], decoded),
                             activebackground=grey3, activeforeground=text1, disabledforeground=text2,
                             bg=grey2, fg=text1, relief='flat', borderwidth=0, state='n')
        startButton.place(relx=0.01, rely=0.165, relwidth=0.15, relheight=0.1)

        # button to score test
        scoreButton = Button(self, text='Score Test', font=('Verdana', 10),
                             command=lambda: scoreTest(submission.get(), metar, scoreLabel),
                             activebackground=grey3, activeforeground=text1, disabledforeground=text2,
                             bg=grey2, fg=text1, relief='flat', borderwidth=0, state='d')
        scoreButton.place(relx=0.01, rely=0.285, relwidth=0.15, relheight=0.1)

        # button to clear test
        clearButton = Button(self, text='Clear/Reset Test', font=('Verdana', 10),
                             command=lambda: clear(decoded, hintLabel, metarEntry),
                             activebackground=grey3, activeforeground=text1, disabledforeground=text2,
                             bg=grey2, fg=text1, relief='flat', borderwidth=0, state='d')
        clearButton.place(relx=0.01, rely=0.405, relwidth=0.15, relheight=0.1)

        # button for random hints
        hintButton = Button(self, text='Give Hint', font=('Verdana', 10), command=lambda: giveHint(hintLabel),
                            activebackground=grey3, activeforeground=text1, disabledforeground=text2,
                            bg=grey2, fg=text1, relief='flat', borderwidth=0, state='d')
        hintButton.place(relx=0.01, rely=0.525, relwidth=0.15, relheight=0.1)

        # label to display test score
        scoreLabel = Label(self, text='SCORE:', font=('Courier', 11), justify='left', anchor='w', padx=8,
                           bg=grey3, fg=text1)
        scoreLabel.place(relx=0.01, rely=0.645, relwidth=0.15, relheight=0.1)

        # function time (button-specific funcitons)
        # function for startButton
        def startTest(eButtons, dButtons, label):
            '''
            enable/disable desire buttons and provide report conditions
            :param eButtons: list of buttons to enable
            :param dButtons: list of buttons to disable
            :param label: label ot update with report conditions
            :return: nothing
            '''
            # enable/disable buttons
            for button in dButtons:
                button.config(state='d')
            for button in eButtons:
                button.config(state='n')
            # enable entry box
            metarEntry.config(state='n')
            # update report data
            # icao = random.choice(stationList)
            url = 'https://www.aviationweather.gov/adds/metars?station_ids=' + 'CYSN' + \
                  '&std_trans=translated&chk_metars=on&hoursStr=past+24+hours'
            global metar
            metar = reportPull(url)
            metarDict = getReport(metar)
            conditionList = formatText(metarDict)
            conditions = '{}'.format('\n'.join(conditionList))
            label.config(text=conditions)
            scoreLabel.config(text='SCORE:')
            metarEntry.delete(0, 'end')

        # function for clear button
        def clear(reportLabel, hintLabel, metarEntry):
            '''
            reset test by clearing user input and hints, as well as changing the report conditions to another city
            :param reportLabel: the label to update the report consitions in
            :param hintLabel: the hint label to reset to '[Hint]'
            :param metarEntry: the entry widget ot clear
            :return: nothing
            '''
            # reset entry box and hint label
            hintLabel.config(text='[Hint]')
            metarEntry.delete(0, 'end')
            # update report data
            icao = random.choice(stationList)
            url = 'https://www.aviationweather.gov/adds/metars?station_ids=' + icao + \
                  '&std_trans=translated&chk_metars=on&hoursStr=past+24+hours'
            # set global variable expected metar text
            global metar
            # run report generating funtions declared above
            metar = reportPull(url)
            metarDict = getReport(metar)
            conditionList = formatText(metarDict)
            conditions = '{}'.format('\n'.join(conditionList))
            # update report label
            reportLabel.config(text=conditions)

        # funtion to update hint label with new hint (sometimes repeats because of random,
        # haven't found a way to exclude current hint from choice)
        def giveHint(hintLabel):
            '''
            display a different hint in the hint label
            :param hintLabel: label where hints are displayed (says '[Hint]' at first
            :return: nothing
            '''
            hintLabel.config(text=random.choice(hintList))

        # function to calculate score of user text input based on expected text
        def scoreTest(entryCodes, expectedCodes, scoreLabel):
            '''
            compare user input METAR text with expected METAR text and provide appropriate score
            also disables all buttons except start button
            :param entryCodes: user input
            :param expectedCodes: expected METAR text
            :param scoreLabel: label to update with user score
            :return: nothing
            '''
            # declare score variable (start score count)
            score = 0
            # split user entry into list
            entryCodes = entryCodes.split()
            # test if each expected code is in user entry and increase scor if it is
            if 'RMK' in expectedCodes:
                expectedCodes = expectedCodes[:expectedCodes.index('RMK')]
            for code in expectedCodes:
                if code in entryCodes:
                    score += 1
            # add final point if user entry is in correct order (test if lists are equal)
            if expectedCodes == entryCodes:
                score += 1
            # update score label with actual score
            scoreLabel.config(text='SCORE: ' + str(score) + '/' + str(len(expectedCodes) + 1))
            # disable all buttons except start button
            scoreButton.config(state='d')
            hintButton.config(state='d')
            clearButton.config(state='d')
            startButton.config(state='n')
            metarEntry.config(state='d')


# define instructions/help frame
class instructionPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        # set background colour
        self.configure(background=grey1)

        # banner label
        banner = Label(self, bg=grey2)
        banner.place(x=-1, y=-1, relwidth=1, height=22)

        # button/tab for homepage
        homeButton = Button(banner, text='Home', command=lambda: controller.show_frame("homePage"),
                            font=('Verdana', 10), activebackground=grey2, activeforeground=text1,
                            disabledforeground=text1, bg=grey2, fg=text1, relief='flat', borderwidth=0, state='n')
        homeButton.place(x=0, y=0, width=50, height=20)
        # button/tab for encoding practice
        encodeTestButton = Button(banner, text='Encoding Practice',
                                  command=lambda: controller.show_frame("encodeTestPage"),
                                  font=('Verdana', 10), activebackground=grey1, activeforeground=text1,
                                  disabledforeground=text1, bg=grey2, fg=text1, relief='flat', borderwidth=0, state='n')
        encodeTestButton.place(x=50, y=0, width=130, height=20)
        # button/tab for encoding practice
        intructionsButton = Button(banner, text='Instructions',
                                   command=lambda: controller.show_frame("instructionPage"),
                                   font=('Verdana', 10), activebackground=grey1, activeforeground=text1,
                                   disabledforeground=text1, bg=grey1, fg=text1, relief='flat', borderwidth=0,
                                   state='d')
        intructionsButton.place(x=180, y=0, width=90, height=20)

        # text variables
        startText = 'Unlocks the other buttons and text entry, and displays decoded METAR text.'
        scoreText = 'Updates your score in the score label and locks all buttons except the start button.'
        clearText = 'Resets the test by clearing the text entry and displaying a random set of METAR data.'
        hintText = 'Provides a random hint. Some are helpful. Some are not. There is no penalty or limit.'
        scoreLabelText = 'Displays your score when the score button is pressed.'

        # instructions content
        instructions = Label(self, text='Descriptions of all buttons and display.',
                             font=('Verdana', 11), bg=grey3, fg=text1)
        instructions.place(relx=0.01, rely=0.075, relwidth=0.98, relheight=0.07)

        # button to get random METAR data
        startButton = Button(self, text='Start Test', font=('Verdana', 10),
                             activebackground=grey3, activeforeground=text1, disabledforeground=text2,
                             bg=grey2, fg=text1, relief='flat', borderwidth=0, state='n')
        startButton.place(relx=0.01, rely=0.165, relwidth=0.15, relheight=0.1)

        # start button description
        startDescript = Label(self, text=startText, font=('Verdana', 11), justify='l', anchor='w', bg=grey3, fg=text1)
        startDescript.place(relx=0.17, rely=0.165, relwidth=0.82, relheight=0.1)

        # button to score test
        scoreButton = Button(self, text='Score Test', font=('Verdana', 10),
                             activebackground=grey3, activeforeground=text1, disabledforeground=text2,
                             bg=grey2, fg=text1, relief='flat', borderwidth=0, state='n')
        scoreButton.place(relx=0.01, rely=0.285, relwidth=0.15, relheight=0.1)

        # score button description
        scoreDescript = Label(self, text=scoreText, font=('Verdana', 11), justify='l', anchor='w',
                              bg=grey3, fg=text1)
        scoreDescript.place(relx=0.17, rely=0.285, relwidth=0.82, relheight=0.1)

        # button to clear test
        clearButton = Button(self, text='Clear/Reset Test', font=('Verdana', 10),
                             activebackground=grey3, activeforeground=text1, disabledforeground=text2,
                             bg=grey2, fg=text1, relief='flat', borderwidth=0, state='n')
        clearButton.place(relx=0.01, rely=0.405, relwidth=0.15, relheight=0.1)

        # clear button description
        clearDescript = Label(self, text=clearText, font=('Verdana', 11), justify='l', anchor='w', bg=grey3, fg=text1)
        clearDescript.place(relx=0.17, rely=0.405, relwidth=0.82, relheight=0.1)

        # button for random hints
        hintButton = Button(self, text='Give Hint', font=('Verdana', 10),
                            activebackground=grey3, activeforeground=text1, disabledforeground=text2,
                            bg=grey2, fg=text1, relief='flat', borderwidth=0, state='n')
        hintButton.place(relx=0.01, rely=0.525, relwidth=0.15, relheight=0.1)

        # hint button description
        hintDescript = Label(self, text=hintText, font=('Verdana', 11), justify='l', anchor='w', bg=grey3, fg=text1)
        hintDescript.place(relx=0.17, rely=0.525, relwidth=0.82, relheight=0.1)

        # label to display test score
        scoreLabel = Label(self, text='SCORE:', font=('Courier', 11), justify='left', anchor='w', padx=8,
                           bg=grey3, fg=text1)
        scoreLabel.place(relx=0.01, rely=0.645, relwidth=0.15, relheight=0.1)

        # score label description
        hintDescript = Label(self, text=scoreLabelText, font=('Verdana', 11), justify='l', anchor='w', bg=grey3,
                             fg=text1)
        hintDescript.place(relx=0.17, rely=0.645, relwidth=0.82, relheight=0.1)


# run main application
weatherApp().mainloop()
