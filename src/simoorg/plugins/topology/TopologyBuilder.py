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
    The Topology builder interface
"""


class TopologyBuilder(object):
    """
        All topology plugins should inherit this class
    """

    def __init__(self, input_file, logger_config):
        """
            Init function of the class
            Args:
                input_file - file containing information about the
                             topology of the nodes to induce failure on
                logger_config - log configuration
            Return:
                None
            Raise:
                None
        """
        self.input_file = input_file
        self.logger_config = logger_config

    def populate_topology(self):
        """
            Loads the topology
            Args:
                None
            Return:
                None
            Raise:
                None
        """
        self.populate_topology()

    def get_random_node(self):
        """
            Get hostname of a random node in cluster
            Args:
                None
            Return:
                hostname
            Raise:
                None

        """
        pass

    def get_all_nodes(self):
        """
            Get hostnames of all nodes in the cluster
            Args:
                None
            Return:
                hostnames
            Raise:
                None
        """
        self.get_all_nodes()
