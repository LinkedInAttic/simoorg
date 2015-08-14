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
     A simple scheduler plugin that returns a random plan
"""

import time
import random
from simoorg.plugins.scheduler.BaseScheduler import BaseScheduler


class NonDeterministicScheduler(BaseScheduler):
    """
        Non deterministic scheduler class
    """
    def __init__(self, destiny_object, verbose=False, debug=False):
        """
            Init function for the class
            Args:
                destiny_object - A dict containing the destiny
                    section of the fate book
                verbose - verbosity flag
                debug - debug flag
            Returns:
                None
            Raise:
                None
        """
        BaseScheduler.__init__(self, destiny_object)
        self.verbose = verbose
        self.debug = debug

        self.destiny_object = destiny_object

        # this will contain randomly generated plan for each failure
        self.plan = []

        self.generate_plan()

    def generate_plan(self):
        """
            Generates a plan by selecting random trigger time
            for random failures
            Args:
                None
            Return:
                None
            Raise:
                None
        """
        if self.debug:
            print ('[VERBOSE INFO]: Generating plan for the NonDeterministic'
                   ' scheduler: ')

        current_timestamp = int(time.time())
        trigger_time = current_timestamp
        planning_completed = False
        failure_list = self.get_failures().keys()
        random.shuffle(failure_list)
        while not planning_completed:
            for failure_name in failure_list:
                random_step = random.randint(self.
                                             get_min_gap_between_failures(),
                                             self.
                                             get_max_gap_between_failures())
                if self.debug:
                    print ('[DEBUG INFO]: randomstep is:',
                           random_step, 'minutes')
                trigger_time = trigger_time + random_step * 60
                if (trigger_time > self.get_total_run_duration() * 60 +
                        current_timestamp):
                    planning_completed = True
                    break
                self.plan.append({failure_name: trigger_time})
                if self.debug:
                    print ('[DEBUG INFO]: Plan item added: ',
                           {failure_name: trigger_time})

        if self.debug:
            print '[VERBOSE INFO]: NonDeterministic plan has been generated'
