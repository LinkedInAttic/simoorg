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
    A mock module for api test, this basically duplicates some
    actions of the Moirai module
"""
import json
import os
import ApiConstants


class MockMoirai(object):
    """
        Mock moirai class
    """
    def __init__(self, input_queue, event_queue, api_config):
        self.atropos_data_queue = input_queue
        self.atropos_event_queue = event_queue
        self.api_config = api_config
        self.event_map = {}
        self.service_map = {}

    def start_moirai(self):
        print "Starting fifo"
        self.api_fifo_read()

    def api_fifo_read(self):
        """
            A thread which keeps reading an input fifo,
            specified in the api configs, each line it reads is expected to
            be a json string encoding a dict of the form
            {
                FIFO_ENDPOINT_KEY: fifo_endpoint,
                COMMAND_ID_KEY: command_id,
                COMMAND_KEY: command,
                ARGS_KEY: args,
                METHOD_KEY: method
            }
            fifo_endpoint - Input FIFO to api server
            command_id - the sequence id of the command
            command - the api command called (command along with method should
                                              map to a unique function in
                                              moirai class)
            args - arugments for the command
            method - api method name (GET/PUT/POST)

            Args:
                None
            Return:
                None
            Raise:
                IOError/OSError - Unable to open input FIFO
        """
        try:
            if not os.path.exists(self.api_config['moirai_input_fifo']):
                os.mkfifo(self.api_config['moirai_input_fifo'])
            print("\nAPI FIFO open for read\n")
            self.fifo_fd = open(self.api_config['moirai_input_fifo'])
        except (IOError, OSError):
            print ("[Error] Unable to read api input FIFO")
            raise
        while True:
            skip_iteration_flag = False
            request_json = self.fifo_fd.readline()
            if request_json:
                try:
                    # if request_json:
                    request_map = json.loads(request_json)
                except ValueError:
                    print ("[Error] Recieved non json object, skipping")
                    print(request_json)
                    continue
                required_keys = [ApiConstants.FIFO_ENDPOINT_KEY,
                                 ApiConstants.COMMAND_ID_KEY,
                                 ApiConstants.COMMAND_KEY,
                                 ApiConstants.ARGS_KEY,
                                 ApiConstants.METHOD_KEY]
                for arr_key in required_keys:
                    if arr_key not in request_map.keys():
                        print ("[Error] Malformed message missing {}"
                               .format(arr_key))
                        skip_iteration_flag = True

                if skip_iteration_flag:
                    continue

                fifo_endpoint = request_map[ApiConstants.FIFO_ENDPOINT_KEY]
                command_id = request_map[ApiConstants.COMMAND_ID_KEY]
                command = request_map[ApiConstants.COMMAND_KEY]
                args = request_map[ApiConstants.ARGS_KEY]
                method = request_map[ApiConstants.METHOD_KEY]
                if command not in ApiConstants.API_COMMANDS:
                    output_msg = {ApiConstants.COMMAND_ID_KEY: command_id,
                                  ApiConstants.COMMAND_OUTPUT_KEY:
                                  "No such command found"}
                else:
                    if method == "GET":
                        moirai_function = (ApiConstants.
                                           MOIRAI_GET_COMMAND_PREFIX +
                                           command)
                    else:
                        moirai_function = (ApiConstants.
                                           MOIRAI_OTHER_COMMAND_PREFIX +
                                           command)
                try:
                    command_handler = getattr(self, moirai_function)
                    command_output = command_handler(args)
                    output_msg = {ApiConstants.COMMAND_ID_KEY: command_id,
                                  ApiConstants.COMMAND_OUTPUT_KEY:
                                  command_output}
                except:
                    output_msg = {ApiConstants.COMMAND_ID_KEY: command_id,
                                  ApiConstants.COMMAND_OUTPUT_KEY:
                                  "Unexpected error in moirai"}
                with open(fifo_endpoint, 'w') as output_fd:
                    output_fd.write(json.dumps(output_msg))

    def update_service_map(self):
        """
            Creates/Update the service map dictionary with items for
            each of the service entry in the input queue
            Args:
                None
            Return:
                None
            Raise:
                None
        """
        while not self.atropos_data_queue.empty():
            service, servers, plan = self.atropos_data_queue.get()
            if service in self.service_map.keys():
                print ("Duplicate service entry for " + service +
                       ". Skipping the new entry!!!")
            else:
                self.service_map[service] = (servers, plan)

    def update_event_map(self):
        """
            Creates/Update the event map dictionary with items for
            each of the service entry in the event queue
            Args:
                None
            Return:
                None
            Raise:
                None
        """
        while not self.atropos_event_queue.empty():
            (service, failure_name, trigger_time, node_name,
             trigger_status) = self.atropos_event_queue.get()
            if service in self.event_map.keys():
                self.event_map[service].append([failure_name, trigger_time,
                                                node_name, trigger_status])
            else:
                self.event_map[service] = [[failure_name, trigger_time,
                                            node_name, trigger_status]]

    def api_get_list(self, args):
        """
            Get the list of services being tested by simoorg
            (defined by the fate books)
            Args:
                args - expects an empty dictionary
            Returns:
                a list of services encoded as a json string
            Raise:
                None
        """
        self.update_service_map()
        return json.dumps(self.service_map.keys())

    def api_get_plan(self, args):
        """
            Get the plan used by atropos for a specific service
            (Generated by the scheduler)
            Args:
                args - expects a dictionary containing a key for service_name
            Returns:
                plan encoded as a json string
            Raise:
                None
        """
        self.update_service_map()
        service_name = args['service_name']
        servers, plan = self.service_map[service_name]
        return json.dumps(plan)

    def api_get_servers(self, args):
        """
            Get the servers present in the service
            (Generated by the topology)
            Args:
                args - expects a dictionary containing a key for service_name
            Returns:
                server list encoded as a json string
            Raise:
                None

        """
        self.update_service_map()
        service_name = args['service_name']
        servers, plan = self.service_map[service_name]
        return json.dumps(servers)

    def api_get_events(self, args):
        """
            Get the status of all the events already executed by atropos
            An event is a tuple containing the elements
            (service name, event name, trigger_time,
             target of the event, Event status)
            Here event name is the failure name if it was a failure event
            for revert events it is failure name + '-revert'

            Args:
                args - expects a dictionary containing a key for service_name
            Returns:
                event list encoded as a json string
            Raise:
                None
        """
        self.update_event_map()
        service_name = args['service_name']
        if service_name not in self.event_map.keys():
            return json.dumps([()])
        return json.dumps(self.event_map[service_name])
