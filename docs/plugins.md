#How to create a new plugin:
In simoorg, we have four types of pluggable component namely Topology, Healthcheck, Scheduler and Handler. Even though we ship a few standard plugins of each category, we understand that it will not meet the requirements of all the potential customers. So one our guiding design principles has been to ensure that system is easily extensible. So in this document, we will be detailing the various steps to be taken to create a new plugin. 

##Topology
First we start with the the topology plugin. Simoorg relies on the topology plugin to retrieve information about the individual nodes of a service. The arguments that are passed to any topology plugin is 
*Args:*
input_file - the config file to be read by the plugin
*Base Class:*
    simoorg.plugins.topology.TopologyBuilder
*Methods:*

* *init* : Read the config file and load the topology in memory 

    return: None

* *get_random_node()* : Get hostname of random node from the cluster

    return: String

* *get_all_nodes()*: Get hostnames of all nodes in the cluster

    return: List of strings

*Path:*
    simoorg.plugins.topology.<topology name>.<topology name>
*Example:*
Let's consider an example of KafkaTopology plugin : 
* KafkaTopology plugin implements TopologyBuilder class
    * It takes in a config file that gives information about the Zookeeper connection url,
            the zookeeper paths specific to kafka and kafka_host_resolution. An example config      
                file looks like this : 
```
zookeeper:
    host: "ZOOKEEPER_URL"

zookeeper_paths:
    broker_ids: "/brokers/ids"
    broker_topics: "/brokers/topics"
    topic_config: "/config/topics"
    controller: "/controller"
    broker_sequence_id:  "/brokers/seqid”

kafka_host_resolution:
        node_type_1:
            CONTROLLER: false
        node_type_2:
            LEADER: {Topic: "Topic1"}
        node_type_3:
            RANDOM_BROKER: {Topic: "Topic2"}
        node_type_4:
            RANDOM_BROKER: {Topic: "Topic1", Partition: 0}
        node_type_5:
            RANDOM_LEADER: false
        node_type_6:
            RANDOM_BROKER: false
        node_type_7:
            RANDOM_BROKER: {Topic: "Topic3"} 
        
````
* This class reads the config file and loads it in memory data structure. At the    
                 time of failure induction, it returns a random host (broker host name) to the    
                 caller method. The selection of this host depends upon the kind of node selected      
                 (node type) for failure induction.

In the above Kafka Topology plugin example, it is possible to modify the config file and write your own logic to populate the topology and get random hosts. This model is designed in a way that users can fit their needs as per their cluster environments.

Path to KafkaTopology plugin : simoorg.plugins.topology.KafkaTopology.KafkaTopology
 

##HealthCheck : 
Healthcheck plugin is responsible for checking the health of the target cluster.
*Args:*
script - Any external script to be used by the plugin
plugin_config - The plugin specific configs
*Base Class:*
    simoorg.plugins.healthcheck.HealthCheck

*Methods:*

* *check()* : Executes the shell script and returns if the cluster is healthy or otherwise.

    return: Boolean

*Path:*
    simoorg.plugins.healthcheck.<healthcheck name>.<healthcheck name>

Let’s take an example of *KafkaHealthCheck plugin* :
    * KafkaHealthCheck plugin implements the HealthCheck class 
    * It accepts a shell script and a config file. The config file here is the Topology config file that is used for loading the kafka topology as described in the Topology section above.
    * It implements the check() method that checks at runtime if kafka cluster on which    
                failure is to be induced is healthy and returns true if it is, else false otherwise.
        
 If users want to use a shell script, that will do the HealthCheck on the target cluster, they can use the DefaultHealtCheck plugin in the fate book and pass it the customized shell_script. The DefaultHealthCheck plugin like KafkaHealthCheck plugin implements the check() method that will return true if the target cluster is healthy, else false otherwise.

##Scheduler:
The Scheduler plugin is responsible for creating the plans that an atropos process will be following. A plan as received by atropos should be a list of single item dictionaries, where the dictionary has the failure name as the key and the trigger time as the value.
*Args:*
    destiny_object - A dictionary containing the contents of the plugin key of the destiny   
              section of the fate book
*Base Class:*
    simoorg.plugins.scheduler.BaseScheduler

*Methods:*

* *get_plan* : Return the plan atropos should follow

    return: list of dictionary

*Path:*
    simoorg.plugins.scheduler.<scheduler name>.<scheduler name>
*Example:*
Let us consider the example of NonDeterministicScheduler plugin:
* It implements the class BaseScheduler
* It accepts the required config values through the dictionary object, and during the init process call it computes a complete plan with the given constraints specified in the destiny object
* For each get_plan call it simply returns the plan that has already been calculated

There are a number of fully implemented methods in BaseScheduler, that you can use in your implementation to better access the destiny object.

##Handler
Handler is the plugin responsible for actually inducing and reverting the failures
*Args:*
config_dir - This is the path to the simoorg config directory
target - This is the target of the failures (normally a host name)
logger_instance - An instance of the logging class, to be used for any logging
verbose - A verbosity flag for logging output
*Base Class:*
    simoorg.plugins.handler.BaseHandler
*Methods:*

* *authenticate* : Should perform any necessary authentication and connection, for the handler to start working

    return: None
* *execute_command* :  Responsible for actually performing a given command, the command could correspond to either a failure or a revert of a failure

    return: A tuple of status, command output (string) and error messages (string)

*Path:*
    simoorg.plugins.handler.<handler name>.<handler name>

*Example:*
Let us consider the example of ShellScriptHandler  plugin:
* it implements the class BaseHandler
* The plugin expects the config file to be present in the location plugins/handler/ShellScriptHandler.yaml (relative to the simoorg config directory root)
* When authenticate function is called, the plugin creates a paramiko client object and connects to the target node
* a call to execute_command in turn calls exec_command method in  the underlying client object and returns the status, stdout outpu and stderr output

