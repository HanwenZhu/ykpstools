import setuptools


with open('README.md', 'r') as README:
    long_description = README.read()


setuptools.setup(
    name='ykpstools',
    version='1.0.1.1',
    description='Tools & utilities associated with online logins of YKPS.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/icreiuheciijc/ykpstools',
    author='Thomas Zhu',
    license='MIT',
    packages=['ykpstools'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'requests',
        'beautifulsoup4',
        'lxml',
    ],
    python_requires='>=3',
)
