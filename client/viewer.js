var WORLD_MAX_WIDTH  = 9216.0
var WORLD_MAX_HEIGHT = 8192.0
var WORLD_MIN_WIDTH = -8576.0
var WORLD_MIN_HEIGHT = -7680.0

var parameters_minimap = new Object();
parameters_minimap["scale_x"] = 0.0185;
parameters_minimap["scale_y"] = 0.0180;
parameters_minimap["offset_x"] = 0;
parameters_minimap["offset_y"] = 0;

function convertCoordinates(position, image_parameters){
    var x_result = (-WORLD_MIN_WIDTH + position.x) * image_parameters.scale_x + image_parameters.offset_x;
    var y_result = (WORLD_MAX_HEIGHT - position.y) * image_parameters.scale_y + image_parameters.offset_y;
    return new Vector2(x_result, y_result);
}