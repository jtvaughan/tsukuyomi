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

if __name__ != "__main__":
  sys.stderr.write("This script is meant to be executed, not imported.\n")
  sys.exit(1)

sys.path = [os.path.realpath(os.path.dirname(__file__))] + sys.path

from tsukuyomi import *



QuizURL = "/"
CurrentDeck = None
CurrentSession = None
DeckFactory = None
DeckName = "Untitled"
DefaultTime = ('', '', '')
DefaultMaxDeckSize = ''
DefaultMaxNewCards = ''
FlashcardsFile = None
FlashcardsStatsLog = None
ImageSettings = None
ImageSource = None
RemainingTimeSecs = 0



def ParseFlashcardSourceFile(flashcard_cb):
  TSourcedフラッシュカード.ParseSourceFile(FlashcardsFile, flashcard_cb)

def ParsePerformanceLogFile(log_record_cb):
  if FlashcardsStatsLog is not None and os.path.isfile(FlashcardsStatsLog):
    with open(FlashcardsStatsLog, 'r') as fsl:
      for record in ConstructLogParser(fsl):
        log_record_cb(record)

@get(QuizURL)
def Config():
  global CurrentSession
  CurrentSession = str(random.random())
  DeckFactory.Refresh()
  return DeckFactory.RenderConfigPage(DeckName + " -- Setup", CurrentSession, QuizURL,
   default_time=DefaultTime, default_max_deck_size=DefaultMaxDeckSize,
   default_max_new_cards=DefaultMaxNewCards, image_settings=ImageSettings)

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
    if request.forms.漢字source not in TStrokeOrderDiagramFSInfo.RemoteSources:
      abort(400, "漢字source is not a valid remote stroke order diagram source.")
    ImageSource = request.forms.漢字source

    # Parse the flashcards file and create a deck from some of the cards.
    DeckFactory.Refresh()
    CurrentDeck = TCardDeck(
      DeckFactory.ConstructDeck(
        StrToInt(request.forms.size, "size")
         if request.forms.size
         else DeckFactory.NumberOfCards,
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
          CurrentDeck.MarkSucceeded(lambda record: ConstructLogWriter(logf).writerow(record))
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

def RenderCard():
  stats = CurrentDeck.Statistics
  return CurrentDeck.GetCard().Render(
    DeckName + " -- " + str(int((stats.NumCards - stats.NumCardsLeft) / stats.NumCards * 100)) + "% Done",
    QuizURL,
    CurrentSession,
    image_settings=ImageSettings,
    image_source=ImageSource,
    timeout_secs=RemainingTimeSecs,
    deck_stats=stats
   )

def RenderFinishPage(timed_out):
  assert CurrentDeck is not None
  return "Timed out!" if timed_out else "Done!"

@get(StrokeOrderDiagramURLBase + "<source>/<kanji>")
def ServeImage(source, kanji):
  if ImageSettings is None:
    abort(404, "File not found, fool.")
  if urllib.parse.unquote(source) != ImageSource:
    abort(403, "unexpected source")
  return ImageSettings.ServeStrokeOrderDiagram(kanji, source)



################################################################################
# Startup code
################################################################################

# Construct the argument parser.
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
delays = [0]  # Bucket zero is implicitly defined.
ポート = None

# Parse the configuration file.
def ハンドラ(config, パス名, PrintErrorAndExit):
  global ポート
  global DeckName
  global DefaultTime
  global DefaultMaxDeckSize
  global DefaultMaxNewCards
  global FlashcardsFile
  global FlashcardsStatsLog
  global ImageSettings

  設定ファイルのディレクトリ = os.path.dirname(パス名)

  if 'general' in config:
    general = config['general']
    if 'flashcards-file' in general:
      FlashcardsFile = EnsureAccessibleAbsoluteFilePath(general['flashcards-file'], 設定ファイルのディレクトリ, os.R_OK, 'flashcards-file')
    if 'stats-log' in general:
      stats_log = general['stats-log']
      FlashcardsStatsLog = EnsureAbsolutePath(stats_log, 設定ファイルのディレクトリ)
      if os.path.exists(FlashcardsStatsLog):
        FlashcardsStatsLog = EnsureAccessibleAbsoluteFilePath(stats_log, 設定ファイルのディレクトリ, os.R_OK | os.W_OK, 'stats-log')
    if 'image-settings' in general:
      ImageSettings = TStrokeOrderDiagramFSInfo(general['image-settings'])
    if 'name' in general:
      DeckName = general['name'].strip()
      if not DeckName:
        DeckName = "Untitled"
    if 'port' in general:
      port = general['port']
      try:
        ポート = int(port)
      except ValueError:
        PrintErrorAndExit("'port' has a non-numeric value: " + port)
  if 'defaults' in config:
    defaults = config['defaults']
    if 'time' in defaults:
      DefaultTime = list(x.strip() for x in defaults['time'].split(':'))
      if len(DefaultTime) > 3:
        PrintErrorAndExit("'time' has more than three components: " + defaults['time'])
      while len(DefaultTime) < 3:
        DefaultTime = [''] + DefaultTime
    if 'max-deck-size' in defaults:
      DefaultMaxDeckSize = defaults['max-deck-size']
    if 'max-new-cards' in defaults:
      DefaultMaxNewCards = defaults['max-new-cards']
  if 'delays' in config:
    for delay in config['delays']:
      try:
        delay = float(delay)
      except ValueError:
        PrintErrorAndExit("'delays' has a non-numeric delay: " + delay)
      delay = int(delay * 86400)
      if delay < 0:
        PrintErrorAndExit("'delays' has a delay that is is less than zero:" + str(delay))
      delays.append(delay)

ツールの設定ファイルを分析する(args.設定ファイル, ハンドラ)

# Adjust settings.
if args.ポート番号 is not None:
    ポート = ポート番号
if ポート is None:
  sys.stderr.write("no port specified\n")
  sys.exit(2)
if ポート <= 0:
  sys.stderr.write("すみません、サーバのポート番号は駄目です。The port number must be positive.\n")
  sys.exit(2)
if ポート > 65535:
  sys.stderr.write("すみません、サーバのポート番号は駄目です。The port number must be less than 65536.\n")
  sys.exit(2)

# Construct the deck factory and read its associated files for the first time.
DeckFactory = TCardDeckFactory(
  ParseFlashcardSourceFile,
  ParsePerformanceLogFile,
  [TLeitnerBucket(delay) for delay in delays]
 )

# Start the server.
run(host="localhost", port=ポート, debug=True)

