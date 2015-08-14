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

'''
    Mock logger modules
'''
class Logger:
    ''' Mock Logger class'''

    def __init__(self):
        """
            init function
        """
        self.log_queue = []

    def clear_logs(self):
        """
            Reset log queue to empty
        """
        self.log_queue = []

    def get_top_msg(self):
        """
            Return the top of the log queue
        """
        return (self.log_queue[-1])

    def log_contains(self, message):
        """
            Check if log queue contains a particular message
        """
        if message in self.log_queue:
            return True
        else:
            return False

    def logit(self, type, message, log_level="INFO"):
        """
            Add a message to the log queue
        """
        self.log_queue.append(message)
