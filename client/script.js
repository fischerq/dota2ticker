function DataConnection(address, port, onmessage, onopen, onclose)
{
	this.address = address
	this.port = port
	var host = "ws://" + this.address + ":" + this.port;
	this.socket = new WebSocket(host, "dota2ticker")
	
	this.
	$.parseJSON
	
	this.send = function(data){
		message = JSON.stringify(data);
		this.socket.send(message);
	}
	

	this.socket.onerror = function(e) {
			console.log("DataConnection Socket error:", e);
	};
			
	function nop(e){}
	
	switch (arguments.length - 2) { // <-- number of required arguments
    case 0:  onmessage = nop;
    case 1:  onopen = nop;
    case 2:  onclose = nop;
	}
	
	this.socket.onmessage = function (e){ 
		onmessage(e.data);
	};
	this.socket.onopen = onopen;
	this.socket.onclose = onclose;
}

$( document ).ready(function() {
	try {
		var server_address = "localhost";
		var requests_port = 29000;
		var listener_port = 29500;
		
		var host = "ws://" + server_address + ":";
		console.log("Host:", host+requests_port);
		
		var requests = new WebSocket(host+requests_port, "dota2ticker");
		var listener = new WebSocket(host+listener_port, "dota2ticker");
		
		requests.onopen = function (e) {
			console.log("requests connection opened.");
		};
		
		requests.onclose = function (e) {
			console.log("requests connection closed.");
		};
		
		var output = $("#output");
		requests.onmessage = function (e) {
			console.log("Socket message:", e.data);
			var p = document.createElement("p");
			p.innerHTML = e.data;
			output.append(p);
		};
		
		requests.onerror = function (e) {
			console.log("Requests Socket error:", e);
		};
		
		
		listener.onopen = function (e) {
			console.log("listener connection opened.");
		};
		
		listener.onclose = function (e) {
			console.log("listener connection closed.");
		};
		
		var listener_display = $("#listener");
		listener.onmessage = function (e) {
			console.log("listener message:", e.data);
			var p = document.createElement("p");
			p.innerHTML = e.data;
			listener_display.append(p);
		};
		
		listener.onerror = function (e) {
			console.log("Listener Socket error:", e);
		};
		
	} catch (ex) {
		console.log("Socket exception:", ex);
	}

	var $inputBox = $("#message");
	
	$( "#thesubmit" ).click(function (e) {
		e.preventDefault();
		console.log("submit: ", e);
		requests.send($inputBox.val());
		$inputBox.val("");
	});

});