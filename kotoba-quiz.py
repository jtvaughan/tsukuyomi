#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月詠 (Tsukuyomi) is a set of Python tools for learning the Japanese language.
It is meant to supplement individuals' learning tools, not to function as a
complete learning suite like Rosetta Stone.  It is coded to be useful but not
necessarily easy to use for average computer users.  If you can run Python
commands on a terminal, then you can use 月詠.

月詠 is the god of the moon in Shinto mythology.

This script starts a local web server that serves 言葉 flashcard quizzes.

Homepage and documentation: https://github.com/joodan-van-github/tsukuyomi

This file was released to the public domain in 2012.  See LICENSE for details.
"""

__author__ = "Joodan Van <joodan.van.github@gmail.com>"
__version__ = "0.1"
__license__ = "Public Domain"

import argparse
import os
import os.path
import sys
import urllib.parse

if __name__ == "__main__":
  sys.path = [os.path.realpath(__file__)] + sys.path

from tsukuyomi import *



QuizURL = "/"
CurrentDeck = None
CurrentSession = None
FlashcardsFile = None
FlashcardsStatsLog = None
ImageSettings = None
ImageSource = None
LeitnerBuckets = [0]      # list of per-bucket delays (in seconds); bucket zero is implicitly defined
RemainingTimeSecs = 0



class T言葉のフラッシュカード(TFlashcard):
  """ Instances of this class are Leitner flashcards with three parts: a
      Japanese text, an English translation (with optional notes), and the
      source of the Japanese text."""

  def __init__(self, 日本語, 英語, source):
    """ Construct a new flashcard with the specified Japanese text (日本語),
        English translation (英語), and source."""
    self.__日本語 = 日本語
    self.__英語 = 英語
    self.__source = source
    super().__init__()

  def __bytes__(self):
    return bytes(self.日本語, encoding="UTF-8") + bytes(self.英語, encoding="UTF-8") + bytes(self.Source, encoding="UTF-8")

  @property
  def 英語(self):
    """the English translation of the Japanese text"""
    return self.__英語

  @property
  def 日本語(self):
    """the Japanese text"""
    return self.__日本語

  @property
  def Source(self):
    """the source of the Japanese text"""
    return self.__source

class T言葉のフラッシュカードFormatError(TConfigurationFormatError):
  """ T言葉のフラッシュカードのパーサ raises this exception when there is a
      flashcard format error."""
  pass

class T言葉のフラッシュカードのパーサ(TConfigurationParser):
  """ This configuration file parser parses 言葉のフラッシュカード files.
      It passes each フラッシュカード to a client-supplied handler."""

  def __init__(self, on_flashcard_handler):
    """ Construct a flashcard parser that passes each flashcard to the specified
        unary handler."""
    self.__source = None
    self.__日本語 = None
    self.__英語 = None
    self.__handler = on_flashcard_handler
    def SectionBeginHandler(section, parent):
      if parent is None:
        if section.Name != "言葉のフラッシュカード":
          raise T言葉のフラッシュカードFormatError(self.Line, self.Column, "top-level section isn't 言葉のフラッシュカード")
      elif self.__source is None:
        self.__source = section.Name
      elif self.__日本語 is not None:
        raise T言葉のフラッシュカードFormatError(self.Line, self.Column, "フラッシュカード sections cannot have subsections")
      else:
        self.__日本語 = section.Name
    def SectionEndHandler(section):
      if self.__日本語 is not None:
        if self.__英語 is None:
          raise T言葉のフラッシュカードFormatError(self.Line, self.Column, "フラッシュカード must have an 英語")
        self.__Handleカード(T言葉のフラッシュカード(self.__日本語, self.__英語, self.__source))
        self.__英語 = None
        self.__日本語 = None
      elif self.__source is not None:
        self.__source = None
    def SettingHandler(setting, section):
      if self.__日本語 is None:
        raise T言葉のフラッシュカードFormatError(self.Line, self.Column, "only フラッシュカード sections may have settings")
      elif self.__英語 is not None:
        raise T言葉のフラッシュカードFormatError(self.Line, self.Column, "フラッシュカード may only have one setting each")
      else:
        self.__英語 = setting
    super().__init__(SectionBeginHandler, SectionEndHandler, SettingHandler)

  def __Handleカード(self, カード):
    self.__handler(カード)

  def SetカードHandler(self, handler):
    """ Set the function (TFlashcard -> ()) that will process parsed cards."""
    self.__handler = handler

  @property
  def カードのHandler(self):
    """the function (TFlashcard -> ()) that will process parsed cards"""
    return self.__handler

@get(QuizURL)
def Config():
  global CurrentSession
  CurrentSession = str(random.random())

  deck_factory = TCardDeckFactory(
    FlashcardsFile,
    lambda: T言葉のフラッシュカードのパーサ(None),
    lambda parser, handler: parser.SetカードHandler(handler),
    FlashcardsStatsLog,
    lambda: TLogParser(None),
    lambda parser, handler: parser.SetRecordCb(handler),
    [TLeitnerBucket(delay) for delay in LeitnerBuckets]
   )

  buf = io.StringIO()
  BeginHTML5(buf, title="言葉の試験 Setup")
  buf.write("</head><body><p><h1>言葉の試験 Setup</h1></p><p>")
  buf.write(str(deck_factory.NumberOfDueCards))
  buf.write(" of ")
  buf.write(str(deck_factory.NumberOfCards))
  buf.write(" cards are due.  (")
  buf.write(str(deck_factory.NumberOfNewCards))
  buf.write(" are new.)</p><p><table border='1'><caption>Leitner Bucket Distribution</caption><tr><th style='text-align: left'>Bucket Number</th>")
  for bucket in range(len(deck_factory.Buckets)):
    buf.write("<td style='text-align: center'>" + str(bucket) + "</td>")
  buf.write("</tr><tr><th style='text-align: left'>Cards Due / Card Count</th>")
  for bucket in deck_factory.Buckets:
    buf.write("<td style='text-align: center'>")
    if bucket.CardCount:
      buf.write((str(bucket.DueCardCount) + "/" if bucket.DueCardCount else "") + str(bucket.CardCount))
    else:
      buf.write("&nbsp;")
    buf.write("</td>")
  buf.write("""</tr></table></p><p><form method="post" action=\"""")
  buf.write(QuizURL)
  buf.write("""\">
