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
    This module is responsibiling for journaling the current status of
    atropos (Currently a stub)
"""


class Journal(object):
    """
        The Journal class
    """
    def __init__(self, impact, logger_instance=None, verbose=False,
                 debug=False):
        """
            Init function for joural class
            Args:
                impact - the maximum impact limit
                logger_instance - an instance of logger class
                verbose - verbosity flag
                debug - debug flag
            Return:
                None
            Raise:
                None
        """
        self.verbose = verbose
        self.debug = debug
        self.impacted_total = 0
        self.impact_limits = impact
        self.logger_instance = logger_instance

    def cast_impact(self, target):
        """
            Increment the current impact of the target by one
            Args:
                target - The current target on which atropos is acting
            Return:
                None
            Raise:
                None
        """
        self.logger_instance.logit("INFO",
                                   "cast_impact(): {0}".format(target),
                                   log_level="DEBUG")

        self.impacted_total = self.impacted_total + 1
        self.logger_instance.logit("INFO",
                                   "Bumped up impacted nodes: {0}".
                                   format(self.impacted_total),
                                   log_level="DEBUG")

    def revert_impact(self, target):
        """
            Decrement the current impact of the target by one
            Args:
                target - The current target on which atropos is acting
            Return:
                None
            Raise:
                None
        """
        self.impacted_total = self.impacted_total - 1
        self.logger_instance.logit("INFO",
                                   "Reverted impact. Current impact: total "
                                   "({0})".format(self.impacted_total),
                                   log_level="DEBUG")

    def get_total_impacted(self):
        """
            Returns the current impact level
            Args:
                None
            Return:
                self.impacted_total - current impact level
            Raise:
                None
        """
        return self.impacted_total

    def is_total_impact_allowed(self):
        """
            Check if the current impact is at acceptable levels
            Args:
                None
            Return:
                True if the current level is below impact level else False
            Raise
                None
        """
        self.logger_instance.logit("INFO",
                                   "Impacted total: {0} (limit: {1})"
                                   .format(self.get_total_impacted(),
                                           self.get_total_impact_limit()),
                                   log_level="DEBUG")
        if self.get_total_impacted() + 1 > self.get_total_impact_limit():
            return False
        else:
            return True

    def get_total_impact_limit(self):
        """
            Fetch the total impact limit
            Args:
                None
            Return:
                self.impact_limits['total_maximum'] - the impact limit
            Raise
                None

        """
        return self.impact_limits['total_maximum']
