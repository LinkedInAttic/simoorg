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

import httplib
import json
import time
import yaml
import os
import subprocess

SIMOORG_COMMAND = "simoorg"
API_PORT = 8000

TEST_CONFIG_DIR = 'test_configs/'
TEST_FATEBOOK = 'fate_books/test_service.yaml'
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
HELPER_SCRIPT_DIR = SCRIPT_DIR + '/helper_scripts/'

# While checking if the failure has happened we need to leave a bit of
# buffer to allow for the execution of command and time taken to check
# for the failure
FAILURE_EXECUTION_BUFFER = 0
FAILURE_CHECK_BUFFER = 0
FAILURE_REVERT_BUFFER = 1


class TestSimoorg(object):
    def __init__(self):
        self.simoorg_pids = []
        self.current_plan = []
        with open(TEST_CONFIG_DIR + TEST_FATEBOOK) as config_fd:
            self.fatebook_config = yaml.load(config_fd)
        with open(TEST_CONFIG_DIR + 'test.yaml') as config_fd:
            self.test_configs = yaml.load(config_fd)
        self.scheduler_config = self.fatebook_config['destiny'][
            'scheduler_plugin']

    def check_simoorg(self):
        all_procs = subprocess.Popen(['ps', 'ax', ], stdout=subprocess.PIPE)
        fate_procs_grep = subprocess.Popen(['grep', SIMOORG_COMMAND],
                                           stdin=all_procs.stdout,
                                           stdout=subprocess.PIPE)
        fate_procs = subprocess.Popen(['grep', '-v', 'grep'],
                                      stdin=fate_procs_grep.stdout,
                                      stdout=subprocess.PIPE)
        # Change this to wc -l
        fate_pids_cmmnd = subprocess.Popen(['awk', '{print $1}', ],
                                           stdin=fate_procs.stdout,
                                           stdout=subprocess.PIPE)
        self.simoorg_pids = list(
            map(str.strip, fate_pids_cmmnd.stdout.readlines()))
        if len(self.simoorg_pids) > 1:
            return True
        else:
            return False

    def main_loop(self):
        """
            Confirm simoorg is running and fetch the plan being followed.
            For a given plan find the entry closest to the current time and
            perform a check to see if the current state matches the plan entry
            in case of a mismatch, perform a random sleep less than the window
            remaining for the current operation and test again. If it fails
            again exit reporting a test failure. On success the system goes
            to a random sleep and repeats the operation till the end of the
            plan is reached
        """
        if not self.check_simoorg():
            print("Error: Simoorg not running")
            exit(1)

        api_base_url = "127.0.0.1:" + str(API_PORT)
        self.current_plan = self.fetch_plan(api_base_url)
        for event in self.current_plan:
            for failure, trigger_time in event.iteritems():
                current_time = time.time()
                if current_time > trigger_time:
                    print ("LOGGER: Skipping failure " + failure + " at " +
                           str(trigger_time))
                    continue
                else:
                    if not self.wait_and_check(trigger_time, failure):
                        print ("LOGGER: Test failed for failure " +
                               failure + " at " + str(trigger_time))
                        exit(1)
                    else:
                        print ("LOGGER: Tests cleared for failure " +
                               failure + " at " + str(trigger_time))

    def do_http_get(self, base_url, get_url):
        try:
            connection = httplib.HTTPConnection(base_url)
            connection.request('GET', get_url)
            resp = connection.getresponse()
        except httplib.HTTPException:
            print ("LOGGER: Unable to perform fetch the given url ",
                   base_url + get_url)
            return (False, None)
        except Exception, exc:
            print ("LOGGER: Unable to perform fetch the given url"
                   " {0} with exception {1}",
                   base_url + get_url, exc)
            raise
        data = resp.read()
        if resp.status != 200:
            print ("LOGGER: The return status for the url get request was ",
                   resp.status)
            return (False, data)
        else:
            return (True, data)

    def fetch_plan(self, base_url):
        api_url = '/' + self.fatebook_config['service'] + "/plan"
        status, data = self.do_http_get(base_url, api_url)
        if status:
            plan_dict = json.loads(data)
        else:
            plan_dict = []
        return plan_dict

    def get_failure_definition(self, failure):
        for failure_def in self.fatebook_config['failures']:
            if failure_def['name'] == failure:
                return failure_def
        return None

    def wait_and_check(self, trigger_time, failure):
        current_time = time.time()
        failure_definition = self.get_failure_definition(failure)
        wait_time = failure_definition['wait_seconds']
        revert_time = trigger_time + FAILURE_EXECUTION_BUFFER + wait_time
        failure_sleep_time = (trigger_time - current_time +
                              FAILURE_EXECUTION_BUFFER +
                              (wait_time / 2) - FAILURE_CHECK_BUFFER)
        time.sleep(failure_sleep_time)
        if not self.check_failure(failure):
            print ("Logger: Failed to induce failure " + failure + " at " +
                   str(trigger_time))
            return False
        else:
            print ("Logger: Successfully induced failure " +
                   failure + " at " + str(trigger_time))
        current_time = time.time()
        if current_time < revert_time:
            revert_sleep_time = (revert_time - current_time +
                                 FAILURE_REVERT_BUFFER)
            time.sleep(revert_sleep_time)
            if not self.check_revert(failure):
                print (" Failed to revert failure " + failure + " at " + str(
                    trigger_time))
                return False
            else:
                print ("Logger: Successfully reverted failure " + failure +
                       " at " + str(trigger_time))
        else:
            print ("LOGGER: Skipping revert failure check " + failure +
                   " at " + str(trigger_time))
        return True

    def check_failure(self, failure):
        """
            For a given plan entry check if the current status
            matches the entry in the plan
        """
        failure_check_command = self.test_configs['check'][failure]['failure'][
            'command']
        failure_check_args = self.test_configs['check'][failure]['failure'][
            'args']
        check_proc = subprocess.Popen(
            [HELPER_SCRIPT_DIR + failure_check_command] + failure_check_args)
        status = check_proc.wait()
        if status == 0:
            return True
        else:
            return False

    def check_revert(self, failure):
        """
            For a given entry in the plan, check if failure was reverted
            properly
        """
        revert_check_command = self.test_configs['check'][failure]['revert'][
            'command']
        revert_check_args = self.test_configs['check'][failure]['revert'][
            'args']
        check_proc = subprocess.Popen(
            [HELPER_SCRIPT_DIR + revert_check_command] + revert_check_args)
        status = check_proc.wait()
        if status == 0:
            return True
        else:
            return False


if __name__ == "__main__":
    test_obj = TestSimoorg()
    test_obj.main_loop()
