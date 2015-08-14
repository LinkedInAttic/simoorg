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
# argument 1: Path to the pid file (mandatory)
#

##
# Main
##

if [ $# -lt "1" ]
then
  exit 255
fi

if [ $# -ge 2 ]
then
  SUDO_USER=$2
  COMMAND_PREFIX="sudo -u $SUDO_USER"
else
  COMMAND_PREFIX=""
fi

PID_PATH=$1
PID=`$COMMAND_PREFIX cat $PID_PATH`

cd /tmp && $COMMAND_PREFIX /bin/kill -9 $PID

if [ $? -eq 0 ]
then
  exit 0
else
  exit 1
fi
