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
    The Health check interface
"""


class HealthCheck(object):
    """
        All healthcheck plugins should inherit this class
    """
    def __init__(self, script, plugin_config=None):
        """
            Init function of the class
            Args:
                script - The health check script
            Return:
                None
            Raise:
                None
        """
        self.script = script

    # return true or false
    def check(self):
        """
            Checks the health, usually involves executing the script and
            returing the status
        """
        pass
