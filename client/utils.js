function DataConnection(address, port, onmessage, onopen, onclose)
{
	this.address = address;
	this.port = port;
	var host = "ws://" + this.address + ":" + this.port;
	this.socket = new WebSocket(host, "dota2ticker");

	this.send = function(data){
		message = JSON.stringify(data);
        console.log("sent "+message);
		this.socket.send(message);
	};


	this.socket.onerror = function(e) {
			console.log("DataConnection Socket error:", e);
	};

	function nop(e){}

    if (arguments.length - 2 == 0) {
        onmessage = nop;
        onopen = nop;
        onclose = nop;
    } else if (arguments.length - 2 == 1) {
        onopen = nop;
        onclose = nop;
    } else if (arguments.length - 2 == 2) {
        onclose = nop;
    } else {
    }

	this.socket.onmessage = function (e){
        //console.log("received "+ e.data);
        var message = JSON.parse(e.data);
		onmessage(message);
	};
	this.socket.onopen = onopen;
	this.socket.onclose = onclose;
}

var MessageType = {
    CONNECT : "CONNECT", //GameID
    CLIENT_INFO : "CLIENT_INFO", //Host, PortRequest, PortListener, ClientID
    GAME_AVAILABILITY : "GAME_AVAILABILITY", //Availability
    REGISTER : "REGISTER", //ClientID, GameID
    CONFIRM : "CONFIRM", //Data
    CONFIGURE : "CONFIGURE", //Setting, Value
    GETSTATE : "GETSTATE", //Time
    SUBSCRIBE : "SUBSCRIBE", //Mode, Time
    UNSUBSCRIBE: "UNSUBSCRIBE", //
    STATE : "STATE", //State
    UPDATE : "UPDATE", //Update
    EVENT : "EVENT" //Event
};

var EventType = {
        STATECHANGE: "StateChange",
        CHATEVENT: "ChatEvent",
        TEXTEVENT: "TextEvent"
};

var AvailabilityType = {
    AVAILABLE: "AVAILABLE",
    PENDING: "PENDING",
    UNAVAILABLE: "UNAVAILABLE"
};

var SubscribeMode = {
    CURRENT: "CURRENT",
    PAST : "PAST"
};

function checkField(message, field) {
    if (!(field in message)) {
        console.log(message["Type"]+" is missing "+field);
        return false;
    }
    else
        return true;
}

function checkMessage(message) {
    if(message == null){
        console.log("Bad message: null");
        return false;
    }
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
    else if (message["Type"] == MessageType.GAME_AVAILABILITY)
        result = checkField(message, "Availability");
    else if (message["Type"] == MessageType.REGISTER)
        result = checkField(message, "ClientID") &&
                 checkField(message, "GameID");
    else if (message["Type"] == MessageType.CONFIRM)
        result = checkField(message, "Data");
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
}

var Commands = {
    CONNECT: "connect",
    SUBSCRIBE: "subscribe",
    CLOSE: "close"
};

var SubscribeCommandModes = {
    CURRENT: "current",
    PAST: "past"
};

function checkCommand(argv){
    if(argv.length < 1)
        return false;
    if(argv[0] == Commands.CONNECT){
        if(argv.length != 2)
            return false;
    }
    else if (argv[0] == Commands.SUBSCRIBE){
        if(argv.length < 2)
            return false;
        if(argv[1] == SubscribeCommandModes.CURRENT) {
            if(argv.length != 2)
                return false;
        }
        else if(argv[1] == SubscribeCommandModes.PAST) {
            if(argv.length != 3)
                return false;
        }
        else return false;
    }
    else if (argv[0] == Commands.CLOSE){
        if(argv.length != 1)
            return false;
    }
    else {
        return false;
    }
    return true;
}

function decodePosition(position){
    return new Vector2(position["x"], position["y"]);
}

function Vector2(x,y){
    this.x = x;
    this.y = y;
}

function zeroPad(num, numZeros) {
	var n = Math.abs(num);
	var zeros = Math.max(0, numZeros - Math.floor(n).toString().length );
	var zeroString = Math.pow(10,zeros).toString().substr(1);
	if( num < 0 ) {
		zeroString = '-' + zeroString;
	}

	return zeroString+n;
}