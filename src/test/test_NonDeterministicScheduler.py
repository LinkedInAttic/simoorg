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
import unittest

import simoorg.plugins.scheduler.NonDeterministicScheduler. \
    NonDeterministicScheduler as NonDeterministicScheduler

FATEBOOK_DIR = (os.path.dirname(os.path.realpath(__file__)) +
                "/unittest_configs/scheduler_configs/fate_books/")


class TestNonDeterministicScheduler(unittest.TestCase):
    """
        Test the NonDeterministicScheduler plugin
    """
    def setUp(self):
        """
            Read all the given fatebooks in the main config
        """
        fate_book_files = os.listdir(FATEBOOK_DIR)
        self.config_list = []
        for config in fate_book_files:
            with open(FATEBOOK_DIR + config) as c_fd:
                self.config_list.append(yaml.load(c_fd))

    def tearDown(self):
        """
            Clear all the configs
        """
        self.config_list = []

    def test_generatePlan(self):
        """
            Make sure the plan generated for each fatebook, follows
            the expected requirements
        """
        for config in self.config_list:
            scheduler_plugin = config['destiny']['scheduler_plugin']
            destiny_object = config['destiny'][scheduler_plugin]
            min_gap = (destiny_object['constraints']
                       ['min_gap_between_failures'])
            max_gap = (destiny_object['constraints']
                       ['max_gap_between_failures'])
            total_run = (destiny_object['constraints']
                         ['total_run_duration'])
            non_det_sched_obj = (NonDeterministicScheduler
                                 .NonDeterministicScheduler(destiny_object,
                                                            verbose=True,
                                                            debug=True))
            last_step = 0
            plan_index = 0
            start_timestamp = int(time.time())
            current_step_time = start_timestamp + 60 * min_gap
            for plan_step in non_det_sched_obj.plan:
                self.assertEqual(len(plan_step), 1)
                failure = plan_step.keys()[0]
                step = plan_step[failure]
                # All failures should belong to destiny object failures
                self.assert_(failure in destiny_object['failures'].keys())
                # Each step should be larger than min wait time while being
                # less than max wait time
                self.assert_(current_step_time <= step)
                self.assert_(current_step_time + 60 * max_gap >= step)
                # Each step should be bigger than the last
                self.assert_(step > last_step)
                # Each step should be less than the max runtime provided
                # its not the last step
                # (Currently last step larger than total time, is this ok ?)
                self.assert_(step <= total_run * 60 + start_timestamp)
                current_step_time = step
                plan_index += 1


if __name__ == '__main__':
    unittest.main()
