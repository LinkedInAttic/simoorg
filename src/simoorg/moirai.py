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
    Our main manager Module, Here moirai spins up multiple worker process
    called atropos. Each atropos is associated with a specific service and
    is responsible for inducing and reverting failure in the service. Moirai
    is also responsible for providing the api server with any required
    information
"""

import yaml
import simoorg.atropos as atropos
import os
import multiprocessing
import threading
import json
import simoorg.Api.ApiConstants as ApiConstants


class Moirai(object):
    """main Moirai class"""

    def __init__(self, config_dir, verbose=True, debug=False):
        """
            init function for the moirai class
            Args:
                config_dir - Path to the configs
                verbose - Verbosity flag
                debug - debug flag
            Raise:
                IOError - if the api config file is missing
            Return:
                None
        """
        self.verbose = verbose
        self.fate_books_dir = config_dir + "/fate_books/"
        self.api_config_file = os.path.join(config_dir,
                                            ApiConstants.API_CONFIG)
        self.config_dir = config_dir
        self.debug = debug
        self.api_proc = None
        self.atropos_fate_book_streams = []
        self.atropos_fate_book_configs = {}
        self.atropos_army = {}
        self.verbose = True
        self.debug = False
        self.fifo_fd = None
        self.fifo_read_lock = threading.Lock()
        self.service_map = {}
        self.event_map = {}
        self.api_read_procs = []
        try:
            with open(self.api_config_file) as api_config_fd:
                self.api_config = yaml.load(api_config_fd)
        except IOError:
            print "Missing API config file, exiting"
            raise
        # Data_queue will enqueue tuples containing the items
        # service-name, plan and server list
        self.atropos_data_queue = multiprocessing.Queue()

        # Event queue will enqueue tuples containing the items
        # service-name, failure_name, trigger_time, node_name (if applicable)
        # and trigger_status
        # node_name = NOT_DECIDED if execution skipped before selecting a node
        # node_name = FAILED_TO_FETCH if execution skipped because a node
        # wasn't found
        # For each failure, we have two events defined
        # failure induction and failure revert
        self.atropos_event_queue = multiprocessing.Queue()

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

    def read_configs(self):
        """
            Create file object to each fate book in the fate book directory
            under the config path
            Args:
                None
            Return:
                None
            Raise:
                IOError/OSError - Unable to open a fate book
        """
        try:
            for fate_file in os.listdir(self.fate_books_dir):
                if os.path.isfile(self.fate_books_dir + "/" + fate_file):
                    if self.verbose:
                        print "[INFO]: Found moirai fate book ", fate_file
                    self.atropos_fate_book_streams.append(open(
                        self.fate_books_dir + "/" + fate_file, "r"))
        except Exception, exc:
            print ("[FATAL]: Failed initializing Moirai fate books..."
                   "bailing out", exc)
            raise

    def load_config(self):
        """
            Read from each file object in self.atropos_fate_book_streams
            Args:
                None
            Return:
                None
            Raise:
                IOError/OSError - Unable to read a fatebook
                ValueError - Duplicate fate book with the same service name
        """
        try:
            for stream in self.atropos_fate_book_streams:
                yaml_def = yaml.load(stream)
                if yaml_def["service"] in self.atropos_fate_book_configs:
                    print ("[FATAL]: Duplicate fate book for",
                           yaml_def["service"])
                    raise ValueError("Duplicate fate book for {}".format(
                        yaml_def["service"]))
                else:
                    self.atropos_fate_book_configs[yaml_def["service"]] = \
                        yaml_def
        except Exception, exc:
            print ("[FATAL]: Failed loading Moirai fate books...bailing out",
                   exc)
            raise

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
            print"\nAPI FIFO open for read\n"
            self.fifo_fd = open(self.api_config['moirai_input_fifo'])
        except (IOError, OSError):
            print "[Error] Unable to read api input FIFO"
            return
        while True:
            skip_iteration_flag = False
            self.fifo_read_lock.acquire()
            try:
                response_json = self.fifo_fd.readline()
            finally:
                self.fifo_read_lock.release()
            if response_json:
                try:
                    # if response_json:
                    response_map = json.loads(response_json)
                except ValueError:
                    print "[Error] Recieved non json object, skipping"
                    print response_json
                    continue

                required_keys = [ApiConstants.FIFO_ENDPOINT_KEY,
                                 ApiConstants.COMMAND_ID_KEY,
                                 ApiConstants.COMMAND_KEY,
                                 ApiConstants.ARGS_KEY,
                                 ApiConstants.METHOD_KEY]
                for arr_key in required_keys:
                    if arr_key not in response_map.keys():
                        print ("[Error] Malformed message missing {}"
                               .format(arr_key))
                        skip_iteration_flag = True

                if skip_iteration_flag:
                    continue

                fifo_endpoint = response_map[ApiConstants.FIFO_ENDPOINT_KEY]
                command_id = response_map[ApiConstants.COMMAND_ID_KEY]
                command = response_map[ApiConstants.COMMAND_KEY]
                args = response_map[ApiConstants.ARGS_KEY]
                method = response_map[ApiConstants.METHOD_KEY]
                if command not in ApiConstants.API_COMMANDS:
                    output_msg = {ApiConstants.COMMAND_ID_KEY: command_id,
                                  ApiConstants.COMMAND_OUTPUT_KEY:
                                  "No such command found"}
                else:
                    if method == "GET":
                        moirai_function = (ApiConstants.
                                           MOIRAI_GET_COMMAND_PREFIX + command)
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

    def spawn_atropos(self):
        """
            Spawn one atropos process for each fate book and also starts
            the FIFO read thread
            Args:
                None
            Return:
                None
            Raise:
                Any exception raise by read_configs or load_config
                IOError/OSError - Unable to read api configs
        """
        try:
            self.read_configs()
            self.load_config()
        except Exception, exc:
            print ("[FATAl]: Calling finish() due to errors ", exc)
            self.finish()
            raise

        atropos_class = getattr(atropos, 'Atropos')

        # Deploy atropos army
        for service_name, config in self.atropos_fate_book_configs.iteritems():
            if self.verbose:
                print "[INFO]: Deploying atropos for:", service_name
            proc = multiprocessing.Process(target=atropos_class.spawn,
                                           args=(config, self.config_dir,
                                                 self.atropos_data_queue,
                                                 self.atropos_event_queue,),
                                           kwargs={'verbose': self.verbose,
                                                   'debug': self.debug})
            proc.start()
            self.atropos_army[service_name] = proc
        for t_index in range(ApiConstants.THREADPOOL_SIZE):
            self.api_read_procs.append(
                threading.Thread(target=self.api_fifo_read,
                                 args=(),
                                 kwargs={}))
            self.api_read_procs[t_index].daemon = True
            self.api_read_procs[t_index].start()

    def finish(self):
        """
            Close all file object and wait for the atropos process to complete
            Args:
                None
            Return:
                None
            Raise:
                IOError - Unable to close fifo file object
        """
        for stream in self.atropos_fate_book_streams:
            stream.close()
        for service, proc in self.atropos_army.iteritems():
            proc.join()
        self.atropos_fate_book_configs = {}
        try:
            if self.fifo_fd:
                self.fifo_fd.close()
        except IOError:
            print "Skipping closing the fifo "
        print "[INFO]: Moirai shut down"
