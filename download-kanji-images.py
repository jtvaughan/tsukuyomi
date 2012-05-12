#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月詠 (Tsukuyomi) is a set of Python tools for learning the Japanese language.
It is meant to supplement individuals' learning tools, not to function as a
complete learning suite like Rosetta Stone.  It is coded to be useful but not
necessarily easy to use for average computer users.  If you can run Python
commands on a terminal, then you can use 月詠.

月詠 is the god of the moon in Shinto mythology.

This script scans configuration files and log files for 漢字 (kanji) and
downloads their stroke order diagrams (SODs) from one or more remote sources.
The script separates SODs into subdirectories according to their sources.

Homepage and documentation: https://github.com/joodan-van-github/tsukuyomi

This file was released to the public domain in 2012.  See LICENSE for details.
"""

__author__ = "Joodan Van <joodan.van.github@gmail.com>"
__version__ = "0.1"
__license__ = "Public Domain"

import argparse
import concurrent.futures
import multiprocessing
import os
import os.path
import sys

if __name__ == "__main__":
  sys.path = [os.path.realpath(__file__)] + sys.path

from tsukuyomi import *

class T設定ファイルのパーサ(TConfigurationParser):
  """ Instances of this class are configuration file parsers that pass individual 漢字 from section names and settings to a unary function."""

  def __init__(self, 漢字ハンドラ):
    """ Construct a configuration file parser that passes individual 漢字 from section names and settings to the specified unary function."""
    def SectionBeginCb(section, parent):
      for c in section.Name:
        if ord(c) in KANJI_RANGE:
          漢字ハンドラ(c)
    def SectionEndCb(section):
      pass
    def SettingCb(setting, section):
      for c in setting:
        if ord(c) in KANJI_RANGE:
          漢字ハンドラ(c)
    super().__init__(SectionBeginCb, SectionEndCb, SettingCb)

class Tログファイルのパーサ(TLogParser):
  """ Instances of this class are log file parsers that pass individual 漢字 from records to a unary function."""

  def __init__(self, 漢字ハンドラ):
    """ Construct a log file parser that passes individual 漢字 from records to the specified unary function."""
    def RecordCb(record):
      for field in record:
        for c in field:
          if ord(c) in KANJI_RANGE:
            漢字ハンドラ(c)
    super().__init__(RecordCb)

def Main():
  parser = argparse.ArgumentParser(description="This is the 漢字 stroke order diagram downloader.")
  parser.add_argument(
    "--max-simultaneous-downloads",
    type=int,
    dest="max_simultaneous_downloads",
    default=multiprocessing.cpu_count(),
    help="the maximum number of simultaneous downloads permitted (default: " + str(multiprocessing.cpu_count()) + ")"
   )
  parser.add_argument(
    "設定ファイル",
    help="path to the file containing the image directory settings"
   )

  args = parser.parse_args(sys.argv[1:])

  # Validate the arguments.
  if args.max_simultaneous_downloads <= 0:
    sys.stderr.write("max_simultaneous_downloads must be a natural number.\n")
    sys.exit(1)

  # Get image directory settings.
  settings = TStrokeOrderDiagramFSInfo(args.設定ファイル)

  # Scan the files for 漢字 and schedule downloads if necessary.
  漢字のセット = set()
  def 漢字ハンドラ(漢字):
    漢字のセット.add(漢字)
  for ファイル in settings.設定ファイル:
    parser = T設定ファイルのパーサ(漢字ハンドラ)
    try:
      with open(ファイル, "r") as f:
        parser.ParseStrings(f)
      parser.Finish()
    except TConfigurationFormatError as e:
      sys.stderr.write("すみません、" + ファイル + "は駄目な設定ファイルです。\n")
      sys.stderr.write(str(e) + "\n")
      sys.exit(2)
    except Exception as e:
      sys.stderr.write("unexpected error while parsing the configuration file " + ファイル + ": " + str(e) + "\n")
      sys.exit(2)
  for ファイル in settings.ログファイル:
    parser = Tログファイルのパーサ(漢字ハンドラ)
    try:
      with open(ファイル, "r") as f:
        parser.ParseStrings(f)
      parser.Finish()
    except TLogFormatError as e:
      sys.stderr.write("すみません、" + ファイル + "は駄目なログファイルです。\n")
      sys.stderr.write(str(e) + "\n")
      sys.exit(2)
    except Exception as e:
      sys.stderr.write("unexpected error while parsing the log file " + ファイル + ": " + str(e) + "\n")
      sys.exit(2)

  def Download漢字(漢字, source):
    source_dir = os.path.join(settings.ImageDirectory, source)
    if not os.path.exists(source_dir):
      os.mkdir(source_dir)
    RemoteSources[source][0](漢字, ConstructStrokeOrderDiagramPath(漢字, settings.ImageDirectory, source), settings.タイムアウト)

  # If there are no 漢字 to download, then do nothing.
  if not 漢字のセット:
    print("No 漢字")
    sys.exit(0)

  # Download 漢字 if necessary.
  print("Found " + str(len(漢字のセット)) + " 漢字")
  with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_simultaneous_downloads) as executor:
    jobs = dict(
      (executor.submit(Download漢字, 漢字, source), (漢字, source))
       for 漢字 in 漢字のセット for source in settings.EnabledSources
       if GetStrokeOrderDiagramPath(漢字, settings.ImageDirectory, source) is False
     )
    for future in concurrent.futures.as_completed(jobs):
      漢字, source = jobs[future]
      if future.exception() is None:
        print("Finished downloading " + 漢字 + " from " + source)
      elif isinstance(future.exception(), urllib.error.HTTPError):
        if future.exception().code not in {403, 404}:
          sys.stderr.write("Unexpected HTTP error while downloading " + 漢字 + " from " + source + ": " + str(future.exception()) + "\n")
      else:
        sys.stderr.write("Unexpected error while downloading " + 漢字 + " from " + source + ": " + str(future.exception()) + "\n")
  print("Done")

if __name__ == "__main__":
  Main()

