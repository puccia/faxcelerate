rotator = function(el) {
	pagesdiv = $(el.target.parentNode.parentNode.parentNode);
	commid = pagesdiv.children(".commid").text();
	pagediv = $(el.target.parentNode.parentNode);
	pagenum = pagediv.children(".pagenumber").text();
	img = pagediv.children("img");
	type = $(el.target).attr("class");
	modifier = function(json) {
/*		console.debug(json);
		console.debug(img);
*/
		img.attr("src", json['newsrc']);
	};
	$.getJSON('/fax/rotate/',
		{'commid': commid, 'page': pagenum, 'type': type},
		modifier);

}

function RotationInit() {
	$(".rotation-tools li").click(rotator);
}

$(document).ready(function(){
 RotationInit();
});

/*

$(document).ready(function(){
	$(".faxpage img").bind("click", function() {
		$(this).toggle(set_all_full, set_all_normal);
	});
});
*/