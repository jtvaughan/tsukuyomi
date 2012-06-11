/* This JS file provides functions for displaying 漢字 stroke order diagrams.
   It doesn't have any template parameters, but it expects the following
   elements in the containing HTML file:

     1. a button named "show_kanji" that enables the 漢字 stroke order diagram
        display when clicked; and
     2. a set of images named "漢字diagram<字>", where <字> is a single
        漢字 character, one per 漢字 with a stroke order diagram.

   This script will display and hide these elements.  It is the containing
   HTML page's responsibility to invoke the functions that show and hide
   these elements.  The API is:

     enableKanjiView: None => None
       Enable 漢字 stroke order diagrams and hide the "show_kanji" button.
     showKanjiImage: 字:string => None
       Show the image named "漢字diagram<字>", where <字> is the single-character
       string parameter 字.
     hideKanjiImage: 字:string => None
       Hide the image named "漢字diagram<字>", where <字> is the single-character
       string parameter 字.

   It's pointless to invoke showKanjiImage() and hideKanjiImage() before
   enableKanjiView() is invoked. */

kanji_diagram_enabled = false;

function enableKanjiView() {
  kanji_diagram_enabled = true;
  enable_kanji_button = document.getElementsByName('show_kanji')[0];
  enable_kanji_button.setAttribute('style', 'display: none;');
}

function showKanjiImage(kanji) {
  kanji_image = document.getElementsByName('漢字diagram' + kanji)[0];
  if (kanji_diagram_enabled) {
    kanji_image.setAttribute('style', 'display: block; max-width: 100%; margin-left: auto; margin-right: auto');
  }
}

function hideKanjiImage(kanji) {
  kanji_image = document.getElementsByName('漢字diagram' + kanji)[0];
  if (kanji_diagram_enabled) {
    kanji_image.setAttribute('style', 'display: none;');
  }
}

