
月詠 (Tsukuyomi): 言葉 (Kotoba) Flashcards
===========================================

Summary
-------

言葉 Flashcards is a web-facing tool for presenting quizzes using two-sided
flashcards.  The tool automatically handles performance statistics and card
scheduling.  Cards are scheduled according to a modified
[Leitner system](http://en.wikipedia.org/wiki/Leitner_system).



Running
-------

1. Download 月詠 if you have not already done so.

2. Open a console or terminal.

3. Navigate to the directory containing the downloaded code.  (You could
   execute the tool from any directory, but these instructions assume that
   you will execute the tool from within the directory in which the tool
   resides.  This simplifies the instructions.)

4. Run the following command:

   > `./kotoba-quiz.py <config-file>`

   where `<config-file>` is the path to a configuration file describing
   the server's properties, such as the path to the file containing flashcards
   and the server's port number.  (See the Configuration Files section below for
   more information.)

   You may override the port number specified in the configuration file via
   the `ポート番号` command-line option:

   > `./kotoba-quiz.py --ポート番号 <port> <config-file>`

   where `<port>` is the server's port number.

   You should see something like this on your terminal:

         Bottle v0.11.dev server starting up (using WSGIRefServer())...
         Listening on http://localhost:8080/
         Hit Ctrl-C to quit.

   The console or terminal will occasionally display diagnostic messages
   ([HTTP](http://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol) request
   and response information) as you interact with the tool through your
   web browser.

5. Open a web browser.

6. Direct the web browser to the URL `http://127.0.0.1:<port>`, where
   `<port>` is the port number used by the tool.

7. You should see a quiz configuration screen.  This screen will display:

   1. the total number of cards in the flashcards file that the tool is using;

   2. the number of cards that are due for review;

   3. a table showing the distribution of cards across the Leitner buckets,
      including how many cards each bucket has and how many of those cards
      are due for review; and

   4. options for configuring the quiz, including:

      * a time limit (defaults to infinity);

      * the maximum number of due cards to show in the quiz _or_ the maximum
        number of cards to review in advance if there are no cards due ("max
        deck size"; defaults to infinity);

      * the maximum number of new cards to show in the quiz
        ("max new cards"; defaults to infinity); and

      * the source of 漢字 stroke order diagrams.

      Most of these fields are optional.

8. Enter your configuration preferences and click on the "始めましょう！" button at
   the bottom of the web page.  This will start the quiz.

9. The tool will show each card's front, called the 言葉 part, first.  After you
   think you know the answer, click on the "Show Answer" button at the bottom
   of the card to show the answer.  The answer will contain the card's back,
   called the 英語 (eigo) part, and the card's source.

10. The web page will display several buttons:

   * **漢字の書き方を見せて**: This enables the 漢字 stroke order diagram display.
     After you click this button, you may move your mouse over any 漢字 on the
     card to display the 漢字's stroke order diagram underneath the card.
     NOTE: If the stroke order diagram source you selected on the configuration
     screen does not have a stroke order diagram for the 漢字, then the page
     will render a broken image underneath the card.

   * **振り仮名を見せて**: This enables the 振り仮名 (furigana) display.  漢字
     annotated with 振り仮名 will display their 振り仮名 next to themselves.
     (See the Flashcard Files section for information about 振り仮名
     annotations.)  Additionally, this button's text will change to
     "Hide 振り仮名"; clicking on it will hide the 振り仮名 annotations.

   * **駄目だ**: Click this button if you answered the card incorrectly.
     The server will record this failure and shuffle the card back into the
     current deck for display later.

   * **やった！**: Click this button if you answered the card correctly.
     The server will record this success and remove the card from the
     current deck.

11. The quiz ends when you answer all cards correctly or you run out of time.
    (Failed cards are shown repeatedly until you answer them correctly.)
    When the quiz ends, you will see a simple web page that says "Done!"

12. If you want to quiz yourself again, go back to step (6).



Configuration Files
-------------------

言葉 Flashcards expects the user to provide a special configuration file
describing the server's properties.  The configuration file's root
must be named "kotoba-quiz-settings" and may contain the following
attributes:

1. _flashcards-file_ (required): This attribute specifies the
   path to a configuration file containing 言葉 flashcards.
   (See the Flashcard Files section for more information.)
2. _stats-log_ (optional): This attribute specifies the path to the log file to
   which the server will append performance data.  (See the Stats Log Files
   section for more information.)
3. _delays_ (optional): This section contains the delays (in days) associated
   with each [Leitner bucket](http://en.wikipedia.org/wiki/Leitner_system).
   
   This section should only contain settings.  Each setting is a natural
   number representing the number of days after which cards placed
   into the corresponding Leitner bucket will be due for review.
   The total number of Leitner buckets is the number of settings in
   this section plus one.  (Bucket zero is always defined.  Its delay
   is zero, which means that cards that the user fails to answer will
   be immediately due for review.)

   Although you can use any natural numbers you want as delays, it makes
   sense to increase the delay as cards move into higher-numbered
   Leitner buckets.  The following example might be a useful configuration:

>     "kotoba-leitner-buckets" {
>         "1";
>         "3";
>         "14";
>         "30";
>         "90";
>         "180"
>     }

   In this example, the Leitner buckets' delays in increasing order by
   Leitner bucket number are 0, 1, 3, 14, 30, 90, and 180 days.  There
   are seven buckets in this example.

4. _port_ (optional): This attribute specifies the server's port number.
   Port numbers must be integers between 1 and 65535, inclusive.  If this
   attribute is absent, then the user will have to specify the port
   via the command-line `ポート番号` option.  (See the Running section
   above for more information.)

5. _image-settings_ (optional): This attribute specifies a path to
   a 漢字 Stroke Order Diagram Downloader configuration file.  (See the
   README file for the 漢字 Stroke Order Diagram Downloader for more
   information.)  If this attribute is present, 言葉 Flashcards will
   try to link to downloaded 漢字 stroke order diagrams according to
   the settings within the specified configuration file; otherwise,
   it will link all stroke order diagrams to remote Internet sources.

All paths in the configuration file are either absolute or relative to
the directory containing the configuration file.

Here is a sample configuration file:

>     "kotoba-quiz-settings" {
        "flashcards-file" { "/日記/日本/日本語/言葉のフラッシュカード.txt" }
        "delays" { "4"; "16" }
        "image-settings" { "./漢字の設定ファイル" }
        "port" { "1337" }
    }



Flashcard Files
---------------

_言葉 flashcards_ are simple two-sided flashcards containing:

1. 日本語：a word, phrase, sentence, or passage written in Japanese;
2. 英語：the English translation of the 日本語 part (possibly with
   additional notes or translation aids); and
3. `Source`：the source of the flashcard (e.g., a friend, 先生, or yourself)

There is nothing stopping you from using these flashcards as regular
two-sided flashcards: You can put anything you want into the two
sides.  However, the algorithms and UI associated with these flashcards
are written to interpret the sides as described above.  (NOTE: 英語 does
not have to be written in English.)

言葉 flashcards are stored within configuration files.  Each file must
follow these rules:

1. The root must be named "言葉のフラッシュカード".
2. The root must contain zero or more sections called _source sections_.
3. Each source section must contain zero or more attributes called
   _flashcard sections_.
4. Neither source sections nor the root may contain settings.
5. Flashcard sections may not have empty values.  (But flashcard sections'
   values may be empty strings.)

Each 言葉 flashcard is constructed as follows:

1. The `Source` side is the name of the source section containing
   the flashcard.
2. The 日本語 side is the name of the flashcard section corresponding to
   the 言葉 flashcard.
3. The 英語 side is the value of the flashcard section corresponding to
   the 言葉 flashcard.

For example, the 言葉 flashcard file

>     "言葉のフラッシュカード" {
        "Japanese class" {
          "私はジョーダンヴァンです。よろしくお願いします。" { "I am Joodan Van.  Nice to meet you. (丁寧語)" }
        "オーストラリア人です。" { "[The subject is] Australian." }
        }
        "もとひろさん" {
          "お手洗いはどこですか。" { "Where is the bathroom? (polite)" }
        }
    }

defines three 言葉 flashcards:

1. 日本語：私はジョーダンヴァンです。よろしくお願いします。  
   英語：I am Joodan Van.  Nice to meet you. (丁寧語)  
   Source：Japanese class

2. 日本語：オーストラリア人です。  
   英語：[The subject is] Australian.  
   Source：Japanese class

3. 日本語：お手洗いはどこですか。  
   英語：Where is the bathroom? (polite)  
   Source：もとひろさん

言葉 Flashcards provides an easy way to annotate Japanese text within 言葉
flashcards.  If a set of [kanji](http://en.wikipedia.org/wiki/Kanji) characters
is followed by a matching pair of parentheses, then the text within the
parentheses will be rendered as the kanji characters'
[振り仮名 (furigana)](http://en.wikipedia.org/wiki/Furigana).  For example:

> ## 今日(きょう)レストランに行って、友(とも)達(だち)と食(しょく)事(じ)をして、たくさんお酒を飲みました。(Note that this text isn't furigana even though it's inside matching parentheses.)今晩家へ(This isn't furigana, either.)帰(かえ)ります。酒(酒(さけ))

produces this 振り仮名-annotated text:

> ## <ruby>今日<rt>きょう</rt></ruby>レストランに行って、<ruby>友<rt>とも</rt></ruby><ruby>達<rt>だち</rt></ruby>と<ruby>食<rt>しょく</rt></ruby><ruby>事<rt>じ</rt></ruby>をして、たくさんお酒を飲みました。(Note that this text isn't furigana even though it's inside matching parentheses.)今晩家へ(This isn't furigana, either.)<ruby>帰<rt>かえ</rt></ruby>ります。<ruby>酒<rt>酒(さけ)</rt></ruby>

Notice:

1. Matching parentheses only denote 振り仮名 when they follow one or more
   consecutive kanji characters.  Matching parentheses appearing anywhere else
   are treated as part of the regular flow of text.
2. 振り仮名 annotations do not work within 振り仮名 annotations.



Stats Log Files
---------------

The user's performance with 言葉 Flashcards will be recorded if the server's
configuration file contains a valid `stats-log` attribute (see above).
Each record has the following fields (in left-to-right order):

1. the timestamp representing the end of the quiz that generated the record;
2. the SHA-1 hash of the flashcard for which the record was created; and
3. the number of times the user had to revisit the card before he successfuly
   answered it.

New records are appended to the log file.  If the log file does not exist,
then 言葉 Flashcards will create it.



License
-------

See LICENSE for the license governing this tool.

