function GameDisplay(node){
    var self = this;
    this.game = null;
    this.node = node;
    this.header_display = null;
    this.events_display = null;
    this.state_display = null;

    this.valid_game = false;

    this.init = function(game) {
        self.game = game;
        var state = self.game.state;
        console.log("state reset", state);

        if(state.exists(0)){
           self.valid_game = true;
        }
        else return;

        self.node.html("<div id=\"header_display\" style=\"text-align: center;\"></div>" +
            "<div class=\"row\">" +
            "<div class=\"col-lg-6\" id=\"state_display\"></div>" +
            "<div class=\"col-lg-6\" id=\"event_display\"></div>" +
            "</div>");

        self.header_display = new HeaderDisplay($("#header_display"));
        self.header_display.init(self.game);

        self.state_display = new StateDisplay($("#state_display"));
        self.state_display.init(self.game);

        self.events_display = new EventDisplay($("#event_display"));
        self.events_display.init(self.game);
    };

    this.update = function(update){
        if(!self.valid_game) {
            var game_creation_change = filterChanges(update["Changes"], 0, undefined, undefined, ChangeTypes.CREATE);
            if(game_creation_change.length > 0){
                self.valid_game = true;
                self.init();
            }
            else return;
        }
        self.header_display.update(update);
        self.state_display.update(update);
    };

    this.addEvent = function(event){
        self.events_display.addEvent(event);
    };
}

function HeaderDisplay(node){
    var self = this;
    this.game = null;
    this.node = node;

    this.init = function(game) {
        self.game = game;
        var state = self.game.state;

        self.node.html("<h2> <div id=\"title\"></div></h2><div id=\"time\"></div>");
        var game_id = state.get(0, "game_id");
        $("#title").html(game_id);
        self.refresh();
    };

    this.update = function(update){
        self.refresh();
    };

    this.refresh = function(){
        var time= $("#time");
        time.html(formattedTime(self.game.state.time));
    };

    this.addEvent = function(event){
    };
}

function StateDisplay(node){
    var self = this;
    this.game = null;
    this.node = node;
    this.draft_display = null;
    this.minimap_display = null;
    this.data_display = null;

    this.init = function(game) {
        self.game = game;
        var state = self.game.state;
        var game_state = state.get(0, "state");
        if(game_state == "draft"){
            self.initDraft();
        }
        else if(game_state == "pregame" || game_state == "game" || game_state == "postgame"){
            self.initMinimap();
        }
    };

    this.initDraft = function(){
        self.node.html("<div id=\"draft_display\"></div>");
        self.draft_display = new DraftDisplay(self.game, $("draft_display"));
        self.draft_display.init();
    };

    this.initMinimap = function(){
        console.log("Set Display to game");
        self.node.html("<div id=\"minimap_display\"></div><div id=\"data_display\"></div>");
        self.data_display = new DataDisplay($("#data_display"));
        self.data_display.init(self.game);
        self.minimap_display = new MinimapDisplay($("#minimap_display"), self.data_display);
        self.minimap_display.init(self.game);
    };

    this.update = function(update){
        var state_changes = filterChanges(update["Changes"], undefined, ObjectTypes.GAME, "state");
        for(var i=0; i<state_changes.length; ++i ){
            console.log("state change", state_changes[i]["Value"]);
            if(state_changes[i]["Value"] == "draft"){
                self.initDraft();
            }
            else if(state_changes[i]["Value"] == "pregame"){
                self.initMinimap();
            }
        }
        if(self.game.state.get(0, "state")== "draft"){
            self.draft_display.update(update);
        }
        else if(self.game.state.get(0, "state")== "pregame" || self.game.state.get(0, "state")== "game" || self.game.state.get(0, "state")== "postgame")
        {
            self.minimap_display.update(update);
            self.data_display.update(update);
        }
    };

    this.addEvent = function(event){

    }
}

