#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月詠 (Tsukuyomi) is a set of Python tools for learning the Japanese language.
It is meant to supplement individuals' learning tools, not to function as a
complete learning suite like Rosetta Stone.  It is coded to be useful but not
necessarily easy to use for average computer users.  If you can run Python
commands on a terminal, then you can use 月詠.

月詠 is the god of the moon in Shinto mythology.

This script adds empty pairs of matching square brackets to 漢字 characters
read from standard input and outputs the result to standard output.

Homepage and documentation: https://github.com/joodan-van-github/tsukuyomi

This file was released to the public domain in 2012.  See LICENSE for details.
"""

__author__ = "Joodan Van <joodan.van.github@gmail.com>"
__version__ = "0.1"
__license__ = "Public Domain"

if __name__ != "__main__":
  sys.stderr.write("This script is meant to be executed, not imported.\n")
  sys.exit(1)

import os.path
import sys

sys.path = [os.path.realpath(os.path.dirname(__file__))] + sys.path

from tsukuyomi import *

for line in sys.stdin:
  for c in line:
    sys.stdout.write(c)
    if ord(c) in KANJI_RANGE:
      sys.stdout.write("[]")

