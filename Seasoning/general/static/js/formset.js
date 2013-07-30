function updateElementIndex(el, ndx) {
	var id_regex = new RegExp('__prefix__');
	var replacement = ndx;
	el.find('*').each(function() {
		if ($(this).attr("for")) $(this).attr("for", $(this).attr("for").replace(id_regex,
				replacement));
		if (this.id) this.id = this.id.replace(id_regex, replacement);
		if (this.name) this.name = this.name.replace(id_regex, replacement);
	});
}

function addForm(btn, prefix) {
	var formCount = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val());
	
	var empty_row = $('.empty.' + prefix + '-form');
	var new_row = $(empty_row).clone(false).removeClass('empty');
	updateElementIndex(new_row, formCount)
	
	new_row.insertBefore(empty_row);
	alert('#id_' + prefix + '-TOTAL_FORMS');
	$('#id_' + prefix + '-TOTAL_FORMS').val(formCount + 1);
		
	return false;
}

function ok() {
	$('#synonym_set-addbtn').click(function() {
		return addForm(this, "synonym_set");
	});

	$('#can_use_unit-addbtn').click(function() {
		return addForm(this, "can_use_unit");
	});

	$('#available_in_country-addbtn').click(function() {
		return addForm(this, "available_in_country");
	});

	$('#uses-addbtn').click(function() {
		return addForm(this, "uses");
	});
}