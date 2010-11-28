hovertipCustomPrepare = function(o, config) {
	str = "";
	for (s in o) {
		str += s + " ";
	}
	hovertipPrepare(o, config);
}

function customHovertipInit() {
	
	var hovertipConfig = {'attribute':'hovertip',
                        'showDelay': 50,
                        'hideDelay': 100};
  
	/**
   * This next section enables this style of markup:
   * <foo><span>target</span><span class="hovertip">blah blah</span></foo>
   * 
   * With drop shadow effect.
   * 
   */
  var hovertipSpanSelect = 'span.hovertip';
  var f = function() { return function(o, el) {
	if (o.attr("loaded") == undefined) {
		n = o.children().children().children();
		link_container = n.children();
		link = link_container.text();
		link_container.text("");
		link_container.append("<img style='border: solid 1px;' src='" + link + "' />");
		o.attr("loaded", 1);
	} };
  }
  $(hovertipSpanSelect).attr({"tiploader": f});
	
  // activate hovertips with wrappers for FX (drop shadow):
  $(hovertipSpanSelect).css('display', 'block').addClass('hovertip_wrap3').
    wrap("<span class='hovertip_wrap0'><span class='hovertip_wrap1'><span class='hovertip_wrap2'>" + 
         "</span></span></span>").each(function() {
           // fix class and attributes for newly wrapped elements
           var tooltip = this.parentNode.parentNode.parentNode;

			if(this.getAttribute('tiploader'))
				tooltip.setAttribute('tiploader', this.getAttribute('tiploader'));
	
           if (this.getAttribute('target'))
             tooltip.setAttribute('target', this.getAttribute('target'));
           if (this.getAttribute('id')) {
             var id = this.getAttribute('id');
             this.removeAttribute('id');
             tooltip.setAttribute('id', id);
           }
         });
  hovertipSpanSelect = 'span.hovertip_wrap0';

  window.setTimeout(function() {
    $(hovertipSpanSelect)
      .hovertipActivate(hovertipConfig,
                        targetSelectByPrevious,
                        hovertipPrepare,
                        hovertipTargetPrepare);
  }, 0);
  
}

$(document).ready(function(){
 customHovertipInit();
});
