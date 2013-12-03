$( document ).ready(function() {
	try {
        var connection_connection;
        var connection;
        var confirmed = false;
        var subscribed = false;
        var valid_game = false;
        var client_id;
        var game_id;

        var events_display = $("#events");

        var view_data = $("#view-data");
        var images = {};

        var minimap = new Kinetic.Stage({
                container: 'minimap',
                width: 300,
                height: 300
              });
        var layers = {};
        var TICKS_PER_SEC = 30;
        var event_window = 60*TICKS_PER_SEC;
        var selected_unit = -1;
        var game = new Game();
        var icon_size = 20;
        var refresh_interval = 2000;

        function registerImage(name, img){
            images[name] = new Kinetic.Image({
                image: img
                });
            console.log("registered ",name, images[name]);
        }

        function loadImage(loader, file, name, callback) {
            if(name in images) {
                console.log("prevented reloading", name, file);
                return;
            }
            loader.addImage(file, name);
            loader.addProgressListener(function(e){
                registerImage(name, e.resource.img);
                callback();
            }, name);
        }

        function refresh(){
            if(valid_game){
                refreshEvents();
                refreshDisplay();
                refreshSelected();
                refreshHeader();
            }
            setTimeout(refresh, refresh_interval);
        }

        function formatTime(time){
            var parsedTime = parseInt(time);
            if(!game.current_state.exists(0)){
                console.log("no info")
                return "";
            }
            return formatTimeState(parsedTime, game.current_state.get(0,"state"));
        }

        function formatTimeState(time, state){
            var TICKS_PER_SECOND = 30.0;
            var offset = 0;
            if(state == "draft"){
                offset = game.current_state.get(0,"draft_start_time");
                if(time - offset < 0)
                    return formatTimeState(time, "loading");
            }
            else if(state == "pregame"){
                offset = game.current_state.get(0,"pregame_start_time");
                if(time - offset < 0)
                    return formatTimeState(time, "draft");
            }
            else if( state == "game"){
                offset = game.current_state.get(0,"game_start_time");
                if(time - offset < 0)
                    return formatTimeState(time, "pregame");
            }
            else if( state == "postgame"){
                offset = game.current_state.get(0,"game_end_time");
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

        function init(){
            var title = $("#header-title");
            //console.log("updated header title");
            title.html(game_id);

            layers["background"] = new Kinetic.Layer();
            minimap.add(layers["background"]);
            layers["buildings"] = new Kinetic.Layer();
            minimap.add(layers["buildings"]);
            layers["heroes"] = new Kinetic.Layer();
            minimap.add(layers["heroes"]);
            var imageLoader = new PxLoader();
            loadImage(imageLoader, "data/minimap.png", "minimap", function(){
                layers["background"].add(images["minimap"]);
                console.log("added minimap");
            });
            imageLoader.addCompletionListener(refresh, "minimap");
            imageLoader.start();

            setTimeout(refresh, refresh_interval);
        }

        function refreshHeader(){
            var time= $("#time");
            var paused = "";
            if(game.current_state.get(0, "pausing_team") != null)
                paused = "<br/> Currently paused by "+game.current_state.get(0, "pausing_team");
            time.html(formatTime(game.current_state.time)+paused);
        }

        function refreshSelected(){
            var state = game.current_state;
            var data_display = $("#view-data");
            //console.log("refreshSelected called");
            var new_html = "";
            if(!(selected_unit in state.data)) {
                selected_unit = -1;
                new_html = "Nothing selected";
            }
            else if(state.get(selected_unit,"type") == ObjectTypes.PLAYER){
                new_html=state.get(selected_unit, "name")+": "+state.get(selected_unit, "kills") +"/"+state.get(selected_unit, "deaths")+"/"
                    +state.get(selected_unit, "assists")+" "+state.get(selected_unit, "last_hits")+"/"+state.get(selected_unit, "denies");
            }
            else if(state.get(selected_unit,"type") == ObjectTypes.HERO){
                //console.log("cant select heroes, bad");
                //selected_unit = state.get(selected_unit, "player");
                new_html=state.get(selected_unit, "name")+"(Lvl "+state.get(selected_unit,"level")+"):<br> HP "+state.get(selected_unit, "health") +"/"+state.get(selected_unit, "max_health")+"<br/>Mana: "
                    +Math.floor(state.get(selected_unit, "mana"))+"/"+Math.floor(state.get(selected_unit, "max_mana"));
            }
            data_display.html(new_html);
        }

        function refreshEvents(){
            events_display.html("");
            for (var key in game.events){
                var event = game.events[key];
                if(event["Time"] < game.current_state.time - event_window)
                    continue;
                var p = document.createElement("p");
                if(event["Type"] == EventType.STATECHANGE)
                {
                    p.innerHTML = formatTime(event["Time"]) +" :<br/> Changed State to "+event["State"];
                }
                else if(event["Type"] == EventType.TEXTEVENT)
                {
                    p.innerHTML = formatTime(event["Time"]) +" :<br/> "+event["Text"];
                }
                else
                {
                    p.innerHTML = "Event at "+formatTime(event["Time"])+" :<br/> "+event["Type"];
                }
                events_display.append(p);
            }
        }

        function refreshDisplay(){
            if(!(0 in game.current_state.data))
                return;
            var players = game.current_state.get(0,"players");
            for(var player in players){
                var hero_id = game.current_state.get(players[player], "hero");
                if(hero_id != null)
                {
                    var icon = game.current_state.get(hero_id, "name")+"_icon";
                    if(!game.current_state.get(hero_id, "is_alive"))
                       images[icon].hide();
                    else
                        images[icon].show();
                    //console.log("Trying to draw ", game.current_state.get(hero_id, "name"));
                    //console.log(game.current_state.get(hero_id, "name"), game.current_state.get(hero_id, "position").x, game.current_state.get(hero_id, "position").y, convertCoordinates(decodePosition(game.current_state.get(hero_id, "position")), parameters_minimap));
                    var icon_position = convertCoordinates(decodePosition(game.current_state.get(hero_id, "position")), parameters_minimap);
                    images[icon].setPosition(icon_position.x - (icon_size/2), icon_position.y - (icon_size/2));
                }
            }
            minimap.draw();
        }

        function filter_changes( changes, object_id, object_type, attribute, change_type){
            var result = new Array();
            for(var change in changes){
                var accepted = true;
                if(object_id != undefined)
                    accepted = accepted && changes[change]["ID"] == object_id;
                if(change_type != undefined)
                    accepted = accepted && changes[change]["Type"] == change_type;
                if (object_type != undefined){
                    if(changes[change]["Type"] == ChangeTypes.CREATE)
                        accepted = false;
                    else
                        accepted = accepted && game.current_state.get(changes[change]["ID"], "type") == object_type;
                }
                if (attribute != undefined)
                    accepted = accepted && changes[change]["Attribute"] == attribute;
                if (accepted)
                    result.push(changes[change])
            }
            return result;
        }

        function getSetSelected(id){
            //console.log("getting setSelected", id)
            return function(){
                //console.log("setting selected", id)
                selected_unit = id;
                refreshSelected();
            }
        }

        function getAddHeroImage(id, name) {
            //console.log("creating adder for ", id, name);
            return function(e){
                    images[name].setSize(icon_size, icon_size);
                    /*images[name].createImageHitRegion(function() {
                        var canvas = new Kinetic.Canvas(this.width, this.height);
                        var context = canvas.getContext();
                        context.drawImage(this.attrs.image, 0, 0);
                    });*/
                    images[name].on("click", getSetSelected(id));
                    layers["heroes"].add(images[name]);
                };
        }

        function loadHeroData(name, id, loader) {
            var icon = name+"_icon";
            loadImage(loader, "data/icons/"+name+"_icon.png", icon, getAddHeroImage(id, icon));
        }

        function updateStateReset(state) {
            console.log("state reset", state);
            init();
            if(state.exists(0)){
                valid_game = true;
                var loader = new PxLoader();
                var players = state.get(0, "players");
                for(var player in players) {
                    var hero_id = state.get(players[player], "hero");
                    if(hero_id != null){
                        loadHeroData(state.get(hero_id, "name"), hero_id, loader);
                    }
                }
                loader.addCompletionListener(refreshDisplay);
                loader.start();
            }
        }

        function updateStateUpdate(update){
            if(!valid_game) {
                var game_creation_change = filter_changes(update["Changes"], 0, undefined, undefined, ChangeTypes.CREATE);
                if(game_creation_change.length > 0)
                    valid_game = true;
                else return;
            }
            //update selected object if needed
            var selected_changes = filter_changes(update["Changes"], selected_unit);
            if(selected_changes.length > 0)
                refreshSelected();
            //load images if needed
            var hero_name_changes = filter_changes(update["Changes"], undefined, ObjectTypes.HERO, "name");
            if(hero_name_changes.length > 0) {
                var heroesLoader = new PxLoader();
                for( var i in hero_name_changes){
                    if(hero_name_changes[i]["Value"] != null){
                        loadHeroData(hero_name_changes[i]["Value"], hero_name_changes[i]["ID"], heroesLoader);
                    }
                }
                heroesLoader.addCompletionListener(refreshDisplay);
                heroesLoader.start();
            }
            else
                refreshDisplay();
            refreshEvents();
            refreshHeader();
        }

        function sendConnect() {
            var connectRequest = new Object();
            connectRequest["Type"] = MessageType.CONNECT;
            connectRequest["GameID"] = game_id;
            connection_connection.send(connectRequest);
            console.log("sending connection message");
        }

        function connect(new_game_id) {
            game_id = new_game_id;
            connection_connection = new DataConnection(HOST_IP, HOST_PORT, handleConnectionMessage, sendConnect);
        }

        function handleConnectionMessage(message) {
            if(message["Type"] == MessageType.GAME_AVAILABILITY){
                if(message["Availability"] == AvailabilityType.AVAILABLE)
                    console.log("Yay, game available. wait for connection info");
                else if(message["Availability"] == AvailabilityType.PENDING)//Try again later
                {
                    setTimeout(function(){connect(game_id)}, 1000);
                    console.log("game is pending, try again in 1sec");
                }
                else if(message["Availability"] == AvailabilityType.UNAVAILABLE)
                    alert("Game unavailable");
            }
            else if (message["Type"] == MessageType.CLIENT_INFO) {
                console.log("received client info");
                client_id = message["ClientID"];
                game_id = message["GameID"];
                connection = new DataConnection(message["Host"], message["Port"], handleMessage, openConnection, closeConnection);
            }
            else{
                console.log("Unknown MessageType: ", message["Type"], message);
            }
        }


        function openConnection(e) {
            console.log("connection opened.");
            var registerRequest = new Object();
            registerRequest["Type"] = MessageType.REGISTER;
            registerRequest["GameID"] = game_id;
            connection.send(registerRequest);
        }

        function handleMessage(message) {
            if(!confirmed){
                if(message["Type"] == MessageType.CONFIRM){
                    confirmed= true;
                    console.log("confirmed requests");
                    requestSubscribe(SubscribeMode.CURRENT, 0);
                }
                else{
                    console.log("unconfirmed channel received message");
                }
                return;
            }
            if(checkMessage(message)) {
                switch(message["Type"]) {
                    case MessageType.STATE:
                        game.setState(message["Time"], message["State"], message["Events"]);
                        updateStateReset(game.current_state);
                        refresh();
                        break;
                    case MessageType.UPDATE:
                        if(message["Time"] < game.current_state.time){
                            console.log("Received bad update: past");
                        }
                        else{
                            game.addUpdate(message["Update"]);
                            updateStateUpdate(message["Update"]);
                        }
                        break;
                    case MessageType.EVENT:
                        //check event time
                        game.addEvent(message["Event"]);
                        refreshEvents();
                        break;
                }
            }
            else{
                console.log("Received bad message", message);
            }
        }
        function closeConnection(e) {
             console.log("connection closed.");
        }

        function requestConfigure(setting, value) {
            if(!confirmed){
                console.log("unconfirmed request channel");
                return;
            }
            var configure = new Object();
            configure["Type"] = MessageType.CONFIGURE;
            configure["Setting"] = setting;
            configure["Value"] = value;
            connection.send(configure);
        }
        function requestSubscribe(mode, time) {
            if(!confirmed){
                console.log("unconfirmed channel");
                return;
            }
            else if(subscribed) {
                console.log("trying to subscribe, already subscribed");
            }
            var subscriptionMessage = new Object();
            subscriptionMessage["Type"] = MessageType.SUBSCRIBE;
            subscriptionMessage["Mode"] = mode;
            subscriptionMessage["Time"] = time;
            connection.send(subscriptionMessage);
            subscribed = true;
        }
        function requestUnsubscribe() {
            if(!confirmed){
                console.log("unconfirmed channel");
                return;
            }
            else if(!subscribed) {
                console.log("trying to unsubscribe, not subscribed");
            }
            var unsubscriptionMessage = new Object();
            unsubscriptionMessage["Type"] = MessageType.UNSUBSCRIBE;
            connection.send(unsubscriptionMessage);
            subscribed = false;
        }
	} catch (ex) {
		console.log("Socket exception:", ex);
	}

    function executeCommand(argv){
        if(!checkCommand(argv)) {
            console.log("Invalid command", argv);
            return;
        }
        if(argv[0] == Commands.CONNECT) {
            connect(argv[1]);
            alert("Connecting to game "+argv[1]);
        }
        else if (argv[0] == Commands.SUBSCRIBE){
            var mode = null;
            var time = 0;
            if(argv[1] == SubscribeCommandModes.CURRENT)
                mode = SubscribeMode.CURRENT;
            else if(argv[1] == SubscribeCommandModes.PAST) {
                mode = SubscribeMode.PAST;
                time = argv[2];
            }
            if(subscribed) {
                requestUnsubscribe();
            }
            requestSubscribe(mode, time);
        }
        else if (argv[0] == Commands.CLOSE){
            connection.close();
            confirmed = false;
            subscribed = false;
        }
    }

	var $inputBox = $("#message");
	
	$( "#thesubmit" ).click(function (e) {
		e.preventDefault();
		console.log("submit: ", e);
        var argv = $inputBox.val().split(" ");
        executeCommand(argv);
		$inputBox.val("");
	});

});