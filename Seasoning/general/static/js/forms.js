/**
 * Functions for formsets
 * 
 * To make a formset dynamically extensible using this code, a formset element must abide
 * to the following rules:
 * 	- The element containing the entire formset must have an 'id' element with a value
 * 	  'id_formset_prefix-formset' and a class of 'formset'
 *  - The containing element must have the following (indirect) child elements:
 *  	o A managament form with a TOTAL_FORMS element (Provided by django).
 *  	o An empty form, with its ordinal numbers replaced by '__prefix__' (Provided by django).
 *  	o An element with a class of 'formset-button-container' which will contain the 
 *  	  'add a form' button.
 */
function updateFormNumber($form, number) {
	var id_regex = new RegExp('__prefix__');
	$form.find('*').each(function() {
		if ($(this).attr("for")) $(this).attr("for", $(this).attr("for").replace(id_regex,
				number));
		if (this.id) this.id = this.id.replace(id_regex, number);
		if (this.name) this.name = this.name.replace(id_regex, number);
	});
}

function add_form(formset_prefix) {
	// Get the neccessary elements
	var $formset = $('#' + formset_prefix + '-formset');
	var $empty_form = $formset.find('.empty');
	
	// Find out what the new forms number is
	var $form_counter = $formset.find('#id_' + formset_prefix + '-TOTAL_FORMS');
	var new_form_number = parseInt($form_counter.val()) + 1;
	
	// Create the new form
	var $new_form = $($empty_form).clone(false).removeClass('empty');
	updateFormNumber($new_form, new_form_number);
	
	// Insert the new form before the empty form
	$new_form.insertBefore($empty_form);
	// Update the amount of forms
	$form_counter.val(new_form_number);
}


$(document).ready(function() {
	/*
	 * Formset functions
	 */
	// Give every formset a button to add an extra form
	$('form .formset').each(function() {
		var prefix = $(this).attr('id').replace('-formset', '');
		var button = $('<a href="#" id="' + prefix + '-addbtn"><img src="http://us.cdn1.123rf.com/168nwm/djordjer/djordjer1103/djordjer110300027/9107139-plus-chrome-button.jpg"></a>')
		button.click(function(event) {
			add_form(prefix);
			return false;
		})
		$(this).find('.formset-button-container').append(button);
	})
	
	/*
	 * Autcomplete fields
	 */
	$( "input.autocomplete-ingredient" ).each(function() {
		$(this).autocomplete({
			source: "/ingredients/ing_list/",
			minLength: 2
		});
	});
});