$(function(){
	$('#getT').click(function(){
		var userID = $('#facultyInp').val();
		$.ajax({
			url: '/getTT',
			type: 'POST',
		    contentType: 'text/json',
			data: {"user_id": userID},
			dataType: "json",
			success: function(response){
				console.log(response);
			},
			error: function(error){
				console.log(error);
			}
		});
	});
});