<fieldset><legend>Limits</legend><p>
<table><tr><th style="text-align:right"><label>Time:</label></th>
<td><input type="text" id="時" name="hours" pattern="[0-9]*" /></td><td><label for="時">時</label></td></tr>
<tr><td></td><td><input type="text" id="分" name="minutes" pattern="[0-9]*" /></td><td><label for="分">分</label></td></tr>
<tr><td></td><td><input type="text" id="秒" name="seconds" pattern="[0-9]*" /></td><td><label for="秒">秒</label></td></tr>
</table></p><p>
<table>
<tr><th style="text-align:right"><label>Max deck size:</label></th><td><input type="text" name="size" pattern="[0-9]*" title="the maximum number of due cards to show or the maximum deck size if no cards are due"/></td></tr>
<tr><th style="text-align:right"><label>Max new cards:</label></th><td><input type="text" name="num_new_cards" pattern="[0-9]*" title="the maximum number of new cards to show" /></td></tr>
</table></p></fieldset>
<fieldset><legend>漢字 Stroke Order Diagram Source</legend><p>""")
  for index, source in enumerate(RemoteSources):
    buf.write("""<input type="radio" name="漢字source" id="source""")
    buf.write(str(index))
    buf.write("""\" checked="checked" value=\"""" if index == 0 else """\" value=\"""")
    buf.write(source)
    buf.write("""\" /><label for="source""")
    buf.write(str(index))
    buf.write("""\">""")
    buf.write(source)
    buf.write("""</label><br />""")
  buf.write("""</p></fieldset>
<input type="submit" value="始めましょう！" autofocus="autofocus" />
<input type="hidden" name="method" value="configure" />
<input type="hidden" name="session_token" value=\"""")
  buf.write(CurrentSession)
  buf.write("""\" /></form></p></body></html>""")
  return buf.getvalue()

