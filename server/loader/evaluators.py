from server.loader.loaders import ObjectTypes
from server.libs import events as Events


class Evaluator(object):
    def __init__(self, loader):
        self.loader = loader
        self.loader.evaluators.append(self)
        self.removed = False

    def evaluate(self):
        pass


class StateEvaluator(Evaluator):
    def __init__(self, loader):
        super(StateEvaluator, self).__init__(loader)
        ChatEvaluator(self.loader)

    def evaluate(self):
        state_changes = self.loader.filter_changes(object_type=ObjectTypes.GAME, attribute="state")
        if len(state_changes) > 0:
            print "state is changing"
            if len(state_changes) > 1:
                print "found multiple state changes?"
            print [x.serialize() for x in state_changes]
            event = Events.StateChange(self.loader.tick, state_changes[0].value)
            self.loader.add_event(event)
            if state_changes[0].value == "draft":
                DraftEvaluator(self.loader, state_changes[0].id)
            elif state_changes[0].value == "pregame":
                GameEvaluator(self.loader)


class GameEvaluator(Evaluator):
    def __init__(self, loader):
        super(GameEvaluator, self).__init__(loader)

    def evaluate(self):
        #message big/relevant changes
        #message pauses
        pause_changes = self.loader.filter_changes(attribute="pausing_team")
        for pause_change in pause_changes:
            if pause_change.value is None:
                event = Events.TextEvent(self.loader.tick, "Game unpaused")
            else:
                event = Events.TextEvent(self.loader.tick, "Game paused by the {}".format(pause_change.value))
            self.loader.add_event(event)
        #message deaths/respawns
        hero_alive_changes = self.loader.filter_changes(object_type=ObjectTypes.HERO, attribute="is_alive")
        for change in hero_alive_changes:
            if change.value is False:
                event = Events.TextEvent(self.loader.tick, "{} died".format(self.loader.game.current_state.get(change.id, "name")))
            else:
                event = Events.TextEvent(self.loader.tick, "{} respawned".format(
                    self.loader.game.current_state.get(change.id, "name")))
            self.loader.add_event(event)


class ChatEvaluator(Evaluator):
    def __init__(self, loader):
        super(ChatEvaluator, self).__init__(loader)

    def evaluate(self):
        chat_events = []  # self.replay.chat_events
        if len(chat_events) > 0:
            for chat_event in chat_events:
                print "event {}".format(chat_event)
                self.loader.self.game.add_event(self.create_chat_event(chat_event))

    def create_chat_event(self, chat_event):
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
        return Events.ChatEvent(self.loader.tick, chat_event.type, chat_event.value, player_ids)


class DraftEvaluator(Evaluator):
    def __init__(self, loader, game_obj):
        super(DraftEvaluator, self).__init__(loader)
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
        state_changes = self.loader.filter_changes(object_type=ObjectTypes.GAME, attribute="state")
        for change in state_changes:
            if change.value != "draft":
                self.removed = True
                print "removing draft eval"