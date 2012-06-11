
月詠 (Tsukuyomi): Japanese Flashcard Generator
=============================================

Summary
-------

This command line tool automatically generates front and back matter for
言葉 flashcards from lines of Japanese text.  The front of each card is the
unaltered Japanese text, whereas the back is the Japanese text but with
漢字 (kanji) replaced by 振り仮名 (furigana) wherever there are
振り仮名 annotations.  (See the README file for the 言葉 Flashcards tool for
more information about 振り仮名 annotations.)



Running
-------

1. Download 月詠 if you have not already done so.

2. Open a console or terminal.

3. Navigate to the directory containing the downloaded code.  (You could
   execute the tool from any directory, but these instructions assume that
   you will execute the tool from within the directory in which the tool
   resides.  This simplifies the instructions.)

4. Run the following command:

   > `./make-japanese-flashcards.py [-r] [text] [[text] ...]`

   where `text` is a string of Japanese text.  You may specify more than
   one string: Each will be transformed separately.  The optional `-r` option
   swaps the generated front and back matter.
   
   The script will output each card's front and back matter to standard
   output, one card per line.  You can put these lines into a 言葉
   Flashcards flashcard file.
   
   NOTE: If you do not specify any strings as command line arguments, then
   the script will read lines of Japanese text from standard input.



Example
-------

> `./make-japanese-flashcards.py 'お大[だい]事[じ]に。' '気をつけて下[くだ]さい。'
> "お大[だい]事[じ]に。","おだいじに。"
> "気をつけて下[くだ]さい。","気をつけてください。"



License
-------

See LICENSE for the license governing this tool.

