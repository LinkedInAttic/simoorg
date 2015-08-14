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
    The logger class responsible for writing the loglines to the given
    file. We can also set the log level to one of the following levels
    WARNING, INFO, VERBOSE and DEBUG
"""
import sys
import datetime


class Logger(object):
    ''' Logger class'''

    def __init__(self, log_config, verbose=False, debug=False):
        """
            Init function for Logger class
            Args:
                log_config - Log config dictionary
                verbose - Verbosity flag
                debug - Debug flag
            Return:
                None
            Raise:
                None
        """
        self.verbose = verbose
        self.debug = debug
        self.log_config = log_config
        self.logger_file_handle = None
        self.full_log_config_path = None
        self.log_levels = ["WARNING", "INFO", "VERBOSE", "DEBUG"]

    def get_current_log_level(self):
        """
            Fetches the current log level, the level set to INFO
            by default if an unknown level given in the config
            Args:
                None
            Return:
                Log level
            Raise:
                None
        """
        try:
            if (self.log_config['log_level'] and
                    self.log_config['log_level'] in self.log_levels):
                return self.log_levels.index(self.log_config['log_level'])
            else:
                print ("[WARNING]: Unknown log_level defined in the log_config"
                       "configuration: {0}. Overriding it to the default"
                       "level: INFO".format(self.log_config['log_level']))
                self.log_config['log_level'] = "INFO"
                return self.log_levels.index(self.log_config['log_level'])
        except KeyError:
            print ("[FATAL]: Logger config is incomplete. Please define "
                   "log_config-> log_level option. Set it to false if you "
                   "want to, disable verbose logging")
            sys.exit(1)

    def is_verbose_logging_enabled(self):
        """
            Check if verbose flag is set
            Args:
                None
            Return:
                True if verbose flag is set else False
            Raise:
                None
        """
        try:
            if self.log_config['verbose']:
                return True
            else:
                return False
        except KeyError:
            print ("[FATAL]: Logger config is incomplete. Please define "
                   "log_config-> verbose option. Set it to false if you want"
                   " to disable verbose logging")
            sys.exit(1)

    def is_console_logging_enabled(self):
        """
            Check if console logging is enabled
            Args:
                None
            Return:
                True if console logging is enabled else False
            Raise:
                None
        """
        try:
            if self.log_config['console']:
                return True
            else:
                return False
        except KeyError:
            print ("[FATAL]: Logger config is incomplete. Please define "
                   "log_config-> console option. Set it to false if you "
                   "want to disable logging into console")
            sys.exit(1)

    def is_file_logging_enabled(self):
        """
            Check if file logging is enabled
            Args:
                None
            Return:
                True if console logging is enabled else False
            Raise:
                None
        """

        try:
            if self.log_config['path']:
                return True
            else:
                return False
        except KeyError:
            print ("[FATAL]: Logger config is incomplete. Please define "
                   "log_config-> path option. Set it to false if you want to "
                   "disable it.")
            sys.exit(1)

    def get_logger_file_path(self):
        """
            Fetch the logger file path
            Args:
                None
            Return:
                Path to the log file
            Raise:
                None
        """
        try:
            if self.log_config['path']:
                return self.log_config['path']
            else:
                return None
        except KeyError:
            print "[FATAL]: Logger configuration is not defined"
            sys.exit(1)

    def get_logger_file_handle(self):
        """
            Returns a file object to the log file
            Args:
                None
            Return:
                file object to the log file
            Raise:
                None
        """
        if not self.logger_file_handle:
            try:
                file_desc = open(self.get_logger_file_path(), "a", 0)
                self.logger_file_handle = file_desc
                return self.logger_file_handle
            except Exception as exc:
                print ("[FATAL]: Could not open file name for logging: {0}.{1}"
                       .format(self.get_logger_file_path(), exc))
                sys.exit(1)
        else:
            return self.logger_file_handle

    def logit(self, log_type, message, log_level="INFO"):
        """
            Add a message to the log if the message log level is acceptable
            Args:
                log_type - the log type
                message - The log message
                log_level - the log level
            Return:
                None
            Raise:
                None
        """
        if self.get_current_log_level() >= self.log_levels.index(log_level):
            if self.is_file_logging_enabled():
                self.get_logger_file_handle()\
                    .write("[{0}] [{1}]: {2}\n".format(datetime.datetime.now(),
                                                       log_type, message))
            if self.is_console_logging_enabled():
                sys.stdout.write("[{0}] [{1}]: {2}\n"
                                 .format(datetime.datetime.now(),
                                         log_type, message))
