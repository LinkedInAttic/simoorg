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
    A test handler plugin mainly for test purposes
    Supports the following features
    failure - Writes the pid of the atropos process to a given test file
    Revert - Removes the test file
    Failure Skip - Allows to 'skip' failure events (failure induction
                                                     returns False)
    Revert Skip - llows to 'skip' revert events (failure induction
                                                     returns False)
    the config file for the class will be called test_handler.yaml and the
    class looks for it at the given config directory path
"""
import os
from simoorg.plugins.handler.BaseHandler import BaseHandler
import yaml

SKIP_FAILURE_KEY = 'skip_failure'
SKIP_REVERT_KEY = 'skip_revert'


class TestHandler(BaseHandler):
    """ Test Handler class"""

    def __init__(self, config_dir, target, logger_instance=None, verbose=True):
        """
            The init class for test handler
            config_dir - The path to config
            target - The target for the handler (currently unused)
            logger_instance - An instance of logger class
            verbose - verbosity flag
        """
        BaseHandler.__init__(self, config_dir, target,
                             logger_instance, verbose)
        self.test_config = None
        if os.path.isfile(config_dir + '/test_handler.yaml'):
            with open(config_dir + '/test_handler.yaml') as config_fd:
                self.test_config = yaml.load(config_fd)
        return

    def execute_command(self, coordinate, argument):
        """
            Test handler supports two types of actions
                failure - writing to a test file
                revert - removing the file
            these actions are differentiated by the first
            element of argument list
            Args:
                coordinate - The test file
                argument - Argument list (expected to contain only a
                                          single item i.e the action type)
        """
        if argument[0] == 'failure':
            if self.test_config is not None:
                if SKIP_FAILURE_KEY in self.test_config.keys() and \
                        self.test_config[SKIP_FAILURE_KEY]:
                    return (1, "", "")
            with open(coordinate.strip(), 'w') as cord_fd:
                cord_fd.write(str(os.getpid()))
            output = ("Test file " + coordinate +
                      " updated with the pid of the atropos process")
            error = ""
            return 0, output, error
        elif argument[0] == 'revert':
            try:
                if self.test_config is not None:
                    if SKIP_REVERT_KEY in self.test_config.keys() and \
                            self.test_config[SKIP_REVERT_KEY]:
                        return (1, "", "")
                os.remove(coordinate)
                output = "Test file " + coordinate + " successfully removed"
                error = ""
            except OSError:
                error = "Incorrect test file provided: " + coordinate
                output = ""
                return 1, output, error
            return 0, output, error
        else:
            error = "Unknown argument"
            output = ""
            return 1, output, error
