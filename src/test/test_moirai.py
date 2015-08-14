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

import unittest
import os
import subprocess

import simoorg.moirai as Moirai
import simoorg.Api.ApiConstants as ApiConstants
import json
import time
import yaml

# Assuming a flat collection of tests
MOIRAI_CONFIG_DIR = (os.path.dirname(os.path.realpath(__file__)) +
                     "/unittest_configs/moirai_configs/")
# Here we have three sets of configurations
# A correct one - sample_base
# An incorrect on (missing service name) - sample_incorrect
# A configuration directory that is missing all the files - sample_missing
CORRECT_FATEBOOK = "sample_base/"
INCORRECT_FATEBOOK = "sample_incorrect/"
MISSING_FATEBOOK = "sample_missing/"
MISSING_API_CONFIGS = "sample_missing_api/"
IMPOSSIBLE_API_CONFIGS = "sample_impossible_api/"
COUNT_FATE = ['ps', 'aux']
TMP_FIFO = "/tmp/test.fifo"


class TestMoirai(unittest.TestCase):
    """
        In this test set we want to test three different behavior of Moirai
        1. When some required configs are missing
        2. When some config is incorrect (missing service name in fatebook)
        3. Correct behavior of moirai
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_missing_configs(self):
        """
            We expect moirai to raise an exception when
            fatebooks are missing
        """
        moirai_obj = Moirai.Moirai(MOIRAI_CONFIG_DIR + MISSING_FATEBOOK)
        caught_exception_flag = False
        try:
            moirai_obj.spawn_atropos()
        except:
            caught_exception_flag = True
        if not caught_exception_flag:
            self.assert_(caught_exception_flag)

    def test_missing_api_configs(self):
        """
            We expect moirai to raise an exception when
            api configs are missing
        """
        caught_exception_flag = False
        try:
            moirai_obj = Moirai.Moirai(MOIRAI_CONFIG_DIR + MISSING_API_CONFIGS)
            moirai_obj.spawn_atropos()
        except IOError:
            caught_exception_flag = True
        if not caught_exception_flag:
            self.assert_(caught_exception_flag)

    def test_incorrect_configs(self):
        """
            We expect moirai to raise an exception when
            fatebooks are missing service name
        """
        moirai_obj = Moirai.Moirai(MOIRAI_CONFIG_DIR + INCORRECT_FATEBOOK)
        caught_exception_flag = False
        try:
            moirai_obj.spawn_atropos()
        except:
            caught_exception_flag = True
        if not caught_exception_flag:
            moirai_obj.finish()
            self.assert_(caught_exception_flag)

    def test_moirai(self):
        """
            Test the correct behavior of Moirai
        """
        moirai_obj = Moirai.Moirai(MOIRAI_CONFIG_DIR + CORRECT_FATEBOOK)
        moirai_obj.spawn_atropos()
        expected_army_size = len(
            os.listdir(MOIRAI_CONFIG_DIR + CORRECT_FATEBOOK + 'fate_books/'))
        # Check if the number of items in atropos army list is
        # same as the number of files in fate_books dir
        self.assertEqual(expected_army_size, len(moirai_obj.atropos_army))
        # Next few checks, expects the atropos instance to be running
        # Hence for these checks to clear the runtime on the configs should
        # be atleast a few minutes
        for service, atropos_inst in moirai_obj.atropos_army.iteritems():
            all_procs = subprocess.Popen(['ps', 'ax', ],
                                         stdout=subprocess.PIPE)
            all_pids = subprocess.Popen(['awk', '{print $1}'],
                                        stdin=all_procs.stdout,
                                        stdout=subprocess.PIPE)
            fate_procs = subprocess.Popen(['grep', str(atropos_inst.pid), ],
                                          stdin=all_pids.stdout,
                                          stdout=subprocess.PIPE)
            fate_count_command = subprocess.Popen(['wc', '-l', ],
                                                  stdin=fate_procs.stdout,
                                                  stdout=subprocess.PIPE)
            fate_count = int(
                fate_count_command.stdout.readline().strip())
            self.assertEqual(fate_count, 1)

        # time.sleep(1)
        moirai_obj.finish()

    def execute_command(self, command, args, method='GET'):
        """
            Send message to moirai
        """
        try:
            self.moirai_fifo_fd = os.open(
                self.api_config['moirai_input_fifo'],
                os.O_WRONLY | os.O_NONBLOCK)
            self.moirai_fifo_file = os.fdopen(self.moirai_fifo_fd, 'w')
        except:
            self.moirai_fifo_fd = None
            return (-1, "Unable to connect to Moirai Service")
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
            print ("LOG: " + op_msg)
            return (-1, op_msg)
        except OSError:
            self.moirai_fifo_fd = None
            op_msg = ("Unable to communicate with moirai")
            print ("LOG: " + op_msg)
            return (-1, op_msg)

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
                print ("LOG: " + op_msg)
                return (-1, op_msg)
        try:
            output_obj = json.loads(output_string)
        except ValueError:
            op_msg = ("Recieved object is not a json object")
            print ("LOG: " + op_msg)
            return (-1, op_msg)
        if (output_obj[ApiConstants.COMMAND_ID_KEY] != self.command_id):
            op_msg = ("Recieved output with incorrect command id")
            print ("LOG: " + op_msg)
            return (-1, op_msg)
        return (0, output_obj[ApiConstants.COMMAND_OUTPUT_KEY])

    def execute_incorrect_command(self):
        """
            Send message to moirai
        """
        try:
            self.moirai_fifo_fd = os.open(
                self.api_config['moirai_input_fifo'],
                os.O_WRONLY | os.O_NONBLOCK)
            self.moirai_fifo_file = os.fdopen(self.moirai_fifo_fd, 'w')
        except:
            self.moirai_fifo_fd = None
            return (-2, "Unable to connect to Moirai Service")
        self.command_id = self.command_id + 1
        command_string = "NOT A JSON STRING"
        try:
            self.moirai_fifo_file.write(command_string)
            self.moirai_fifo_file.flush()
        except IOError:
            op_msg = ("Unable to communicate with moirai")
            print ("LOG: " + op_msg)
            return (-2, op_msg)
        except OSError:
            self.moirai_fifo_fd = None
            op_msg = ("Unable to communicate with moirai")
            print ("LOG: " + op_msg)
            return (-2, op_msg)

        NEW_READ_TIMEOUT_SECS = 20
        # Read from api fifo
        start_time = time.time()
        output_string = ''
        while output_string == '':
            try:
                output_string = self.api_fifo_file.read()
            except IOError:
                pass
            current_time = time.time()
            if current_time - start_time > NEW_READ_TIMEOUT_SECS:
                op_msg = ("No message recieved from Moirai")
                print ("LOG: " + op_msg)
                return (-1)
        return 0

    def test_impossible_moiriai_fifo(self):
        """
            Looks at the behaviour of moirai when an
            impossible path is provided to ti
        """

        moirai_obj = Moirai.Moirai(MOIRAI_CONFIG_DIR + IMPOSSIBLE_API_CONFIGS)
        moirai_obj.spawn_atropos()
        time.sleep(1)
        self.assert_(not moirai_obj.api_read_procs[0].is_alive())
        moirai_obj.finish()

    def test_moirai_api_commands(self):
        """
            Test the api hooks for moirai
        """
        moirai_obj = Moirai.Moirai(MOIRAI_CONFIG_DIR + CORRECT_FATEBOOK)
        moirai_obj.spawn_atropos()
        expected_list_op = ['test_service']
        failure_list = ['test_failure']
        server_list = ['localhost']
        self.command_id = 0
        event_list_cnt = 4
        try:
            os.mkfifo(TMP_FIFO)
        except (IOError, OSError):
            print ("the temp fifo file already exists, moving along")
        self.api_fifo_path = TMP_FIFO
        with open(MOIRAI_CONFIG_DIR + CORRECT_FATEBOOK + '/api.yaml') \
                as conf_fd:
            self.api_config = yaml.load(conf_fd)
        try:
            api_fifo_fd = os.open(TMP_FIFO, os.O_NONBLOCK)
            self.api_fifo_file = os.fdopen(api_fifo_fd)
        except (IOError, OSError):
            self.assert_(False)
        # Test the list command
        status, output = self.execute_command('list', {})
        if status == -1:
            self.assert_(False)
        self.assertEqual(json.loads(output), expected_list_op)
        # Test the list command
        status, output = self.execute_command('list', {})
        if status == -1:
            self.assert_(False)
        self.assertEqual(json.loads(output), expected_list_op)
        # check plan
        status, output = self.execute_command('plan',
                                              {'service_name': 'test_service'})
        if status == -1:
            self.assert_(False)
        output_list = json.loads(output)
        for event in output_list:
            for failure, trigger_time in event.iteritems():
                try:
                    time_stmp = int(trigger_time)
                    if time_stmp <= 0:
                        self.assert_(False)
                except:
                    self.assert_(False)
                if failure not in failure_list:
                    self.assert_(False)

        # check servers
        status, output = self.execute_command('servers',
                                              {'service_name': 'test_service'})
        if status == -1:
            self.assert_(False)
        output_list = json.loads(output)
        for server in output_list:
            if server not in server_list:
                self.assert_(False)

        # check events
        status, output = self.execute_command('events',
                                              {'service_name': 'test_service'})
        if status == -1:
            self.assert_(False)
        output_list = json.loads(output)
        for event in output_list:
            self.assertEqual(len(event), event_list_cnt)
        moirai_obj.finish()

        # check unknown commands
        status, output = self.execute_command('dummy',
                                              {'service_name': 'test_service'})
        if status == -1:
            self.assert_(False)

        # check incorrect message
        status = self.execute_incorrect_command()
        print status
        if status != -1:
            self.assert_(False)


if __name__ == '__main__':
    unittest.main()
