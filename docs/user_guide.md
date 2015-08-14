#Introduction
This document describes the process of setting up and running simoorg against an application cluster.
##Installation
The system requirements for Simoorg are as follows
OS: Any Linux distribution
Python Version : Python-2.6
Additional Python Modules: multiprocessing, yaml, paramiko

Simoorg is currently distributed via pip, so to install the package please run the following command 
````
(sudo) pip install simoorg
```
If you want to work with the latest code, please run the following commands
```
git clone git@github.com:linkedin/Simoorg.git
cd Simoorg
```
When installing from the source, we recommend that you run all the unit and integration tests that are included with the source code, before starting the installations. You can do this by running the command
```
    python setuptools.py test
```
Once you have confirmed that the tests have passed, you can install the code by running the command
```
    python setuptools.py install
```
If you are planning to use ssh handler plugin to induce failures against a specific service cluster, please ensure that the user you are using to run simoorg have Passwordless SSH access to all the nodes in the cluster. You should also ensure that any failure scripts you plan to use are already present on all the nodes in the target service cluster.

##Basic Usage
Simoorg is started using the command *simoorg* which takes the path to your config directory as the only argument. Please check the config document ([link][docs/config.rst]) to better understand the configuration files.  The sample config directory packaged with the product can be used to set up your configs.  
```
    Ex:     simoorg ~/configs/
```

##Usage Example
In this section of the document, we will be describing how to use Simoorg against a kafka cluster. For this examples we will be running three predefined failures (graceful stop, ungraceful stop and simulate full GC) on random nodes in the cluster using the Shell script handler plugin. We will be executing the failures in a random manner using the non deterministic scheduler.  We will also be using the Kafka Topology plugin and  Kafka HealthCheck plugin. Both of these plugins are packaged with the product and are ready to use out of the box.

Before we start , we need to make sure that all the required failure scripts (the ones required for these failure scenario is present in the repo under Simoorg/failure_scripts/base/) are present on all the broker nodes in the kafka cluster. Let’s assume that the script is present in the location ~/test/failure_scripts/base/ on the kafka brokers, we will need this path later when we are updating our configurations.

Assuming that your user has passwordless ssh access to all the broker nodes in the cluster, we can start updating the configs to work against the kafka cluster. We start by copying over the sample configs provided in the repo (Simoorg/sample_configs/). First configuration file that needs to be updated, will be the fate book, the sample configs comes with a single fate book file called sample_service.yaml, rename the file to a name which better represents your cluster. Next we update the key service in the fate book, the current content of the key should look like
```
    service: sample-service
```
Now lets update this to some unique value that better represents your specific cluster. For example, we can update it to
```
    service: kafka
```
Next we move on to the topology section of the fatebook. Here we have to update two keys, namely topology_plugin and topology_config. Set the topology_plugin to KafkaTopology and provide the location of the topology config, relative to the root of the config directory. We recommend you use the path plugins/topology/kafka/ within the config directory to store the topology config file. Let us assume the kafka topology file name is kafka_topo.yaml, then the topology section would look like
```
Topology:
topology_plugin: KafkaTopology
    topology_config: plugins/topology/kafka/kafka_topo.yaml
```

For creating the topology config, you can make use of the file Simoorg/sample_configs/plugins/topology/kafka/kafka_sample.yaml. The config mainly expects the user to provide the following information
* Zookeeper Url - In Zookeeper url you list the zookeeper path for your kafka cluster (eg: test-zookeeper.test.com:2181/kafka-cluster1), you need to fill this information under the key host under zookeeper section
* Zookeeper paths - The paths already listed in the config should work for our example
* Kafka host resolution - This contains list of node types we want to induce failure on, let’s assume we only want to induce failures on brokers for the topic “Topic1”. Please check the design doc to better understand what each of the node type mean
```yaml
zookeeper:
    host: “test-zookeeper.test.com:2181/kafka-cluster1”

zookeeper_paths:
    broker_ids: "/brokers/ids"
    broker_topics: "/brokers/topics"
    topic_config: "/config/topics"
    controller: "/controller"
    broker_sequence_id:  "/brokers/seqid"

kafka_host_resolution:
    node_type_1:
        RANDOM_BROKER: {Topic: "Topic1"}
```
Following the topology section we update the logger section with the desired path to the log, our desired log level and enable or disable the console logging flag.The logger section would look something like the following
```
Logger:
  # Set this to the path where the log file will be created. This must be an existing full path including the filename.
  # The file name should be present and writable by the user under which the failure inducer runs
  path: /home/test/logs/kafka.log
  # Set this to True if you want to output logs to stdout. This is a complimentary logging and does not replace logging to the file.
  console: True
  # Loglevel can be one of the following: WARNING, INFO, VERBOSE, DEBUG
  log_level: VERBOSE


```

Next section in the fate book would be the impact limit, which can be set to 1 (This means that there can only be one failure in the cluster at a time)
```
impact_limits:
  total_maximum: 1
