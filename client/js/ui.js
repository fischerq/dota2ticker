var Commands = {
    CONNECT: "connect",
    SUBSCRIBE: "subscribe",
    CONFIGURE: "configure",
    CLOSE: "close"
};

var SubscribeCommandModes = {
    CURRENT: "current",
    PAST: "past"
};

function checkCommand(argv){
    if(argv.length < 1)
        return false;
    switch(argv[0]){
        case Commands.CONNECT:
            if(argv.length != 2)
                return false;
            break;
        case Commands.SUBSCRIBE:
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
            break;
        case Commands.CONFIGURE:
            if(argv.length != 3)
                return false;
            break;
        case Commands.CLOSE:
            if(argv.length != 1)
                return false;
            break;
        default :
            return false;
    }
    return true;
}

var connection_connection;
var game_connection;
var main_viewer;

function createGame(game_id, host, port){
    console.log("creating game", game_id, host, port);
    main_viewer = new GameDisplay($("#main_display"));
    game_connection = new GameConnection(game_id, host, port, main_viewer);
}

function executeCommand(argv){
    if(!checkCommand(argv)) {
        console.log("Invalid command", argv);
        return;
    }
    console.log("command", argv);
    switch(argv[0]){
        case Commands.CONNECT:
            var game_id = parseInt(argv[1]);
            connection_connection = new ConnectionConnection(game_id, createGame, function(){console.log("Connection got rejected, game not available");});
            alert("Connecting to game "+argv[1]);
            break;
        case Commands.SUBSCRIBE:
            var mode = null;
            var time = 0;
            if(argv[1] == SubscribeCommandModes.CURRENT)
                mode = SubscribeMode.CURRENT;
            else if(argv[1] == SubscribeCommandModes.PAST) {
                mode = SubscribeMode.PAST;
                time = argv[2];
            }
            if(game_connection.subscribed) {
                game_connection.unsubscribe();
            }
            game_connection.subscribe(mode, time);
            break;
        case Commands.CONFIGURE:
            console.log("Configuring: setting", argv[1], argv[2]);
            game_connection.configure(argv[1], argv[2]);
            break;
        case Commands.CLOSE:
            game_connection.close();
    }
}