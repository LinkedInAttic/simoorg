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
    This class represents metadata about a failure scenario in kafka
"""


class MetaData(object):
    """
        The metadata class
    """
    def __init__(self, broker_type):
        """
            Init function for the MetaData class
            Args:
                broker_type - The type of kafka node(broker)
            Return:
                None
            Raise:
                None
        """
        self.broker_type = broker_type
        self.partition = None
        self.topic = None

    def __str__(self):
        """
            Get the metaData about the failure
            Return:
                  metadata about the failure
            Raise:
                  None
        """
        if self.topic is None:
            return str(self.broker_type)
        else:
            return (str(self.broker_type) + " for " +
                    str(self.topic) + "/" + str(self.partition))

    def get_partition(self):
        """
            Get the partition id if specified in the failure
            Return:
                  partition id
            Raise:
                  None
        """
        return self.partition

    def get_topic(self):
        """
            Get the topic if specified in the failure
            Return:
                  topic
            Raise:
                  None
        """
        return self.topic

    def set_topic(self, topic):
        """
            Set the topic if specified in the failure
            Return:
                  None
            Raise:
                  None
        """
        self.topic = topic

    def set_partition(self, partition):
        """
            Set the partition id if specified in the failure
            Return:
                  None
            Raise:
                  None
        """
        self.partition = partition

    def get_node_type(self):
        """
            Get the kind of kafka node (broker) specified in the failure
            Return:
                  None
            Raise:
                  None
        """
        return self.broker_type
