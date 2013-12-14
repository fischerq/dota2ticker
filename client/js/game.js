var SNAPSHOT_INTERVAL = 1000;
var TICKS_PER_SEC = 30;


function Game(){
    this.events = new Array();
    this.state = new State();

    this.setState = function(time, state, events) {
        this.state.set(time, state);
        this.events = events;
    }

    this.addUpdate = function(update) {
        this.state.apply(update);
    }

    this.addEvent = function(event) {
        this.events.push(event);
    }
}

var ObjectTypes = {
    GAME : "GAME",
    DRAFT : "DRAFT",
    PLAYER : "PLAYER",
    HERO : "HERO",
    ILLUSION : "ILLUSION"
};

var ChangeTypes = {
    CREATE : "CREATE",
    SET : "SET",
    DELETE : "DELETE"
};

function State(){
    this.time = -1;
    this.data = new Object();

    this.set = function(time, state){
        this.time = time;
        this.data = state;/*new Object();
        for(obj in state){
            this.data[obj] = new Object();
            for(key in state[obj]){
                this.data[obj][key] = state[obj][key];
            }
        }*/
        console.log("set state", this);
    }

    this.apply = function(update){
        if(update.time < this.time){
            console.log("ERROR: Applied past update");
        }
        this.time = update["Time"];
        for(var change in update["Changes"]){
            var type = update["Changes"][change]["Type"];
            var id = update["Changes"][change]["ID"];
            if(type == ChangeTypes.CREATE){
                if(id in this.data)
                    console.log("Creating already existing obj");
                this.data[id] = new Object();
                this.data[id]["type"] = update["Changes"][change]["Value"];
            }
            else if(type == ChangeTypes.SET){
                this.data[id][update["Changes"][change]["Attribute"]] = update["Changes"][change]["Value"];
            }
            else if(type == ChangeTypes.DELETE){
                if(!(id in this.data))
                    console.log("Trying to delete non-existing object");
                delete this.data[id];
            }
            else
                console.log("Bad change type");
        }
    }

    this.get = function(id, attribute){
        if(!(id in this.data)){
            console.log("Bad Id",id);
            return null;
        }
        if(!(attribute in this.data[id]))
            return null;
        return this.data[id][attribute];
    }

    this.exists = function(id) {
        if(this.data == null || this.data == undefined){
            console.log("Querying invalid state");
            return false;
        }
        return id in this.data;
    }
}

function filterChanges( changes, object_id, object_type, attribute, change_type){
    var result = [];
    for(var change in changes){
        var accepted = true;
        if(object_id != undefined)
            accepted = accepted && changes[change]["ID"] == object_id;
        if(change_type != undefined)
            accepted = accepted && changes[change]["Type"] == change_type;
        if(changes[change]["Type"] == ChangeTypes.SET){
            if (object_type != undefined)
                accepted = accepted && game.state.get(changes[change]["ID"], "type") == object_type;
            if (attribute != undefined)
                accepted = accepted && changes[change]["Attribute"] == attribute;
        }
        else{
            if (object_type != undefined || attribute != undefined)
                accepted = false;
        }
        if (accepted)
            result.push(changes[change])
    }
    return result;
}