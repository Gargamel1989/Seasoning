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
			var next_slide = current_slide % 3 + 1;
			goto_slide(next_slide);
			return;
		}
	});
}

$(document).ready(function() {
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
		timeoutHandle = setTimeout(delay_next_slide, 10000);
		return false;
	});
	
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
});

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