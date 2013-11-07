#!/usr/bin/env python

from threading import Thread
from game import *
import time
import tarrasque

from events import *


class GameLoader:
    def __init__(self, game_id, game):
        self.game = game
        self.game_id = game_id
        pass

    def load(self):
        Thread(target=self.load_game).start()

    def load_game(self):
        state = State(0)
        self.game.initialise(state)

        file_replay = "data/replays/{}.dem".format(self.game_id)
        replay = tarrasque.StreamBinding.from_file(file_replay, start_tick="start")
        last_state = None
        last_tick = 0
        current_tick = 0
        for tick in replay.iter_ticks():
            last_tick = current_tick
            current_tick = replay.tick
            if replay.info.game_state is not last_state:
                event = StateChange(current_tick, replay.info.game_state)
                self.game.add_event(event)
                if replay.info.game_state is "loading":
                    pass
                elif replay.info.game_state is "draft":
                    pass
                elif replay.info.game_state is "pregame":
                    pass
                elif replay.info.game_state is "game":
                    pass
                elif replay.info.game_state is "postgame":
                    pass

                else:
                    print "strange state {}".format(replay.info.game_state)
                last_state = replay.info.game_state

            #print chat information in every state
            chat_events = replay.chat_events
            if len(chat_events) > 0:
                for chat_event in chat_events:
                    print "event {}".format(chat_event)
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
                    self.game.add_event(ChatEvent(current_tick, chat_event.type, chat_event.value))

            if replay.info.game_state is "start":
                #message loading information
                pass
            elif replay.info.game_state is "draft":
                #message drafting
                pass
            elif replay.info.game_state is "pregame" or replay.info.game_state is "game":
                #update changes in game
                #message big changes
                pass
            elif replay.info.game_state is "postgame":

                pass
            elif replay.info.game_state is "end":
                pass
        self.game.finish()