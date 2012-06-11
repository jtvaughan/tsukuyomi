/* This JS file provides a countdown timer that automatically updates
   timeout displays and submits a form upon timeout.

   The HTML file including this JS must have the following elements:

     1. a form named "timeout" that will be submitted when the timer times out;
     2. a single tag named "rts" with an attribute named "value" that stores
        the remaining time in seconds;
     3. zero or more hidden input tags named "secs_left" that store the
        remaining time, in seconds, in their "value" attributes; and
     4. a single span or div named "time_left" that contains a string
        displaying the amount of time left.

   This JS will modify most of the aforementioned elements every second. */

var secs_left = 1;
var t = setTimeout("UpdateSecondsDisplay();", 1000);

function UpdateSecondsDisplay() {
  rts_elem = document.getElementsByName("rts")[0];
  secs_left = rts_elem.getAttribute("value");
  secs_left = secs_left - 1;
  rts_elem.setAttribute("value", secs_left);
  if (secs_left <= 0) {
    document.forms["timeout"].submit()
  }
  var secs_left_fields = document.getElementsByTagName("input");
  var i = 0;
  for (i = 0; i < secs_left_fields.length; i++) {
    var elem = secs_left_fields.item(i);
    if (elem.getAttribute("name") == "secs_left") {
      elem.setAttribute("value", secs_left.toString());
    }
  }
  var timefield = document.getElementById("time_left");
  while (timefield.childNodes.length >= 1) {
    timefield.removeChild(timefield.firstChild);
  }
  timefield.appendChild(timefield.ownerDocument.createTextNode(
    Math.floor(secs_left / 3600).toString() + "時" + Math.floor((secs_left % 3600) / 60).toString() + "分" + ((secs_left % 3600) % 60).toString() + "秒"
   ));
  t = setTimeout("UpdateSecondsDisplay();", 1000);
}
