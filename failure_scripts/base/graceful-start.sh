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

#!/bin/bash
# This script accepts 1 argument
#
# argument 1: Path to the graceful start/stop script (mandatory)
#

##
# Main
##

if [ $# -lt "1" ]
then
  exit 255
fi

GRACEFUL_START_SCRIPT=$1
if [ $# -ge 2 ]
then
  SUDO_USER=$2
  COMMAND_PREFIX="sudo -u $SUDO_USER"
else
  COMMAND_PREFIX=""
fi

cd `dirname $GRACEFUL_START_SCRIPT`

# get the status of the service. We expect the service is down
STATUS=`$COMMAND_PREFIX $GRACEFUL_START_SCRIPT status |grep 'not running'`

if [ $? -eq 0 ]
then
  # start the service
  $COMMAND_PREFIX $GRACEFUL_START_SCRIPT start 2>&1 > /dev/null

  # give it 20 seconds and check the status
  sleep 20
  STATUS=`$COMMAND_PREFIX $GRACEFUL_START_SCRIPT status |grep 'not running' 2>&1 > /dev/null`

  if [ $? -eq 1 ]
  then
    exit 0
  else
    exit 1
  fi
else
  exit 1
fi
