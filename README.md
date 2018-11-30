# YKPS Tools
Tools &amp; Utilities associated with online logins of YKPS.

## Dependencies
YKPS Tools require a distribution of `Python 3.x` installed.
Install dependencies within Python for YKPS Tools:
```sh
python3 -m pip install -r requirements.txt
```

## Quick Start
In Python shell:
```python
>>> from ykpstools import User, load_soup
>>>
>>> # Login to Powerschool Learning
>>> resp = User(prompt=True).psl_login()
>>> # Print html
>>> print(load_soup(resp).find('div', id='navbarowner'))
<div id="navbarowner">
    *Your name should appear here*
  </div>
```
