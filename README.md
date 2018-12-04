# YKPS Tools
Tools &amp; utilities associated with online logins of YKPS.
YKPS Tools require a distribution of `Python 3.x` installed.

## Installation
YKPS Tools can be installed by using `pip` in shell:
```sh
python3 -m pip install ykpstools
```
Or, to get the newest version of YKPS Tools:
```sh
python3 -m pip install git+https://github.com/icreiuheciijc/ykpstools.git
```

## Demonstration
### Test
To test what the repository can do:
```sh
python3 -m ykpstools
```
### Example
In Python shell:
```python
>>> import ykpstools as yt
>>>
>>> # Login to Powerschool Learning
>>> page = yt.User(prompt=True).psl_login()
>>> # Print html
>>> print(page.soup().find('div', id='navbarowner'))
<div id="navbarowner">
    *Your name should appear here*
  </div>
```
