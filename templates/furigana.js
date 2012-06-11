/* This JS file provides 振り仮名 display toggling in ruby elements.  It doesn't
   have any template parameters, but it expects the following elements in the
   containing HTML:

     1. a series of rp tags that are initially hidden via inline CSS;
     2. a series of rt tags that are initially hidden via inline CSS; and
     3. a button named 振り仮名を見せて whose value is initially "振り仮名を見せて".

   This script will modify the aforementioned elements.  However, it is the
   containing HTML's responsibility to invoke the function that toggles
   the 振り仮名 display, which has the following signature:

     toggle_visibility: string => None
       Toggle the 振り仮名 display given that the aforementioned rp and rt tags'
       class is the specified string.

   The 振り仮名を見せて button should invoke this function. */

var furigana = 'hidden';

function toggle_visibility(furigana_class) {
  furigana = (furigana == 'visible' ? 'hidden' : 'visible');
  var spans = document.getElementsByTagName('rp');
  var i = 0;
  for (i = 0; i < spans.length; i++) {
    var span_node = spans.item(i);
    if (span_node.getAttribute('class') == furigana_class) {
      span_node.setAttribute('style', 'visibility:' + furigana);
    }
  }
  spans = document.getElementsByTagName('rt');
  i = 0;
  for (i = 0; i < spans.length; i++) {
    var span_node = spans.item(i);
    if (span_node.getAttribute('class') == furigana_class) {
      span_node.setAttribute('style', 'visibility:' + furigana);
    }
  }
  var show_button = document.getElementsByName('振り仮名を見せて')[0];
  if (furigana == 'visible') {
    show_button.setAttribute('value', 'Hide 振り仮名');
  } else {
    show_button.setAttribute('value', '振り仮名を見せて');
  }
}
