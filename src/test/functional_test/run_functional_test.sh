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

#!/bin/bash -x

SIMOORG_DIR="../../Simoorg"
SLEEP_TIME=1
SIMOORG_LOGS="/tmp/simoorg_test.logs"

# Set up simoorg with test configs
# Run simoorg in test mode, sleep for X secs to give atropos a chance to spin up

gunicorn 'simoorg.Api.MoiraiApiServer:create_app("test_configs/api.yaml")' > /dev/null 2>&1 &
GUNICORN_PID=$!
python -m simoorg.__main__ test_configs/ > $SIMOORG_LOGS &
SIMOORG_PID=$$

sleep $SLEEP_TIME

python run_test.py
TEST_STATUS=$?

kill $GUNICORN_PID

if [ $TEST_STATUS -ne 0 ]
then
    echo "LOGGER: The functional test has failed"
else
    echo "LOGGER: Functional test has run successfully"
    exit 0
fi

exit 1
