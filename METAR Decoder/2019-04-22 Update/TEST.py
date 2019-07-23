# import requests
# import requests
# import bs4
#
# # create lookup dictionary of canadian cities and their codes only only
# # lut = open('stations.txt', 'r').readlines()[3793:4673]
# url = 'https://www.aviationweather.gov/adds/metars?station_ids=CYSM&std_trans=translated&chk_metars=on'
#
# metarHTML = requests.get(url)
# metar = bs4.BeautifulSoup(metarHTML.text, 'lxml').select('strong')[1].getText().split()
#
# print(metar)

numDict = {}

numDict[6] = ['six']

numDict[6].append('seven')

print(numDict)
