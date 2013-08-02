$(document).ready(function() {
	/*
	 * Autcomplete field
	 */
	$( "input.autocomplete-ingredient" ).each(function() {
		$(this).autocomplete({
			source: "/ingredients/ing_list/",
			minLength: 2
		});
	});
	
	$("input.autocomplete-ingredient").change(function() {
		$.ajax({
			type: "POST",
			url: "/ingredients/ing_page/",
			data: {"page": 1, "query": $(this).val(), 'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()}
		}).done(function(msg) {
			alert(msg);
		});
	});
});