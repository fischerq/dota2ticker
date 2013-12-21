/*
    Connection Connection
    Get connection information of a game server that provides a requested game
 */

var ConnectMessageType = {
    CONNECT : "CONNECT", //GameID
    CLIENT_INFO : "CLIENT_INFO", //Host, PortRequest, PortListener, ClientID
    GAME_AVAILABILITY : "GAME_AVAILABILITY" //Availability
};


var AvailabilityType = {
    AVAILABLE: "AVAILABLE",
    PENDING: "PENDING",
    UNAVAILABLE: "UNAVAILABLE"
};

function checkConnectMessage(message) {
    if(message == null){
        console.log("Bad message: null");
        return false;
    }
    if (!("Type" in message)) {
        console.log("Bad message: no type");
        return false;
    }
    var result = true;
    switch(message["Type"]) {
        case ConnectMessageType.CONNECT:
            result = checkField(message, "GameID");
            break;
        case ConnectMessageType.CLIENT_INFO:
            result = checkField(message, "Host") &&
                checkField(message, "Port") &&
                checkField(message, "GameID");
            break;
        case ConnectMessageType.GAME_AVAILABILITY:
            result = checkField(message, "Availability");
            break;
        default:
            result = false;
            console.log("unknown connect message");
            break;
    }
    return result;
}

function ConnectionConnection(game_id, game_callback, rejection_callback){
    if(typeof(game_callback)==='undefined') game_callback = function(game_id, host, port){};
    if(typeof(rejection_callback)==='undefined') rejection_callback = function(){};

    var self = this;
    this.connection = null;
    this.game_id = game_id;
    this.game_callback = game_callback;
    this.rejection_callback = rejection_callback;

    this.handleMessage = function(message) {
        console.log("connect message", message);
        if(checkConnectMessage(message)) {
            switch(message["Type"]) {
                case ConnectMessageType.GAME_AVAILABILITY:
                    if(message["Availability"] == AvailabilityType.AVAILABLE)
                        console.log("Yay, game available. wait for connection info");
                    else if(message["Availability"] == AvailabilityType.PENDING)//Try again later
                    {
                        setTimeout(function(){self.connection = new DataConnection(HOST_IP, HOST_PORT, self.handleMessage, self.sendConnect);}, 1000);
                        console.log("game is pending, try again in 1sec");
                    }
                    else if(message["Availability"] == AvailabilityType.UNAVAILABLE) {
                        alert("Game unavailable");
                        self.rejection_callback();
                    }
                    break;
                case ConnectMessageType.CLIENT_INFO:
                    console.log("received client info");
                    if(message["GameID"] != self.game_id) {
                        console.log("received info for different game");
                    }
                    else {
                        self.game_callback(message["GameID"], message["Host"], message["Port"]);
                    }
                    break;
                default :
                    console.log("Unknown MessageType: ", message["Type"], message);
            }
        }
        else{
            console.log("Received bad connect message", message);
        }
    };

    this.sendConnect = function() {
        var connectRequest = {};
        connectRequest["Type"] = ConnectMessageType.CONNECT;
        connectRequest["GameID"] = self.game_id;
        self.connection.send(connectRequest);
    };

    this.connection = new DataConnection(HOST_IP, HOST_PORT, this.handleMessage, this.sendConnect);
}


/*
    Game Connection
    Communication with a game server
 */

