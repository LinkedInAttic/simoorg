#SIMOORG - CONFIG FILES
This document provides a quick overview of the various configuration files currently used by Simoorg. Simoorg expects path to the config directory as the first console argument and a standard simoorg config directory should have the following structure
```
configs/
├── api.yaml
├── fate_books
│   └── service1.yaml
└── plugins
    ├── handler
    │   └── ShellScriptHandler
    │       └── ShellScriptHandler.yaml
    └── topology
        ├── kafka
        │   └── topo.yaml
        └── static
            └── topo.yaml
```
Next we will go through each one of these configurations in details


##API CONFIG api.yaml
This is our main api config file, this needs to be passed to both Moirai process and Api server as well. This is a yaml file, which is mainly used to store input named pipe location for Moirai process. It may be used to contain more config items in the future as the api functionalities are extended.


```yaml
# file: configs/api.yaml

moirai_input_fifo: '/tmp/moirai.fifo'

```

##FATE BOOKS fate_books/*
Fate Book is a collection of configurations used to to describe failures to be induced against your service. Each service should have a unique Fate Book associated with it. Upon starting up, Simoorg scans configs/fate_books subdirectory for files with .yaml extension. Each qualified file is treated as Fate Book and used to instantiate observers that are watching and executing failures based on the conditions defined in a Fate Book.
Fate Books are human readable and can be edited using a conventional editor.

###Fate Book Format
Format of the Fate Books are chosen to be YAML for its simplicity yet being capable to formally describe nested objects in a human readable form.

###Fate Book Contents
Each service that needs to receive failure commands from the Failure Inducer, has to have a Fate Book associated with it. Below there is a sample Fate Book for an example service (called test-service)

```yaml
# file: configs/fate_books/test-service.yaml

# Service name listed in each fate book should be unique, else it results in simoorg to exit
service: test-service

# Topology section
# plugins: StaticTopology,, KafkaTopology
# default is set to StaticTopology if no plugin is sepcified
topology:
  topology_plugin: StaticTopology
  topology_config: plugins/topology/static/topo.yaml

# #
# Logging configuration
# #
logger:
  # Set this to the path where the logfile will be created. This must be an existing full path including the filename.
  # The file name should be present and writable by the user under which the failure inducer runs
  path: /tmp/test-service.log
  # Set this to True if you want to output logs to stdout. This is a complimentary logging and does not replace logging to the file.
  console: True
  # Loglevel can be one of the following: WARNING, INFO, VERBOSE, DEBUG
  log_level: VERBOSE


impact_limits:
  total_maximum: 1

##
# Healthcheck configuration. Healthchecks are run before inducing failures
##

healthcheck:
  # plugin can be set to either of: DefaultHealthCheck, KafkaHealthCheck
  plugin: DefaultHealthCheck
  # coordinate to the healthcheck script. Required for default plugin
  coordinate: /tmp/healthCheck.sh
  plugin_configs: None

destiny:
  scheduler_plugin: NonDeterministicScheduler
  NonDeterministicScheduler:
    # global constraints for all failures. Unit is minutes.
    constraints:
      min_gap_between_failures: 1
      max_gap_between_failures: 2
      total_run_duration: 5
    failures:
      test_failure:
        timeout: 5

failures:
  - name: test_failure
    sudo_user: test
    induce_handler:
      type: TestHandler
      coordinate: /tmp/atropos_unittest
      arguments: ['failure']
    restore_handler:
      type: TestHandler
      coordinate: /tmp/atropos_unittest
      arguments: ['revert']
    wait_seconds: 5


```

###Fate Book Sections
Next we take a closer look at the various sections of the fatebook


####service:
Required : Yes
Default: None
The value for service key is used to uniquely identify the service being specified in that fate book. Simoorg enforces that no two fate books can have the same value for the service key.

####topology:
Required : Yes
All values related to topology plugin should be stored under this section. We expect only two values under this key, they are as follows

Key name | Description | Mandatory | Default |
------------ | ----------- |-------|-------|
topology_plugin| Name of the topology plugin| Yes | StaticTopology|
topology_config| plugin specific config file| Yes | None|

topology_plugin : 
The name of the topology plugin should be same as plugin class (please check the plugin development doc to better understand the naming requirements)
topology_config :  
Any plugin specific values should be added to this section.Simoorg expects the config to be contained inside the main config directory and the path provided here is relative to the config root

####logger
Required : Yes

Contains the logging related information, we expect it to contain the following keys

Key name | Description | Mandatory | Default |
------------ | ----------- |-------|-------|
path| path to the log file| Yes | None|
console | Flag for console logging | Yes | False|
log_level | the level of logging required | Yes | INFO |


path : - 
The path to the log file. Simoorg expects absolute path to the file here. Simoorg currently does not support any log rotation functionality

console :  
This key is used to enable console logging
log_level :  
Simoorg expects the value for this key to be "WARNING", "INFO", "VERBOSE" or "DEBUG"

####healthcheck
Required : Yes

In this section we list all of our health check related configs. the various keys we expect in this section are as follows

Key name | Description | Mandatory | Default |
------------ | ----------- |-------|-------|
plugin | the name of the healthcheck plugin| Yes | None|
coordinate | the coordinate for the healthcheck plugin | Yes | None|
plugin_config| any plugin specific config| No| None|

