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

import os
import yaml
import time
import signal
import unittest
import threading
import multiprocessing

import simoorg.atropos as atropos
import mock_modules.Logger as Logger

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_FATEBOOK_FILE = (TEST_DIR + "/unittest_configs/atropos_configs/" +
                      "sample_base/fate_books/test.yaml")
CONFIG_DIR = TEST_DIR + "/../configs/"
HANDLER_CONFIG_DIR = TEST_DIR + "/../configs/"
TEST_CONFIG_DIR = TEST_DIR + "/unittest_configs/atropos_configs/sample_base/"
REVERT_SKIP_CONFIG_DIR = (TEST_DIR + "/unittest_configs/atropos_configs" +
                          "/sample_revert_skip/")
FAILURE_SKIP_CONFIG_DIR = (TEST_DIR + "/unittest_configs/atropos_configs/" +
                           "sample_failure_skip/")
MISSING_SCHED_FATEBOOK = (TEST_DIR + "/unittest_configs/atropos_configs/" +
                          "sample_missing_sched/fate_books/test.yaml")
INCORRECT_SCHED_FATEBOOK = (TEST_DIR + "/unittest_configs/atropos_configs/" +
                            "sample_incorrect_sched/fate_books/test.yaml")
MISSING_RANDOM_NODE_FATEBOOK = (TEST_DIR + "/unittest_configs/" +
                                "atropos_configs/sample_missing_random_node/" +
                                "fate_books/test.yaml")
MISSING_RANDOM_NODE_CONFIG_DIR = (TEST_DIR + "/unittest_configs/" +
                                  "atropos_configs/" +
                                  "sample_missing_random_node/")
MISSING_TOPOLOGY_FATEBOOK = (TEST_DIR + "/unittest_configs/atropos_configs/" +
                             "sample_missing_topology/fate_books/test.yaml")
INCORRECT_HC_FATEBOOK = (TEST_DIR + "/unittest_configs/atropos_configs/" +
                         "sample_incorrect_hc/fate_books/test.yaml")
MISSING_DESTINY_FATEBOOK = (TEST_DIR + "/unittest_configs/atropos_configs/" +
                            "sample_missing_destiny/fate_books/test.yaml")
HASH_LENGTH = 8

EVENT_SCHEDULE_BUFFER = 10
ATROPOS_START_BUFFER = 2

TEST_FAILURE_NAME = 'test_failure'


def KillerThread(pid, sleep_time):
    time.sleep(sleep_time)
    os.kill(pid, signal.SIGTERM)


