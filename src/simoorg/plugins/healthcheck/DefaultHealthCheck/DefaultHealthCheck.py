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
    The default health check module
"""
import os
from simoorg.plugins.healthcheck.HealthCheck import HealthCheck


class DefaultHealthCheck(HealthCheck):
    """
        Default Health check class
    """
    def __init__(self, script, plugin_config):
        """
            Init function
            Args:
                script - Health check script
            Return:
                None
            Raise:
                None
        """
        HealthCheck.__init__(self, script, plugin_config)

    def check(self):
        """
            Check the health of the service (Assuming the script captures
                                             that logic, just return the
                                             execution srarus)
            Args:
                None
            Return:
                True if command was executed successfully else False
            Raise:
                None
        """
        status = os.system(str(self.script))
        if status == 0:
            return True
        else:
            return False
