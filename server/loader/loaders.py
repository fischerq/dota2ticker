from server.libs.utils import enum
from server.libs.game import ChangeType, Change


class ObjectLoader(object):
    def __init__(self, loader):
        self.loader = loader
        self.id = self.loader.game.get_object_id()
        self.loader.add_change(Change(ChangeType.CREATE, self.id, value=None))
        self.identifier = None
        self.changes = []
        self.state = None
        self.removed = False
        self.checks = []
        self.loader.loaders.append(self)

    def check(self):
        self.state = self.loader.game.current_state
        for check in self.checks:
            check()
            if self.removed:
                break

    def remove(self):
        self.loader.add_change(Change(ChangeType.DELETE, self.id))
        self.removed = True

    def set_attribute(self, attribute, value):
        self.loader.add_change(Change(ChangeType.SET, self.id, attribute, value))

    def check_attribute(self, attribute, value):
        if self.state.get(self.id, attribute) != value:
            if attribute == "name":
                print "setting name {}:{}".format(self.id, value)
            self.loader.add_change(Change(ChangeType.SET, self.id, attribute, value))
            return True
        else:
            return False

ObjectTypes = enum("GAME",
                   "DRAFT",
                   "PLAYER",
                   "HERO",
                   "ILLUSION")


class GameLoader(ObjectLoader):
    def __init__(self, loader, game_id):
        super(GameLoader, self).__init__(loader)
        self.replay = loader.replay
        self.set_attribute("type", ObjectTypes.GAME)
        self.set_attribute("game_id", game_id)
        self.set_attribute("game_mode", self.replay.info.game_mode)
        self.set_attribute("state", self.replay.info.game_state)
        self.checks.append(self.check_game)

    def check_game(self):
        if self.replay.info.game_state is not self.state.get(self.id, "state"):
            if self.replay.info.game_state is "loading":
                pass
            elif self.replay.info.game_state is "draft":
                print "draft {}".format(self.replay.tick)
                self.set_attribute("draft_start_time", self.replay.tick)
                draft_loader = DraftLoader(self.loader, self.replay.info)
                self.set_attribute("draft", draft_loader.id)
            elif self.replay.info.game_state is "pregame":
                print "pregame {}".format(self.replay.tick)
                self.set_attribute("pregame_start_time", self.replay.tick)
                #start game loading
                players = []
                for player in self.replay.players:
                    if player.index is not None:
                        player_loader = PlayerLoader(self.loader, player)
                        players.append(player_loader.id)
                self.set_attribute("players", players)
            elif self.replay.info.game_state is "game":
                print "game {}".format(self.replay.tick)
                self.set_attribute("game_start_time", self.replay.tick)
            elif self.replay.info.game_state is "postgame":
                self.set_attribute("game_end_time", self.replay.tick)
            else:
                print "strange state {}".format(self.replay.info.game_state)
        self.check_attribute("state", self.replay.info.game_state)
        self.check_attribute("pausing_team", self.replay.info.pausing_team)


class DraftLoader(ObjectLoader):
    def __init__(self, loader, info):
        super(DraftLoader, self).__init__(loader)
        self.info = info
        self.set_attribute("type", ObjectTypes.DRAFT)
        self.checks.append(self.check_draft)

    def check_draft(self):
        self.check_attribute("active_team", self.info.active_team)
        if self.info.pick_state is not None:
            action, number = self.info.pick_state
            self.check_attribute("active_action", action)
            self.check_attribute("action_number", number)
#        print "extra time: {}".format(self.info.extra_time)
        self.check_attribute("extra_time", self.info.extra_time)
        self.check_attribute("captain_ids", self.info.captain_ids)
        self.check_attribute("banned_heroes", self.info.banned_heroes)
        self.check_attribute("selected_heroes", self.info.selected_heroes)


class EntityLoader(ObjectLoader):
    def __init__(self, loader, entity):
        super(EntityLoader, self).__init__(loader)
        self.identifier = entity.ehandle
        self.entity = entity
        self.checks.append(self.check_entity)

    def check_entity(self):
        if not self.entity.exists:
            print "Removing {} {}".format(self.id, self.__class__)
            self.remove()


def encode_position(position):
    result = dict()
    result["x"] = position[0]
    result["y"] = position[1]
    return result


