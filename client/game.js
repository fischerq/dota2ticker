var SNAPSHOT_INTERVAL = 1000;


function Game(){
    this.events = new Array();
    this.snapshots = new Array();
    this.updates = new Array();
    this.current_state = new State();

    this.resetState = function(time, state){
        this.events = new Array();
        this.snapshots = new Array();
        this.updates = new Array();
        this.current_state = new State();
        this.current_state.set(time, state);
        this.snapshots.push(this.current_state);
    }

    this.addUpdate = function(update){
        this.updates.push(update);
        this.current_state.apply(update);
        if(this.current_state.time - this.snapshots[this.snapshots.length-1] > SNAPSHOT_INTERVAL)
            this.snapshots.push(this.current_state);
    }
    this.addEvent = function(event){
        this.events.push(event);
    }
}

var ObjectTypes = {
    GAME : "GAME",
    PLAYER : "PLAYER",
    HERO : "HERO",
    ILLUSION : "ILLUSION"
};

var ChangeTypes = {
    CREATE : "CREATE",
    SET : "SET",
    DELETE : "DELETE"
};

function State(time){
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
        console.log("set state", state, this.data);
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
}
