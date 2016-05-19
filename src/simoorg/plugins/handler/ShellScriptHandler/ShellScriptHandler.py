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
    The shell script handler plugin for simoorg and uses paramiko to execute
    command on remote servers through ssh.
    The user credntial required for the ssh (username/passwd/ssh_key etc..)
    should be specifed in the config file 'ShellScriptHandler.yaml'
"""
import os
import paramiko
from simoorg.plugins.handler.BaseHandler import BaseHandler
import yaml

PLUGIN_CONFIG_PATH = 'plugins/handler/ShellScriptHandler/'


class ShellScriptHandler(BaseHandler):
    """ Shell Script Handler piggybacking on paramiko SSH"""

    def __init__(self, config_dir, hostname, logger_instance=None,
                 verbose=False, debug=False):
        """
            Constructor method responsible for reading the config and
            setting up the ssh client.
            Args:
                config_dir - Path to config files
                hostname - hostname to run the handler against
                logger_instance - An instance of logger class
                verbose - verbosity flag
                debug - debug flag
            Raise:
                None
            Return:
                None
        """
        BaseHandler.__init__(self, config_dir, hostname,
                             logger_instance, verbose)
        self.debug = debug
        self.verbose = verbose
        self.ssh_client = None
        self.shell_scripthandler_config_path = (config_dir + "/" +
                                                PLUGIN_CONFIG_PATH +
                                                self.__class__.__name__ +
                                                ".yaml")

        if self.debug:
            paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
        self.config = None
        self.load_config()

        # read in yaml configuration
        for key, val in self.config.iteritems():
            setattr(self, key, val)
        del self.config

        self.hostname = hostname

    def authenticate(self):
        """
            Authenticate ssh connection
            Args:
                None
            Return:
                None
            Raise:
                None
        """
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.load_host_keys(os.path.expanduser(self.host_key_path))
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect()

    def connect(self):
        """
            Connect to the given hostname, using the provided credentials
            Args:
                None
            Return:
                None
            Raise:
                paramiko.BadHostKeyException: if host key is not readable
                paramiko.AuthenticationException: if authentication failed

        """
        try:
            self.ssh_client.connect(self.hostname, port=self.port,
                                    username=self.username,
                                    password=self.password, pkey=self.pkey,
                                    key_filename=self.key_filename,
                                    timeout=self.connect_timeout,
                                    allow_agent=self.allow_agent,
                                    look_for_keys=self.look_for_keys)
        except paramiko.BadHostKeyException:
            print "[FATAL]: Server's host key could not be retrieved"
            raise
        except paramiko.AuthenticationException:
            print "[FATAL]: Authentication failed"
            raise
        except Exception, exc:
            print ("Unknown exception while connecting to server: ",
                   self.hostname, exc)
            raise

    def execute_command(self, script, arguments):
        """
            Execute the command specified in the arguments
            Args:
                script - The script to be executed
                arguments - arguments to the script
            Return:
                status - command_output and error_messages
            Raise:
                paramiko.SSHException - if remote command exception failed
        """
        command = script + ' ' + self.comma_separate_args(arguments)
        try:
            (stdin, stdout, stderr) = self.ssh_client.exec_command(
                command, bufsize=-1, timeout=self.command_timeout)
        except paramiko.SSHException, exc:
            print "Server failed to execute command", exc
            raise
        except Exception, exc:
            print ("Unkown exception while trying to execute ssh command: ",
                   command, exc)
            raise
        else:
            while not stdout.channel.exit_status_ready():
                pass
            status = stdout.channel.recv_exit_status()
            command_output = stdout.readlines()
            error_messages = stderr.readlines()
            if status == 0:
                self.logger_instance.logit("INFO", "Command finished"
                                                   " successfully",
                                           log_level="INFO")
                self.logger_instance.logit("INFO", "Closing ssh connection",
                                           log_level="DEBUG")
            elif status == 127:
                self.logger_instance.logit("WARN",
                                           "Command failed. Invalid arguments"
                                           "specified", log_level="WARNING")
                self.logger_instance.logit("INFO",
                                           "Closing ssh connection",
                                           log_level="DEBUG")
            else:
                self.logger_instance.logit("WARN",
                                           "Comand failed. Return value: {0}"
                                           .format(stdout.channel.
                                                   recv_exit_status()),
                                           log_level="WARNING")
                self.logger_instance.logit("INFO",
                                           "Closing ssh connection",
                                           log_level="DEBUG")
            return (status, command_output, error_messages)

    def load_config(self):
        """
            Read the shellscript handler configs
            Args:
                None
            Return:
                None
            Raise:
                OSError/IOError - if we are unable to read the config

        """
        try:
            with open(self.shell_scripthandler_config_path, "r") as \
                    shell_scrip_handler_config:
                self.config = yaml.load(shell_scrip_handler_config)
        except (OSError, IOError) as exc:
            print ("[FATAL]: Failed loading ShellScriptHandler"
                   "config...bailing out", exc)
            raise

    def comma_separate_args(self, arguments):
        """
            Takes a list of strings and returns a single string
            containing each list elements seperated by a whitespace
            Args:
                arguments - A list of string
            Return:
                The resultant string
            Raise:
                None
        """
        # XXX rename the function to more intuitive name
        if arguments:
            return ' '.join(arguments)
        else:
            return ''