function MinimapDisplay(node, data_display){
    var self = this;
    this.game = null;
    this.node = node;
    this.minimap = null;
    this.layers = [];
    this.images = ImageDirectory();

    this.data_display = data_display;

    var icon_size = 20;

    //Constants and helpers
    var WORLD_MAX_WIDTH  = 9216.0;
    var WORLD_MAX_HEIGHT = 8192.0;
    var WORLD_MIN_WIDTH = -8576.0;
    var WORLD_MIN_HEIGHT = -7680.0;

    var parameters_minimap = {};
    parameters_minimap["scale_x"] = 0.0185;
    parameters_minimap["scale_y"] = 0.0180;
    parameters_minimap["offset_x"] = 0;
    parameters_minimap["offset_y"] = 0;


    function decodePosition(position){
        return new Vector2(position["x"], position["y"]);
    }

    function convertCoordinates(position, image_parameters){
        var x_result = (-WORLD_MIN_WIDTH + position.x) * image_parameters.scale_x + image_parameters.offset_x;
        var y_result = (WORLD_MAX_HEIGHT - position.y) * image_parameters.scale_y + image_parameters.offset_y;
        return new Vector2(x_result, y_result);
    }

    this.init = function(game) {
        self.game = game;
        var state = self.game.state;
        self.node.html("<div id=\"minimap\"></div>");

        self.minimap = new Kinetic.Stage({
            container: 'minimap',
            width: 300,
            height: 300
          });

        self.layers["background"] = new Kinetic.Layer();
        self.minimap.add(self.layers["background"]);
        self.layers["buildings"] = new Kinetic.Layer();
        self.minimap.add(self.layers["buildings"]);
        self.layers["heroes"] = new Kinetic.Layer();
        self.minimap.add(self.layers["heroes"]);
        var loader = new PxLoader();
        self.images.loadImage(loader, "data/minimap.png", "minimap", function(){
            self.layers["background"].add(self.images["minimap"]);
            console.log("added minimap");
        });
        var players = state.get(0, "players");
        for(var player in players) {
            var hero_id = state.get(players[player], "hero");
            if(hero_id != null){
                console.log("requesting to load", hero_id, state.get(hero_id, "name"));
                self.loadHeroData(state.get(hero_id, "name"), hero_id, loader);
            }
        }
        loader.addCompletionListener(self.refresh);
        loader.start();
    };

    function getSetSelected(id){
        //console.log("getting setSelected", id)
        return function(){
            //console.log("setting selected", id)
            self.data_display.setSelected(id);
        }
    }

    function getAddHeroImage(id, name) {
        //console.log("creating adder for ", id, name);
        return function(e){
                self.images[name].setSize(icon_size, icon_size);
                /*images[name].createImageHitRegion(function() {
                    var canvas = new Kinetic.Canvas(this.width, this.height);
                    var context = canvas.getContext();
                    context.drawImage(this.attrs.image, 0, 0);
                });*/
                self.images[name].on("click", getSetSelected(id));
                self.layers["heroes"].add(self.images[name]);
            };
    }

    this.loadHeroData = function(name, id, loader) {
        var icon = name+"_icon";
        self.images.loadImage(loader, "data/icons/"+name+"_icon.png", icon, getAddHeroImage(id, icon));
    };

    this.update = function(update){
        var hero_name_changes = filterChanges(update["Changes"], undefined, ObjectTypes.HERO, "name");
        if(hero_name_changes.length > 0) {
            var heroesLoader = new PxLoader();
            for( var i in hero_name_changes){
                if(hero_name_changes[i]["Value"] != null){
                    self.loadHeroData(hero_name_changes[i]["Value"], hero_name_changes[i]["ID"], heroesLoader);
                }
            }
            heroesLoader.addCompletionListener(self.refresh);
            heroesLoader.start();
        }
        else
            self.refresh();
    };

    this.refresh = function(){
        var state = self.game.state;
        var players = state.get(0,"players");
        for(var player in players){
            var hero_id = state.get(players[player], "hero");
            if(hero_id != null)
            {
                var icon = state.get(hero_id, "name")+"_icon";
                if(!state.get(hero_id, "is_alive"))
                    self.images[icon].hide();
                else{
                    //console.log("icon",icon);
                    self.images[icon].show();
                }
                //console.log("Trying to draw ", game.state.get(hero_id, "name"));
                //console.log(game.state.get(hero_id, "name"), game.state.get(hero_id, "position").x, game.state.get(hero_id, "position").y, convertCoordinates(decodePosition(game.state.get(hero_id, "position")), parameters_minimap));
                var icon_position = convertCoordinates(decodePosition(game.state.get(hero_id, "position")), parameters_minimap);
                self.images[icon].setPosition(icon_position.x - (icon_size/2), icon_position.y - (icon_size/2));
            }
        }
        self.minimap.draw();
    }
}

