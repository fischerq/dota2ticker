#!/usr/bin/env python

from threading import Thread
from database import *
import time
import tarrasque

from events import *


class GameLoader:
    def __init__(self, game_id, game):
        self.game = game
        self.game_id = game_id
        self.loaders = []
        self.replay = None

    def load(self):
        Thread(target=self.load_game).start()

    def load_game(self):
        self.game.initialise()
        file_replay = "data/replays/{}.dem".format(self.game_id)
        self.replay = tarrasque.StreamBinding.from_file(file_replay, start_tick="start")
        last_state = None
        for tick in self.replay.iter_ticks():
            current_tick = self.replay.tick
            update = Update(current_tick)
            if self.replay.info.game_state is not last_state:
                event = StateChange(current_tick, self.replay.info.game_state)
                self.game.add_event(event)
                if self.replay.info.game_state is "loading":
                    pass
                elif self.replay.info.game_state is "draft":
                    pass
                elif self.replay.info.game_state is "pregame":
                    print "Found pregame"
                    print len(self.replay.players)
                    for player in self.replay.players:
                        if player.index is not None:
                            self.loaders.append(PlayerLoader(self, update, player))
                elif self.replay.info.game_state is "game":
                    pass
                elif self.replay.info.game_state is "postgame":
                    pass
                else:
                    print "strange state {}".format(self.replay.info.game_state)
                last_state = self.replay.info.game_state
                if len(update.changes) > 0:
                    self.game.add_update(update)
                    update = Update(current_tick)
            #print chat information in every state
            chat_events = self.replay.chat_events
            if len(chat_events) > 0:
                for chat_event in chat_events:
                    print "event {}".format(chat_event)
                    self.add_chat_event(current_tick, chat_event)
            if self.replay.info.game_state is "start":
                #message loading information
                pass
            elif self.replay.info.game_state is "draft":
                #message drafting
                pass
            elif self.replay.info.game_state is "pregame" or self.replay.info.game_state is "game":
                #update changes in game
                #message big/relevant changes
                for loader in self.loaders:
                    loader.check_changes(update)
            elif self.replay.info.game_state is "postgame":
                pass
            elif self.replay.info.game_state is "end":
                pass
            if len(update.changes) > 0:
                #print "added update"
                self.game.add_update(update)
        self.game.finish()

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


class ObjectLoader(object):
    def __init__(self, loader, update):
        self.loader = loader
        self.id = self.loader.game.get_object_id()
        self.last_time = -1
        update.changes.append(Change(ChangeType.CREATE, self.id))

    def check_changes(self, update):
        if update.time > self.last_time:
            saved_time = self.last_time
            self.last_time = update.time
            update.changes.extend(self.changes(self.loader.game.current_state))
        else:
            print "tried to check bad changes"

    def changes(self, state):
        print "Not implemented"

UnitTypes = enum("PLAYER")


class PlayerLoader(ObjectLoader):
    def __init__(self, loader, update, player):
        super(PlayerLoader, self).__init__(loader, update)
        self.player = player
        update.changes.append(Change(ChangeType.SET, self.id, "type", UnitTypes.PLAYER))
        update.changes.append(Change(ChangeType.SET, self.id, "team", self.player.team))
        update.changes.append(Change(ChangeType.SET, self.id, "steam_id", self.player.steam_id))
        update.changes.append(Change(ChangeType.SET, self.id, "name", self.player.name))
        update.changes.append(Change(ChangeType.SET, self.id, "index", self.player.index))
        update.changes.append(Change(ChangeType.SET, self.id, "connected", True))

    def changes(self, state):
        changes = []
        if not self.player.exists:
            index = state.get(self.id, "index")
            found = False
            for player in self.loader.replay.players:
                if player.index is index:
                    self.player = player
                    changes.append(Change(ChangeType.SET, self.id, "connected", True))
                    found = True
            if not found and state.get(self.id, "connected") is True:
                changes.append(Change(ChangeType.SET, self.id, "connected", False))
                return changes
            elif not found:
                return changes
        if state.get(self.id, "kills") is not self.player.kills:
            changes.append(Change(ChangeType.SET, self.id, "kills", self.player.kills))
        if state.get(self.id,"deaths") is not self.player.deaths:
            changes.append(Change(ChangeType.SET, self.id, "deaths", self.player.deaths))
        if state.get(self.id,"assists") is not self.player.assists:
            changes.append(Change(ChangeType.SET, self.id, "assists", self.player.assists))
        if state.get(self.id,"streak") is not self.player.streak:
            changes.append(Change(ChangeType.SET, self.id, "streak", self.player.streak))
        if state.get(self.id,"last_hits") is not self.player.last_hits:
            changes.append(Change(ChangeType.SET, self.id, "last_hits", self.player.last_hits))
        if state.get(self.id,"denies") is not self.player.denies:
            changes.append(Change(ChangeType.SET, self.id, "denies", self.player.denies))
        #if state.get(self.id,"reliable_gold") is not self.player.reliable_gold:
        #    changes.append(Change(ChangeType.SET, self.id, "reliable_gold", self.player.reliable_gold))
        #if state.get(self.id,"unreliable_gold") is not self.player.unreliable_gold:
        #    changes.append(Change(ChangeType.SET, self.id, "unreliable_gold", self.player.unreliable_gold))
        #if state.get(self.id,"earned_gold") is not self.player.earned_gold:
        #    changes.append(Change(ChangeType.SET, self.id, "earned_gold", self.player.earned_gold))
        #if state.get(self.id,"has_buyback") is not self.player.has_buyback:
        #    changes.append(Change(ChangeType.SET, self.id, "has_buyback", self.player.has_buyback))
        #if state.get(self.id,"buyback_cooldown_time") is not self.player.buyback_cooldown_time:
        #    changes.append(Change(ChangeType.SET, self.id, "buyback_cooldown_time", self.player.buyback_cooldown_time))
        #if state.get(self.id,"last_buyback_time") is not self.player.last_buyback_time:
        #    changes.append(Change(ChangeType.SET, self.id, "last_buyback_time", self.player.last_buyback_time))
        return changes