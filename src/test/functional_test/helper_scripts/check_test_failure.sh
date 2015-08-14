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

# Find the PIDS of all the fate.py process
# and check if one of them is present in the file given in arg1

if [ $# -lt 1 ]
then
    echo "Error: Test file Argument missing"
    exit 1
fi

TEST_FILE=$1

if [ ! -f $TEST_FILE ]
then
    echo "Error: Provided test file is not a regular file"
    exit 1
fi


PIDS=`ps ax | grep simoorg |grep -v grep |awk '{print $1}'`

for pid in $PIDS
do
    test_pid=`cat $TEST_FILE`
    if [ $test_pid -eq  $pid ]
    then
        echo "Success: Test pid is an actual atropos pid"
        exit 0
    fi
done

echo "Error: Test pid is not an actual atropos pid"
exit 1
