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

$(document).ready(function() {
	check_ing_type();
	
	$('#id_type').change(function() {
		check_ing_type()
	});
})