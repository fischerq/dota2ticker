function DataConnection(address, port, onmessage, onopen, onclose)
{
	this.address = address
	this.port = port
	var host = "ws://" + this.address + ":" + this.port;
	this.socket = new WebSocket(host, "dota2ticker");

	this.send = function(data){
		message = JSON.stringify(data);
        console.log("sent "+message);
		this.socket.send(message);
	}


	this.socket.onerror = function(e) {
			console.log("DataConnection Socket error:", e);
	};

	function nop(e){}

	switch (arguments.length - 2) { //number of required arguments, no breaks intended
    case 0:  onmessage = nop;
    case 1:  onopen = nop;
    case 2:  onclose = nop;
	}

	this.socket.onmessage = function (e){
        console.log("recieved "+ e.data);
        var message = JSON.parse(e.data);
		onmessage(message);
	};
	this.socket.onopen = onopen;
	this.socket.onclose = onclose;
}

var MessageType = {
    CONNECT : "CONNECT", //GameID
    CLIENT_INFO : "CLIENT_INFO", //Host, PortRequest, PortListener, ClientID
    REJECT_CONNECTION : "REJECT_CONNECTION", //
    REGISTER : "REGISTER", //ClientID, GameID
    CONFIGURE : "CONFIGURE", //Setting, Value
    GETSTATE : "GETSTATE", //Time
    SUBSCRIBE : "SUBSCRIBE", //Time, MessageDetail, Mode, [Interval]
    STATE : "STATE", //State
    UPDATE : "UPDATE", //Update
    EVENT : "EVENT" //Event
};

function checkField(message, field) {
    if (!(field in message)) {
        console.log(message["Type"]+" is missing "+field);
        return false;
    }
    else
        return true;
};

function checkMessage(message) {
    if (!("Type" in message)) {
        console.log("Bad message: no type");
        return false;
    }
    var result = true;
    if (message["Type"] == MessageType.CONNECT)
        result = checkField(message, "GameID");
    else if (message["Type"] == MessageType.CLIENT_INFO)
        result = checkField(message, "Host") &&
                 checkField(message, "PortRequest") &&
                 checkField(message, "PortListener") &&
                 checkField(message, "ClientID");
    else if (message["Type"] == MessageType.REJECT_CONNECTION)
        result = true;
    else if (message["Type"] == MessageType.REGISTER)
        result = checkField(message, "ClientID") &&
                 checkField(message, "GameID");
    else if (message["Type"] == MessageType.CONFIGURE)
        result = checkField(message, "Setting") &&
                 checkField(message, "Value");
    else if (message["Type"] == MessageType.GETSTATE)
        result = checkField(message, "Time");
    else if (message["Type"] == MessageType.SUBSCRIBE) {
        result = checkField(message, "Time") &&
                 checkField(message, "MessageDetail") &&
                 checkField(message, "Mode");
        if(message["Mode"] == SubscribeMode.FIXED)
            result = result && checkField(message, "Step");
    }
    else if (message["Type"] == MessageType.STATE)
        result = checkField(message, "State");
    else if (message["Type"] == MessageType.UPDATE)
        result = checkField(message, "Update");
    else if (message["Type"] == MessageType.EVENT)
        result = checkField(message, "Event");
    return result;
};