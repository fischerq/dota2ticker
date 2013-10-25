$( document ).ready(function() {
	try {
        var connection_connection;
        var requests_connection;
        var listener_connection;
        var client_id;
        var game_id = 0;
        var output = $("#output");
        var listener_display = $("#listener");

        function openConnectionConnection(){
            var connection = new Object();
            connection["Type"] = MessageType.CONNECT;
            connection["GameID"] = game_id;
            connection_connection.send(connection);
        }

        function handleConnectionMessage(message)
        {
            if (message["Type"] != MessageType.CLIENT_INFO) {
                console.log("Unknown MessageType: ", message["Type"]);
            }
            else {
                client_id = message["ClientID"];
                game_id = message["GameID"];
                requests_connection = new DataConnection(message["Host"], message["PortRequest"], handleRequestMessage, openRequestsConnection, closeRequestsConnection);
                listener_connection = new DataConnection(message["Host"], message["PortListener"], handleListenerMessage, openListenerConnection, closeListenerConnection);
            }
        };


        function openRequestsConnection(e) {
            console.log("requests connection opened.");
            var registration = new Object();
            registration["Type"] = MessageType.REGISTER;
            registration["ClientID"] = client_id;
            registration["GameID"] = game_id;
            requests_connection.send(registration);
        };

        function handleRequestMessage(message) {
            console.log("got request",message);
            var p = document.createElement("p");
            p.innerHTML = e.data;
            output.append(p);
        };

        function closeRequestsConnection(e) {
            console.log("requests connection closed.");
        };

        function openListenerConnection(e) {
            console.log("listener connection opened.");
            var registration = new Object();
            registration["Type"] = MessageType.REGISTER;
            registration["ClientID"] = client_id;
            registration["GameID"] = game_id;
            listener_connection.send(registration);
        };

        function handleListenerMessage(message) {
            console.log("got listener notice ",message);
            if(checkMessage(message)) {
                switch(message["Type"]) {
                    case MessageType.STATE:
                        break;
                    case MessageType.UPDATE:
                        break;
                    case MessageType.EVENT:
                        break;
                }
            }
            var p = document.createElement("p");
			p.innerHTML = e.data;
			listener_display.append(p);
        };

        function closeListenerConnection(e) {
                console.log("requests connection closed.");
        };

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