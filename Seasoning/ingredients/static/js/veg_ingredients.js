function check_ing_type() {
	sel = $('#id_type');
	
	if (sel.val() == 'VE') {
		$('.VE-fieldset').show();
	} else {
		$('.VE-fieldset').hide();
	}
	
	if (sel.val() == 'FI') {
		$('.FI-fieldset').show();
	} else {
		$('.FI-fieldset').hide();
	}
}

$(document).ready(function() {
	check_ing_type();
	
	$('#id_type').change(function() {
		check_ing_type()
	});
})