function DataDisplay(node){
    var self = this;
    this.game = null;
    this.node = node;
    this.selected_unit = -1;

    this.init = function(game) {
        self.game = game;
        self.node.html("<h3>Unit Data</h3><div id=\"data\"></div>");
        self.refresh();
    };

    this.update = function(update){
        var selected_changes = filterChanges(update["Changes"], selected_unit);
            if(selected_changes.length > 0)
                self.refresh();
    };

    this.refresh = function(){
        var state = self.game.state;
        //console.log("refreshSelected called");
        var data_node = $("#data");
        var new_html = "";
        if(!(self.selected_unit in state.data)) {
            self.selected_unit = -1;
            new_html = "Nothing selected";
        }
        else {
            switch(state.get(self.selected_unit,"type")){
                case ObjectTypes.PLAYER:
                    new_html = state.get(self.selected_unit, "name")+": "+state.get(self.selected_unit, "kills") +"/"+state.get(self.selected_unit, "deaths")+"/"
                        +state.get(self.selected_unit, "assists")+" "+state.get(self.selected_unit, "last_hits")+"/"+state.get(self.selected_unit, "denies");
                    break;
                case ObjectTypes.HERO:
                    new_html = state.get(self.selected_unit, "name")+"(Lvl "+state.get(self.selected_unit,"level")+"):<br> HP "+state.get(self.selected_unit, "health") +"/"+state.get(self.selected_unit, "max_health")+"<br/>Mana: "
                        +Math.floor(state.get(self.selected_unit, "mana"))+"/"+Math.floor(state.get(self.selected_unit, "max_mana"));
                    break;
                default:
                    break;
            }
        }
        data_node.html(new_html);
    };

    this.addEvent = function(event){};

    this.setSelected = function(new_id){
        if(!(new_id in self.game.state.data)) {
            self.selected_unit = -1;
            console.log("Tried to select invalid object, reset to default");
        }
        else
            self.selected_unit = new_id;
        self.refresh();
    }
}

function DraftDisplay(node){
    var self = this;
    this.game = null;
    this.node = node;

    this.init = function(game) {
        self.game = game;
        var i;
        var draft_display = "<table><tr><td colspan = 5>Radiant</td><td id=\"reserve_radiant\"></td></tr><tr><td>Bans</td>";
        for(i =0; i<5; ++i)
            draft_display+="<td id=\"radiant_ban_"+i+"\"></td>";
        draft_display += "</tr><tr><td>Picks</td>";
        for(i =0; i<5; ++i)
            draft_display+="<td id=\"radiant_pick_"+i+"\"></td>";
        draft_display += "</tr>";

        draft_display += "<tr><td colspan = 5>Dire</td><td id=\"reserve_dire\"></td></tr><tr><td>Bans</td>";
        for(i =0; i<5; ++i)
            draft_display+="<td id=\"dire_ban_"+i+"\"></td>";
        draft_display += "</tr><tr><td>Picks</td>";
        for(i =0; i<5; ++i)
            draft_display+="<td id=\"dire_pick_"+i+"\"></td>";
        draft_display += "</tr></table>";
        console.log("Set Display to draft");
        self.node.html(draft_display);
        self.refresh();
    };

    this.update = function(update){
        var ban_changes = filterChanges(update["Changes"], undefined, ObjectTypes.DRAFT, "banned_heroes");
        var pick_changes = filterChanges(update["Changes"], undefined, ObjectTypes.DRAFT, "selected_heroes");
        if(ban_changes.length > 0 || pick_changes.length > 0)
            self.refresh();
    };

    this.refresh = function(){
        var state = game.state;
        var draft = state.get(0, "draft");
        var banned = state.get(draft, "banned_heroes");
        var picked = state.get(draft, "selected_heroes");
        var i;
        for(i =0; i<5; ++i){
            if(banned[i] != null){
                $("#radiant_ban_"+i).html("<img src=\"data/heroes/"+banned[i]+".png\" width=50px/>");
                //console.log("radiant ban ",i, banned[i]);
            }
            if(banned[i+5] != null){
                $("#dire_ban_"+i).html("<img src=\"data/heroes/"+banned[i+5]+".png\" width=50px/>");
                //console.log("dire ban ",i+5, banned[i+5]);
            }
        }
        for(i =0; i<5; ++i){
            if(picked[i] != null){
                $("#radiant_pick_"+i).html("<img src=\"data/heroes/"+picked[i]+".png\" width=50px/>");
                //console.log("radiant pick ",i, picked[i]);
            }
            if(picked[i+5] != null){
                $("#dire_pick_"+i).html("<img src=\"data/heroes/"+picked[i+5]+".png\" width=50px/>");
                //console.log("dire pick ",i+5, picked[i+5]);
            }
        }
    };
}

