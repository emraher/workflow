setTimeout(function wait() {
	var wrapper = document.querySelector(".toolbar-addressbar.toolbar > .extensions-wrapper");
	var footer = document.getElementById('footer');
	if (wrapper != null) {
		footer.style = "height: 27px";
		footer.appendChild(wrapper);
	}
	else {
		setTimeout(wait, 300);
	}
}, 300);