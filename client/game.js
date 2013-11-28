var SNAPSHOT_INTERVAL = 1000;


function Game(){
    this.events = new Array();
    this.current_state = new State();

    this.setState = function(time, state) {
        this.current_state.set(time, state);
    }

    this.addUpdate = function(update) {
        this.current_state.apply(update);
    }

    this.addEvent = function(event) {
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
        console.log("applying",this)
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
            console.log("data ", id, this.data, this.data[id]);
        }
    }

    this.get = function(id, attribute){
        console.log("getting", this)
        console.log("getting2", this.data, id);
        if(!(id in this.data)){
            console.log("Bad Id",id);
            return null;
        }
        if(!(attribute in this.data[id]))
            return null;
        return this.data[id][attribute];
    }
}