@post(QuizURL)
def HandlePost():
  global CurrentDeck
  global CurrentSession
  global ImageSource
  global RemainingTimeSecs

  session = request.forms.session_token
  if not session:
    abort(400, "no session")
  if CurrentSession is None:
    CurrentSession = session
  elif session != CurrentSession:
    abort(400, "session is no longer valid")

  method = request.forms.method
  if method == "configure":
    # TODO Detect when another session is running and confirm overwriting it.

    # Parse the quiz's configuration and create a deck.
    RemainingTimeSecs = 60 * 60 * StrToInt(request.forms.hours, "hours")
    RemainingTimeSecs += 60 * StrToInt(request.forms.minutes, "minutes")
    RemainingTimeSecs += StrToInt(request.forms.seconds, "seconds")

    # Get the 漢字 stroke order diagram source.
    if not request.forms.漢字source:
      abort(400, "no 漢字source defined")
    if request.forms.漢字source not in RemoteSources:
      abort(400, "漢字source is not a valid remote stroke order diagram source.")
    ImageSource = request.forms.漢字source

    # Parse the flashcards file and create a deck from some of the cards.
    deck_factory = TCardDeckFactory(
      FlashcardsFile,
      lambda: T言葉のフラッシュカードのパーサ(None),
      lambda parser, handler: parser.SetカードHandler(handler),
      FlashcardsStatsLog,
      lambda: TLogParser(None),
      lambda parser, handler: parser.SetRecordCb(handler),
      [TLeitnerBucket(delay) for delay in LeitnerBuckets]
     )
    CurrentDeck = TCardDeck(
      deck_factory.ConstructDeck(
        StrToInt(request.forms.size, "size")
         if request.forms.size
         else deck_factory.NumberOfCards,
        StrToInt(request.forms.num_new_cards, "num_new_cards")
         if request.forms.num_new_cards
         else 0
       )
     )

    # Finally, render the first card.
    return RenderCard()

  assert CurrentDeck
  RemainingTimeSecs = StrToInt(request.forms.secs_left, "secs_left")
  if method == "success":
    if FlashcardsStatsLog is not None:
      try:
        with open(FlashcardsStatsLog, "a") as logf:
          CurrentDeck.MarkSucceeded(TLogWriter(logf))
      except IOError as e:
        abort(500, "WARNING: Failed to open or write to the stats log: " + str(e) + "\n")
    else:
      CurrentDeck.MarkSucceeded(None)
    if CurrentDeck.HasCards:
      return RenderCard()
    else:
      return RenderFinishPage(False)
  elif method == "failure":
    CurrentDeck.MarkFailed()
    if CurrentDeck.HasCards:
      return RenderCard()
    else:
      return RenderFinishPage(False)
  elif method == "timeout":
    return RenderFinishPage(True)
  else:
    abort(400, "bad method choice")

