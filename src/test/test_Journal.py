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
import yaml

import simoorg.Journal as Journal
import simoorg.Logger as Logger

FATEBOOK_DIR = (os.path.dirname(os.path.realpath(__file__)) +
                "/unittest_configs/journal_configs/fate_books/")


class TestJournal(unittest.TestCase):
    """
        Test basic functionalities of Journal module
    """
    def setUp(self):
        """
            Create a journal object from the standard fatebook
        """
        fate_book_file = os.listdir(FATEBOOK_DIR)[0]
        with open(FATEBOOK_DIR + fate_book_file) as c_fd:
            self.config = yaml.load(c_fd)
        self.logger_obj = Logger.Logger(self.config['logger'])
        self.test_impact_limit = self.config['impact_limits']
        self.journal_obj = Journal.Journal(self.test_impact_limit,
                                           self.logger_obj)

    def tearDown(self):
        pass

    def test_journaling(self):
        """
            Test impact cast, impact revert and total allowed impact
        """
        target_string = ""
        # Test casting and limit checks
        for index in range(1, self.test_impact_limit['total_maximum'] + 2):
            self.journal_obj.cast_impact(target_string)
            self.assertEqual(self.journal_obj.get_total_impacted(), index)
            if index < self.test_impact_limit['total_maximum']:
                self.assert_(self.journal_obj.is_total_impact_allowed())
            else:
                self.assert_(not self.journal_obj.is_total_impact_allowed())

        # Test the revert function
        self.journal_obj.revert_impact(target_string)
        self.assertEqual(self.journal_obj.get_total_impacted(),
                         self.test_impact_limit['total_maximum'])


if __name__ == '__main__':
    unittest.main()
