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
    The interface for all the scheduler plugins, all scheduler plugins should
    inherit this class
"""


class BaseScheduler(object):
    """
        BaseScheduler class
    """

    def __init__(self, destiny_object):
        """
            Init function for the scheduler class
        """
        self.plan = []
        self.destiny_object = destiny_object

    def generate_plan(self):
        """
            The main function of any scheduler plugin, this function
            creates a valid plan. A plan is a list of dictionary,
            where each element maps a failure name to a trigger time
        """
        pass

    def get_destiny_object(self):
        """
            Fetches the destiny config
            Args:
                None
            Return:
                self.destiny_object - destiny section of fate book
            Raise:
                None
        """
        return self.destiny_object

    def get_failures(self):
        """
            Fetches the failure from the destiny config
            Args:
                None
            Return:
                failures listed in destiny section of fate book
            Raise:
                None
        """
        return self.get_destiny_object()['failures']

    def get_constraints(self):
        """
            Fetches the constraints from the destiny config
            Args:
                None
            Return:
                constraint section in destiny section of fate book
            Raise:
                None
        """
        return self.get_destiny_object()['constraints']

    def get_count_of_failures(self):
        """
            Returns the count of failures listed in destiny
            Args:
                None
            Return:
                count of failures listed in destiny section of fate book
            Raise:
                None
        """
        return len(self.get_failures())

    def get_min_gap_between_failures(self):
        """
            Fetches the min_gap_between_failures listed in constraints from the
            destiny config
            Args:
                None
            Return:
                min_gap_between_failures listed in constraint section in
                destiny section of fate book
            Raise:
                None

        """
        return self.get_constraints()['min_gap_between_failures']

    def get_max_gap_between_failures(self):
        """
            Fetches the max_gap_between_failures listed in constraints from
            the destiny config
            Args:
                None
            Return:
                min_gap_between_failures listed in constraint section in
                destiny section of fate book
            Raise:
                None
        """
        return self.get_constraints()['max_gap_between_failures']

    def get_total_run_duration(self):
        """
            Fetches the total_run_duration listed in constraints from the
            destiny config
            Args:
                None
            Return:
                total_run_duration listed in constraint section in destiny
                section of fate book
            Raise:
                None
        """
        return self.get_constraints()['total_run_duration']

    def get_plan(self):
        """
            Returns the plan generated at the beginning
            Args:
                None
            Return:
                the plan generated at object creation
            Raise:
                None

        """
        return self.plan