```
Now we move on to the healthcheck section of the fate book. We need to update three keys here, namely plugin, coordinate and plugin_config. We set the plugin to KafkaHealthCheck, the coordinate should be the location of the kafka-server-hc.sh, which will be used by the health check plugin to check if any nodes have a non zero under replicated partition count. We can find this script in our repo, under the location Simoorg/helper_Script/health_check/kafka-server-hc.sh. You can copy this script to a desired location and just update the coordinate key with that path (We expect the absolute path to the script here, and make sure the script has execute permissions enabled). Next comes the plugin specific config information. The kafka health check plugin requires topology information and so we need to pass the topology config to the health check plugin as well, you can reuse the file we had created for topology plugin, But here we just need to pass the absolute path to that file. The kafka Healthcheck plugin expects the location of the file to be specified under the key ‘topology_config’. So the health check section should look something like the following

```
healthcheck:
  # plugin can be set to either of: default, kafka
  plugin: kafka
  # coordinate to the healthcheck script. Required for default plugin
  coordinate: /tmp/kafka-server-hc.sh
  plugin_configs:
    topology_config: /home/test_user/configs/plugins/topology/kafka/kafka_sample.yaml
```
The next section to update is the destiny section, which determines the frequency of failures, the failures to be run and what the total duration of the run should be. The destiny section we will be using looks something like this
```
destiny:
  scheduler_plugin: NonDeterministicScheduler
  NonDeterministicScheduler:
    # global constraints for all failures. Unit is minutes.
    constraints:
      min_gap_between_failures: 10
      max_gap_between_failures: 20
      total_run_duration: 1000
    failures:
      simulate_full_gc:
        timeout: 20
      graceful_bounce:
        timeout: 50
      ungraceful_bounce:
        timeout: 50


```
scheduler_plugin gives us the name of the scheduler we will be using for the run, following that we need to provide the configs required for the scheduler. We start with the constraints, which the scheduler plan must satisfy. In constraints section we need to provide the minimum and maximum gap between each failure (which we have set to 20 and 30 minutes respectively) followed by the total time for which simoorg should keep running (given here as 1000 minutes). After the constraint sections, we list all the failures we need to test along with their respective time outs.

The final section of the fate book, gives the definition of each failures under the key ‘failures’. The sample config should already contain a template for the three failures we are considering, we just need to update the script location and pid location to reflect your particular system. So in our case our failure scripts are present in the location  ~/test/failure_scripts/base/ and let us assume that the pid path for our kafka brokers are at /var/tmp/kafka.pid. Then our failure definitions should look like

```
 - name: graceful_bounce
    sudo_user: test
    induce_handler:
      type: ShellScriptHandler
      coordinate: ~/test/failure_scripts/base/graceful-stop.sh
      arguments: ['/var/tmp/kafka.pid']
    restore_handler:
      type: ShellScriptHandler
      coordinate: ~/test/failure_scripts/base/graceful-start.sh
      arguments: ['/path/to/start/script.sh']
    wait_seconds: 10

  - name: ungraceful_bounce
    sudo_user: test
    induce_handler:
      type: ShellScriptHandler
      coordinate: ~/test/failure_scripts/base/ungraceful-stop.sh
      arguments: ['/var/tmp/kafka.pid']
    restore_handler:
      type: ShellScriptHandler
      coordinate: ~/test/failure_scripts/base/graceful-start.sh
      arguments: ['/path/to/start/script.sh']
    wait_seconds: 10

 - name: simulate_full_gc
    sudo_user: test
    induce_handler:
      type: ShellScriptHandler
      coordinate: ~/test/failure_scripts/base/sigstop.sh
      arguments: ['/var/tmp/kafka.pid']
    restore_handler:
      type: ShellScriptHandler
      coordinate: ~/test/failure_scripts/base/sigcont.sh
      arguments: ['/var/tmp/kafka.pid']
    wait_seconds: 10
```


Here the key `sudo_user: test` means that each of the script will be executed under the sudo user test. If this is not required in your system, just remove that key from the configs. Also the `wait_seconds: 10` signifies that there will be a 10 second delay between failure and revert of the failure. Simoorg will maintain the failure state in target kafka cluster for 10 seconds.

Now that we are ready with our new fate book, we move on to our handler config. For this example run we are going to rely on our ShellScriptHandler plugin to induce and revert failure. So in order to use that we need to update the ShellScriptHandler config, which the plugin expects at the location plugins/handler/ShellScriptHandler/ShellScriptHandler.yaml under your configs directory. The only value we need to set in this file is the location of your ssh host key, so the config should look something like

```
host_key_path: ~/.ssh/known_hosts
```

With the ShellScriptHandler.yaml set up, we are finally done with our configurations and we are ready to start simoorg. As mentioned before, you can do it by running the command

```
simoorg ~/kafka_configs/
```

Where ~/kafka_configs/ is the path to your failure inducer configs. For longer run times, we recommend you run simoorg under a screen session. By turning on the console logging flag in the fate book, you can easily follow the progress of each failure event through the messages on the screen. You can also check your logs or query the api endpoint to get these information. You can start the api server by running the command
```
    gunicorn 'simoorg.Api.MoiraiApiServer:create_app("~/kafka_configs/api.yaml")'
```
Where api.yaml should contain a valid path for the named pipe used by both the api server and Simoorg. Our current implementation of api, relies on the simoorg process to retrieve all information and do not serve any data once the process is dead. Please check the design doc to better understand the various REST API endpoints

