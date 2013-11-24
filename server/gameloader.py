#!/usr/bin/env python

from threading import Thread
import tarrasque

from events import *
from loaders import GameLoader, ObjectTypes
from game import Update


class ReplayLoader:
    def __init__(self, game_id, game):
        self.listeners_update = []
        self.listeners_event = []
        self.listeners_finish = []
        self.game = game
        self.game_id = game_id
        self.loaders = []
        self.tick = -1
        self.changes_tick =[]
        self.replay = None

    def load(self):
        Thread(target=self.load_replay).start()

    def load_replay(self):
        self.game.initialise()
        file_replay = "data/replays/{}.dem".format(self.game_id)
        self.replay = tarrasque.StreamBinding.from_file(file_replay, start_tick="start")

        self.tick = 0
        self.loaders.append(GameLoader(self, self.game_id))
        self.commit_update()

        for _ in self.replay.iter_ticks():
            self.tick = self.replay.tick
            self.changes_tick = []
            #execute all loaders
            new_loaders = []
            for loader in self.loaders:
                loader.check()
                if not loader.check_removal():
                    new_loaders.append(loader)
                else:
                    loader.remove()
            self.loaders = new_loaders
            #print "changed {}".format(self.changes_tick)
            #message game state changes
            state_changes = self.filter_changes(object_type=ObjectTypes.GAME, attribute="state")
            if len(state_changes) > 0:
                print "state is changing"
                if len(state_changes) > 1:
                    print "found multiple state changes?"
                event = StateChange(self.tick, state_changes[0].value)
                self.add_event(event)
             #always message chat information
            chat_events = [] #self.replay.chat_events
            if len(chat_events) > 0:
                for chat_event in chat_events:
                    print "event {}".format(chat_event)
                    self.add_chat_event(self.tick, chat_event)
            #message
            if self.replay.info.game_state is "start":
                #message loading information
                pass
            elif self.replay.info.game_state is "draft":
                #message drafting
                pass
            elif self.replay.info.game_state is "pregame" or self.replay.info.game_state is "game":
                #update changes in game
                #message big/relevant changes
                hero_alive_changes = self.filter_changes(object_type=ObjectTypes.HERO, attribute="is_alive")
                for change in hero_alive_changes:
                    if change.value is False:
                        event = TextEvent(self.tick, "{} died".format(self.game.current_state.get(change.id, "name")))
                    else:
                        event = TextEvent(self.tick, "{} respawned".format(self.game.current_state.get(change.id, "name")))
                    self.add_event(event)

            elif self.replay.info.game_state is "postgame":
                pass
            elif self.replay.info.game_state is "end":
                pass
            self.commit_update()
        self.finish()

    def add_change(self, change):
        self.game.add_update(Update(self.tick, [change]))
        self.changes_tick.append(change)

    def commit_update(self):
        if len(self.changes_tick) > 0:
            update = Update(self.tick, self.changes_tick)
            for listener in self.listeners_update:
                listener(update)

    def finish(self):
        self.game.finish()
        for listener in self.listeners_finish:
            listener()

    def add_event(self,event):
        self.game.add_event(event)
        for listener in self.listeners_event:
            listener(event)

    def add_update_listener(self, listener):
        self.listeners_update.append(listener)

    def add_event_listener(self, listener):
        self.listeners_event.append(listener)

    def add_finish_listener(self, listener):
        self.listeners_finish.append(listener)

    def filter_changes(self, object_id=None, change_type=None, object_type=None, attribute=None):
        result = []
        for change in self.changes_tick:
            accepted = True
            if object_id is not None:
                accepted = accepted and (change.id is object_id)
            if change_type is not None:
                accepted = accepted and (change.type is change_type)
            if object_type is not None:
                accepted = accepted and (self.game.current_state.get(change.id, "type") is object_type)
            if attribute is not None:
                accepted = accepted and (change.attribute is attribute)
            if accepted:
                result.append(change)
        return result

    def add_chat_event(self, current_tick, chat_event):
        player_ids = []
        if chat_event.playerid_1 is not None:
            player_ids.append(chat_event.playerid_1)
        if chat_event.playerid_2 is not None:
            player_ids.append(chat_event.playerid_2)
        if chat_event.playerid_3 is not None:
            player_ids.append(chat_event.playerid_3)
        if chat_event.playerid_4 is not None:
            player_ids.append(chat_event.playerid_4)
        if chat_event.playerid_5 is not None:
            player_ids.append(chat_event.playerid_5)
        if chat_event.playerid_6 is not None:
            player_ids.append(chat_event.playerid_6)
        self.game.add_event(ChatEvent(current_tick, chat_event.type, chat_event.value, player_ids))


