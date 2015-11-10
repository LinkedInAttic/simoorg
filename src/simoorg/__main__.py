#!/usr/bin/env python
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
    The main entry point to the simoorg tool
"""
import simoorg.moirai as moi
import sys


def main():
    if len(sys.argv) != 2:
        print "Please provide config path"
        exit(1)
    CONFIG_PATH = sys.argv[1]

    MOIRAI = moi.Moirai(CONFIG_PATH, verbose=True, debug=False)

    MOIRAI.spawn_atropos()

    for service_name, proc_handler in MOIRAI.atropos_army.iteritems():
        print service_name, proc_handler.pid

    # Wait for all the atropos to finish

    MOIRAI.finish()

if __name__ == '__main__':
    main()