var event_window = 60*TICKS_PER_SEC;

function EventDisplay(node){
    var self = this;
    this.game = null;
    this.node = node;
    this.events_div = null;

    this.init = function(game) {
        self.game = game;
        var state = self.game.state;
        var event_display = "<h3>Events</h3><div id=\"events\">events</div>";
        self.node.html(event_display);
        self.events_div = $("#events");
    };

    this.update = function(update){};

    this.refresh = function(){
        self.events_div.html("");
        var events = self.game.events
        for (var i = events.length -1; i >= 0; --i){
            var event = events[i];
            if(event["Time"] < self.game.state.time - event_window)
                break;
            var p = document.createElement("p");
            if(event["Type"] == EventType.STATECHANGE)
            {
                p.innerHTML = formattedTime(event["Time"]) +" :<br/> Changed State to "+event["State"];
            }
            else if(event["Type"] == EventType.TEXTEVENT)
            {
                p.innerHTML = formattedTime(event["Time"]) +" :<br/> "+event["Text"];
            }
            else if(event["Type"] == EventType.DRAFTEVENT)
            {
                p.innerHTML = formattedTime(event["Time"]) +" :<br/>The "+event["Team"]+ " " + event["Action"]+" "+ event["Hero"]+ " after "+Math.floor(event["TimeUsed"]/TICKS_PER_SEC)+" sec.";
            }
            else
            {
                p.innerHTML = "Event at "+formattedTime(event["Time"])+" :<br/> "+event["Type"];
            }
            self.events_div.append(p);
        }
    };

    this.addEvent = function(event){
        this.refresh();
    };
}


/*
    Helpers for displaying
 */

function formattedTime(state){
    var parsedTime = parseInt(state.time);
    if(!state.exists(0)){
        console.log("no info");
        return "";
    }
    return formatTimeState(parsedTime, state.get(0,"state"));
}

function formatTimeState(time, state){
    var TICKS_PER_SECOND = 30.0;
    var offset = 0;
    if(state == "draft"){
        offset = game.state.get(0,"draft_start_time");
        if(time - offset < 0)
            return formatTimeState(time, "loading");
    }
    else if(state == "pregame"){
        offset = game.state.get(0,"pregame_start_time");
        if(time - offset < 0)
            return formatTimeState(time, "draft");
    }
    else if( state == "game"){
        offset = game.state.get(0,"game_start_time");
        if(time - offset < 0)
            return formatTimeState(time, "pregame");
    }
    else if( state == "postgame"){
        offset = game.state.get(0,"game_end_time");
        if(time - offset < 0)
            return formatTimeState(time, "game");
    }
    var seconds = (time - offset) / TICKS_PER_SECOND;
    var result = "";

    var formattedState = "";
    if(state == "loading")
        formattedState = "Loading";
    else if(state == "pregame")
        formattedState = "Pregame";
    else if(state == "game")
        formattedState = "Game";
    else if(state == "postgame")
        formattedState = "Postgame";
    result += state + " "+zeroPad(Math.floor(seconds/60),2) + ":" + zeroPad(Math.floor(seconds%60),2);
    return result;
}