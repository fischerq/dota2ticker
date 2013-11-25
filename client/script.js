$( document ).ready(function() {
	try {
        var connection_connection;
        var requests_connection;
        var requests_confirmed = false;
        var listener_connection;
        var listener_confirmed = false;
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

        var current_time;
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
            if(!(selected_unit in state.data)) {
                selected_unit = -1;
                data_display.html("Nothing selected");
            }
            else if(state.get(selected_unit,"type") == ObjectTypes.PLAYER){
                var new_html=state.get(selected_unit, "name")+": "+state.get(selected_unit, "kills") +"/"+state.get(selected_unit, "deaths")+"/"
                    +state.get(selected_unit, "assists")+" "+state.get(selected_unit, "last_hits")+"/"+state.get(selected_unit, "denies");
                data_display.html(new_html);
            }
            else if(state.get(selected_unit,"type") == ObjectTypes.HERO){
                //console.log("cant select heroes, bad");
                //selected_unit = state.get(selected_unit, "player");
                var new_html=state.get(selected_unit, "name")+"(Lvl "+state.get(selected_unit,"level")+"): HP "+state.get(selected_unit, "health") +"/"+state.get(selected_unit, "max_health")+"<br/>Mana: "
                    +state.get(selected_unit, "mana")+"/"+state.get(selected_unit, "max_mana");
                data_display.html(new_html);
            }
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
        function updateStateReset(){
            current_time = game.current_state.time;
            //Display state

            console.log("started loading");
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
            var connection = new Object();
            connection["Type"] = MessageType.CONNECT;
            connection["GameID"] = game_id;
            connection_connection.send(connection);
        }

        function handleConnectionMessage(message)
        {
            if (message["Type"] == MessageType.CLIENT_INFO) {
                client_id = message["ClientID"];
                game_id = message["GameID"];
                requests_connection = new DataConnection(message["Host"], message["PortRequest"], handleRequestMessage, openRequestsConnection, closeRequestsConnection);
                listener_connection = new DataConnection(message["Host"], message["PortListener"], handleListenerMessage, openListenerConnection, closeListenerConnection);
                init();
            }
            else if(message["Type"] == MessageType.REJECT_CONNECTION){
                alert("Connection Rejected");
                //Try other server
            }
            else{
                console.log("Unknown MessageType: ", message["Type"], message);
            }
        }


        function openRequestsConnection(e) {
            console.log("requests connection opened.");
            var registration = new Object();
            registration["Type"] = MessageType.REGISTER;
            registration["ClientID"] = client_id;
            registration["GameID"] = game_id;
            requests_connection.send(registration);
        }

        function handleRequestMessage(message) {
            console.log("got request",message);
            if (message["Type"] == MessageType.CONFIRM){
                requests_confirmed = true;
                console.log("confirmed requests");
                if(listener_confirmed)
                    requestSubscribe(0,0,SubscribeMode.IMMEDIATE);
            }
            else{
                console.log("Received message on request channel: ", message);
            }
        }

        function requestConfigure(setting, value) {
            if(!requests_confirmed){
                console.log("unconfirmed request channel");
                return;
            }

            var configure = new Object();
            configure["Type"] = MessageType.CONFIGURE;
            configure["Setting"] = setting;
            configure["Value"] = value;
            requests_connection.send(configure);
        }
        function requestSubscribe(time, message_detail, mode, interval) {
            if(!requests_confirmed){
                console.log("unconfirmed request channel");
                return;
            }
            else if(! listener_confirmed){
                console.log("unconfirmed listener channel");
                return;
            }
            var subscribe = new Object();
            subscribe["Type"] = MessageType.SUBSCRIBE;
            subscribe["Time"] = time;
            subscribe["MessageDetail"] = message_detail;
            subscribe["Mode"] = mode;
            subscribe["Interval"] = interval;
            requests_connection.send(subscribe);
        }
        function closeRequestsConnection(e) {
            console.log("requests connection closed.");
        }

        function openListenerConnection(e) {
            console.log("listener connection opened.");
            var registration = new Object();
            registration["Type"] = MessageType.REGISTER;
            registration["ClientID"] = client_id;
            registration["GameID"] = game_id;
            listener_connection.send(registration);
        }

        function handleListenerMessage(message) {
            //console.log("got listener notice ",message);
            if(!listener_confirmed){
                if(message["Type"] == MessageType.CONFIRM){
                    listener_confirmed= true;
                    console.log("confirmed requests");
                    if(requests_confirmed)
                        requestSubscribe(0,0,SubscribeMode.IMMEDIATE)
                }
                else{
                    console.log("unconfirmed listener channel received message");
                }
                return;
            }
            if(checkMessage(message)) {
                switch(message["Type"]) {
                    case MessageType.STATE:
                        game.resetState(message["Time"], message["State"]);
                        updateStateReset();
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
        }

        function closeListenerConnection(e) {
                console.log("listener connection closed.");
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