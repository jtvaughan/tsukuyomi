
月詠 (Tsukuyomi): Furigana Delimiter Adder
===========================================

Summary
-------

This command line script copies standard input to standard ouptut but adds
a matching pair of 振り仮名 (furigana) delimiters (the square brackets '[' and
']') after each 漢字 (kanji) character.



Running
-------

1. Download 月詠 if you have not already done so.

2. Open a console or terminal.

3. Navigate to the directory containing the downloaded code.  (You could
   execute the tool from any directory, but these instructions assume that
   you will execute the tool from within the directory in which the tool
   resides.  This simplifies the instructions.)

4. Run the command

   > `./add-furigana-delimiters.py`

   with standard input and standard output redirected or piped as you wish.
   For example, if you want to add delimiters to the contents of `a.txt` and
   save the results in `b.txt`, then this command will do it:

   > `./add-furigana-delimiters.py <a.txt >b.txt`



Examples
--------

> `# echo 'Here is some text: 今日は。お元気ですか。' | ./add-furigana-delimiters.py`
> `Here is some text: 今[]日[]は。お元[]気[]ですか。`



License
-------

See LICENSE for the license governing this tool.

