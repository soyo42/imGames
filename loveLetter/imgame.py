# python module imgame

from abc import ABCMeta, abstractmethod
import sys
import json
import random
import pickle
import os
import logging

class Dispatcher:
    '''holds configuration, responsible for dispatching game action to appropriate handler'''

    _LOGGER = logging.getLogger('imgame.Dispatcher')
    STATE_INIT = 'init'
    STATE_TURN = 'turn'

    def __init__(self, localStore):
        self.localStore = localStore

    def dispatch(self, action, data):
        Dispatcher._LOGGER.debug('dispatching action: \033[35;1m{0}\033[0m'.format(action))

        heapBox = HeapBox(data)
        handler = None
        if action == 'init':
            handler = InitHandler(self)
        elif action == 'turn':
            handler = TurnHandler(self)
        elif action == 'inspect':
            pass

        handler.handle(heapBox)


class LocalContext:
    '''local data store'''
    
    def __init__(self):
        self.hand = []
        self.heapInitStash = None
        self.name = None

class HeapBox:
    '''mobile data store, exchanged among users'''

    _PLAYER_LIST = 'playerList'
    _ACTIVE_PLAYER = 'activePlayer'
    _HEAP = 'heap'
    _STATE = 'state'

    def __init__(self, rawData):
        self._data = {}
        self._data[HeapBox._PLAYER_LIST] = []
        self._data[HeapBox._ACTIVE_PLAYER] = None
        self._data[HeapBox._HEAP] = []
        self._data[HeapBox._STATE] = 'init'

        self.isEmpty = rawData == None or rawData.strip() == ''
        if not self.isEmpty:
            self._data = self._decode(rawData)


    def addPlayer(self, playerName):
        if playerName in self._data[HeapBox._PLAYER_LIST]:
            raise Exception('\033[31;1mplayer already added -> {}\033[0m'.format(playerName))
        self._data[HeapBox._PLAYER_LIST].append(playerName)

    def getPlayerList(self):
        return self._data[HeapBox._PLAYER_LIST]

    def setActivePlayer(self, playerName):
        self._data[HeapBox._ACTIVE_PLAYER] = playerName

    def getActivePlayer(self):
        return self._data[HeapBox._ACTIVE_PLAYER]

    def getNextPlayer(self):
        active = self.getActivePlayer()
        allPlayers = self.getPlayerList()
        nextIndex = allPlayers.index(active) + 1
        if nextIndex >= len(allPlayers):
            nextIndex = 0

        return allPlayers[nextIndex]

    def setState(self, state):
        self._data[HeapBox._STATE] = state

    def getState(self):
        return self._data[HeapBox._STATE]

    def getHeap(self):
        return self._data[HeapBox._HEAP]


    def _decode(self, rawData):
        # base64 decode
        # ungzip
        # unmarshall json
          
        # heap - cards left
        # last round history
        # players list
        # active player
        # game state
        return json.loads(rawData)

    def encode(self):
        # marshall json
        # gzip
        # base64 decode
        out = json.dumps(self._data)
        return out


class BaseHandler():
    __metaclass__ = ABCMeta
    _LOG = logging.getLogger('imgame.BaseHandler')

    def __init__(self, config):
        self._localStore = config.localStore
        if os.path.isfile(self._localStore):
            with open(self._localStore, 'rb') as storageFile:
                self._localContext = pickle.load(storageFile)
            if self._localContext.heapInitStash:
                BaseHandler._LOG.debug('HEAP STASH in use - you are the firestarter!')
        else:
            self._localContext = None

    def storeLocalContext(self):
        with open(self._localStore, 'wb') as storageFile:
            pickle.dump(self._localContext, storageFile)

    def drawCard(self, heapBox):
        if len(self._localContext.hand) > 1:
            raise Exception('hand full already: {}'.format(self._localContext.hand))

        random.shuffle(heapBox.getHeap())
        self._localContext.hand.append(heapBox.getHeap().pop(0))
        BaseHandler._LOG.info('on hand:{}'.format(self._localContext.hand))

    def dumpHeapBox(self, heapBox):
        out = heapBox.encode()
        BaseHandler._LOG.debug('\n{0}\n{1}\n{0}'.format(10*'-', out))
        with open('out', 'w') as msgOut:
            msgOut.write(out)

    @staticmethod
    def askForChoice(question, options):
        print question
        choice = None
        while not choice:
            for i in range(len(options)):
                print '{}. {}'.format(i, options[i])
            idx = raw_input('Enter choice number: ')
            try:
                choice = options[int(idx)]
            except Exception as e:
                BaseHandler._LOG.warn('answer not understood: {}'.format(e))
        return choice

    @abstractmethod
    def handle(self, heapBox):
        pass


