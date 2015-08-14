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
    Moving api related constants to a common location so that both
    Api Server and Moirai can use it
"""

DEBUG_CONFIG_KEY = 'debug'
API_CONFIG = 'api.yaml'
API_PIPE_DIR = '/tmp/'
READ_TIMEOUT_SECS = 2
MOIRAI_GET_COMMAND_PREFIX = 'api_get_'
MOIRAI_OTHER_COMMAND_PREFIX = 'api_other_'
API_COMMANDS = ['list', 'plan', 'events', 'servers']
THREADPOOL_SIZE = 1

# Moriai fifo msg keys
FIFO_ENDPOINT_KEY = "api_fifo_path"
COMMAND_ID_KEY = "command_id"
COMMAND_KEY = "command"
ARGS_KEY = "args"
METHOD_KEY = 'method'

# Api Fifo msg keys
COMMAND_OUTPUT_KEY = "command_output"
