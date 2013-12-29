/*
    General data connection using JSON
 */

function DataConnection(address, port, onmessage, onopen, onclose)
{
    if(typeof(onmessage)==='undefined') onmessage = function(data){};
    if(typeof(onopen)==='undefined') onopen = function(e){};
    if(typeof(onclose)==='undefined') onclose = function(e){};
    console.log("data connection", address, port, onmessage, onopen, onclose);
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

	this.socket.onmessage = function (e){
        //console.log("received "+ e.data);
        var message = JSON.parse(e.data);
		onmessage(message);
	};

	this.socket.onopen = onopen;
	this.socket.onclose = onclose;
}

var EventType = {
        STATECHANGE: "StateChange",
        CHATEVENT: "ChatEvent",
        DRAFTEVENT: "DraftEvent",
        TEXTEVENT: "TextEvent"
};

/*
    Protocol checking
 */

function checkField(message, field) {
    if (!(field in message)) {
        console.log(message["Type"]+" is missing "+field);
        return false;
    }
    else
        return true;
}

/*
    Image loading
 */

function ImageDirectory(){
    var self = this;
    this.images = {};

    this.registerImage = function(name, img){
        self.images[name] = img
        console.log("registered ",name, self.images[name]);
    };

    this.loadImage = function(loader, file, name, callback) {
        if(callback === undefined) callback = function(){};
        if(name in self.images) {
            console.log("prevented reloading", name, file);
            return;
        }
        self.images[name] = null;
        loader.addImage(file, name);
        loader.addProgressListener(function(e){
            self.registerImage(name, e.resource.img);
            callback();
        }, name);
    };

    this.get = function(name){
        return self.images[name];
    }
}


/*
    2D vectors
 */

function Vector2(x,y){
    this.x = x;
    this.y = y;
}

/*
    Formatting
 */

function zeroPad(num, numZeros) {
	var n = Math.abs(num);
	var zeros = Math.max(0, numZeros - Math.floor(n).toString().length );
	var zeroString = Math.pow(10,zeros).toString().substr(1);
	if( num < 0 ) {
		zeroString = '-' + zeroString;
	}

	return zeroString+n;
}