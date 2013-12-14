$( document ).ready(function() {
	$( "#thesubmit" ).click(function (e) {
		e.preventDefault();
        var $inputBox = $("#message");
		console.log("submit: ", e);
        var argv = $inputBox.val().split(" ");
        executeCommand(argv);
		$inputBox.val("");
        $("#cmd").modal('hide');
	});

});