plugin : 
The name of the healthcheck plugin should be same as plugin class (please check the plugin development doc to better understand the naming requirements)
coordinate : - 
Depends on what plugin you use. In case of Defaulthealthcheck this is the absolute path to the healthcheck script which will be executed
plugin_config :   
Place to specify any plugin specific configurations, Currently is None Default Health check plugin.

####destiny
Required : Yes

This section is responsible for listing all the scheduler specific information. We expect the following keys to be present under the destiny section

Key name | Description | Mandatory | Default |
------------ | ----------- |-------|-------|
scheduler_plugin| the name of the scheduler plugin| Yes | None|
"scheduler_plugin"| this key should have the same name as the value of previous key| Yes | None|
"scheduler_plugin"->constraints | This key lists the constraints that the scheduler should follow| Yes | None|
"scheduler_plugin"->constraints->min_gap_between_failures | Minimum gap between two failure | Yes | None|
"scheduler_plugin"->constraints->max_gap_between_failures | Maximum gap between two failure | Yes | None|
"scheduler_plugin"->constraints->total_run_duration | total run duration of simoorg instance | Yes | None|
"scheduler_plugin"->failures | This key lists the failures that the scheduler should use| Yes | None|
"scheduler_plugin"->failures->"failure_name" | provides the information for a specific failure "failure_name"| Yes | None|
"scheduler_plugin"->failures->"failure_name"->timeout | timeout for the failure "failure_name"| Yes | None|

Please check the plugins document to better understand the plugin names. In addition to the keys listed above, the "scheduler_plugin" key could also contain any plugin specific config, also the failure name given in "scheduler_plugin"->failures->"failure_name" should have a valid failure definition in the failures sections of the fate book

####failures
This section includes a list of failure definition and each item in the list should contain the following keys

Key name | Description | Mandatory | Default |
------------ | ----------- |-------|-------|
name | failure name|Yes | None|
induce_handler | configurations for failure induction | Yes | None |
induce_handler->type | The handler name to be used for failure induction | Yes | None |
induce_handler->coordinate | The coordinate against which the handler should be run | Yes | None |
induce_handler->args | The args passed to the handler during failure induction | Yes | None |
restore_handler | configurations for failure induction | Yes | None |
restore_handler->type | The handler name to be used for reverting the failure | Yes | None |
restore_handler->coordinate | The coordinate against which the revert handler should be run | Yes | None |
restor_handler->args | The args passed to the handler during failure revert | Yes | None |
wait_seconds |  The wait seconds between failure induction and failure revert | Yes | None |


###Plugin Configs
=================
These are config files that may be specific to some plugin. Since these configs are closely related to the plugins, we will mainly be covering configs for the plugins that are shipped out of the box.

####Handler Configs

For any handler plugin (lets assume the handler name is test_handler), we expect the config to be located in the path config/plugins/handler/test_handler/test_handler.yaml, the config contents greatly depends on the specific handler.The ShellScriptHandler plugin file for example,  looks like this :

```
# file: config/plugins/handler/ShellScriptHandler/ShellScriptHandler.yaml
host_key_path: ~/.ssh/known_hosts
```

####Topology Configs
The location of the topology plugin is usually provided under the topology section of the fate book. Again the content of this configuration file depends heavily on the specific plugin.But here are two sample configuration files for StaticTopology and KafkaTopology plugins respectively. In StaticTopology we list all the servers present in the service under the key node
```
# file: configs/plugins/topology/static/topo.yaml 
topology:
  nodes: ['test_node_1', 'test_node_2']
```
Kafka topology plugin returns the list of different types of brokers on which failures can be induced. Topology config for kafka lists the different types of brokers on which failures can be induced. The Topology config file for kafka also has other information about the cluster like the Zookeeper Connection Url and the Zookeeper paths that store metadata about the cluster.

The Topology config file has 3 parts :
* Zookeeper Url - Connection url that can used to establish a zookeeper connection
* Zookeeper paths - Store meta information like topics, partitions, consumers etc.. about the cluster
* Kafka host resolution - This section specifies the different groups of node on which the failure can be induced. Please check the design doc to understand the various types of nodes we can use here.

Below is an example of Kafka Topology file
```
# file: configs/plugins/topology/kafka/topo.yaml 
zookeeper:
    host: "kafka-zookeeper-connection url"

zookeeper_paths:
    broker_ids: "/brokers/ids"
    broker_topics: "/brokers/topics"
    topic_config: "/config/topics"
    controller: "/controller"
    broker_sequence_id:  "/brokers/seqid"

kafka_host_resolution:
    node_type_1:
        CONTROLLER: false 
    node_type_2:
        RANDOM_BROKER: false
    node_type_3:
        RANDOM_BROKER: {Topic: "Topic1", Partition: 0}
    node_type_4:
        RANDOM_BROKER: {Topic: "Topic2"}
    node_type_5:
        RANDOM_LEADER: false
    node_type_6:
        LEADER: {Topic: "Topic1", Partition: 0}
    node_type_7:
        LEADER: {Topic: "Topic1"}

```