var GameMessageType = {
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

var SubscribeMode = {
    CURRENT: "CURRENT",
    PAST : "PAST"
};

function checkGameMessage(message) {
    if(message == null){
        console.log("Bad message: null");
        return false;
    }
    if (!("Type" in message)) {
        console.log("Bad message: no type");
        return false;
    }
    var result = true;
    switch(message["Type"]){
        case GameMessageType.REGISTER:
            result = checkField(message, "ClientID") &&
                     checkField(message, "GameID");
            break;
        case GameMessageType.CONFIRM:
            break;
        case GameMessageType.CONFIGURE:
            result = checkField(message, "Setting") &&
                 checkField(message, "Value");
            break;
        case GameMessageType.GETSTATE:
            result = checkField(message, "Time");
            break;
        case GameMessageType.SUBSCRIBE:
            result = checkField(message, "Mode");
            if(message["Mode"] == SubscribeMode.PAST)
                result = result && checkField(message, "Time");
            break;
        case GameMessageType.STATE:
            result = checkField(message, "State");
            break;
        case GameMessageType.UPDATE:
            result = checkField(message, "Update");
            break;
        case GameMessageType.EVENT:
            result = checkField(message, "Event");
            break;
        default:
            result = false;
            console.log("unknown game message");
            break;
    }
    return result;
}

function GameConnection(game_id, host, port, viewer){
    var self = this;
    this.connection = null;
    this.game = new Game();
    this.confirmed = false;
    this.viewer = viewer;

    this.openConnection = function(e) {
        console.log("connection opened.");
        var registerRequest = {};
        registerRequest["Type"] = GameMessageType.REGISTER;
        registerRequest["GameID"] = game_id;
        self.connection.send(registerRequest);
    };

    this.handleMessage = function(message) {
        if(!self.confirmed){
            if(message["Type"] == GameMessageType.CONFIRM){
                self.confirmed= true;
                console.log("confirmed requests");
                self.subscribe(SubscribeMode.CURRENT, 0);
            }
            else{
                console.log("unconfirmed channel received message");
            }
            return;
        }
        if(checkGameMessage(message)) {
            switch(message["Type"]) {
                case GameMessageType.STATE:
                    self.game.setState(message["Time"], message["State"], message["Events"]);
                    self.viewer.init(self.game);
                    break;
                case GameMessageType.UPDATE:
                    if(message["Time"] < self.game.state.time){
                        console.log("Received bad update: past");
                    }
                    else{
                        self.game.addUpdate(message["Update"]);
                        self.viewer.update(message["Update"]);
                    }
                    break;
                case GameMessageType.EVENT:
                    //check event time
                    self.game.addEvent(message["Event"]);
                    self.viewer.addEvent(message["Event"]);
                    break;
                default :
                    console.log("received unknown game message", message);
            }
        }
        else{
            console.log("Received bad game message", message);
        }
    };

    this.closeConnection = function(e) {
         console.log("connection closed.");
    };

    this.configure = function(setting, value) {
        if(!self.confirmed){
            console.log("unconfirmed game connection");
            return;
        }
        var configure = {};
        configure["Type"] = GameMessageType.CONFIGURE;
        configure["Setting"] = setting;
        configure["Value"] = value;
        self.connection.send(configure);
    };

    this.subscribe = function (mode, time) {
        if(!self.confirmed){
            console.log("unconfirmed game connection");
            return;
        }
        else if(self.subscribed) {
            console.log("trying to subscribe, already subscribed");
            return;
        }
        var subscriptionMessage = {};
        subscriptionMessage["Type"] = GameMessageType.SUBSCRIBE;
        subscriptionMessage["Mode"] = mode;
        subscriptionMessage["Time"] = time;
        self.connection.send(subscriptionMessage);
        self.subscribed = true;
    };

    this.unsubscribe = function() {
        if(!self.confirmed){
            console.log("unconfirmed channel");
            return;
        }
        else if(!self.subscribed) {
            console.log("trying to unsubscribe, not subscribed");
            return;
        }
        var unsubscriptionMessage = {};
        unsubscriptionMessage["Type"] = GameMessageType.UNSUBSCRIBE;
        self.connection.send(unsubscriptionMessage);
        self.subscribed = false;
    };

    this.close = function(){
        self.connection.close();
        self.confirmed = false;
        self.subscribed = false;
    };

    this.connection = new DataConnection(host, port, this.handleMessage, this.openConnection, this.closeConnection);
}