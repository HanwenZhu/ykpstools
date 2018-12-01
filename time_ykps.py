"""Using timeit to time ykpstools."""

from timeit import timeit


print('Importing ykpstools: ')
print(timeit('import ykpstools as yt', number=1), 'seconds')
print('Importing sklearn: ')
print(timeit('import sklearn', number=1), 'seconds')
