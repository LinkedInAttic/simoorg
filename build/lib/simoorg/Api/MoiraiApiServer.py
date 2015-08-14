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
    The Api server for moirai, here we have a global function create_app
    which returns a flask app
"""
import json
import socket
import yaml
import time
from flask import Flask
from flask import request
import simoorg.Api.ApiConstants as ApiConstants
import uuid
import os
import signal


class MoiraiApiServer(object):
    """
        The main api server class
    """
    def __init__(self, config_dir):
        self.app = Flask(__name__)
        self.service_map = {}
        self.event_map = {}
        signal.signal(signal.SIGTERM, self.term_handler)
        signal.signal(signal.SIGQUIT, self.term_handler)
        signal.signal(signal.SIGINT, self.term_handler)

        with open(config_dir) as config_fd:
            self.api_config = yaml.load(config_fd)
        self.api_fifo_name = str(uuid.uuid4()) + '.fifo'
        self.api_fifo_path = os.path.join(ApiConstants.API_PIPE_DIR,
                                          self.api_fifo_name)
        os.mkfifo(self.api_fifo_path)
        try:
            self.api_fifo_fd = os.open(self.api_fifo_path, os.O_NONBLOCK)
            self.api_fifo_file = os.fdopen(self.api_fifo_fd)
        except (IOError, OSError) as exc:
            print ("Unable to read the fifo file due to error {0} "
                   .format(exc))
            raise

        if not os.path.exists(self.api_config['moirai_input_fifo']):
            os.mkfifo(self.api_config['moirai_input_fifo'])

        try:
            self.moirai_fifo_fd = os.open(self.api_config['moirai_input_fifo'],
                                          os.O_WRONLY | os.O_NONBLOCK)
            self.moirai_fifo_file = os.fdopen(self.moirai_fifo_fd, 'w')
        except (IOError, OSError) as exc:
            print "Unable to connect to Moirai Server"
            self.moirai_fifo_fd = None
        self.setup_routes()
        self.command_id = 0

    def term_handler(self, recvd_signal, frame):
        """
            Handle appication shutdown
        """
        print "SHUTTING DOWN THE API SERVER"

        # close api fifo file obj
        try:
            self.api_fifo_file.close()
        except Exception, exc:
            print "Unable to close api fifo file obj {0}".format(exc)

        # close moirai fifo file obj
        try:
            self.moirai_fifo_file.close()
        except Exception, exc:
            print "Unable to close moirai fifo file obj {0}".format(exc)

        # close api fifo file descriptor
        try:
            os.close(self.api_fifo_fd)
        except Exception, exc:
            print "Unable to close api fifo file descriptor {0}".format(exc)

        # close moirai fifo file descriptor
        try:
            os.close(self.moirai_fifo_fd)
        except Exception, exc:
            print ("Unable to close moirai fifo file descriptor {0}"
                   .format(exc))
        exit(0)

    def app_run(self):
        """
            Start the flask app
        """
        try:
            self.app.run()
        except socket.error, msg:
            print "Error: {1}".format(msg[1])
            print "Unable to start api server"

    def fetch_app(self):
        """
            Return Flask app
        """
        return self.app

    def setup_routes(self):
        """
            Sets up the routes for various api calls
        """

        @self.app.route('/<command>')
        def list_services(command):
            """
                Set up a route that returns a list of services
            """
            args = {}
            op_msg = self.execute_command(command, args, request.method)
            return op_msg

        @self.app.route('/<service_name>/<command>')
        def get_plan(service_name, command):
            """
                Set up a route that returns the current plan
            """
            args = {'service_name': service_name}
            op_msg = self.execute_command(command, args, request.method)
            return op_msg

    def execute_command(self, command, args, method):
        """
            For any given command and arguments, the function connects to
            the moirai FIFO and reads the ouput via api FIFO
        """
        if self.moirai_fifo_fd is None:
            try:
                self.moirai_fifo_fd = os.open(
                    self.api_config['moirai_input_fifo'],
                    os.O_WRONLY | os.O_NONBLOCK)
                self.moirai_fifo_file = os.fdopen(self.moirai_fifo_fd, 'w')
            except:
                self.moirai_fifo_fd = None
                return "Unable to connect to Moirai Service"
        self.command_id = self.command_id + 1
        command_map = {ApiConstants.FIFO_ENDPOINT_KEY: self.api_fifo_path,
                       ApiConstants.COMMAND_ID_KEY: self.command_id,
                       ApiConstants.COMMAND_KEY: command,
                       ApiConstants.ARGS_KEY: args,
                       ApiConstants.METHOD_KEY: method}
        command_string = json.dumps(command_map) + '\n'
        try:
            self.moirai_fifo_file.write(command_string)
            self.moirai_fifo_file.flush()
        except IOError:
            op_msg = ("Unable to communicate with moirai")
            print "LOG: " + op_msg
            return op_msg
        except OSError:
            self.moirai_fifo_fd = None
            op_msg = ("Unable to communicate with moirai")
            print "LOG: " + op_msg
            return op_msg

        # Read from api fifo
        start_time = time.time()
        output_string = ''
        while output_string == '':
            try:
                output_string = self.api_fifo_file.read()
            except IOError:
                pass
            current_time = time.time()
            if current_time - start_time > ApiConstants.READ_TIMEOUT_SECS:
                op_msg = ("No message recieved from Moirai")
                print "LOG: " + op_msg
                return op_msg
        try:
            output_obj = json.loads(output_string)
        except ValueError:
            op_msg = "Recieved object is not a json object"
            print "LOG: " + op_msg
            return op_msg
        if output_obj[ApiConstants.COMMAND_ID_KEY] != self.command_id:
            op_msg = ("Recieved output with incorrect command id")
            print "LOG: " + op_msg
            return op_msg
        return output_obj[ApiConstants.COMMAND_OUTPUT_KEY]


def create_app(config_path):
    """
        Creates a flask app and returns it
    """
    api = MoiraiApiServer(config_path)
    application = api.fetch_app()
    return application
