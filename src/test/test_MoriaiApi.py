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
    Unit test for API Server
"""
import os
import yaml
import time
import json
import unittest
import httplib
import multiprocessing

import simoorg.Api.MoiraiApiServer as MoiraiApiServer
import mock_modules.MockMoirai as MockMoirai
MOIRAIAPI_CONFIG_DIR = (os.path.dirname(os.path.realpath(__file__)) +
                        "/unittest_configs/moiraiapi_configs/")
APISERVER_WARMUP_TIME = 1

APIHOST = '127.0.0.1'
APIPORT = 8000


def api_server():
    """
        Will be run as a seperate process
    """
    api_config = MOIRAIAPI_CONFIG_DIR + '/api.yaml'
    api_app = MoiraiApiServer.create_app(api_config)
    api_app.run(port=APIPORT)


def mock_moirai_thread(data_queue, event_queue, api_config):
    """
        The mock moirai thread
    """
    m_obj = MockMoirai.MockMoirai(data_queue, event_queue, api_config)
    m_obj.start_moirai()


class TestMoiraiAPI(unittest.TestCase):
    """
        Here we run a test moirai service, to which we feed test information
        Here each one of the api end point is tested, by looking at the api
        output
    """
    def do_http_get(self, base_url, get_url):
        """
            Generic http get function
        """
        try:
            connection = httplib.HTTPConnection(base_url)
            connection.request('GET', get_url)
            resp = connection.getresponse()
        except httplib.HTTPException:
            print ("LOGGER: Unable to perform fetch to the"
                   " given url due to HTTPLIB exception",
                   base_url + get_url)
            return (False, None)
        except Exception, exc:
            print ("LOGGER: Unable to perform fetch to the given"
                   " url {0} due to exception {1}"
                   .format(base_url + get_url, exc))
            raise
        data = resp.read()
        print data
        if resp.status != 200:
            print ("LOGGER: The return status for the url get request was ",
                   resp.status)
            return (False, data)
        else:
            return (True, data)

    def setUp(self):
        """
            SetUp function for each test, reads the api.yaml config file
            Starts the api server and mock moirai api service
        """
        with open(MOIRAIAPI_CONFIG_DIR + 'api.yaml') as config_fd:
            self.api_config = yaml.load(config_fd)
        self.data_queue = multiprocessing.Queue()
        self.event_queue = multiprocessing.Queue()
        self.api_proc = multiprocessing.Process(target=api_server,
                                                args=(),
                                                kwargs={})

        self.api_proc.start()
        self.m_proc = multiprocessing.Process(target=mock_moirai_thread,
                                              args=(self.data_queue,
                                                    self.event_queue,
                                                    self.api_config))
        # self.m_thread.daemon = True
        self.m_proc.start()
        time.sleep(APISERVER_WARMUP_TIME)

    def tearDown(self):
        """
            tearDown function for each test, kill the api server
        """
        self.api_proc.terminate()
        self.api_proc.join()
        self.m_proc.terminate()
        self.m_proc.join()

    def test_api_running(self):
        """
            Make sure the api server is running
        """
        self.assert_(self.api_proc.is_alive())

    def test_api_list(self):
        """
            Confirm the GET /list works correctly
        """
        test_service_info = ('test_service', [], [])
        test_service2_info = ('test_service2', [], [])
        expected_srvc_list = ['test_service', 'test_service2']
        self.data_queue.put(test_service_info)
        self.data_queue.put(test_service2_info)
        status, data = self.do_http_get(APIHOST + ':' +
                                        str(APIPORT), '/list')
        self.assertEqual(json.loads(data), expected_srvc_list)

    def test_api_get_plan(self):
        """
            Confirm the GET <service_name>/plan works correctly
        """
        test_plan = {1: 'a', 2: 'b'}
        test_service_info = ('test_service', [], test_plan)
        self.data_queue.put(test_service_info)
        status, data = self.do_http_get(APIHOST + ':' +
                                        str(APIPORT),
                                        '/test_service/plan')
        recvd_plan = {}
        for step, failure in json.loads(data).iteritems():
            recvd_plan[int(step)] = str(failure)
        self.assertEqual(recvd_plan, test_plan)

    def test_api_get_servers(self):
        """
            Confirm the GET <service_name>/servers works correctly
        """
        test_servers = ['a', 'b']
        test_service_info = ('test_service', test_servers, [])
        self.data_queue.put(test_service_info)
        status, data = self.do_http_get(APIHOST + ':' +
                                        str(APIPORT),
                                        '/test_service/servers')
        self.assertEqual(json.loads(data), test_servers)

    def test_api_get_events(self):
        """
            Confirm the GET <service_name>/events works correctly
        """
        test_service = 'test_service'
        test_failure_name = 'failure1'
        test_trigger_time = 1
        test_node_name = 'random_node'
        test_trigger_status = 'True'
        test_service_info = ('test_service', [], [])
        self.data_queue.put(test_service_info)
        test_service_event = (test_service, test_failure_name,
                              test_trigger_time, test_node_name,
                              test_trigger_status)
        expected_event = [test_failure_name, test_trigger_time,
                          test_node_name, test_trigger_status]
        self.event_queue.put(test_service_event)
        status, data = self.do_http_get(APIHOST + ':' +
                                        str(APIPORT),
                                        '/test_service/events')
        self.assertEqual(json.loads(data)[0], expected_event)
