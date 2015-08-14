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
    This class is responsible for checking if the kafka cluster is healthy
    and return true or false accordingly
"""
import os
from kazoo.client import KazooClient
import yaml
from simoorg.plugins.common.ZKUtil import KafkaZkHelper
from simoorg.plugins.healthcheck.HealthCheck import HealthCheck


class KafkaHealthCheck(HealthCheck):
    """
        Kafka Healthcheck class
    """
    def __init__(self, shell_script, plugin_config):
        """
            Init function for the KafkaHealthCheck class
            Args:
                shell_script - script that is used to check the health
                of the cluster
            Return:
                None
            Raise:
                None
        """
        HealthCheck.__init__(self, shell_script, plugin_config)
        self.config_file = plugin_config['topology_config']
        with open(self.config_file, 'r') as file_desc:
            doc = yaml.load(file_desc)

        # Declare the config variables
        self.zookeeper = None
        self.zookeeper_paths = None
        self.kafka_host_resolution = None

        for key, val in doc.iteritems():
            setattr(self, key, val)

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

    def check(self):
        """
          Checks the health of the cluster
          Args:
              None
          Return:
              True or False
          Raise:
              None
        """
        brokers = self.helper.get_all_hosts()
        for broker in brokers:
            #  the shell script takes a host broker as an input
            status = os.system(str(self.script) + " " +
                               str(broker) + " > /dev/null")
            # print("status : " + str(status) + " for broker : " + str(broker))
            if status != 0:
                return False
        return True
