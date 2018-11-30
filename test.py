"""For demonstration and testing purposes."""

import re

from ykpstools import User, load_soup


# Create a user. ('prompt' means to prompt for username and password in python
#                 shell if not available.)
user = User(prompt=True)

# YKPS site Wi-Fi authorization
user.wifi_auth()

# Login to Powerschool ()
powerschool = load_soup(user.ps_login(), features='html.parser')
print(powerschool)
# Parse all the classes and grades
classes = [
    tr
    for tr in powerschool.find_all('tr', id=re.compile(r'ccid_[0-9]{6}'))
    if tr.find('a', class_='bold').string[0].isalpha()
]
names = [
    c.find('td', align='left').get_text()
    for c in classes
]
grades = [
    ord(c.find('a', class_='bold').string[0])
    for c in classes
]
# Lowest score (ouch!)
lowest = grades.index(max(grades))
print('Your class with lowest score is: %s' % names[lowest])
