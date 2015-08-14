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
    A test scheduler plugin meant to be used in tests, the main feature of
    the plugin is the fact that you can define the what the plan trigger
    times will be through the use of an event file, the event file itself is
    listed under constraints in the destiny section of the fate book
"""

import random
from simoorg.plugins.scheduler.BaseScheduler import BaseScheduler


class TestScheduler(BaseScheduler):
    """
        Test scheduler class
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
        event_times = []
        with open(self.get_constraints()['event_file']) as ev_fd:
            for event_str in ev_fd.readlines():
                event_times.append(long(float(event_str.strip())))
        self.generate_plan(event_times)

    def generate_plan(self, event_times):
        """
            Generates a plan containing trigger time provided by the event file
            Args:
                event_times - a list containing the event times listed
                    in the event file
            Return:
                None
            Raise:
                None
        """
        for event in event_times:
            failure_list = list(self.get_failures().keys())
            failure_name = random.choice(failure_list)
            self.plan.append({failure_name: event})
