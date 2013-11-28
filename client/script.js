$( document ).ready(function() {
	try {
        var connection_connection;
        var connection;
        var confirmed = false;
        var client_id;
        var game_id = 303487989;

        var events_display = $("#events");

        var view_data = $("#view-data");
        var images = {};

        var minimap = new Kinetic.Stage({
                container: 'minimap',
                width: 300,
                height: 300
              });
        var layers = {};

        var current_time = -1;
        var event_window = 60*30;
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
    function refresh(){
        current_time = game.current_state.time;
        refreshEvents();
        refreshDisplay();
        refreshSelected();
        refreshHeader();
        setTimeout(refresh, refresh_interval);
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
            imageLoader.addImage("data/minimap.png", "minimap");
            imageLoader.addProgressListener(function(e){
                registerImage("minimap", e.resource.img);
                layers["background"].add(images["minimap"]);
                console.log("added minimap");
            }, "minimap");
            imageLoader.addCompletionListener(refresh, "minimap");
            imageLoader.start();

            setTimeout(refresh, refresh_interval);
        }

        function refreshHeader(){
            var time= $("#time");
            time.html(current_time);
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
                new_html=state.get(selected_unit, "name")+"(Lvl "+state.get(selected_unit,"level")+"): HP "+state.get(selected_unit, "health") +"/"+state.get(selected_unit, "max_health")+"<br/>Mana: "
                    +state.get(selected_unit, "mana")+"/"+state.get(selected_unit, "max_mana");
            }
            data_display.html(new_html);
        }
        function refreshEvents(){
            events_display.html("");
            for (var key in game.events){
                var event = game.events[key];
                if(event["Time"] < current_time - event_window)
                    continue;
                var p = document.createElement("p");
                if(event["Type"] == EventType.STATECHANGE)
                {
                    p.innerHTML = event["Time"]+": Changed State to "+event["State"];
                }
                else if(event["Type"] == EventType.TEXTEVENT)
                {
                    p.innerHTML = event["Time"]+": "+event["Text"];
                }
                else
                {
                    p.innerHTML = "Event at "+event["Time"]+": "+event["Type"];
                }
                events_display.append(p);
            }
        }

        function refreshDisplay(){
            console.log("refreshing", game);
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
                    registerImage(name, e.resource.img);
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

        function updateStateUpdate(update){
            current_time = update["Time"];
            game.setState(update["Time"], update["State"]);
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
                        var icon = hero_name_changes[i]["Value"]+"_icon";
                        heroesLoader.addImage("data/icons/"+hero_name_changes[i]["Value"]+"_icon.png", icon);
                        heroesLoader.addProgressListener(getAddHeroImage(hero_name_changes[i]["ID"], icon),icon);
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

        function openConnectionConnection(){
            var connectRequest = new Object();
            connectRequest["Type"] = MessageType.CONNECT;
            connectRequest["GameID"] = game_id;
            connection_connection.send(connectRequest);
        }

        function handleConnectionMessage(message)
        {
            if(message["Type"] == MessageType.GAME_AVAILABILITY){
                if(message["Availability"] == AvailabilityType.AVAILABLE)
                    console.log("Yay, game available. wait for connection info");
                else if(message["Availability"] == AvailabilityType.PENDING)//Try again later
                    setTimeout(function(){connection_connection = new DataConnection(server_address, connection_server_port, handleConnectionMessage, openConnectionConnection)}, 1000);
                else if(message["Availability"] == AvailabilityType.UNAVAILABLE)
                    alert("Game unavailable");
            }
            else if (message["Type"] == MessageType.CLIENT_INFO) {
                client_id = message["ClientID"];
                game_id = message["GameID"];
                connection = new DataConnection(message["Host"], message["Port"], handleMessage, openConnection, closeConnection);
                init();
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
                        game.setState(message["Time"], message["State"]);
                        refresh();
                        break;
                    case MessageType.UPDATE:
                        console.log("got update",message);
                        if(message["Time"] < game.current_state.time){
                            console.log("Received bad update: past");
                        }
                        else{
                            game.addUpdate(message["Update"]);
                            updateStateUpdate(message["Update"]);
                        }
                        break;
                    case MessageType.EVENT:
                        console.log("got event",message);
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
            var subscriptionMessage = new Object();
            subscriptionMessage["Type"] = MessageType.SUBSCRIBE;
            subscriptionMessage["Mode"] = mode;
            subscriptionMessage["Time"] = time;
            connection.send(subscriptionMessage);
        }

        //start connection server
		var server_address = "localhost";
		var connection_server_port = 29000;

        connection_connection = new DataConnection(server_address, connection_server_port, handleConnectionMessage, openConnectionConnection);

		console.log("Host:", server_address, connection_server_port);
	} catch (ex) {
		console.log("Socket exception:", ex);
	}

	var $inputBox = $("#message");
	
	$( "#thesubmit" ).click(function (e) {
		e.preventDefault();
		console.log("submit: ", e);
		requests.send($inputBox.val());
		$inputBox.val("");
	});

});