class TestAtropos(unittest.TestCase):
    """
        Here we will be testing for the following conditions
        1. Is sig handler working properly?
            1.a Is it catching the signal (checked via log)
                and continuing to execute?
        2. Are all the revert failures being logges properly in event queue?


    """
    def setUp(self):
        with open(TEST_FATEBOOK_FILE) as c_fd:
            self.config_ = yaml.load(c_fd)
        test_config_file = TEST_CONFIG_DIR + "atropos_config.yaml"
        with open(test_config_file) as config_fd:
            self.test_config = yaml.load(config_fd)
        self.logger = Logger.Logger()

    def tearDown(self):
        pass

    def fetch_failure_definition(self, failure_name):
        """
            Fetch the failure definition of a specific failure from the configs
            Arguments:
            failure_name -- The specific failure whose config we need

            Return -- Failure config dictionary
        """
        for failure in self.config_['failures']:
            if failure['name'] == failure_name:
                return failure
        return None

    def test_atropos_sighandler(self):
        """
            Generate a new process that sleep for the min wait time
            Then produces the kill signal to the current process
            Make sure the atropos ran for more than the wait time
            (To make sure the kill signal didnt cause the atropos to exit)
        """
        input_q = multiprocessing.Queue()
        event_q = multiprocessing.Queue()
        random_start_time = ATROPOS_START_BUFFER
        my_pid = os.getpid()
        event_time = time.time() + EVENT_SCHEDULE_BUFFER

        # Create an event file to be consumed by a scheduler
        with open(self.test_config['event_file'], 'w') as ev_fd:
            ev_fd.write(str(event_time))

        # Start a thread that produces a SIGTERM signal
        # at a random time after the event time
        thrd1 = threading.Thread(target=KillerThread, args=(
            my_pid, random_start_time + EVENT_SCHEDULE_BUFFER))
        thrd1.start()

        # Create the atropos object
        atropos_strt_time = time.time()
        self.atropos_obj = atropos.Atropos(self.config_, TEST_CONFIG_DIR,
                                           input_q, event_q,
                                           logger_instance=self.logger)
        atropos_finish_time = time.time()

        # Confirm the time taken by atropos object is more than the wait time
        # + the initial sleep time

        failure_def = self.fetch_failure_definition(TEST_FAILURE_NAME)
        if atropos_finish_time - atropos_strt_time < \
                (failure_def['wait_seconds'] +
                 (event_time - atropos_strt_time)):
            print (atropos_finish_time - atropos_strt_time)
            print (failure_def['wait_seconds'] +
                   (event_time - atropos_strt_time))
            self.assert_(False)

        # confirm the logger queue has the expected log line
        expected_log_msg = ("Atropos received SIGTERM, "
                            "but a failure is inflight. "
                            "Ignoring. Pid: {0}, "
                            "Service name in fate book: {1}"
                            .format(my_pid, self.config_['service']))
        print self.logger.log_queue
        self.assert_(self.logger.log_contains(expected_log_msg))

    def test_revert_skip(self):
        """
            Checks if  revert failures are being logged
            properly into the event queue.
        """
        input_q = multiprocessing.Queue()
        event_q = multiprocessing.Queue()
        # Create the atropos object
        event_time = time.time() + EVENT_SCHEDULE_BUFFER
        with open(self.test_config['event_file'], 'w') as ev_fd:
            ev_fd.write(str(event_time))
        # Create an atropos object with revert_skip flag
        # enabled in the handler config
        self.atropos_obj = atropos.Atropos(self.config_,
                                           REVERT_SKIP_CONFIG_DIR, input_q,
                                           event_q,
                                           logger_instance=self.logger)
        failure_event = list(event_q.get())
        revert_event = list(event_q.get())
        self.assert_(failure_event[-1] and not (revert_event[-1]))

    def test_failure_skip(self):
        """
            Check if unsuccessful failures are being
            logged properly to the event queue
        """
        input_q = multiprocessing.Queue()
        event_q = multiprocessing.Queue()
        # Create the atropos object
        event_time = time.time() + EVENT_SCHEDULE_BUFFER
        with open(self.test_config['event_file'], 'w') as ev_fd:
            ev_fd.write(str(event_time))
        # Create an atropos object with failure_skip flag
        # enabled in the handler config
        self.atropos_obj = atropos.Atropos(self.config_,
                                           FAILURE_SKIP_CONFIG_DIR, input_q,
                                           event_q,
                                           logger_instance=self.logger)
        failure_event = list(event_q.get())
        revert_event = list(event_q.get())
        self.assert_(not (failure_event[-1]) and not (revert_event[-1]))

    def test_atropos_failure_effect(self):
        """
            Check if successful failures are being executed properly
        """
        input_q = multiprocessing.Queue()
        event_q = multiprocessing.Queue()
        # Create the atropos object
        event_time = time.time() + EVENT_SCHEDULE_BUFFER
        with open(self.test_config['event_file'], 'w') as ev_fd:
            ev_fd.write(str(event_time))
        my_pid = os.getpid()
        # We create an atropos object with revert skip flag
        # enabled in the handler config so only failure occurs
        # and failures can be checked
        self.atropos_obj = atropos.Atropos(self.config_,
                                           REVERT_SKIP_CONFIG_DIR, input_q,
                                           event_q,
                                           logger_instance=self.logger)
        result_file = self.test_config['result_file'].strip()
        with open(result_file) as atr_fd:
            result_pid = atr_fd.readline().strip()
        os.remove(result_file)
        if int(my_pid) == int(result_pid):
            self.assert_(True)
        else:
            self.assert_(False)

    def test_missing_sched(self):
        """
            Check the system exits when we skip scheduler name in the fatebook
        """
        with open(MISSING_SCHED_FATEBOOK) as c_fd:
            self.config_ = yaml.load(c_fd)
        input_q = multiprocessing.Queue()
        event_q = multiprocessing.Queue()
        # Create the atropos object
        event_time = time.time() + EVENT_SCHEDULE_BUFFER
        with open(self.test_config['event_file'], 'w') as ev_fd:
            ev_fd.write(str(event_time))
        exit_exception_flag = False
        try:
            self.atropos_obj = atropos.Atropos(self.config_, TEST_CONFIG_DIR,
                                               input_q, event_q,
                                               logger_instance=self.logger)
        except SystemExit:
            exit_exception_flag = True
        if not exit_exception_flag:
            self.assert_(False)

    def test_incorrect_sched(self):
        """
            Check the system produces an import exception and
            exits if an incorrect scheduler name is provided
        """
        with open(INCORRECT_SCHED_FATEBOOK) as c_fd:
            self.config_ = yaml.load(c_fd)
        input_q = multiprocessing.Queue()
        event_q = multiprocessing.Queue()
        # Create the atropos object
        event_time = time.time() + EVENT_SCHEDULE_BUFFER
        with open(self.test_config['event_file'], 'w') as ev_fd:
            ev_fd.write(str(event_time))
        exit_exception_flag = False
        try:
            self.atropos_obj = atropos.Atropos(self.config_, TEST_CONFIG_DIR,
                                               input_q, event_q,
                                               logger_instance=self.logger)
        except ImportError:
            exit_exception_flag = True
        if not exit_exception_flag:
            self.assert_(False)

    def test_missing_topology(self):
        """
            Check the system uses default plugin when we skip topology
            plugin name in the fatebook
        """
        with open(MISSING_TOPOLOGY_FATEBOOK) as c_fd:
            self.config_ = yaml.load(c_fd)
        input_q = multiprocessing.Queue()
        event_q = multiprocessing.Queue()
        default_plugin = 'StaticTopology'
        # Create the atropos object
        event_time = time.time() + EVENT_SCHEDULE_BUFFER
        with open(self.test_config['event_file'], 'w') as ev_fd:
            ev_fd.write(str(event_time))
        self.atropos_obj = atropos.Atropos(self.config_, TEST_CONFIG_DIR,
                                           input_q, event_q,
                                           logger_instance=self.logger)
        self.assertEqual(self.atropos_obj.topology_object.__class__.__name__,
                         default_plugin)

    def test_wrong_plan(self):
        """
            Check both failure and revert items are marked as false in the
            event queue if the trigger time is in the past
        """
        input_q = multiprocessing.Queue()
        event_q = multiprocessing.Queue()
        event_time = time.time() - EVENT_SCHEDULE_BUFFER
        # Add an older time in the event file for the scheduler
        with open(self.test_config['event_file'], 'w') as ev_fd:
            ev_fd.write(str(event_time))
        # Create the atropos object
        self.atropos_obj = atropos.Atropos(self.config_, TEST_CONFIG_DIR,
                                           input_q, event_q,
                                           logger_instance=self.logger)
        failure_event = list(event_q.get())
        revert_event = list(event_q.get())
        self.assert_(not (failure_event[-1] or revert_event[-1]))

    def test_missing_random_node(self):
        """
            Check that both failure and revert items  are marked as false in
            the event queue if the topology plugin doesn't produce a random
            node
        """
        with open(MISSING_RANDOM_NODE_FATEBOOK) as c_fd:
            self.config_ = yaml.load(c_fd)

        input_q = multiprocessing.Queue()
        event_q = multiprocessing.Queue()
        # Create the atropos object
        event_time = time.time() + EVENT_SCHEDULE_BUFFER
        with open(self.test_config['event_file'], 'w') as ev_fd:
            ev_fd.write(str(event_time))
        self.atropos_obj = atropos.Atropos(self.config_,
                                           MISSING_RANDOM_NODE_CONFIG_DIR,
                                           input_q, event_q,
                                           logger_instance=self.logger)
        failure_event = list(event_q.get())
        revert_event = list(event_q.get())
        self.assert_(not (failure_event[-1] or revert_event[-1]))

    def test_incorrect_healthcheck(self):
        """
            Check that atropos produces an import exception,
            if an incorrect healthcheck is provided in the fatebook
        """
        with open(INCORRECT_HC_FATEBOOK) as c_fd:
            self.config_ = yaml.load(c_fd)
        input_q = multiprocessing.Queue()
        event_q = multiprocessing.Queue()
        # Create the atropos object
        event_time = time.time() + EVENT_SCHEDULE_BUFFER
        with open(self.test_config['event_file'], 'w') as ev_fd:
            ev_fd.write(str(event_time))
        exit_exception_flag = False
        try:
            self.atropos_obj = atropos.Atropos(self.config_, TEST_CONFIG_DIR,
                                               input_q, event_q,
                                               logger_instance=self.logger)
        except ImportError:
            exit_exception_flag = True
        if not exit_exception_flag:
            self.assert_(False)

    def test_missing_destiny(self):
        """
            Check that the atropos object generates an exception
            if the destiny section is missing from the fatebook
        """
        with open(MISSING_DESTINY_FATEBOOK) as c_fd:
            self.config_ = yaml.load(c_fd)
        input_q = multiprocessing.Queue()
        event_q = multiprocessing.Queue()
        # Create the atropos object
        event_time = time.time() + EVENT_SCHEDULE_BUFFER
        with open(self.test_config['event_file'], 'w') as ev_fd:
            ev_fd.write(str(event_time))
        exit_exception_flag = False
        try:
            self.atropos_obj = atropos.Atropos(self.config_, TEST_CONFIG_DIR,
                                               input_q,
                                               event_q,
                                               logger_instance=self.logger)
        except KeyError:
            exit_exception_flag = True
        if not exit_exception_flag:
            self.assert_(False)


if __name__ == '__main__':
    unittest.main()
