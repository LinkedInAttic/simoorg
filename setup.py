#!/usr/bin/env python2.6
#
# Copyright 2015 LinkedIn Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
  
from setuptools import find_packages, setup
from os import path, listdir
 
def list_files(directory):
  return [path.join(directory, file)
      for file in listdir(directory)
          if not path.isdir(path.join(directory, file))]  
  
setup(
  name = 'simoorg',
  version = '0.0.1',
  description = __doc__,
  long_description = open('README.rst').read(),
  author = 'Tofig Suleymanov',
  author_email = 'TBD',
  url = 'http://github.com/linkedin/simoorg',
  download_url = 'https://github.com/linkedin/simoorg/tarball/0.2.2',
  license = 'Apache',
  package_dir={'': 'src'},
  packages=find_packages('src'),
  include_package_data=True,
  test_suite = 'test',
  classifiers = [
      'Intended Audience :: Developers',
      'License :: OSI Approved :: Apache Software License',
      'Programming Language :: Python',
      'Programming Language :: Python :: 2.6',
      'Programming Language :: Python :: 2.7',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.3',
  ],
  install_requires=[
        'argparse',
        'flake8',
        'Flask>=0.10.1',
        'PyYAML>=3.11',
        'gunicorn>=19.3.0',
        'kazoo'
  ],
  entry_points = {
      'console_scripts': [
          'simoorg = simoorg.__main__:main'
      ]
  }
)
