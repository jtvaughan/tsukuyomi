#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月詠 (Tsukuyomi) is a set of Python tools for learning the Japanese language.
It is meant to supplement individuals' learning tools, not to function as a
complete learning suite like Rosetta Stone.  It is coded to be useful but not
necessarily easy to use for average computer users.  If you can run Python
commands on a terminal, then you can use 月詠.

月詠 is the god of the moon in Shinto mythology.

This script creates two-sided flashcard entries for Japanese strings passed
as command-line arguments.  It replaces 漢字 with their 振り仮名 when
振り仮名 annotations are present.  The two-sided flashcard entries are
written as CSV rows to standard output and can be added to flashcard files.
This will read Japanese strings one line at a time from standard input
if no strings are provided as command-line arguments.

Homepage and documentation: https://github.com/joodan-van-github/tsukuyomi

This file was released to the public domain in 2012.  See LICENSE for details.
"""

__author__ = "Joodan Van <joodan.van.github@gmail.com>"
__version__ = "0.1"
__license__ = "Public Domain"

import argparse
import os.path
import sys

if __name__ != "__main__":
  sys.stderr.write("This script is meant to be executed, not imported.\n")
  sys.exit(1)

sys.path = [os.path.realpath(os.path.dirname(__file__))] + sys.path

from tsukuyomi import *

parser = argparse.ArgumentParser(description="Translate Japanese strings into two-sided flashcard entries in CSV format, replacing 漢字 with 振り仮名 wherever there are 振り仮名 annotations.")
parser.add_argument(
  "-r",
  dest="reversed",
  action="store_const",
  const=True,
  default=False,
  help="Reverse the generated cards: The original Japanese strings become the backs of the generated cards."
 )
parser.add_argument(
  "日本語の言葉",
  nargs="*",
  help="日本語の言葉です。"
 )

# Parse and validate the arguments.
args = parser.parse_args(sys.argv[1:])

if args.reversed:
  def GenerateCard(言葉, transformed言葉):
    return (transformed言葉, 言葉)
else:
  def GenerateCard(言葉, transformed言葉):
    return (言葉, transformed言葉)
writer = ConstructLogWriter(sys.stdout)
言葉と振り仮名 = T言葉と振り仮名Producer()
for 言葉 in (args.日本語の言葉 if args.日本語の言葉 else (line[:-1] for line in sys.stdin)):
  writer.writerow(GenerateCard(言葉, ''.join((piece.言葉 if not piece.振り仮名 else piece.振り仮名) for piece in 言葉と振り仮名.ProcessAndReset(言葉))))