class InitHandler(BaseHandler):
    '''Provisioning of game:
    - player name
    - draw first card
    '''
    _LOG = logging.getLogger('imgame.InitHandler')

    def __init__(self, localstore):
        super(InitHandler, self).__init__(localstore)
        self._stashSize = 8
        

    def handle(self, heapBox):
        if heapBox.isEmpty:
            InitHandler._LOG.debug('creating heapBox from SCRATCH')
        else:
            InitHandler._LOG.debug('init with EXISTING heapBox')
            if heapBox.getState() != Dispatcher.STATE_INIT:
                raise Exception('incorrect state occured: {}, expected: {}'.format(heapBox.getState(), Dispatcher.STATE_INIT))

        # get player name from localContext
        if self._localContext == None:
            self._localContext = LocalContext()
        defaultName = self._localContext.name

        # detection of point where the heap stash must be moved back to heapBox
        if defaultName and not heapBox.isEmpty and self._localContext.heapInitStash:
            # move stashed heap back to heapBox
            heapBox.getHeap().extend(self._localContext.heapInitStash)
            InitHandler._LOG.debug('\033[35mHEAP STASH moved back to heapBox (+{})\033[0m'.format(len(self._localContext.heapInitStash)))
            self._localContext.heapInitStash = None

            heapBox.setActivePlayer(defaultName)
            heapBox.setState(Dispatcher.STATE_TURN)
            InitHandler._LOG.info('\033[32;1mgame initialized, let\'s play\033[0m')

        else:
            # get user name from stdin
            playerName = InitHandler.askForPlayerName(defaultName)

            heapBox.addPlayer(playerName)
            heapBox.setActivePlayer(playerName)
            self._localContext.name = playerName
            if heapBox.isEmpty:
                heapBox.getHeap().extend(InitHandler.createHeap())
                heapBox.setState(Dispatcher.STATE_INIT)
                # stash half of cards from heap
                self._localContext.heapInitStash = heapBox.getHeap()[0:self._stashSize]
                del(heapBox.getHeap()[0:self._stashSize])
                InitHandler._LOG.debug('\033[35mHEAP STASH created ({})\033[0m'.format(len(self._localContext.heapInitStash)))


            # draw first card
            del(self._localContext.hand[:])
            self.drawCard(heapBox)
        

        self.dumpHeapBox(heapBox)
        self.storeLocalContext()

    @staticmethod
    def askForPlayerName(defaultName):
        nameQuery = 'Enter player name [{}]: '.format(defaultName)
        playerName = None
        while not playerName:
            playerName = raw_input(nameQuery)
            if not playerName and defaultName != None:
                playerName = defaultName
        return playerName

    @staticmethod
    def createHeap():
        heap = [1,1,1,1, 2,2, 3,3, 4,4, 5,5, 6,6, 7, 8]
        InitHandler._LOG.debug('heap created: {}({})'.format(heap, len(heap)))
        random.shuffle(heap)
        return heap


class TurnHandler(BaseHandler):
    '''Pulling through a turn:
    - draw card
    - dump card + choose target, if feasible
    Or interact as target:
    - reply upon request
    '''
    _LOG = logging.getLogger('imgame.TurnHandler')

    def handle(self, heapBox):
        if heapBox.getState() == Dispatcher.STATE_TURN:
            self.prepareNextTurn(heapBox)
        elif heapBox.getState() == Dispatcher.STATE_INTERACTION:
            self.interact(heapBox)
        else:
            TurnHandler._LOG.error('unexpected game state: {}'.format(heapBox.getState()))

    def prepareNextTurn(self, heapBox):
        # simple check of order
        nextPlayer = heapBox.getNextPlayer()
        if nextPlayer != self._localContext.name:
            raise Exception('wrong player, expected: {}'.format(nextPlayer))

        heapBox.activePlayer = nextPlayer
        self.drawCard(heapBox)
        # ask user for action
        # check and warn (offer fix)
        # optional: offer target
        # log draw to heapBox
        
        # send heapBox to next player or target
        self.storeLocalContext()



if __name__ == '__main__':
    raise Exception('Package invoked, but it does not contain any standalone code.')
