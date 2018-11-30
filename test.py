"""For demonstration and testing purposes."""

import re

import ykpstools as yt


# Create a user. ('prompt' means to prompt for username and password in python
#                 shell if not available.)
user = yt.User(prompt=True)

# YKPS site Wi-Fi authorization
try:
    user.auth()
except yt.LoginConnectionError as error:
    print("Can't log in to school Wi-Fi.\n")

# Login to Powerschool (here I use html.parser because lxml has wierd issues)
powerschool = user.ps_login().soup(features='html.parser')

# Parse all the classes and grades
classes = [
    tr
    for tr in powerschool.find_all('tr', id=re.compile(r'ccid_[0-9]{6}'))
    if (tr.find('a', class_='bold') is not None
        and tr.find('a', class_='bold').string[0].isalpha())
]
names = [
    c.find('td', align='left').get_text()
    for c in classes
]
grades = [
    ord(c.find('a', class_='bold').string[0]) # ord built-in to find rank
    for c in classes
]

# Lowest score (ouch!)
lowest = grades.index(max(grades)) # max(ord) <= e.g. ord('E') > ord('A')
print('Your class with lowest score is: %s.\n' % names[lowest])
print('Score: %s' % classes[lowest].find('a', class_='bold').string)
