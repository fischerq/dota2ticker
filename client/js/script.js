$( document ).ready(function() {
	$( "#exec" ).click(function (e) {
		e.preventDefault();
        var $inputBox = $("#cmd");
		console.log("submit: ", e);
        var argv = $inputBox.val().split(" ");
        executeCommand(argv);
		$inputBox.val("");
        $("#cmdModal").modal('hide');
	});

    $('#replay_form').ajaxForm({
        beforeSend: function() {
            $('#replay_progress').html("Progress: 0%");
        },
        uploadProgress: function(event, position, total, percentComplete) {
            $('#replay_progress').html("Progress: "+percentComplete+"%");
        },
        complete: function(xhr) {
            $('#replay_progress').html("Finished");
        }
    });
});