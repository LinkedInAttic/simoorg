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

"""
    The base class for all the handler plugins
"""


class BaseHandler(object):
    """ Base handler class"""

    def __init__(self, config_dir, target, logger_instance=None, verbose=True):
        """
            BaseHandler Constructor
        """
        pass

    def authenticate(self):
        """
            If the handler requires any authentication, those steps
            Should be included in this function
        """
        pass

    def execute_command(self):
        """
            This method should read the custom log output
            and return it to the caller, Also Expected to return a tuple
            of three values, namely. Execution Status, Output and Error message
        """
        pass

    def load_config(self):
        """
            Method to load any required configs
        """
        pass