def Main():
  global FlashcardsFile
  global FlashcardsStatsLog
  global ImageSettings

  parser = argparse.ArgumentParser(description="月詠は日本語を勉強するツールです。")
  parser.add_argument(
    "--ポート番号",
    type=int,
    default=None,
    dest="ポート番号",
    help="サーバのポート番号です。"
   )
  parser.add_argument(
    "設定ファイル",
    help="path to the file containing the server's settings"
   )

  # Parse and validate the arguments.
  args = parser.parse_args(sys.argv[1:])

  # Default settings and flags.
  設定ファイルのディレクトリ = os.path.abspath(os.path.dirname(args.設定ファイル))
  ポート = None
  delays_defined = False

  # Parse the configuration file.
  def ハンドラ(section, パス名, PrintErrorAndExit):
    nonlocal ポート
    nonlocal delays_defined
    global FlashcardsFile
    global FlashcardsStatsLog
    global ImageSettings

    if section.Name == "flashcards-file":
      if not section.IsAttribute:
        PrintErrorAndExit("'flashcards-file' must be an attribute.")
      if FlashcardsFile is not None:
        PrintErrorAndExit("'flashcards-file' must be defined once.")
      FlashcardsFile = EnsureAccessibleAbsoluteFilePath(section.Value, 設定ファイルのディレクトリ, os.R_OK, "flashcards-file")
    elif section.Name == "stats-log":
      if not section.IsAttribute:
        PrintErrorAndExit("'stats-log' must be an attribute.")
      if FlashcardsStatsLog is not None:
        PrintErrorAndExit("'stats-log' must be defined once.")
      FlashcardsStatsLog = EnsureAbsolutePath(section.Value, 設定ファイルのディレクトリ)
      if os.path.exists(FlashcardsStatsLog):
        FlashcardsStatsLog = EnsureAccessibleAbsoluteFilePath(section.Value, 設定ファイルのディレクトリ, os.R_OK | os.W_OK, "stats-log")
    elif section.Name == "delays":
      if delays_defined:
        PrintErrorAndExit("'delays' must be defined once.")
      delays_defined = True
      if section.HasSections:
        PrintErrorAndExit("'delays' cannot have subsections.")
      for delay in section.Settings:
        try:
          delay = float(delay)
        except ValueError:
          PrintErrorAndExit("'delays' has a non-numeric delay: " + delay)
        delay = int(delay * 86400)
        if delay < 0:
          PrintErrorAndExit("'delays' has a delay that is is less than zero.")
        LeitnerBuckets.append(delay)
    elif section.Name == "image-settings":
      if not section.IsAttribute:
        PrintErrorAndExit("'image-settings' must be an attribute.")
      if ImageSettings is not None:
        PrintErrorAndExit("'image-settings' must be defined at most once.")
      ImageSettings = TStrokeOrderDiagramFSInfo(section.Value)
    elif section.Name == "port":
      if not section.IsAttribute:
        PrintErrorAndExit("'port' must be an attribute.")
      if ポート is not None:
        PrintErrorAndExit("'port' must be defined at most once.")
      try:
        ポート = int(section.Value)
      except ValueError:
        PrintErrorAndExit("'port' has a non-numeric value: " + section.Value)
      if ポート <= 0:
        PrintErrorAndExit("'port' must be positive.")
      if ポート > 65535:
        PrintErrorAndExit("'port' must be less than 65536.")
    else:
      PrintErrorAndExit("A section has an invalid name: " + section.Name)
  ツールの設定ファイルを分析する(args.設定ファイル, "kotoba-quiz-settings", False, ハンドラ)

  # Adjust settings.
  if args.ポート番号 is not None:
    try:
      ポート = int(args.ポート番号)
    except ValueError:
      sys.stderr.write("すみません、サーバのポート番号は駄目です。外のポート番号を使って下さい。\n")
      sys.exit(2)
  if ポート is None:
    sys.stderr.write("no port specified\n")
    sys.exit(2)
  if ポート <= 0:
    sys.stderr.write("すみません、サーバのポート番号は駄目です。The port number must be positive.\n")
    sys.exit(2)
  if ポート > 65535:
    sys.stderr.write("すみません、サーバのポート番号は駄目です。The port number must be less than 65536.\n")
    sys.exit(2)

  # Start the server.
  run(host="localhost", port=ポート, debug=True)

