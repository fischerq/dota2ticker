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

    def check(self):
        self.state = self.loader.game.current_state
        self.check_changes()

    def check_changes(self):
        pass

    def remove(self):
        self.loader.add_change(Change(ChangeType.DELETE, self.id))

    def set_attribute(self, attribute, value):
        self.loader.add_change(Change(ChangeType.SET, self.id, attribute, value))

    def check_attribute(self, attribute, value):
        if self.state.get(self.id,attribute) is not value:
            if attribute is "name":
                print "setting name {}:{}".format(self.id, value)
            self.loader.add_change(Change(ChangeType.SET, self.id, attribute, value))

    def check_removal(self):
        return False

ObjectTypes = enum("GAME",
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
        self.set_attribute("draft_start_time", self.replay.info.draft_start_time)
        self.set_attribute("game_start_time", self.replay.info.game_start_time)

    def check_changes(self):
        if self.replay.info.game_state is not self.state.get(self.id, "state"):
            if self.replay.info.game_state is "draft":
                pass
            elif self.replay.info.game_state is "pregame":
                #start game loading
                players = []
                for player in self.replay.players:
                    if player.index is not None:
                        player_loader = PlayerLoader(self.loader, player)
                        players.append(player_loader.id)
                        self.loader.loaders.append(player_loader)
                self.set_attribute("players", players)
            elif self.replay.info.game_state is "postgame":
                pass
            elif self.replay.info.game_state is "loading" or self.replay.info.game_state is "game":
                pass
            else:
                print "strange state {}".format(self.replay.info.game_state)
        self.check_attribute("state", self.replay.info.game_state)


class EntityLoader(ObjectLoader):
    def __init__(self, loader, entity):
        super(EntityLoader, self).__init__(loader)
        self.identifier = entity.ehandle
        self.entity = entity

    def check_removal(self):
        return not self.entity.exists


def encode_position(position):
    result = dict()
    result["x"] = position[0]
    result["y"] = position[1]
    return result


class BaseNPCLoader(EntityLoader):
    def __init__(self, loader, npc):
        super(BaseNPCLoader, self).__init__(loader, npc)
        self.npc = npc

    def check_changes(self):
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

    def check_changes(self):
        super(HeroLoader, self).check_changes()
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

    def check_changes(self):
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

    def check_removal(self):
        # keep players after disconnect
        return False