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
    A topology plugin for test purpose, Similar to static topology expect
    that we can induce the plugin to fail through a key in the config file
"""
from simoorg.plugins.topology.TopologyBuilder import TopologyBuilder
import yaml
import random

CONFIG_KEY = 'config'
SKIP_NODE_FLAG = 'skip_node'


class TestTopology(TopologyBuilder):
    """
        Test topology class
    """
    def __init__(self, input_file, logger_config):
        """
            The init function, reads the server list from the config file
            Args:
                input_file - config file path
                logger_config - configuration for logger
            Return:
                None
            Raise:
                None
        """
        TopologyBuilder.__init__(self, input_file, logger_config)
        self.resolved_topology = []
        self.topology = None
        with open(self.input_file, 'r') as file_desc:
            doc = yaml.load(file_desc)

        for key, val in doc.iteritems():
            setattr(self, key, val)

        self.populate_topology()

    def get_all_nodes(self):
        """
            Return the list of all the nodes
            Args:
                None
            Return:
                List of all the nodes
            Raise:
                None
        """
        return self.resolved_topology

    def get_random_node(self):
        """
            Return a random nodes from the full list
            Args:
                None
            Return:
                if SKIP_NODE_FLAG is set it returns False else returns
                a random node
            Raise:
                None
        """
        if CONFIG_KEY in self.topology:
            if SKIP_NODE_FLAG in self.topology[CONFIG_KEY] and \
                    self.topology[CONFIG_KEY][SKIP_NODE_FLAG] is True:
                return False
        return random.choice(self.resolved_topology)

    def populate_topology(self):
        """
            Read the node list from the config file
            Args:
                None
            Return:
                None
            Raise:
                None
        """
        for node in self.topology['nodes']:
            self.resolved_topology.append(node)
