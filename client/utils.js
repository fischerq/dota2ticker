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

function ImageMap(loaded){
    var self = this;
    this.keys = new Array();
    this.to_load = new Array();
    this.images = {};
    this.loading_counter = 0;
    this.loaded = loaded;

    var registerLoad = function(self, key){
        self.loading_counter--;
        console.log("Registered load", key, self.loading_counter);
        self.keys.push(key);
        var loading_key = null;
        for(var i in self.to_load){
            if(self.to_load[i] == key){
                loading_key = i;
                break;
            }
        }
        if(loading_key != null)
            self.to_load.splice(loading_key, 1);
        if(self.loading_counter == 0){
            self.loaded();
        }
    };

    this.addImage = function(key, file){
        this.loading_counter++;
        this.images[key] = new DynamicImage(file, function(){registerLoad(self, key);});
        this.to_load.push(key);
        console.log("adding image",this.to_load);
    };

    this.getImage = function(key){
        if(key in this.images)
            return this.images[key].image;
        else{
            console.log("failed getting", this, key);
            return null;
        }
    };

    this.load = function(){
        //console.log(this.to_load);
        this.to_load.forEach(function (element) {
            this.images[element].load();
        });
    };

    this.setLoaded = function(new_loaded){
        this.loaded = new_loaded;
    }

    this.isReady = function(){
        return (this.loading_counter == 0);
    }
}

function DynamicImage(file, onload){
    this.image = new Image();
    this.file = file;
    this.image.onload = onload;
    var self = this;
    this.load = function(){
        this.image.src = this.file;
    };
}


var MessageType = {
    CONNECT : "CONNECT", //GameID
    CLIENT_INFO : "CLIENT_INFO", //Host, PortRequest, PortListener, ClientID
    REJECT_CONNECTION : "REJECT_CONNECTION", //
    REGISTER : "REGISTER", //ClientID, GameID
    CONFIRM : "CONFIRM", //Data
    CONFIGURE : "CONFIGURE", //Setting, Value
    GETSTATE : "GETSTATE", //Time
    SUBSCRIBE : "SUBSCRIBE", //Time, MessageDetail, Mode, [Interval]
    STATE : "STATE", //State
    UPDATE : "UPDATE", //Update
    EVENT : "EVENT" //Event
};

var EventType = {
        STATECHANGE: "StateChange",
        CHATEVENT: "ChatEvent",
        TEXTEVENT: "TextEvent"
};


var SubscribeMode = {
    IMMEDIATE : "IMMEDIATE",
    COMPRESSED : "COMPRESSED",
    FIXED : "FIXED"
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

function decodePosition(position){
    return new Vector2(position["x"], position["y"]);
}

function Vector2(x,y){
    this.x = x;
    this.y = y;
}