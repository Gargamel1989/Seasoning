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


/**
 * Functions for homepage slideshow
 */
function goto_slide(slide_num) {
	/*
	 * Go to the slide with the given ordinal
	 */
	var active_slide = 0;
	$('#slideshow .slide').each(function() {
		// Make every slide stop its current animation
		$(this).stop();
		if ($(this).css('display') != 'none') {
			// Look for the slide that is currently being displayed
			if (active_slide != 0) {
				// If more than 1 slide is displayed, quickly hide one of them
				$('#slide-' + active_slide).hide();
			}
			active_slide = $(this).attr('id').replace('slide-', '');
		}
	});
	
	$('#slideshow-controls a').each(function() {
		// Deactivate every slideshow control that does not correspond to the
		// the goto-slide
		if ($(this).attr('id') != 'slideshow-control-' + slide_num) {
			$(this).removeClass('active');
		}
	});
	
	// Activate the goto-slides button
	$('#slideshow-control-' + slide_num).addClass('active');
	// Hide the currently active slide and then show the goto-slide
	$('#slide-' + active_slide).fadeOut(500, function() {
		$('#slide-' + slide_num).fadeIn(500);
	});
}

function next_slide() {
	/*
	 * Show the slide after the current slide (wrap around)
	 */
	$('#slideshow .slide').each(function() {
		if ($(this).css('display') != 'none') {
			var current_slide = parseInt($(this).attr('id').replace('slide-', ''), 10);
			var next_slide = current_slide % 4 + 1;
			goto_slide(next_slide);
			return;
		}
	});
}





/**
 * Function executed when the page is ready (but maybe not fully loaded)
 */
$(document).ready(function() {
	/*
	 * Base functions
	 */
	// Show subnavigation when hovering over main navigation element
	$('.main-nav-link').each(function() {
		var link_name = $(this).attr('id').replace('main-nav-link-', '');
		$(this).mouseenter(function() {
			$('.sub-nav').each(function() {
				if ($(this).attr('id') != 'sub-nav-' + link_name) {
					$(this).removeClass('active');
				}
			});
			$('#sub-nav-' + link_name).addClass('active');
		});
	});
	
	
	/*
	 * Homepage slideshow functions
	 */
	// Go to the next slide every 10 seconds
	var timeoutHandle;
	function delay_next_slide() {
		next_slide();
		timeoutHandle = setTimeout(delay_next_slide, 10000);
	}
	timeoutHandle = setTimeout(delay_next_slide, 10000);
	
	// Activate the slide controls
	$('#slideshow-controls a').click(function() {
		goto_slide($(this).attr('id').replace("slideshow-control-", ""));
		clearTimeout(timeoutHandle);
		return false;
	});
	
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
		$(this).append(button);
		$(this).children('.formset-button-container')
	})
});


/**
 * Functions executed when the page is fully loaded
 */
$(window).load(function() {
	// Remove loader and display slideshow when everything is loaded
	$('#introbox-loader').fadeOut(500, function() { 
		$(this).remove();
		// Find the active slide
		var active_slide = $('#slideshow-controls a.active').attr('id').replace('slideshow-control-', '');
		$('#slideshow #slide-' + active_slide).fadeIn(500);
		$('#slideshow-controls').fadeIn(500);
	});
});