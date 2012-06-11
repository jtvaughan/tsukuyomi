#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月詠 (Tsukuyomi) is a set of Python tools for learning the Japanese language.
It is meant to supplement individuals' learning tools, not to function as a
complete learning suite like Rosetta Stone.  It is coded to be useful but not
necessarily easy to use for average computer users.  If you can run Python
commands on a terminal, then you can use 月詠.

月詠 is the god of the moon in Shinto mythology.

This script scans files for 漢字 (kanji) and downloads their stroke order
diagrams (SODs) from one or more remote sources.  The script separates SODs
into subdirectories according to their sources.

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

if __name__ != "__main__":
  sys.stderr.write("This script is meant to be executed, not imported.\n")
  sys.exit(1)

sys.path = [os.path.realpath(os.path.dirname(__file__))] + sys.path

from tsukuyomi import *

# Construct the argument parser.
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

# Parse the command-line arguments.
args = parser.parse_args(sys.argv[1:])

# Validate the arguments.
if args.max_simultaneous_downloads <= 0:
  sys.stderr.write("max_simultaneous_downloads must be a natural number.\n")
  sys.exit(1)

# Get image directory settings.
downloader = TStrokeOrderDiagramFSInfo(args.設定ファイル)

# Scan the files for 漢字 and schedule downloads if necessary.
漢字のセット = set()
def ParseTextFile(ファイル):
  with open(ファイル, "r") as f:
    for line in f:
      for c in line:
        if ord(c) in KANJI_RANGE:
          漢字のセット.add(c)
for ファイル in downloader.ファイル:
  try:
    if os.path.isdir(ファイル):
      for dirpath, _, filenames in os.walk(ファイル):
        for textfile in (os.path.join(dirpath, fp) for fp in filenames):
          ファイル = textfile
          ParseTextFile(textfile)
    else:
      ParseTextFile(ファイル)
  except Exception as e:
    sys.stderr.write("unexpected error while opening or reading the file/directory " + ファイル + ": " + str(e) + "\n")
    sys.exit(2)

# If there are no 漢字 to download, then do nothing.
if not 漢字のセット:
  print("漢字がありません。")
  sys.exit(0)

# Download 漢字 if necessary.
print("Found " + str(len(漢字のセット)) + " 漢字")
with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_simultaneous_downloads) as executor:
  jobs = dict(
    (executor.submit(downloader.Download, 漢字, source), (漢字, source))
     for 漢字 in 漢字のセット for source in downloader.EnabledSources
     if not downloader.Downloaded(漢字, source)
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

