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
        var view_canvas = $("#view-canvas")[0];
        var view_context = view_canvas.getContext("2d");
        var view_data = $("#view-data");
        var images = new ImageMap();
        var current_time;
        var event_window = 2000000;
        var selected_unit = 3;
        var game = new Game();

        function draw(){
            view_context.drawImage(images.getImage("minimap"), 0, 0);
        }

        function updateHeaderTitle(){
            var title = $("#header-title");
            console.log("updated header title");
            title.html(game_id);
        }
        function refreshSelectedUnit(){
            console.log("refreshing selected");
            var state = game.current_state;
            var data_display = $("#view-data");
            if(state.get(selected_unit,"type") == UnitTypes.PLAYER){
                var new_html=state.get(selected_unit, "name")+": "+state.get(selected_unit, "kills") +"/"+state.get(selected_unit, "deaths")+"/"
                    +state.get(selected_unit, "assists")+" "+state.get(selected_unit, "last_hits")+"/"+state.get(selected_unit, "denies");
                data_display.html(new_html);
            }
        }
        function updateEvents(){
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
                else
                {
                    p.innerHTML = "Event at "+event["Time"]+": "+event["Type"];
                }
                events_display.append(p);
            }
        }

        function updateStateReset(){
            current_time = game.current_state.time;
            //Display state
            images.setLoaded(draw);
            images.addImage("minimap", "data/minimap.png");
            images.load();
            console.log("started loading");
        }

        function updateStateUpdate(update){
            //update changed objects
            var changed_selected = false;
            for(var change in update["Changes"]){
                if(update["Changes"][change]["ID"] == selected_unit)
                    changed_selected = true;
            }
            if(changed_selected){
                refreshSelectedUnit();
            }
        }


        var change_handlers = [];

        function ChangeHandler(property, handler){
            this.property = property;
            this.handler = handler;

            this.check = function(property){
                //returns true if responsible for this property
                return false;
            }

            this.execute = function(value){
                this.handler(value);
            }
        }
        var refresh_changes = [];

        function refresh(refresh_changes){

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
                updateHeaderTitle();
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
            console.log("got listener notice ",message);
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
                        if(message["Time"] < game.current_state.time)
                            console.log("Received bad update: past");
                        else{
                            game.addUpdate(message["Update"]);
                        }
                        updateStateUpdate(message["Update"]);
                        break;
                    case MessageType.EVENT:
                        //check event time
                        game.addEvent(message["Event"]);
                        updateEvents();
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