class BaseNPCLoader(EntityLoader):
    def __init__(self, loader, npc):
        super(BaseNPCLoader, self).__init__(loader, npc)
        self.npc = npc
        self.checks.append(self.check_base_npc)

    def check_base_npc(self):
        self.check_attribute("is_alive", self.npc.is_alive)
        self.check_attribute("position", encode_position(self.npc.position))
        self.check_attribute("level", self.npc.level)
        self.check_attribute("health", self.npc.health)
        self.check_attribute("health_regen", self.npc.health_regen)
        self.check_attribute("max_health", self.npc.max_health)
        self.check_attribute("mana", self.npc.mana)
        self.check_attribute("mana_regen", self.npc.mana_regen)
        self.check_attribute("max_mana", self.npc.max_mana)


class HeroLoader(BaseNPCLoader):
    def __init__(self, loader, hero):
        super(HeroLoader, self).__init__(loader, hero)
        self.hero = hero
        if self.hero.replicating_hero is None:
            self.set_attribute("type", ObjectTypes.HERO)
        else:
            self.set_attribute("type", ObjectTypes.ILLUSION)
            replicating_id = None
            for loader in self.loader.loaders:
                if loader.identifier is self.hero.replication_hero.ehandle:
                    replicating_id = loader.id
            self.set_attribute("replicating", replicating_id)
        self.checks.append(self.check_hero)

    def check_hero(self):
        self.check_attribute("name", self.hero.name)
        self.check_attribute("respawn_time", self.hero.respawn_time)
        self.check_attribute("xp", self.hero.xp)
        self.check_attribute("ability_points", self.hero.ability_points)
        self.check_attribute("strength", self.hero.strength)
        self.check_attribute("agility", self.hero.agility)
        self.check_attribute("intelligence", self.hero.intelligence)
        self.check_attribute("natural_strength", self.hero.natural_strength)
        self.check_attribute("natural_agility", self.hero.natural_agility)
        self.check_attribute("natural_intelligence", self.hero.natural_intelligence)


class PlayerLoader(EntityLoader):
    def __init__(self, loader, player):
        super(PlayerLoader, self).__init__(loader, player)
        self.player = player
        self.identifier = player.ehandle
        self.set_attribute("type", ObjectTypes.PLAYER)
        self.set_attribute("team", self.player.team)
        self.set_attribute("steam_id", self.player.steam_id)
        self.set_attribute("name", self.player.name)
        self.set_attribute("index", self.player.index)
        self.set_attribute("connected", True)
        if self.player.hero is not None:
            hero_loader = HeroLoader(self.loader, self.player.hero)
            self.set_attribute("hero", hero_loader.id)
            self.loader.loaders.append(hero_loader)
        else:
            self.set_attribute("hero", None)
        self.checks.append(self.check_hero)
        #print "checks {} {}".format(self.id, self.checks)
        self.checks.remove(self.check_entity)  #do not remove players when they get invalid -> reconnecting
        #print "checks removed {}".format(self.checks)

    def check_hero(self):
        if not self.player.exists:
            index = self.state.get(self.id, "index")
            found = False
            for player in self.loader.replay.players:
                if player.index is index:
                    self.player = player
                    self.set_attribute("connected", True)
                    found = True
            if not found and self.state.get(self.id, "connected") is True:
                self.set_attribute("connected", False)
                return
            elif not found:
                return
        if self.state.get(self.id, "hero") is None and self.player.hero:
            hero_loader = HeroLoader(self.loader, self.player.hero)
            self.set_attribute("hero", hero_loader.id)
            self.loader.loaders.append(hero_loader)
        self.check_attribute("kills", self.player.kills)
        self.check_attribute("deaths", self.player.deaths)
        self.check_attribute("assists", self.player.assists)
        self.check_attribute("streak", self.player.streak)
        self.check_attribute("last_hits", self.player.last_hits)
        self.check_attribute("denies", self.player.denies)
        self.check_attribute("reliable_gold", self.player.reliable_gold)
        self.check_attribute("unreliable_gold", self.player.unreliable_gold)
        self.check_attribute("earned_gold", self.player.earned_gold)
        self.check_attribute("has_buyback", self.player.has_buyback)
        self.check_attribute("buyback_cooldown_time", self.player.buyback_cooldown_time)
        self.check_attribute("last_buyback_time", self.player.last_buyback_time)