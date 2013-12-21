#!/usr/bin/env python
from threading import Thread
import tarrasque

from server.loader.loaders import GameLoader
from server.loader.evaluators import StateEvaluator
from server.libs.game import Game, Update, ChangeType
from server.libs.utils import UNDEFINED


COMPRESSION_PRECISION = 10


class ReplayLoader:
    def __init__(self, game_id, loader_server):
        self.loader_server = loader_server
        self.game = Game()
        self.game_id = game_id
        self.loaders = []
        self.evaluators = []
        self.tick = -1
        self.cache_start = 0
        self.cache_end = None
        self.cache_update = Update(0)
        self.replay = None
        self.changes_tick = []

    def load(self):
        Thread(target=self.load_replay).start()

    def load_replay(self):
        self.game.initialise()
        file_replay = "server/data/replays/{}.dem".format(self.game_id)
        self.replay = tarrasque.StreamBinding.from_file(file_replay, start_tick="start")
        self.tick = 0
        GameLoader(self, self.game_id) #spawn loader for game
        StateEvaluator(self)
        for _ in self.replay.iter_ticks():
            self.update_time()
            #execute all loaders
            for loader in self.loaders:
                loader.check()
            self.loaders = [loader for loader in self.loaders if not loader.removed]
            for evaluator in self.evaluators:
                evaluator.evaluate()
            self.evaluators = [evaluator for evaluator in self.evaluators if not evaluator.removed]
        self.finish()

    def update_time(self):
        self.tick = self.replay.tick
        self.changes_tick = []
        if self.tick >= self.cache_start + COMPRESSION_PRECISION:
            self.loader_server.send_update(self.cache_update)
            self.cache_start = self.tick
            self.cache_update = Update(self.tick)

    def add_change(self, change):
        self.changes_tick.append(change)
        update = Update(self.tick, [change])
        self.game.add_update(update)
        self.cache_update.merge(update)

    def finish(self):
        self.game.finish()
        self.loader_server.finish()

    def add_event(self, event):
        self.game.add_event(event)
        self.loader_server.send_event(event)

    def filter_changes(self, object_id=None, change_type=None, object_type=None, attribute=None, value=UNDEFINED):
        result = []
        for change in self.changes_tick:
            accepted = True
            if object_id is not None:
                accepted = accepted and (change.id == object_id)
            if change_type is not None:
                accepted = accepted and (change.type == change_type)
            if change.type is ChangeType.SET:
                if object_type is not None:
                    accepted = accepted and (self.game.current_state.get(change.id, "type") == object_type)
                if attribute is not None:
                    accepted = accepted and (change.attribute == attribute)
                if value is not UNDEFINED:
                    accepted = accepted and (change.value == value)
            else:
                if object_type is not None or attribute is not None or value is not UNDEFINED:
                    accepted = False
            if accepted:
                result.append(change)
        return result

