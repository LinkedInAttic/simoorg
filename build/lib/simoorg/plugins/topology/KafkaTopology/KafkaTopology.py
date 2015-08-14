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
    This class is responsible for loading the Topology
    plan of the cluster
"""
from simoorg.plugins.topology.TopologyBuilder import TopologyBuilder
from simoorg.Logger import Logger
import yaml
import random

from simoorg.plugins.topology.KafkaTopology.MetaData import MetaData
from kazoo.client import KazooClient
from simoorg.plugins.common.ZKUtil import KafkaZkHelper


PARTITION = "Partition"
TOPIC = "Topic"


class KafkaTopology(TopologyBuilder):
    """
        Topology class for kafka
    """
    def __init__(self, input_file, logger_config):
        """
            Init function for the KafkaTopology class
            Args:
                input_file - file containing information about
                             kind of hosts on which the failure must
                             be induced , zookeeper paths and zookeeper
                             connection
                logger_config - configuration for logger
            Return:
                None
            Raise:
                None
        """
        TopologyBuilder.__init__(self, input_file, logger_config)

        with open(self.input_file, 'r') as file_descr:
            doc = yaml.load(file_descr)

        # Declaring the config variables
        self.plan = []
        self.zookeeper = None
        self.zookeeper_paths = None
        self.kafka_host_resolution = None
        self.resolved_topology = []

        # initializing Logger
        self.logger_instance = Logger(self.logger_config)

        # Reading from the config
        for key, val in doc.iteritems():
            setattr(self, key, val)

        # setup the zookeeper client
        if self.zookeeper:
            zook = KazooClient(hosts=self.zookeeper.get("host"),
                               read_only=True)
            zook.start()

            # read ZK Paths into a dictionary
            zk_paths = {}
            if self.zookeeper_paths:
                for path_type, path in self.zookeeper_paths.items():
                    zk_paths[path_type] = path
            # create zk_helper object
            helper = KafkaZkHelper(zook, zk_paths)
            self.helper = helper
        self.generate_plan()

    def get_plan(self):
        """
            Get the plan that indicates the kind of nodes to induce failure on
            Args:
                None
            Return:
                topology plan
        """
        return self.plan

    def generate_plan(self):
        """
            Generate a plan indicating the type of nodes for failure induction
            Args:
                None
            Return:
                None
        """
        if self.kafka_host_resolution:
            for key, value in self.kafka_host_resolution.items():
                for node_type, node_data in value.items():
                    metadata = MetaData(node_type)
                    if len(node_data) != 0:
                        # check if "Topic" is specified
                        if TOPIC in node_data:
                            topic = node_data[TOPIC]
                            metadata.set_topic(topic)
                            # check if "Partition" is specified
                            if PARTITION in node_data:
                                partition = node_data[PARTITION]
                                metadata.set_partition(partition)
                    self.plan.append(metadata)

    def get_random_node(self):
        """
            Get a hostname of broker to induce failure on
            Args:
                None
            Return:
                hostname
        """
        failure = random.choice(self.plan)

        if failure.get_node_type() == "RANDOM_BROKER":
            if failure.get_topic() is None:
                topic = self.helper.get_topic()
                partition = self.helper.get_partition(topic)
                self.logger_instance.logit("INFO",
                                           "Selecting a random broker"
                                           " for a Random Topic : {0},"
                                           " Random Partition : {1}"
                                           .format(topic, partition),
                                           log_level="VERBOSE")
                isr_list = self.helper.get_isr(topic, partition)
                return random.choice(isr_list)
            else:
                topic = failure.get_topic()
                # check if the partition is specified for the topic
                if failure.get_partition() is not None:
                    partition = failure.get_partition()
                    self.logger_instance.logit("INFO",
                                               "Selecting a random broker"
                                               " for a Specified Topic : {0},"
                                               " Specified Partition : {1}"
                                               .format(topic, partition),
                                               log_level="VERBOSE")
                else:
                    # get a random partition
                    partition = self.helper.get_partition(topic)
                    self.logger_instance.logit("INFO",
                                               "Selecting a random broker"
                                               " for a Specified Topic : {0},"
                                               " Random Partition : {1}"
                                               .format(topic, partition),
                                               log_level="VERBOSE")
                isr_list = self.helper.get_isr(topic, partition)
                return random.choice(isr_list)

        elif failure.get_node_type() == "RANDOM_LEADER":
            topic = self.helper.get_topic()
            partition = self.helper.get_partition(topic)
            self.logger_instance.logit("INFO",
                                       "Selecting a Leader for a"
                                       " Random Topic : {0},"
                                       " Random Partition : {1}"
                                       .format(topic, partition),
                                       log_level="VERBOSE")
            return self.helper.get_leader(topic, partition)

        elif failure.get_node_type() == "LEADER":
            topic = failure.get_topic()
            # check if the partition is specified for the topic
            if failure.get_partition() is not None:
                partition = failure.get_partition()
                self.logger_instance.logit("INFO",
                                           "Selecting a Leader"
                                           " for a Specified Topic"
                                           " : {0}, Specified Partition"
                                           " : {1}".format(topic, partition),
                                           log_level="VERBOSE")
            else:
                # get a random partition
                partition = self.helper.get_partition(topic)
                self.logger_instance.logit("INFO",
                                           "Selecting a Leader"
                                           " for a Specified Topic"
                                           " : {0}, Random Partition"
                                           " : {1}".format(topic, partition),
                                           log_level="VERBOSE")
            return self.helper.get_leader(topic, partition)

        elif failure.get_node_type() == "CONTROLLER":
            self.logger_instance.logit("INFO",
                                       "Selecting Controller",
                                       log_level="VERBOSE")
            return self.helper.get_controller()

    def populate_topology(self):
        self.resolved_topology = []

    def get_all_nodes(self):
        """
           Get the hostnames of all brokers in the cluster
           Args:
               None
           Return:
               hostnames of all brokers

       """
        return self.helper.get_all_hosts()
