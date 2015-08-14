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

# Check if the provided test file handler no longer exists

if [ $# -lt 1 ]
then
    echo "Error: Test file Argument missing"
    exit 1
fi

TEST_FILE=$1

if [ ! -e $TEST_FILE ]
then
    echo "Success: Provided test file no longer exists"
    exit 0
fi
echo "Error: Provided test file still exists"
exit 1

