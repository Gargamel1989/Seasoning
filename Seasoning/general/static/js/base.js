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
	
	$('#bookmark-link').click(function() {
        if (window.sidebar && window.sidebar.addPanel) { // Mozilla Firefox Bookmark
            window.sidebar.addPanel(document.title,window.location.href,'');
        } else if(window.external && ('AddFavorite' in window.external)) { // IE Favorite
            window.external.AddFavorite(location.href,document.title); 
        } else if(window.opera && window.print) { // Opera Hotlist
            this.title=document.title;
            return true;
        } else { // webkit - safari/chrome
            alert('Press ' + (navigator.userAgent.toLowerCase().indexOf('mac') != - 1 ? 'Command/Cmd' : 'CTRL') + ' + D to bookmark this page.');
        }
        return false;
	});
});