# YKPS Tools
YKPS Tools are tools &amp; utilities associated with online logins of YKPS, under the [MIT License](/LICENSE). YKPS Tools require a distribution of _Python 3.x_ installed. It is also published on [PyPI](https://pypi.org/project/ykpstools/).

## Features
YKPS Tools has the following tools:
- Authorize to school Wi-Fi
- Request to Powerschool Learning
- Request to Powerschool
- Request to Outlook

## Installation

### Dependencies
YKPS Tools depends on (See [Insights / Dependency graph](https://github.com/icreiuheciijc/ykpstools/network/dependencies)):
- A distribution of **Python3.x** ([Python](https://www.python.org/downloads/), [Anaconda](https://www.anaconda.com/downloads/), etc.)
- [requests / **requests**](https://github.com/requests/requests)
- [waylan / **beautifulsoup**](https://github.com/waylan/beautifulsoup)
- [lxml / **lxml**](https://github.com/lxml/lxml)

### Installation on Python
YKPS Tools can be installed using `pip` in shell:
```sh
python3 -m pip install --upgrade ykpstools
```
Or, to get the newest version of YKPS Tools:
```sh
python3 -m pip install --upgrade git+https://github.com/icreiuheciijc/ykpstools.git
```
Or, with local installation:
```sh
git clone https://github.com/icreiuheciijc/ykpstools.git
cd ykpstools
python3 -m pip install --upgrade -e .
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
>>> page.soup().find('div', id='navbarowner').get_text(strip=True)
*Your name should appear here*
```
