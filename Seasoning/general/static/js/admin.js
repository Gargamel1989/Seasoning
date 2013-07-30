/*
 * Edit Ingredient functions
 */
function check_ing_type() {
	sel = $('#id_type');
	
	if (sel.val() == 1) {
		$('.VE-fieldset').show();
	} else {
		$('.VE-fieldset').hide();
	}
	
	if (sel.val() == 2) {
		$('.FI-fieldset').show();
	} else {
		$('.FI-fieldset').hide();
	}
}

/**
 * Function executed when the page is ready (but maybe not fully loaded)
 */
$(document).ready(function() {
	/*
	 * Edit Ingredient functions
	 */
	// Show and hide certain parts of the form depending on the currently
	// selected ingredient type
	check_ing_type();	
	$('#id_type').change(function() {
		check_ing_type()
	});
});