def RenderCard():
  カード = CurrentDeck.GetCard()
  漢字のセット = set()
  振り仮名がある = False
  振り仮名producer = T言葉と振り仮名Producer('(', ')')
  def KanjiOnClickGenerator(字):
    quoted = urllib.parse.quote(字)
    return """window.open('http://jisho.org/kanji/details/""" + quoted + """', '""" + quoted + """')"""
  def KanjiOnMouseoverGenerator(字):
    漢字のセット.add(字)
    return "showKanjiImage('" + 字 + "')"
  def KanjiOnMouseoutGenerator(字):
    return "hideKanjiImage('" + 字 + "')"

  def GenerateHead(buf):
    buf.write("""<style type="text/css">
span.passed {
  color: green;
}

span.failed {
  color: red;
}

span.seen {
  color: blue;
}

span.kanji:hover {
  color: blue;
}

</style><script type="text/javascript">
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

kanji_diagram_enabled = false;

function enableKanjiView() {
  kanji_diagram_enabled = true;
  enable_kanji_button = document.getElementsByName('show_kanji')[0];
  enable_kanji_button.setAttribute('style', 'display: none;');
}

function showKanjiImage(kanji) {
  kanji_diagram_src_set = true;
  kanji_image = document.getElementsByName('漢字diagram' + kanji)[0];
  if (kanji_diagram_enabled) {
    kanji_image.setAttribute('style', 'display: block; max-width: 100%; margin-left: auto; margin-right: auto');
  }
}

function hideKanjiImage(kanji) {
  kanji_diagram_src_set = true;
  kanji_image = document.getElementsByName('漢字diagram' + kanji)[0];
  if (kanji_diagram_enabled) {
    kanji_image.setAttribute('style', 'display: none;');
  }
}

</script>""")
  def RenderSource(buf):
    nonlocal 振り仮名がある
    buf.write("<br />(Source: ")
    振り仮名producer.Reset()
    振り仮名producer.Process(カード.Source)
    振り仮名producer.Finish()
    GenerateHTML5Ruby(振り仮名producer.Results, buf, "kanji", KanjiOnClickGenerator, KanjiOnMouseoverGenerator, KanjiOnMouseoutGenerator, "furigana", False)
    buf.write(")")
    振り仮名がある = 振り仮名がある or any(ペア.振り仮名 for ペア in 振り仮名producer.Results)
  def GenerateFront(buf):
    nonlocal 振り仮名がある
    振り仮名producer.Reset()
    振り仮名producer.Process(カード.日本語)
    振り仮名producer.Finish()
    GenerateHTML5Ruby(振り仮名producer.Results, buf, "kanji", KanjiOnClickGenerator, KanjiOnMouseoverGenerator, KanjiOnMouseoutGenerator, "furigana", False)
    振り仮名がある = 振り仮名がある or any(ペア.振り仮名 for ペア in 振り仮名producer.Results)
  def GenerateBack(buf):
    nonlocal 振り仮名がある
    振り仮名producer.Reset()
    振り仮名producer.Process(カード.英語)
    振り仮名producer.Finish()
    GenerateHTML5Ruby(振り仮名producer.Results, buf, "kanji", KanjiOnClickGenerator, KanjiOnMouseoverGenerator, KanjiOnMouseoutGenerator, "furigana", False)
    振り仮名がある = 振り仮名がある or any(ペア.振り仮名 for ペア in 振り仮名producer.Results)
    RenderSource(buf)
  def GenerateSelectors(buf):
    buf.write("<form><input type='button' name='show_kanji' value='漢字の書き方を見せて' onclick='enableKanjiView()'/>")
    if 振り仮名がある:
      buf.write("""<input type="button" name="振り仮名を見せて" value="振り仮名を見せて" onclick="toggle_visibility('furigana')"/>""")
    buf.write("</form>")
  def GenerateStats(buf):
    stats = CurrentDeck.Statistics
    buf.write("""<span class="passed">""")
    buf.write(str(stats.NumPassedOnFirstTry))
    buf.write(""" passed</span>, <span class="failed">""")
    buf.write(str(stats.NumFailedOnFirstTry))
    buf.write(""" failed</span>, <span class="seen">""")
    buf.write(str(stats.NumAttempts))
    buf.write(" seen</span>, ")
    buf.write(str(stats.NumCardsLeft))
    buf.write(" of ")
    buf.write(str(stats.NumCards))
    buf.write(" left")
    if RemainingTimeSecs > 0:
      buf.write(""" <span id="time_left">""" +
        str(RemainingTimeSecs // 3600) + "時" +
        str((RemainingTimeSecs % 3600) // 60) + "分" +
        str((RemainingTimeSecs % 3600) % 60) + "秒</span>"
       )
  def GenerateBottom(buf):
    for 字 in 漢字のセット:
      buf.write("""<img name="漢字diagram""")
      buf.write(字)
      buf.write("""\" style="display: none" alt="漢字 Stroke Diagram" src=\"""")
      buf.write(
        GetStrokeOrderDiagramURL(字, ImageSettings.ImageDirectory, ImageSource)
         if ImageSettings is not None and ImageSource is not None
         else ""
       )
      buf.write("""\" />""")

  return GenerateCardHTML("/", CurrentSession, "言葉の試験", RemainingTimeSecs,
   GenerateHead, GenerateFront, GenerateBack, GenerateSelectors, GenerateStats,
   GenerateBottom)

def RenderFinishPage(timed_out):
  assert CurrentDeck is not None
  buf = io.StringIO()
  buf.write("Timed out!" if timed_out else "Done!")
  return buf.getvalue()

@get(StrokeOrderDiagramURLBase + "<source>/<kanji>")
def ServeImage(source, kanji):
  if urllib.parse.unquote(source) != ImageSource:
    abort(403, "unexpected source")
  return ServeStrokeOrderDiagram(
    kanji,
    ImageSettings.ImageDirectory if ImageSettings is not None else None,
    source
   )

if __name__ == "__main__":
  Main()

