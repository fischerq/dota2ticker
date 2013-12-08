#!/usr/bin/env python
from threading import Thread
import tarrasque

from server.libs import events as Events
from server.loader.loaders import GameLoader, ObjectTypes
from server.libs.game import Game, Update, ChangeType
from server.libs.utils import UNDEFINED


COMPRESSION_PRECISION = 10


class ReplayLoader:
    def __init__(self, game_id, loader_server):
        self.loader_server = loader_server
        self.game = Game()
        self.game_id = game_id
        self.loaders = []
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
        game_loader = GameLoader(self, self.game_id)
        draft_evaluator = None
        for _ in self.replay.iter_ticks():
            self.tick = self.replay.tick
            self.changes_tick = []
            #execute all loaders
            new_loaders = []
            for loader in self.loaders:
                loader.check()
            self.loaders = [loader for loader in self.loaders if not loader.removed]
            #print "changed {}".format(self.changes_cache)
            #message game state changes
            state_changes = self.filter_changes(object_type=ObjectTypes.GAME, attribute="state")
            if len(state_changes) > 0:
                print "state is changing"
                if len(state_changes) > 1:
                    print "found multiple state changes?"
                print [x.serialize() for x in state_changes]
                event = Events.StateChange(self.tick, state_changes[0].value)
                self.add_event(event)
                if state_changes[0].value == "draft":
                    draft_evaluator = DraftEvaluator(self, state_changes[0].id)
             #always message chat information
            chat_events = []  # self.replay.chat_events
            if len(chat_events) > 0:
                for chat_event in chat_events:
                    print "event {}".format(chat_event)
                    self.add_chat_event(self.tick, chat_event)
            #generate messages
            if self.replay.info.game_state is "start":
                #message loading information
                pass
            elif self.replay.info.game_state is "draft":
                draft_evaluator.evaluate()
            elif self.replay.info.game_state is "pregame" or self.replay.info.game_state is "game":
                #message big/relevant changes
                #message pauses
                pause_changes = self.filter_changes(attribute="pausing_team")
                for pause_change in pause_changes:
                    if pause_change.value is None:
                        event = Events.TextEvent(self.tick, "Game unpaused")
                    else:
                        event = Events.TextEvent(self.tick, "Game paused by the {}".format(pause_change.value))
                    self.add_event(event)
                #message deaths/respawns
                hero_alive_changes = self.filter_changes(object_type=ObjectTypes.HERO, attribute="is_alive")
                for change in hero_alive_changes:
                    if change.value is False:
                        event = Events.TextEvent(self.tick, "{} died".format(self.game.current_state.get(change.id, "name")))
                    else:
                        event = Events.TextEvent(self.tick, "{} respawned".format(self.game.current_state.get(change.id, "name")))
                    self.add_event(event)
            elif self.replay.info.game_state is "postgame":
                pass
            elif self.replay.info.game_state is "end":
                pass
        self.finish()

    def add_change(self, change):
        self.changes_tick.append(change)
        update = Update(self.tick, [change])
        self.game.add_update(update)
        if self.tick >= self.cache_start + COMPRESSION_PRECISION:
            self.loader_server.send_update(self.cache_update)
            self.cache_start = self.tick
            self.cache_update = Update(self.tick)
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
        self.game.add_event(Events.ChatEvent(current_tick, chat_event.type, chat_event.value, player_ids))


class DraftEvaluator:
    def __init__(self, loader, game_obj):
        self.loader = loader
        self.draft_id = self.loader.game.current_state.get(game_obj, "draft")
        self.team_drafting = None
        self.pick_start_time = None
        self.old_bans = None
        self.old_picks = None
        self.update()

    def update(self):
        self.team_drafting = self.loader.game.current_state.get(self.draft_id, "active_team")
        self.pick_start_time = self.loader.tick
        self.old_bans = self.loader.game.current_state.get(self.draft_id, "banned_heroes")
        self.old_picks = self.loader.game.current_state.get(self.draft_id, "selected_heroes")

    def evaluate(self):
        ban_changes = self.loader.filter_changes(object_type=ObjectTypes.DRAFT, attribute="banned_heroes")
        for ban_change in ban_changes:
            for i in range(0, 10):
                if ban_change.value[i] != self.old_bans[i]:
                    self.loader.add_event(
                        Events.DraftEvent(self.loader.tick, self.team_drafting, "ban", ban_change.value[i],
                                          self.loader.tick-self.pick_start_time))
                    self.update()
        pick_changes = self.loader.filter_changes(object_type=ObjectTypes.DRAFT, attribute="selected_heroes")
        for pick_change in pick_changes:
            for i in range(0, 10):
                if pick_change.value[i] != self.old_picks[i]:
                    self.loader.add_event(
                        Events.DraftEvent(self.loader.tick, self.team_drafting, "pick", pick_change.value[i],
                                          self.loader.tick-self.pick_start_time))
                    print "Messaged pick {}".format(pick_change.value[i])
                    self.update()
