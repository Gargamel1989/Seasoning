$(document).ready(function() {
	$('#id_uses_ingredient-0-ingredient').on('input',function(e){
		$.ajax({
			url: "/ingredients/ing_list/" + $('#id_uses_ingredient-0-ingredient').val() + "/"
		}).done(function (data ) {
			if( console && console.log ) {
				console.log("Sample of data:", data.slice(0, 100));
			}
		});
	});
})