#!/usr/bin/env python
# Copyright (c) 2014 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#pylint: disable=R0904

import os
import os.path
import unittest

from ClientTestLib import debug    #pylint: disable=W0611
from ClientTestLib import Bootstrap, BaseTest
from ClientTestLib import cli_log, file_log, remove_file
from ClientTestLib import startup_config_action, clear_startup_config

class ServerNotRunningTest(BaseTest):
    
    def test(self):
        bootstrap = Bootstrap(server='127.0.0.2')
        bootstrap.start_test()

        self.failUnless(bootstrap.server_connection_failure())
        self.assertEquals(cli_log(), [])
        self.failIf(bootstrap.error)

        bootstrap.end_test()

class EAPIErrorTest(BaseTest):

    def test(self):
        bootstrap = Bootstrap(eapi_port=54321)
        bootstrap.ztps.set_config_response()
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_configured())
        self.failUnless(bootstrap.eapi_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()

class MissingStartupConfigTest(BaseTest):

    def test(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_definition_response()
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.missing_startup_config_failure())
        self.failIf(bootstrap.error)

        bootstrap.end_test()

class FileLogConfigTest(BaseTest):

    def test(self):
        filenames = {
            'DEBUG' : '/tmp/ztps-log-%s-debug' % os.getpid(),
            'ERROR' : '/tmp/ztps-log-%s-error' % os.getpid(),
            'INFO' : '/tmp/ztps-log-%s-info' % os.getpid(),
            'bogus' : '/tmp/ztps-log-%s-bogus' % os.getpid() 
            }

        logging = []
        for level, filename in filenames.iteritems():
            logging += {'destination' : 'file:%s' % filename,
                        'level' : level},

        for filename in filenames.itervalues():
            self.failIf(os.path.isfile(filename))

        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(logging=logging)
        bootstrap.ztps.set_definition_response()
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.missing_startup_config_failure())
        for filename in filenames.itervalues():
            self.failUnless(file_log(filename))
        self.assertEquals(file_log(filenames['DEBUG']),
                         file_log(filenames['bogus']))
        self.assertEquals(file_log(filenames['DEBUG']),
                         file_log(filenames['INFO']))
        self.failIfEqual(file_log(filenames['DEBUG']),
                            file_log(filenames['ERROR']))
        self.failUnless(set(file_log(filenames['ERROR'])).issubset(
                set(file_log(filenames['DEBUG']))))
        for filename in filenames.itervalues():
            remove_file(filename)
        self.failIf(bootstrap.error)

        bootstrap.end_test()

class XmppConfigTest(BaseTest):

    def test_full(self):
        self.xmpp_sanity_test({'server' : 'test-server',
                               'port' : 112233,
                               'username' : 'test-username',
                               'password' : 'test-password',
                               'domain' :   'test-domain',
                               'nickname' : 'test-nickname',
                               'rooms' : ['test-room-1', 'test-room-2']})


    def test_partial(self):
        self.xmpp_sanity_test({'server' : 'test-server',
                               'username' : 'test-username',
                               'password' : 'test-password',
                               'domain' :   'test-domain'})

    def xmpp_sanity_test(self, xmpp):
        log = '/tmp/ztps-log-%s-debug'

        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response(logging=[
                {'destination' : 'file:%s' % log,
                 'level' : 'DEBUG'},],
                                           xmpp=xmpp)
        bootstrap.ztps.set_definition_response()
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.missing_startup_config_failure())
        self.failIf(bootstrap.error)
        self.failIf('XmppClient' not in ''.join(file_log(log)))

        bootstrap.end_test()

class ActionTest(BaseTest):

    def test(self):
        bootstrap = Bootstrap()
        bootstrap.ztps.set_config_response()
        bootstrap.ztps.set_definition_response(actions={'save_config' : {}})
        bootstrap.ztps.set_action_response('save_config', 'text/plain',
                                           startup_config_action())
        bootstrap.start_test()

        self.failUnless(bootstrap.eapi_node_information_collected())
        self.failUnless(bootstrap.success())
        self.failIf(bootstrap.error)

        clear_startup_config()
        bootstrap.end_test()

if __name__ == '__main__':
    unittest.main()