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
    This class is responsible for handling communication with Zookeeper.
    It has helper functions to get the info that is required by Simoorg
    to induce failures into kafka.
"""
import json
import random

DECODER = "utf-8"
PARTITIONS = "partitions"
BROKER_IDS = "broker_ids"
BROKER_TOPICS = "broker_topics"
TOPIC_CONFIG = "topic_config"
CONTROLLER = "controller"
BROKER_SEQUENCE_ID = "broker_sequence_id"
STATE = "/state"


class KafkaZkHelper(object):
    """
        ZkHelper class for Kafka plugins
    """
    def __init__(self, zk_client, zk_paths):
        """
            Init function for the KafkaZkHelper class
            Args:
                zk_client - A client to talk to Zookeeper
                zk_paths - All paths in Zookeeper where the info regarding
                kafka cluster is stored.
            Return:
                None
            Raise:
                None
        """
        self.zk_client = zk_client
        self.zk_paths = zk_paths

    def get_controller(self):
        """
            Get the hostname of the controller
            Return:
                  hostname of the controller
            Raise:
                  None
        """
        zook = self.zk_client

        # if zook.exists(CONTROLLER_PATH):
        controller_path = self.zk_paths[CONTROLLER]
        if zook.exists(controller_path):
            # data, stat = zook.get(CONTROLLER_PATH)
            data, stat = zook.get(controller_path)
            # data is of the form : {"version":1,"brokerid":874,
            # "timestamp":"1425584134783"}
            data_values = data.decode(DECODER).split(',')
            broker_id = data_values[1].split(':')[1]

            # get hostname of the broker from the Id
            return self.get_host(broker_id)

    def get_host(self, broker_id):
        """
            Get hostname of the broker with id = broker_id
            Args:
                broker_id - An identifier that identifies the broker
                uniquely in the Zookeeper
            Return:
                Hostname
            Raise:
                None
        """
        zook = self.zk_client
        broker_id_path = self.zk_paths[BROKER_IDS]
        # broker_path = BROKER_IDS_PATH + "/" + str(broker_id)
        broker_path = broker_id_path + "/" + str(broker_id)

        if zook.exists(broker_path):
            data, stat = zook.get(broker_path)
            # data is of the form : {"jmx_port":-1,"timestamp":"1425582849624",
            # "host":"hostname","version":1,"port":10251}
            return json.loads(data)["host"]

    def get_topics(self):
        """
            Get a list of all topics
            Return:
                  list of topic names
            Raise:
                  None
        """
        zook = self.zk_client
        broker_topics_path = self.zk_paths[BROKER_TOPICS]

        if zook.exists(broker_topics_path):
            topics = zook.get_children(broker_topics_path)

            return topics

    def get_number_of_partitions(self, topic):
        """
            Get the number of partitions for the topic
            Args:
                topic - topic name
            Return:
                number of partitions
            Raise:
                None
        """
        zook = self.zk_client
        broker_topics_path = self.zk_paths[BROKER_TOPICS]
        path = broker_topics_path + "/" + str(topic) + "/" + PARTITIONS

        if zook.exists(path):
            partitions = zook.get_children(path)

            return partitions.__len__()

    def get_leader(self, topic, partition):
        """
            Get host name of Leader for topic and partition
            Args:
                topic - topic name
                partition - partition id
            Return:
                hostname
            Raise:
                None
        """
        zook = self.zk_client
        broker_topics_path = self.zk_paths[BROKER_TOPICS]
        path = (broker_topics_path + "/" + str(topic) + "/" +
                PARTITIONS + "/" + str(partition) + STATE)

        if zook.exists(path):
            data, stat = zook.get(path)
            # data is of the form : data : {"controller_epoch":32,
            # "leader":873,"version":1,"leader_epoch":18,"isr":[873,1272]}
            data_values = data.decode(DECODER).split(',')
            leader_id = data_values[1].split(':')[1]

            return self.get_host(leader_id)

    def get_isr(self, topic, partition):
        """
            Get in-sync replicas for topic and partition
            Args:
                topic - topic name
                partition - partition id
            Return:
                list of hostname
            Raise:
                None
       """
        zook = self.zk_client
        broker_topics_path = self.zk_paths[BROKER_TOPICS]
        path = (broker_topics_path + "/" + str(topic) +
                "/" + PARTITIONS + "/" + str(partition) + STATE)

        if zook.exists(path):
            data, stat = zook.get(path)
            # data is of the form : data : {"controller_epoch":32,
            # "leader":873,"version":1,"leader_epoch":18,"isr":[873,1272]}
            data_values = data.decode(DECODER).split(':')
            isr = str(data_values[5])
            length = isr.__len__()
            broker_list = isr[1:length - 2].split(',')
            isr_list = []

            for broker in broker_list:
                isr_list.append(self.get_host(broker))

            return isr_list

    def get_topic(self):
        """
            Get an existing topic name
            Args:
                None
            Return:
                topic name
            Raise:
                None
       """
        topics = self.get_topics()

        return random.choice(topics)

    def get_partition(self, topic):
        """
            Get partition for a topic
            Args:
                topic - topic name
            Return:
                partition id
            Raise:
                None
       """
        zook = self.zk_client
        broker_topics_path = self.zk_paths[BROKER_TOPICS]
        path = broker_topics_path + "/" + str(topic) + "/" + PARTITIONS

        if zook.exists(path):
            partitions = zook.get_children(path)
            return random.choice(partitions)

    def get_all_hosts(self):
        """
            Get list of all hosts in cluster
            Args:
                None
            Return:
                list of hostnames
            Raise:
                None
       """
        zook = self.zk_client
        broker_id_path = self.zk_paths[BROKER_IDS]

        if zook.exists(broker_id_path):
            broker_ids = zook.get_children(broker_id_path)
            brokers = []
            for broker_id in broker_ids:
                brokers.append(self.get_host(broker_id))
            return brokers
