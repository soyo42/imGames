#!/usr/bin/python

import sys
from optparse import OptionParser
import logging
import os

gameTitle = 'love letter'

defaultLocalStore = '.llStore'
defaultAction = 'inspect'
actions = (defaultAction, 'init', 'turn', 'interact')

gameTitleLong = 'IM-game [\033[35;1m{0}\033[0m]'.format(gameTitle)
usageMsg = '\n{0}\n{1}\nusage:: {2} [-h|--help]'.format(gameTitleLong, 42*'-', sys.argv[0])

# ------ logging
LOG_FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
logging.basicConfig(format=LOG_FORMAT)
LOG = logging.getLogger()


# ------ parse parameters
parser = OptionParser(usage=usageMsg)

parser.add_option('-a', '--action', dest='action', type='choice', choices=actions,
                  help='action, default: {0}, available: {1}'.format(defaultAction, actions), metavar='ACTION', 
                  default=defaultAction)
parser.add_option('-l', '--local-store', dest='localStore',
                  help='local store file, default: {0}'.format(defaultLocalStore), metavar='FILE', 
                  default=defaultLocalStore)
parser.add_option('-m', '--message-file', dest='messageFile',
                  help='incoming message file', metavar='FILE')
parser.add_option('-v', '--verbose',
                  action='store_true', dest='verbose', default=False,
                  help='print debug info')

(options, args) = parser.parse_args()


if options.verbose:
    LOG.setLevel(10)
else:
    LOG.setLevel(20)

LOG.info('{} -> START'.format(gameTitleLong))
LOG.debug('local store: {}'.format(options.localStore))
LOG.debug('action: {}'.format(options.action))
#LOG.debug('arguments: {}'.format(args))

data = None
if options.messageFile:
    if os.path.isfile(options.messageFile):
        with open(options.messageFile, 'r') as messageFile:
            data = messageFile.read()
if not data and len(args) == 1:
    data = args[0]

#hitTheGame
LOG.debug('data >' + str(data) + '<')
from imgame import Dispatcher
dispatcher = Dispatcher(options.localStore)
dispatcher.dispatch(options.action, data)


LOG.info('{} -> END'.format(gameTitleLong))


