'''
Maksim Stadler
April 2019

This program will scrape METARs from www.aviationweather.gov.
The specific page of a specific location's data will be determined by entering a city name.
The program will convert the city name to its 4-letter code with a look up table.
The raw METAR text is parsed and will be formatted similarly to how the website does so itself.
'''

# import requests

# set user mode to True/False

# check if user mode is on
#   ask user for city name
#   convert city name to code
#   generate URL variable with that city's data

# check if user mode is off
#   set URL variable
#   set city name variable

# pull html code from webpage

# isolate report text only

# parse through METAR text and extract variables according to naming order and conventions

# create dictionary of reformatted data with proper value labels (Temperature, Visibility, etc.)
# use extracted variables as data in dictionary

# print labels and values in dictionary in formatted lines similarly to website

# Example

# Weather Report
# Conditions At:            St. Catherines
# Temperture:               45
# Dewpoint:	                -5.0°C (23°F) [RH = 60%]
# Pressure (altimeter):	    30.27 inches Hg (1025.1 mb)
# Sea-level pressure:       1025.4 mb
# Winds:                    from the E (90 degrees) at 8 MPH (7 knots; 3.6 m/s)
# Visibility:               15 miles (24 km)
# Ceiling:                  5500 feet AGL
# Clouds:                   overcast cloud deck at 5500 feet AGL
# Weather:                  -RA  (light rain)

# Note:
# - Both columns are left justified
# - Values must align after longest label (dot leaders?)
# - Values listed in same order as METAR text
