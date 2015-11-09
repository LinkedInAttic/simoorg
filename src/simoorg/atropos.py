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
    The main worker module, each atropos instance is tied to a specific
    fate book. Atropos receives a plan from the scheduler, induces and
    reverts failures as specified in it.
"""
import sys
import time
import datetime
import os
import signal
from simoorg.Logger import Logger
from simoorg.Journal import Journal


# PATH to handler plugins
HANDLER_PLUGIN_PATH = "simoorg.plugins.handler"
SCHEDULER_PLUGIN_PATH = "simoorg.plugins.scheduler"
TOPOLOGY_PLUGIN_PATH = "simoorg.plugins.topology"
HEALTHCHECK_PLUGIN_PATH = "simoorg.plugins.healthcheck"
DEFAULT_TOPOPLOGY_PLUGIN = "StaticTopology"

# config key name
HEALTHCHECK_PLUGINCONFIG_KEY = "plugin_configs"

# other constants
SUDO_USER_KEY = 'sudo_user'


def sleep_correctly(period):
    """
        Sleep function can be interrupted by external signals,
        during failure run we cant let signals effect our sleep time
        This small wrapper ensure that even if one sleep command
        is interrupted, we are still blocked for the equested duration
    """
    current_time = time.time()
    end_time = current_time + period
    while current_time < end_time:
        time.sleep(end_time - current_time)
        current_time = time.time()


class Atropos(object):
    """
        The Atropos class
    """

    def __init__(self, config, config_dir, output_queue,
                 event_queue, verbose=False, debug=False,
                 logger_instance=None):
        """
            Init function for the atropos class
            Args:
                config - A dict containing fate book contents
                config_dir - Path to config directory
                output_queue - A multi processing queue to add atropos
                information
                event_queue - A multi processing queue to record event status
                verbose - Verbosity flag
                debug - debug flag
            Return:
                None
            Raise:
                None
        """
        self.verbose = verbose
        self.config = config
        self.debug = debug
        self.config_dir = config_dir

        self.nyx = False
        self.non_deterministic_schdlr_flag = False
        self.deterministic_schdlr_flag = False
        self.logger_instance = None
        self.failure_in_flight = False
        # Adding an empty initialization of all the config variables
        # Config variables
        self.destiny = None
        self.logger = None
        self.logger_file_handle = None
        self.failures = None
        self.topology = None
        self.service = None
        self.impact_limits = None
        self.scheduler_plugin = None
        self.journal = None
        self.topology_object = None
        self.healthcheck = None
        self.output_queue = output_queue
        self.event_queue = event_queue

        for key, val in config.iteritems():
            setattr(self, key, val)
        del self.config

        if logger_instance is None:
            self.logger_instance = Logger(self.logger)
        else:
            self.logger_instance = logger_instance

        if 'topology_config' in self.topology.keys():
            self.topology_config = self.topology['topology_config']
        else:
            self.topology_config = None
        if 'topology_plugin' in self.topology.keys():
            self.topology_plugin = self.topology['topology_plugin']
        else:
            self.topology_plugin = None

        if self.topology_config is not None:
            self.topology_config = os.path.join(self.config_dir,
                                                self.topology_config)
        self.populate_topology()

        self.populate_scheduler_plugin()

        signal.signal(signal.SIGTERM, self.sigterm_handler)

    def main_loop(self):
        """
            Atropos receives the plan from the scheduler and follows
            each item in the plan
            Args:
                None
            Return:
                None
            Raise:
                AttributeError: If the scheduler class does not exist
                KeyError: If destiny is malformed (missing important
                                                   information)
        """
        self.journal = Journal(self.impact_limits,
                               logger_instance=self.logger_instance)
        if self.scheduler_plugin is None:
            self.logger_instance.logit("Error",
                                       "Scheduler NOT found")
            sys.exit(0)
        self.logger_instance.logit("INFO",
                                   "As defined in destiny, using"
                                   " the scheduler plugin: {0}"
                                   .format(self.scheduler_plugin),
                                   log_level="VERBOSE")
        try:
            scheduler_module = __import__(SCHEDULER_PLUGIN_PATH + '.' +
                                          self.scheduler_plugin + '.' +
                                          self.scheduler_plugin,
                                          fromlist=self.scheduler_plugin)
        except ImportError:
            self.logger_instance.logit("Error",
                                       "The scheduler plugin {0}"
                                       " not found"
                                       .format(self.scheduler_plugin),
                                       log_level="VERBOSE")
            raise
        try:
            scheduler_class = getattr(scheduler_module, self.scheduler_plugin)
            scheduler = scheduler_class(self.get_scheduler_destiny(),
                                        verbose=True)
        except (AttributeError, KeyError):
            self.logger_instance.logit("Error",
                                       "The scheduler class {0}"
                                       " not found"
                                       .format(self.scheduler_plugin),
                                       log_level="VERBOSE")
            raise

        # Put all the atropos specific info into the output queue
        self.output_queue.put((self.service, self.get_all_nodes(),
                               scheduler.get_plan()))

        for event in scheduler.get_plan():
            for failure_name, trigger_time in event.iteritems():
                self.logger_instance.logit("INFO", "Acting on NonDeterministic"
                                                   " plan: {0}, triggertime:"
                                                   " {1}, service name: {2}".
                                           format(failure_name,
                                                  datetime.datetime.
                                                  fromtimestamp(
                                                      int(trigger_time)),
                                                  self.service),
                                           log_level="VERBOSE")
                current_timestamp = int(time.time())
                if current_timestamp > trigger_time:
                    self.logger_instance.logit("WARNING",
                                               "Encountered a missed event"
                                               " in the plan. Skipping: {0}"
                                               .format(failure_name))
                    # Add an item in event queue specifying that
                    self.event_queue.put((self.service, failure_name,
                                          trigger_time, "NOT_DECIDED", False))
                    self.event_queue.put((self.service, failure_name +
                                          "-revert", trigger_time,
                                          "NOT_DECIDED", False))
                    continue
                else:
                    self.logger_instance.logit("INFO",
                                               "Sleeping till {0} to induce:"
                                               " {1} on random node"
                                               .format(
                                                   datetime.datetime.
                                                   fromtimestamp(
                                                       int(trigger_time)),
                                                   failure_name))
                    sleep_correctly(trigger_time - current_timestamp)
                    random_node = self.get_random_node()
                    if not random_node:
                        self.logger_instance.logit("FATAL",
                                                   "Could not "
                                                   "get_random_node()."
                                                   " Skipping this cycle.")
                        self.event_queue.put((self.service, failure_name,
                                              trigger_time, "FAILED_TO_FETCH",
                                              False))
                        self.event_queue.put((self.service, failure_name +
                                              "-revert", trigger_time,
                                              "FAILED_TO_FETCH", False))

                        continue
                    self.logger_instance.logit("INFO",
                                               "Waking up to induce: {0}"
                                               " on the node: {1}".
                                               format(failure_name,
                                                      random_node))
                    self.execute_fate(random_node, failure_name, trigger_time)
        if self.verbose:
            print '[VERBOSE INFO]:', self.service, 'main_loop completed'

    def get_failure_definition(self, failure_name):
        """
            Returns the definition of specific failure from the configs
            Args:
                failure_name -- Name of the failure whose config is required
            Return:
                Failure definition dictionary if it exists else False
            Raise:
                None
        """
        for failure in self.get_failures():
            if failure['name'] == failure_name:
                return failure
        return False

    def populate_scheduler_plugin(self):
        """
           Obtain the name of the scheduler to be used
           and save it to self.scheduler_plugin
            Args:
                None
            Return:
                None
            Raise:
                None
        """
        try:
            self.scheduler_plugin = self.destiny['scheduler_plugin']
        except KeyError:
            self.scheduler_plugin = None

    def get_failures(self):
        """
            Fetch all the failure definitions from the failures
            section of the fate book
            Args:
                None
            Return:
                None
            Raise:
                None
        """
        if self.failures:
            return self.failures
        else:
            return False

    def get_scheduler_destiny(self):
        """
            Fetch destiny section of the fate book
            Args:
                None
            Return:
                None
            Raise:
                KeyError - If destiny section is not present in the config
        """
        if self.verbose:
            pass
        try:
            if self.destiny[self.scheduler_plugin]:
                return self.destiny[self.scheduler_plugin]
        except KeyError:
            raise

    def get_random_node(self):
        """
            Call topology plugin to get a random node
            Args:
                None
            Return:
                Output of the call to get_random_node
                in the topology plugin
            Raise:
                None

        """
        return self.topology_object.get_random_node()

    def get_all_nodes(self):
        """
            fetches all the nodes that are supported by topology plugin
            Args:
                None
            Return:
                Output of the call to get_all_nodes
                in the topology plugin
            Raise:
                None
        """
        return self.topology_object.get_all_nodes()

    def populate_topology(self):
        """
            Imports the topology plugin specified in the configs,
            If there are none specified, we use the static topology plugin
            Args:
                None
            Returns:
                None
            Raises:
                AttributeError - If we are unable to fetch the expected
                    topology class
        """
        if self.topology_plugin is None:
            # We could enforce a topoplogy requirement on the configs
            self.logger_instance.logit("INFO",
                                       "No topology plugin has been"
                                       " defined in the fate book. "
                                       "Trying default topology plugin:" +
                                       DEFAULT_TOPOPLOGY_PLUGIN,
                                       log_level="WARNING")
            self.topology_plugin = DEFAULT_TOPOPLOGY_PLUGIN
        try:
            # Try importing the plugin specified in the config
            topology_module = __import__(TOPOLOGY_PLUGIN_PATH + '.' +
                                         self.topology_plugin + '.' +
                                         self.topology_plugin,
                                         fromlist=[self.topology_plugin])
        except ImportError:
            # if topology import failed try import the default topology
            self.logger_instance.logit("WARNING",
                                       "Specified Topology plugin does"
                                       " not exist."
                                       "Trying default topology plugin:" +
                                       DEFAULT_TOPOPLOGY_PLUGIN,
                                       log_level="WARNING")
            self.topology_plugin = DEFAULT_TOPOPLOGY_PLUGIN
            topology_module = __import__(TOPOLOGY_PLUGIN_PATH + '.' +
                                         self.topology_plugin + '.' +
                                         self.topology_plugin,
                                         fromlist=[self.topology_plugin])
        try:
            topology_class = getattr(topology_module, self.topology_plugin)
        except AttributeError as exc:
            self.logger_instance.logit("ERROR",
                                       "Something went wrong in class fetch"
                                       "with exception {0}".format(exc),
                                       log_level="ERROR")
            raise
        self.logger_instance.logit("INFO",
                                   "Topology plugin initialized : {0}"
                                   .format(self.topology_plugin),
                                   log_level="VERBOSE")
        self.topology_object = topology_class('{0}'
                                              .format(self.topology_config),
                                              self.logger)

    def get_health_check(self):
        """
            Fetch the current health check
            Args:
                None
            Return:
                Healthcheck if defined else False
            Raise:
                None
        """
        try:
            return self.healthcheck
        except NameError:
            return None

    def import_health_check(self, plugin_name, coordinate,
                            hc_plugin_config=None):
        """
            Imports the healthcheck that has been defined in the fatebook
            Args:
                plugin_name: Name of healthcheck plugin
                coordinate: Any specific coordinate for the health check
                    (for eg: could be an executable script
                     to be executed by the healthcheck)
            Return:
                An object of the healthcheck class
            Raise:
                ImportError if the system is unable to import it
        """
        try:
            self.logger_instance.logit("INFO",
                                       "Healthceck plugin defined: {0}"
                                       .format(plugin_name),
                                       log_level="VERBOSE")
            healthcheck_module = __import__(HEALTHCHECK_PLUGIN_PATH + '.' +
                                            plugin_name + '.' + plugin_name,
                                            fromlist=[plugin_name])
        except ImportError as exc:
            self.logger_instance.logit("INFO",
                                       "Healthcheck block defined,"
                                       " but content is bad."
                                       " Disabling healthcheck altogether"
                                       " {0}".format(exc),
                                       log_level="WARNING")
            self.healthcheck = None
            raise
        health_check_class = getattr(healthcheck_module, plugin_name)
        return health_check_class(coordinate, hc_plugin_config)

    def execute_fate(self, node, failure_name, trigger_time=0):
        """
            Induce the specified failure on the node, wait for the
            configured wait seconds and then revert the failure. Both
            of the event execution status are captured in the event queue
            Args:
                node - The target node for the failure
                failure_name- The failure to be induced and reverted
                trigger_time - The time at which the failure is being induced
                                (this is mainly for the event queue)
            Return:
                None
            Raise:
                Any exception returned by the handler
        """
        self.logger_instance.logit("INFO",
                                   "Atropos executing fate: {0} for target {1}"
                                   .format(failure_name, node),
                                   log_level="VERBOSE")

        custom_failure_definition = \
            self.get_failure_definition(failure_name)

        if custom_failure_definition:
            if self.debug:
                print ('[DEBUG INFO]: FOUND IN CUSTOM FAILRUES. '
                       'about to run handler:', custom_failure_definition,
                       'for', failure_name)
            # break immediately, as custom failures overried base failures
            handler_data = custom_failure_definition
            if SUDO_USER_KEY in handler_data:
                sudo_user = handler_data[SUDO_USER_KEY]
            else:
                sudo_user = None
        else:
            print ('[WARNING]: Failure', failure_name,
                   'has not been found in nyx.yaml and FateBook for ',
                   self.service)

        hc_config = self.get_health_check()
        hc_plugin_config = None

        if HEALTHCHECK_PLUGINCONFIG_KEY in hc_config.keys():
            hc_plugin_config = hc_config[HEALTHCHECK_PLUGINCONFIG_KEY]

        if hc_config:
            h_chck = self.import_health_check(hc_config['plugin'],
                                              hc_config['coordinate'],
                                              hc_plugin_config)
        try:
            if not h_chck.check():
                self.logger_instance.logit("INFO", "HealthCheck failed."
                                                   " Skipping the failure"
                                                   " scenario",
                                           log_level="INFO")
            else:
                self.logger_instance.logit("INFO",
                                           "HealthCheck successfully finished."
                                           " Proceeding with the failure"
                                           " scenario", log_level="INFO")
                if self.journal.is_total_impact_allowed():
                    self.logger_instance.logit("INFO",
                                               "Total impact is allowed",
                                               log_level="VERBOSE")
                    self.journal.cast_impact(node)
                    self.failure_in_flight = True
                    if self.run_inducer(node, handler_data['induce_handler'],
                                        sudo_user):
                        self.logger_instance.logit("INFO",
                                                   "Successfully executed "
                                                   "induce handler for: {0}"
                                                   .format(failure_name))
                        self.event_queue.put((self.service, failure_name,
                                              trigger_time, node,
                                              True))

                        self.logger_instance.logit("INFO",
                                                   "Waiting {0} seconds before"
                                                   " waking up "
                                                   "and issuing a revert"
                                                   .format(
                                                       handler_data[
                                                           'wait_seconds']))
                        sleep_correctly(handler_data['wait_seconds'])
                        if self.run_reverter(node,
                                             handler_data['restore_handler'],
                                             sudo_user):
                            self.logger_instance.logit("INFO",
                                                       "Successfully executed"
                                                       " revert handler for:"
                                                       " {0}"
                                                       .format(failure_name))
                            self.journal.revert_impact(node)
                            self.failure_in_flight = False
                            self.event_queue.put((self.service,
                                                  failure_name + '-revert',
                                                  trigger_time, node,
                                                  True))

                        else:
                            self.logger_instance.logit("WARNING",
                                                       "Could not run revert "
                                                       "hadler for: {0}"
                                                       .format(failure_name))
                            self.event_queue.put((self.service,
                                                  failure_name + '-revert',
                                                  trigger_time, node,
                                                  False))

                    else:
                        self.logger_instance.logit("WARNING",
                                                   "Could not run induce "
                                                   "handler for: {0}"
                                                   .format(failure_name))
                        self.event_queue.put((self.service, failure_name,
                                              trigger_time, node,
                                              False))
                        self.event_queue.put((self.service,
                                              failure_name + '-revert',
                                              trigger_time, node,
                                              False))

                else:
                    self.logger_instance.logit("WARNING",
                                               "Impact limit reached. Please "
                                               "fix the service and rerun the "
                                               "failure inducer")
                    sys.exit()
        except Exception:
            raise

    def run_inducer(self, node, handler_data, sudo_user):
        """
            Runs the failure inducer on a specific target node
            Args:
                node - The target node on which failure should be run
                handler_data - Any data required by the handler
            Return:
                True if the handler was successful else False
            Raise:
                None
        """
        return self.run_handler(node, handler_data, sudo_user)

    def run_reverter(self, node, handler_data, sudo_user):
        """
            Runs the failure revert on a specific target node
            Args:
                node - The target node on which failure should be run
                handler_data - Any data required by the handler
            Return:
                True if the handler was successful else False
            Raise:
                None
        """
        return self.run_handler(node, handler_data, sudo_user)

    def run_handler(self, target, handler_data, sudo_user):
        """
            Runs a specified coordinate on a specific target node
            Args:
                node - The target node on which failure should be run
                handler_data - Any data required by the handler, includes
                    information like Handler name, coordinate and arguments
            Return:
                True if the handler was successful else False
            Raise:
                None
        """
        if sudo_user is not None:
            handler_data['arguments'].append(sudo_user)
        return self.abstract_handler(handler_data['type'],
                                     target, handler_data['coordinate'],
                                     handler_data['arguments'])

    def abstract_handler(self, handler_name, target, coordinate, arguments):
        """
            Runs the specified handler for a given target (eg: server) and a
            coordinate (eg: a shell script) and arguments
            Args:
                handler_name - Name of the handler should be user
                target - Target on which handler should act on
                coordinate - The command that should be executed on the target
                arguments - Any arguments to the coordinate
            Return:
                True - if the command_status returned by handler is 0
                False - if it is not zero
            Raise:
                None
        """
        self.logger_instance.logit("INFO",
                                   "Starting {0} on: {1},"
                                   " coodrinate: {2}, args: {3}"
                                   .format(handler_name, target,
                                           coordinate, arguments), "VERBOSE")
        # XXX add try catch exception
        handler_module = __import__(HANDLER_PLUGIN_PATH + '.' +
                                    handler_name + '.' + handler_name,
                                    fromlist=[handler_name])
        handler_class = getattr(handler_module, handler_name)
        handler = handler_class(self.config_dir, target,
                                self.logger_instance, verbose=True)
        handler.authenticate()
        command_status, command_output, command_error = \
            handler.execute_command(coordinate, arguments)
        self.logger_instance.logit("INFO", "STDOUT: {0}"
                                   .format(command_output))
        self.logger_instance.logit("INFO", "STDERR: {0}"
                                   .format(command_error))
        if command_status != 0:
            self.logger_instance.logit("ERROR", "Command Execution failed")
            return False
        return True

    def sigterm_handler(self, recvd_signal, frame):
        """
            Signal handler for atropos
                - Atropos perform ignores the signal if in the
                  middle of a failure
                - If not it exits the process
            Args:
                recvd_signal - Signal that was received
                frame - Current stack frame
            Return:
                None
            Raise:
                None
        """
        if self.failure_in_flight:
            self.logger_instance.logit("INFO",
                                       "Atropos received SIGTERM, "
                                       "but a failure is inflight. "
                                       "Ignoring. Pid: {0}, "
                                       "Service name in fate book: {1}"
                                       .format(os.getpid(), self.service),
                                       log_level="WARNING")
        else:
            self.logger_instance.logit("INFO",
                                       "Atropos received SIGTERM. Pid: "
                                       "{0}, Service name in fate book:"
                                       "{1}. Wrapping up and exiting"
                                       .format(os.getpid(), self.service),
                                       log_level="WARNING")
            sys.exit(0)
