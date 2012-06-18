#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月詠 (Tsukuyomi) is a set of Python tools for learning the Japanese language.
It is meant to supplement individuals' learning tools, not to function as a
complete learning suite like Rosetta Stone.  It is coded to be useful but not
necessarily easy to use for average computer users.  If you can run Python
commands on a terminal, then you can use 月詠.

月詠 is the god of the moon in Shinto mythology.

Homepage and documentation: https://github.com/joodan-van-github/tsukuyomi

This file was released to the public domain in 2012.  See LICENSE for details.
"""

__author__ = "Joodan Van <joodan.van.github@gmail.com>"
__version__ = "0.1"
__license__ = "Public Domain"

import argparse
import collections
import configparser
import csv
import errno
import hashlib
import heapq
import io
import itertools
import jinja2
import os
import os.path
import random
import sys
import time
import urllib.parse
import urllib.request

dirname = os.path.realpath(os.path.dirname(__file__))
sys.path = [dirname] + sys.path

from bottle import *



################################################################################
# Useful globals
################################################################################

TemplateDirectory = os.path.join(dirname, "templates")
JinjaEnvironment = jinja2.Environment(loader=jinja2.FileSystemLoader(TemplateDirectory))



################################################################################
# Miscellaneous Functions
################################################################################

def ConstructConfigurationParser():
  """Construct a configparser.ConfigParser with correct default settings."""
  return configparser.ConfigParser(interpolation=None, allow_no_value=True)

def ConstructLogParser(log_file):
  """Construct a csv.reader with correct default settings for the specified file-like object."""
  return csv.reader(log_file, dialect='unix')

def ConstructLogWriter(log_file):
  """Construct a csv.writer with correct default settings for the specified file-like object."""
  return csv.writer(log_file, dialect='unix')

def ForEachConfigurationSetting(config, section_name, callback):
  """ Invoke the specified callback for each setting in the specified section of the specified configuration file object.
      The callback must accept two parameters: the name of the setting and
      its value.  This method does not invoke the callback if the specified
      section does not exist or has no settings."""
  if section_name in config:
    section = config[section_name]
    for key in section:
      callback(key, section[key])

def EnsureAbsolutePath(path, base):
  """ Convert a path into an absolute path if it is not one already.
      If 'path' is absolute, then this function returns it untouched;
      otherwise, it joins it to 'base'.  'base' must be an absolute path."""
  assert os.path.isabs(base)
  return path if os.path.isabs(path) else os.path.join(base, path)

def EnsureAccessibleAbsoluteDirectoryPath(path, base, perms, path_title=None, error_code=2):
  """ Convert a path into an absolute path and ensure that it refers to a directory with the specified permissions.
      This function expects the following parameters:

        path :: str
          The path to convert and check.
        base :: str
          An absolute path.  If 'path' is not absolute, then it is joined to
          this absolute path.
        perms :: int
          A combination of os.access() flags joined by bitwise OR.

      The following parameters are optional:

        path_title :: str
          A name for the file or setting associated with 'path'.  This becomes
          part of error messages printed by this function.  If this is None
          (the default), then no name is used: Error messages will contain
          the value of 'path' instead.
        error_code :: int
          The error code that the program will return when this function
          terminates it.  This function only terminates the program if
          'path' has problems.

    """
  path = EnsureAbsolutePath(path, base)
  def PrintErrorAndExit(message_stub):
    sys.stderr.write("すみません、" + (path_title if path_title is not None else path) + message_stub + "\n")
    sys.exit(error_code)
  if not os.path.isdir(path):
    PrintErrorAndExit("はディレクトリじゃありません。")
  if not os.access(path, perms):
    PrintErrorAndExit(" does not have the expected access permissions.")
  return path

def EnsureAccessibleAbsoluteFilePath(path, base, perms, path_title=None, error_code=2):
  """ Convert a path into an absolute path and ensure that it refers to a file with the specified permissions.
      This function expects the following parameters:

        path :: str
          The path to convert and check.
        base :: str
          An absolute path.  If 'path' is not absolute, then it is joined to
          this absolute path.
        perms :: int
          A combination of os.access() flags joined by bitwise OR.

      The following parameters are optional:

        path_title :: str
          A name for the file or setting associated with 'path'.  This becomes
          part of error messages printed by this function.  If this is None
          (the default), then no name is used: Error messages will contain
          the value of 'path' instead.
        error_code :: int
          The error code that the program will return when this function
          terminates it.  This function only terminates the program if
          'path' has problems.

    """
  path = EnsureAbsolutePath(path, base)
  def PrintErrorAndExit(message_stub):
    sys.stderr.write("すみません、" + (path_title if path_title is not None else path) + message_stub + "\n")
    sys.exit(error_code)
  if not os.path.isfile(path):
    PrintErrorAndExit("はファイルじゃありません。")
  if not os.access(path, perms):
    PrintErrorAndExit(" does not have the expected access permissions.")
  return path

def StrToInt(text, name):
  """ Convert a string to an integer.  This is meant to be invoked while
      servicing an HTTP request.  'text' is the string that will be converted.
      'name' is a descriptive title for the converted value."""
  try:
    return int(text) if text else 0
  except ValueError:
    abort(400, name + " is not an integer: " + str(text))



################################################################################
# Useful, General-Purpose Data Structures
################################################################################

class TRandomSelector(object):
  """Instances of this class randomly sample elements from sequences.

  Unlike random.sample(), this class accepts generators or anything else
  that can appear in a for-statement because it doesn't need to know the
  sequence's length.  The quality of the random sample depends on the
  quality of the supplied random number generator: The default is the
  random module's default generator.

  Use this class when you want to sample data from a very large data set
  without realizing the entire data set in memory.  For example, if you
  need to select random rows from a database, then this class will
  work handsomely.

  """
  def __init__(self, capacity, sequence=None, randomizer=random):
    """Construct a new randomized selector with the specified capacity.

    At most 'capacity' items will be chosen from those fed to the selector.
    If 'sequence' is not None, then the selector will immediately sample
    data from the specified sequence.  'sequence' can be a generator.

    'randomizer' must not be None.  It must refer to an object (possibly a
    module) that implements a nullary function named "random" that returns
    one random number per invocation.  The default value is the 'random' module.

    Arguments:

      capacity :: numeric -- the sample list's capacity in entries
      sequence -- a sequence of objects
      randomizer -- something that implements a nullary random() method that
       returns random numbers

    """
    self.__capacity = int(capacity)
    self.__sample = []
    self.__randomizer = randomizer
    if sequence is not None:
      self.ConsumeSequence(sequence)

  def __iter__(self):
    """Get a generator that traverses the sample."""
    for _, _, selected in self.__sample:
      yield selected

  def __len__(self):
    """Get the number of sampled items."""
    return len(self.__sample)

  def Add(self, o):
    """Consider the specified object.

    The selector might add the specified object to its sample list.

    Arguments:

      o -- an object

    Returns:

      This method returns True if the selector added the object to its
      sample list.  Otherwise, it returns False.  Note that the object
      might be removed from the sample list later if Add() is invoked again
      with a different object.

    """
    tag = self.__randomizer.random()
    if len(self.__sample) < self.Capacity:
      heapq.heappush(self.__sample, (tag, id(o), o))
      return True
    elif tag >= self.__sample[0][0]:
      heapq.heapreplace(self.__sample, (tag, id(o), o))
      return True
    else:
      return False

  def Clear(self):
    """Clear the sample list."""
    self.__sample = []

  def ConsumeSequence(self, sq):
    """Consider every value in the specified sequence.

    If the sequence is a generator, then this method will exhaust the
    generator.  Infinite generators should not be used.

    Arguments:

      sq -- a sequence or generator

    """
    for x in sq:
      self.Add(x)

  @property
  def Capacity(self):
    """the sample list's capacity in entries"""
    return self.__capacity



################################################################################
# Data structures and algorithms for Japanese text
################################################################################

class T言葉と振り仮名(object):
  """Instances of this class represent pairs of Japanese texts: a string of
     characters representing a word or phrase (言葉) and its reading (振り仮名).
     A tuple-based pair could do the same thing, but this class has
     two advantages:

       1. the elements of the pair are named; and
       2. the pair is immutable."""

  def __init__(self, 言葉, 振り仮名):
    """Create a 言葉-振り仮名 pair."""
    self.__言葉 = 言葉
    self.__振り仮名 = 振り仮名
    super().__init__()

  def __eq__(self, that):
    return isinstance(that, T言葉と振り仮名) and self.言葉 == that.言葉 and self.振り仮名 == that.振り仮名

  def __lt__(self, that):
    return (self.言葉, self.振り仮名) < (that.言葉, that.振り仮名)

  @property
  def 言葉(self):
    """the word or phrase (言葉) part of the pair"""
    return self.__言葉

  @property
  def 振り仮名(self):
    """the reading text (振り仮名) part of the pair"""
    return self.__振り仮名

class TRange(object):
  """ Instances of this class represent simple numeric ranges of the form
      [low, high].  This class supports fast membership testing; in other
      words, for some value 'n', an instance of this class can quickly
      determine whether it contains 'n'."""

  def __init__(self, low, high):
    """ Construct a new inclusive range [low, high].  'low' must be
        less than or equal to 'high'."""
    assert low <= high
    self.__low = low
    self.__high = high
    super().__init__()

  def __contains__(self, val):
    """ Determine whether the specified value is within this range."""
    return val >= self.__low and val <= self.__high

# Unicode character ranges of interest.
KANJI_RANGE = TRange(0x4e00, 0x9fcf)
KANA_RANGE = TRange(0x3000, 0x30ff)
FULLWIDTH_RANGE = TRange(0x0ff00, 0x0ffef)

class T言葉と振り仮名Producer(object):
  """ Instances of this class parse strings of Japanese text into lists
      of T言葉と振り仮名.  Instances must be told how to delimit 言葉 and 振り仮名
      in strings; consequently, clients must provide two delimiting characters,
      such as parentheses or quotation marks, that surround 振り仮名.

      Note that 振り仮名 will only be attached to Chinese characters (漢字).
      振り仮名 delimiters found after non-漢字 characters will be treated as
      part of the 言葉.  For example, if '(' and ')' are the 振り仮名
      delimiters, then

        きょう漢字(かんじ)を勉強する。

      will produce five T言葉と振り仮名 objects:

        1. 言葉：きょう　　　　　振り仮名：<Nothing>
        2. 言葉：漢字　　　　　振り仮名：かんじ
        3. 言葉：を勉強する。　　振り仮名：<Nothing>

      However,

        きょう(きょう)漢字を勉強する。

      will produce just one T言葉と振り仮名 object:

        1. 言葉：きょう(きょう)漢字を勉強する。　　 振り仮名：<Nothing>"""

  def __init__(self, 振り仮名start='[', 振り仮名end=']'):
    """ Construct a new parser using the specified 振り仮名 delimiter characters.
        The characters must be single-character strings."""
    self.__漢字 = False
    self.__振り仮名 = False
    self.__振り仮名start = 振り仮名start
    self.__振り仮名end = 振り仮名end
    self.__results = []
    self.__buffer = io.StringIO()
    self.__buffer_start = self.__buffer.tell()
    super().__init__()

  def __AddResult(self, 言葉, 振り仮名):
    """ Create a new T言葉と振り仮名 object with the specified 言葉 and 振り仮名 and add it to the Results.
        If 振り仮名 is empty, then the new object will be coalesced with the
        last T言葉と振り仮名 if it, too, has empty 振り仮名."""
    if self.__results and not 振り仮名 and not self.__results[-1].振り仮名:
      言葉 = self.__results.pop().言葉 + 言葉
    self.__results.append(T言葉と振り仮名(言葉, 振り仮名))

  def Finish(self):
    """ Tell the parser that parsing is complete.  You should invoke this
        before accessing the parser's results."""
    if self.__漢字:
      if self.__振り仮名:
        self.__AddResult(self.__temp漢字, self.__buffer.getvalue())
        self.__振り仮名 = False
        self.__temp漢字 = None
      else:
        self.__AddResult(self.__buffer.getvalue(), "")
      self.__ResetBuffer()
      self.__漢字 = False
    elif not self.__BufferIsEmpty:
      self.__AddResult(self.__buffer.getvalue(), "")
      self.__ResetBuffer()

  def Process(self, text):
    """ Process the characters in the specified iterable.  The iterable must
        implement __iter__() and each of the iterable's values must be a
        single-character string."""
    for char in text:
      cp = ord(char)
      if cp in KANJI_RANGE:
        # 漢字
        if not self.__漢字:
          self.__漢字 = True
          if not self.__BufferIsEmpty:
            self.__AddResult(self.__buffer.getvalue(), "")
            self.__ResetBuffer()
        self.__buffer.write(char)
      else:
        # ASCII, 仮名, or CJK punctuation
        if not self.__漢字:
          self.__buffer.write(char)
        else:
          if self.__振り仮名:
            if char == self.__振り仮名end:
              self.__AddResult(self.__temp漢字, self.__buffer.getvalue())
              self.__ResetBuffer()
              self.__漢字 = False
              self.__振り仮名 = False
              self.__temp漢字 = None
            else:
              self.__buffer.write(char)
          else:
            if char == self.__振り仮名start:
              self.__振り仮名 = True
              self.__temp漢字 = self.__buffer.getvalue()
              self.__ResetBuffer()
            else:
              self.__漢字 = False
              self.__AddResult(self.__buffer.getvalue(), "")
              self.__ResetBuffer()
              self.__buffer.write(char)

  def ProcessAndReset(self, text):
    """ Invoke Process() for the specified iterable of characters, reset the processor, and return the results.
        This combines Process(), Finish(), and Reset() into one method."""
    try:
      self.Process(text)
      self.Finish()
      results = self.Results
    finally:
      self.Reset()
    return results

  def Reset(self):
    """Reset the parser and empty the Results list."""
    self.__漢字 = False
    self.__振り仮名 = False
    self.__temp漢字 = None
    self.__ResetBuffer()
    self.__results = []

  def __ResetBuffer(self):
    self.__buffer = io.StringIO()

  @property
  def __BufferIsEmpty(self):
    return self.__buffer.tell() == self.__buffer_start

  @property
  def Results(self):
    """ the list of T言葉と振り仮名 that the parser produced
        (Invoke Finish() first!)"""
    return self.__results

def GenerateHTML5Ruby(言葉と振り仮名sequence, buf, kanji_class,
 kanji_onclick_generator, kanji_onmouseover_generator,
 kanji_onmouseout_generator, 振り仮名のクラス, 振り仮名が見える=True):
  """ Write HTML5 ruby-annotated text from the specified iterable of
      T言葉と振り仮名 into the specified buffer.  振り仮名のクラス should be a
      valid CSS class name: It will be the value of each rt tag's
      "class" attribute.  If 振り仮名を見える is True, then the generated
      HTML5 text will ensure that the 振り仮名 is initially visible via
      the "style" tag attribute; otherwise, the generated HTML5 text
      will ensure that the 振り仮名 is hidden."""
  visible = ('" style="visibility:visible;">' if 振り仮名が見える else '" style="visibility:hidden;">')
  rt_start = '<rp class="' + 振り仮名のクラス + visible + ' (</rp><rt class="' + 振り仮名のクラス + visible
  rt_end = '<rp class="' + 振り仮名のクラス + visible + ') </rp></rt></ruby>'

  def Write漢字(字):
    buf.write('<span class=\"')
    buf.write(kanji_class)
    buf.write('" onclick="' + kanji_onclick_generator(字) if kanji_onclick_generator is not None else '')
    buf.write('" onmouseover="' + kanji_onmouseover_generator(字) if kanji_onmouseover_generator is not None else '')
    buf.write('" onmouseout="' + kanji_onmouseout_generator(字) + '">' if kanji_onmouseout_generator is not None else '">')
    buf.write(字)
    buf.write('</span>')

  for ペア in 言葉と振り仮名sequence:
    if ペア.振り仮名:
      buf.write("""<ruby>""")
      for 字 in ペア.言葉:
        assert ord(字) in KANJI_RANGE
        Write漢字(字)
      buf.write(rt_start)
      buf.write(ペア.振り仮名)
      buf.write(rt_end)
    else:
      for 字 in ペア.言葉:
        (Write漢字 if ord(字) in KANJI_RANGE else buf.write)(字)



################################################################################
# Functions for downloading 漢字 stroke order diagrams from remote sources
################################################################################

def WriteDiagramFile(データ, ファイルのパス名):
  """ Write the bytes represented by データ to a new file at the path ファイルのパス名.
      The file must not already exist.  This will delete the file if an IO
      error occurs."""
  assert not os.path.exists(ファイルのパス名)
  try:
    with データ as remote_data:
      with open(ファイルのパス名, "wb") as f:
        f.write(データ.read())
  except Exception as e:
    if os.path.exists(ファイルのパス名):
      os.unlink(ファイルのパス名)
    raise e

def GetJishoDotOrgURL(漢字):
  """ Get a URL string for the specified 漢字's stroke order diagram from jisho.org."""
  assert len(漢字) == 1
  assert ord(漢字) in KANJI_RANGE
  return "http://jisho.org/static/images/stroke_diagrams/" + str(ord(漢字)) + "_frames.png"

def DownloadJishoDotOrgDiagram(漢字, ファイルのパス名, タイムアウト):
  """ Download the stroke order diagram for the specified 漢字 from jisho.org.
      The image will be stored in the path specified by ファイルのパス名.
      The download will timeout after タイムアウト seconds."""
  WriteDiagramFile(urllib.request.urlopen(GetJishoDotOrgURL(漢字), timeout=タイムアウト), ファイルのパス名)

def GetSaigaJPURL(漢字):
  """ Get a URL string for the specified 漢字's stroke order diagram from saiga-jp.com."""
  assert len(漢字) == 1
  assert ord(漢字) in KANJI_RANGE
  return "http://www.saiga-jp.com/dic/img/stroke/" + urllib.parse.quote(漢字).replace('%', '').lower() + ".gif"

def DownloadSaigaJPDiagram(漢字, ファイルのパス名, タイムアウト):
  """ Download the animated stroke order diagram for the specified 漢字 from saiga-jp.com.
      The image will be stored in the path specified by ファイルのパス名.
      The download will timeout after タイムアウト seconds."""
  WriteDiagramFile(urllib.request.urlopen(GetSaigaJPURL(漢字), timeout=タイムアウト), ファイルのパス名)

def GetSLJFAQURL(漢字):
  """ Get a URL string for the specified 漢字's stroke order diagram from sljfaq.org."""
  assert len(漢字) == 1
  assert ord(漢字) in KANJI_RANGE
  return "http://kanji.sljfaq.org/kanjivg/memory.cgi?c=" + hex(ord(漢字))[2:]

def DownloadSLJFAQDiagram(漢字, ファイルのパス名, タイムアウト):
  """ Download the stroke order diagram for the specified 漢字 from kanji.sljfaq.org.
      The image will be stored in the path specified by ファイルのパス名.
      The download will timeout after タイムアウト seconds."""
  WriteDiagramFile(urllib.request.urlopen(GetSLJFAQURL(漢字), timeout=タイムアウト), ファイルのパス名)



################################################################################
# A class for downloading 漢字 stroke order diagrams and managing them on disk
################################################################################

""" This is the start of URL paths for 漢字 stroke order diagrams.  Clients that
    need to access locally-stored stroke order diagrams should access the
    diagrams through this path.  See GetStrokeOrderDiagramURL()."""
StrokeOrderDiagramURLBase = "/images/"

class TStrokeOrderDiagramFSInfo(object):
  """ This class facilitates 漢字 stroke order diagram downloading and management.
      It provides the standard way to parse image diagram filesystem
      configuration files and convenient methods for initiating downloads."""

  """a dictionary mapping stroke order diagram sources to their download handlers and file extensions"""
  RemoteSources = {
    "jisho.org": (DownloadJishoDotOrgDiagram, GetJishoDotOrgURL, "jpg"),
    "saiga-jp.com": (DownloadSaigaJPDiagram, GetSaigaJPURL, "gif"),
    "sljfaq.org": (DownloadSLJFAQDiagram, GetSLJFAQURL, "png")
   }

  def __init__(self, 設定ファイルのパス):
    """ Construct a 漢字 stroke order diagram downloader that uses the specified configuration file's settings."""
    # Flags and default settings
    self.__設定ファイルのディレクトリ = os.path.abspath(os.path.dirname(設定ファイルのパス))
    self.__タイムアウト = None
    self.__ファイル = []
    self.__enabled_sources = []
    self.__image_directory = None

    # Parse the configuration file.
    def ProcessSettings(config, パス名, PrintErrorAndExit):
      # Parse the configuration file.
      def HandleSource(source, unused):
        if source not in self.RemoteSources:
          PrintErrorAndExit("This image source is not known: " + source)
        self.__enabled_sources.append(source)
      ForEachConfigurationSetting(config, 'enabled-sources', HandleSource)
      ForEachConfigurationSetting(config, 'files',
        lambda ファイル, _: self.__ファイル.append(EnsureAbsolutePath(ファイル, self.__設定ファイルのディレクトリ))
       )
      section = config['general'] if 'general' in config else {}
      if 'timeout' in section:
        try:
          self.__タイムアウト = int(section['timeout'])
        except ValueError:
          PrintErrorAndExit("timeout is not a number: " + section['timeout'])
      self.__image_directory = section.get('image-directory', None)

    ツールの設定ファイルを分析する(設定ファイルのパス, ProcessSettings)

    # Validate settings.
    if not self.__enabled_sources and (self.__設定ファイル or self.__ログファイル):
      sys.stderr.write("すみません、you must enable at least one source in the 設定ファイル.")
      sys.exit(2)
    self.__image_directory = os.path.join(self.__設定ファイルのディレクトリ, self.__image_directory)
    if not os.path.isdir(self.__image_directory):
      sys.stderr.write("This path does not refer to a directory: " + image_directory + "\n")
      sys.exit(3)
    if self.__タイムアウト is None:
      self.__タイムアウト = 30
    super().__init__()

  def ConstructStrokeOrderDiagramPath(self, 字, source):
    """ Get a string representing the path to the stroke order diagram for the specified 漢字 from the specified source.
        The file might not exist."""
    assert source in self.EnabledSources
    return os.path.join(self.ImageDirectory, source, 字 + os.extsep + self.RemoteSources[source][2])

  def Download(self, 漢字, source):
    """ Download the stroke order diagrams for the 漢字 characters in the specified string from the specified source, which must be one of the EnabledSources."""
    assert source in self.EnabledSources
    source_dir = os.path.join(self.ImageDirectory, source)
    if not os.path.exists(source_dir):
      os.mkdir(source_dir)
    for 字 in 漢字:
      if ord(字) in KANJI_RANGE:
        self.RemoteSources[source][0](字, self.ConstructStrokeOrderDiagramPath(字, source), self.タイムアウト)

  def Downloaded(self, 字, source):
    """ Determine whether the specified 漢字's stroke order diagram has already been downloaded from the specified source."""
    return self.GetStrokeOrderDiagramPath(字, source) is not False

  def GetLocalStrokeOrderDiagramPaths(self, 字):
    """ Get a list of paths to locally-stored stroke order diagrams for the specified 漢字 character."""
    assert len(字) == 1
    assert ord(字) in KANJI_RANGE
    local_sources = set(self.GetStrokeOrderDiagramSources()) ^ set(self.EnabledSources)
    字 = 字 + os.extsep
    パス名 = []
    for source in local_sources:
      パス = self.GetStrokeOrderDiagramPath(字, source)
      if パス is not False:
        パス名.append(パス)
    return パス名

  def GetStrokeOrderDiagramPath(self, 字, source):
    """ Get the path to a stroke order diagram from the specified source for the specified 漢字.
        This function returns the path to the stroke order diagram if it is found.
        Otherwise, this function returns False."""
    assert len(字) == 1
    assert ord(字) in KANJI_RANGE
    assert source in self.EnabledSources
    パス = self.ConstructStrokeOrderDiagramPath(字, source)
    return パス if os.path.isfile(パス) else False

  def GetStrokeOrderDiagramSources(self):
    """ Get a list of sources from which 漢字 stroke order diagrams were downloaded.
        'image_directory' must be a path to a root image directory that was
        previously managed by the download-kanji-images.py tool."""
    sources = os.listdir(self.ImageDirectory)
    for source in sources:
      if not os.path.isdir(os.path.join(self.ImageDirectory, source)):
        sys.stderr.write("image directory is corrupted: " + self.ImageDirectory + ": " + source + " is not a directory\n")
        sys.exit(3)
      if source not in self.RemoteSources:
        sys.stderr.write("image directory is corrupted: " + self.ImageDirectory + ": " + source + " is not a recognized remote source\n")
        sys.exit(3)
    return sources

  def GetStrokeOrderDiagramURL(self, 字, source):
    """ Get a URL to the stroke order diagram from the specified source for the specified 漢字.
        This function returns a string representing a URL.  The URL will be the
        contatenation of the string specified by the global variable
        StrokeOrderDiagramURLBase, the source (URL quoted, UTF-8 encoding),
        a "/", and the string representation of the integral value of 字
        (UTF-8 encoding) if there is a local stroke order diagram for 字.
        If no local stroke order diagram exists for the specified
        字 from the specified source, then the returned URL will refer to a
        remote stroke order diagram from the specified source."""
    assert len(字) == 1
    assert ord(字) in KANJI_RANGE
    assert source in self.EnabledSources
    パス = self.GetStrokeOrderDiagramPath(字, source)
    return (
      self.RemoteSources[source][1](字)
       if パス is False
       else StrokeOrderDiagramURLBase + urllib.parse.quote(source) + "/" + str(ord(字))
     )

  def ServeStrokeOrderDiagram(self, 字, source):
    """ Serve the locally-stored stroke order diagram for the specified 漢字.
        字 must be the Unicode code point of a 漢字 expressed as an integer.
        This function must be invoked while handling a GET request.
        If all of the parameters are valid, then this will serve the stroke
        order diagram for the specified 漢字: The return value will be the
        value returned by Bottle's static_file() function.  If 'source'
        is None but 字 is valid, then this function will return the empty
        string.  Otherwise, an HTTP error will be generated."""
    try:
      字 = chr(int(字))
    except Exception as e:
      abort(400, "invalid 漢字 encoding")
    if len(字) != 1:
      abort(400, "not a single-character 漢字")
    if ord(字) not in KANJI_RANGE:
      abort(400, "not 漢字")
    data = ""
    if source is not None and source in self.EnabledSources:
      local_path = self.GetStrokeOrderDiagramPath(字, source)
      if local_path is not False:
        data = static_file(os.path.basename(local_path), os.path.dirname(local_path))
    return data

  @property
  def 設定ファイルのディレクトリ(self):
    return self.__設定ファイルのディレクトリ

  @property
  def タイムアウト(self):
    return self.__タイムアウト

  @property
  def ファイル(self):
    return self.__ファイル

  @property
  def EnabledSources(self):
    return self.__enabled_sources

  @property
  def ImageDirectory(self):
    return self.__image_directory



################################################################################
# Code designed specifically for organizing and displaying flashcards
################################################################################

class TEmptyDeckError(Exception):
  """TCardDeck raises this exception whenever clients try to draw cards when none are left."""
  pass

class TLeitnerBucket(object):
  """ Instances of this class represent Leitner buckets.  Each Leitner bucket
      tracks the number of flashcards associated with it and records the
      delay (in seconds) that should be added to each card that moves to
      the bucket."""

  def __init__(self, delay_in_secs):
    """ Construct a new Leitner bucket with no associated cards.
        'delay_in_secs' is the number of seconds that should be to incoming
        cards' due dates."""
    assert delay_in_secs >= 0
    self.__delay_in_secs = delay_in_secs
    self.Reset()
    super().__init__()

  def AddStub(self, stub, date_touched, now):
    """ Increment the total card count by one.  Also increment the due card
        count if necessary.  'date_touched' must be a timestamp representing
        the last time the card represented by the stub was touched.
        'now' must be a timestamp representing the present."""
    self.__num_cards += 1
    stub.SetDueDate(date_touched, self.DelayInSeconds)
    if stub.IsDue(now):
      self.__num_due_cards += 1

  def RemoveStub(self, stub, now):
    """ Decrement the total card count.  Also decrement the due card count
        if the card associated with the specified stub is due.  'now' must be
        a timestamp representing the present."""
    assert self.__num_cards > 0
    self.__num_cards -= 1
    if stub.IsDue(now):
      assert self.__num_due_cards > 0
      self.__num_due_cards -= 1

  def Reset(self):
    """ Reset the card counts."""
    self.__num_cards = 0
    self.__num_due_cards = 0

  @property
  def CardCount(self):
    """the number of cards in this bucket"""
    return self.__num_cards

  @property
  def DelayInSeconds(self):
    """the delay in seconds added to cards' due dates when they are added to this bucket"""
    return self.__delay_in_secs

  @property
  def DueCardCount(self):
    """the number of cards in this bucket that are due"""
    return self.__num_due_cards

class TFlashcardStub(object):
  """ Instances of this class contain flashcard metadata.  The deck construction
      algorithms construct stubs instead of full-blown flashcards while parsing
      stats logs to avoid hogging memory."""

  _NEVER_TOUCHED = float("-inf")

  def __init__(self, card_hash):
    """ Construct a flashcard stub with the specified hash.  The stub will
        represent a flashcard that is due immediately."""
    self.__hash = card_hash
    self.__bucket_index = 0
    self.__due_date = self._NEVER_TOUCHED
    super().__init__()

  def IsDue(self, now):
    """ Determine whether the flashcard associated with this stub is due at the specified time."""
    return self.DueDate <= now

  def SetBucketIndex(self, index):
    """ Set this stub's Leitner bucket index."""
    self.__bucket_index = index

  def SetDueDate(self, now, delay_in_secs):
    """ Set this stub's due date to the sum of the specified timestamp and delay in seconds."""
    self.__due_date = now + delay_in_secs

  @property
  def BucketIndex(self):
    """the index of the TLeitnerBucket associated with this stub"""
    return self.__bucket_index

  @property
  def DueDate(self):
    """the associated flashcard's due date as a timestamp"""
    return self.__due_date

  @property
  def Hash(self):
    """the associated flashcard's hash as a hex string"""
    return self.__hash

  @property
  def IsNewCard(self):
    """True if the card was never touched, False otherwise"""
    return self.__due_date == self._NEVER_TOUCHED

class TFlashcard(object):
  """ This is the base class for flashcards.  Subclasses should
      override __bytes__()."""

  def __init__(self):
    """何もしません。"""
    super().__init__()

  @property
  def Hash(self):
    """the hash digest of the flashcard as a hex string"""
    return hashlib.sha1(bytes(self)).hexdigest()

class TCardDeckStatistics(object):
  """Instances of this class record information about decks of cards and
     how well users perform with the decks."""

  def __init__(self, cards):
    """ Construct a new stats object that records information about the specified collection of cards.
        NOTE: 'cards' must have a __len__() method."""
    self.__cards = set()                  # the set of all cards that the user has seen
    self.__num_cards = len(cards)         # total number of cards
    self.__num_passed_on_first_try = 0    # number passed on first attempt
    self.__num_failed_on_first_try = 0    # number failed on first attempt
    self.__num_left = self.__num_cards    # number of cards left to see (including failures)
    self.__num_attempts = 0               # total number of cards shown
    self.__retry_map = {}                 # maps retried cards to their retry counts
    super().__init__()

  def CardFailed(self, card):
    """Note that the user failed to correctly answer the specified card."""
    self.__num_attempts += 1
    if card not in self.__retry_map:
      self.__num_failed_on_first_try += 1
      self.__cards.add(card)
    self.__retry_map[card] = self.__retry_map.get(card, 0) + 1

  def CardPassed(self, card, write_to_log):
    """ Note that the user successfully answered the specified card.
        Additionally, the user's performance with the card will be recorded
        via the specified function.  A card's performance record has
        the following fields (in order):

          1. the current timestamp as returned by time.time();
          2. the SHA-1 hash of the byte representation of the card (that is,
             the SHA-1 hash of the result of constructing a bytes object from
             the card); and
          3. the number of times the user had to retry the card before he
             successfully answered it.

        write_to_log should take a single tuple parameter containing these
        fields.  (Ideally, write_to_log should not need to know how many
        fields each record contains.)  If write_to_log is None, then no
        performance data will be recorded."""
    self.__num_attempts += 1
    if card not in self.__retry_map:
      self.__num_passed_on_first_try += 1
    self.__cards.add(card)
    self.__num_left -= 1
    if write_to_log is not None:
      write_to_log((time.time(), card.Hash, self.__retry_map.get(card, 0)))

  @property
  def CardsSeen(self):
    """the cards that the user has tried to answer"""
    return frozenset(self.__cards)

  @property
  def NumAttempts(self):
    """the number of cards seen, including retries"""
    return self.__num_attempts

  @property
  def NumCards(self):
    """the number of cards in the deck"""
    return self.__num_cards

  @property
  def NumCardsLeft(self):
    """the number of cards that have not been passed"""
    return self.__num_left

  @property
  def NumFailedOnFirstTry(self):
    """the number of cards that the user failed the first time he saw them"""
    return self.__num_failed_on_first_try

  @property
  def NumPassedOnFirstTry(self):
    """the number of cards that the user passed the first time he saw them"""
    return self.__num_passed_on_first_try

  @property
  def RetryNumbers(self):
    """a map of failed cards to the number of times the user has retried them"""
    return self.__retry_map

class TCardDeck(object):
  """ Instances of this class represent decks of flashcards.  The cards may
      be of any type extending TFlashcard.

      Clients typically use this class as follows:

        1. Construct a deck of cards.
        2. If there are any cards left (HasCards), then draw a card (GetCard());
           otherwise, the test is over.
        3. If the user answers the card correctly, then invoke MarkSucceeded();
           otherwise, invoke MarkFailed().
        4. Go to step (2).

      Decks automatically recycle failed cards."""

  def __init__(self, cards):
    """ Construct a deck from the specified sequence of flashcards."""
    self.__cards = list(cards)
    self.__failed_cards = []
    self.__current_card = None
    self.__current_card_marked = False
    self.__statistics = TCardDeckStatistics(self.__cards)
    super().__init__()

  def GetCard(self):
    """ Get the next card from the top of the deck.  The current card (that
        is, the last card that was drawn), if any, must have been marked
        beforehand via MarkedFailed() or MarkSucceeded().  This method
        raises TEmptyDeckError if the deck is empty."""
    assert self.__current_card is None or self.__current_card_marked
    if not self.__cards:
      if not self.__failed_cards:
        raise TEmptyDeckError("no cards left")
      random.shuffle(self.__failed_cards)
      self.__cards = self.__failed_cards
      self.__failed_cards = []
    self.__current_card = self.__cards.pop()
    self.__current_card_marked = False
    return self.CurrentCard

  def MarkFailed(self):
    """ Mark the current card (that is, the card that was last drawn) as
        "failed" (that is, the user did not answer it correctly or in time).
        This method will put the card back into the deck."""
    assert self.__current_card is not None
    assert not self.__current_card_marked
    self.__failed_cards.append(self.__current_card)
    self.__current_card_marked = True
    self.Statistics.CardFailed(self.__current_card)

  def MarkSucceeded(self, write_to_log):
    """ Mark the current card (that is, the card that was last drawn) as
        "succeeded" (that is, the user answered it correctly).  This method
        will remove the card from the deck.  Additionally, it will record
        the user's performance with the card via the specified unary
        function; see TCardDeckStatistics.CardPassed() for more information
        about this parameter."""
    assert self.__current_card is not None
    assert not self.__current_card_marked
    self.__current_card_marked = True
    self.Statistics.CardPassed(self.__current_card, write_to_log)

  @property
  def CurrentCard(self):
    """the current card (that is, the card that was last drawn from the deck)"""
    return self.__current_card

  @property
  def HasCards(self):
    """True if the deck is not empty, False otherwise"""
    return bool(self.__cards) or bool(self.__failed_cards)

  @property
  def Statistics(self):
    """the TCardDeckStatistics object associated with this deck"""
    return self.__statistics

class TInvalidFlashcardStatsRecord(Exception):
  """ ApplyStatsLogToFlashcards() raises this exception when it processes an invalid log record."""

  def __init__(self, line, reason):
    """ Construct an exception with the specified log file line number and reason for the exception."""
    self.__line = line
    self.__reason = reason
    super().__init__(line, reason)

  def __str__(self):
    return str(self.Line) + ": " + str(self.Reason)

  @property
  def Line(self):
    """the log file line of the record that generated this exception"""
    return self.__line

  @property
  def Reason(self):
    """the reason why this exception was generated (should be a string)"""
    return self.__reason

def CreateFlashcardStubMap(flashcard_parser_cb, buckets, now):
  """ Parse flashcards and construct a dictionary mapping flashcard hashes to TFlashcardStubs.
      "Flashcards" are objects that have Hash() functions that return
      hexadecimal hash codes as strings.

      This method expects these parameters:

        flashcard_parser_cb :: (TFlashcard -> None) -> None
          This function constructs a flashcard file parser that will invoke
          the specified callback for each flashcard it parses, then executes
          the parser completely.
        buckets :: [TLeitnerBucket]
          a list of TLeitnerBuckets
        now :: numeric
          a timestamp representing the present"""
  hashes_to_stubs = {}
  def Handleカード(カード):
    stub = TFlashcardStub(カード.Hash)
    hashes_to_stubs[stub.Hash] = stub
    buckets[0].AddStub(stub, TFlashcardStub._NEVER_TOUCHED, now)
  flashcard_parser_cb(Handleカード)
  return hashes_to_stubs

def ApplyStatsToStubMap(log_parser_cb, hashes_to_stubs, buckets, now):
  """ Parse flashcard performance log entries and adjust the TFlashcardStubs in the specified stub map accordingly.
      "Flashcards" are objects that have Hash() functions that return
      hexadecimal hash codes as strings.

      This method expects these parameters:

        log_parser_cb :: (tuple -> None) -> None
          This function constructs a performance log parser that will invoke
          the specified callback for each log record (tuple) it parses, then
          executes the parser completely.
        hashes_to_stubs :: dict<str,TFlashcardStub>
          a dictionary mapping flashcard hash hex strings to flashcard stubs;
          see CreateFlashcardStubMap()
        buckets :: [TLeitnerBucket]
          a list of TLeitnerBuckets
        now :: numeric
          a timestamp representing the present

      This function returns a pair containing the number of new cards and
      the number of cards that are due for review.  It also modifies the
      TFlashcardStubs within 'hashes_to_stubs' and the TLeitnerBuckets
      within 'buckets'.

      This function raises TInvalidFlashcardStatsRecord if it processes an
      invalid flashcard stats record."""
  num_new_cards = len(hashes_to_stubs)
  max_leitner_bucket = len(buckets) - 1
  def HandleLogEntry(record):
    nonlocal num_new_cards
    if len(record) != 3:
      raise TInvalidFlashcardStatsRecord(parser.Line, "record does not have three fields")
    stub = hashes_to_stubs.get(record[1], None)
    if stub is not None:
      try:
        date_touched = float(record[0])
      except ValueError:
        raise TInvalidFlashcardStatsRecord(parser.Line, "timestamp field is not a float")
      try:
        num_retries = int(record[2])
      except ValueError:
        raise TInvalidFlashcardStatsRecord(parser.Line, "num_retries field is not an integer")
      old_bucket = stub.BucketIndex
      new_bucket = (
        old_bucket + (1 if old_bucket < max_leitner_bucket else 0)
         if num_retries == 0
         else 0
       )
      if stub.IsNewCard:
        num_new_cards -= 1
      buckets[old_bucket].RemoveStub(stub, now)
      buckets[new_bucket].AddStub(stub, date_touched, now)
      stub.SetBucketIndex(new_bucket)
  log_parser_cb(HandleLogEntry)
  return (num_new_cards, sum(bucket.DueCardCount for bucket in buckets))

class TCardDeckFactory(object):
  """ Instances of this class construct flashcard decks (TCardDeck objects).
      The cards are selected randomly from a flashcard file (usually a
      configuration file) after the pool of cards is decorated with performance
      data from a stats log file.

      This class relies heavily on CreateFlashcardStubMap() and
      ApplyStatsToStubMap()."""

  def __init__(self, flashcard_parser_cb, log_parser_cb, buckets):
    """ Construct a new factory.  This constructor expects three arguments:

          flashcard_parser_cb :: (TFlashcard -> None) -> None
            This function constructs a flashcard file parser that will invoke
            the specified callback for each flashcard it parses, then executes
            the parser completely.
          log_parser_cb :: (tuple -> None) -> None
            This function constructs a performance log parser that will invoke
            the specified callback for each log record (tuple) it parses, then
            executes the parser completely.
          buckets :: [TLeitnerBuckets]
            self-explanatory"""
    self.__flashcard_parser_cb = flashcard_parser_cb
    self.__log_parser_cb = log_parser_cb
    self.__buckets = buckets
    self.__now = time.time()
    self.Refresh()
    super().__init__()

  def ConstructDeck(self, size, num_new_cards):
    """ Get an iterable collection of randomly-sampled flashcards.

        If no cards are due, then this will return an iterable collection of
        up to 'size' cards that are due soonest; otherwise, this will return
        an iterable collection of all due cards.

        New cards are always due.  Exactly 'num_new_cards' will be returned in
        the iterable collection if possible.

    """
    # Adjust the parameters.
    if size <= 0:
      raise RuntimeError("size must be positive")
    if num_new_cards < 0:
      raise RuntimeError("num_new_cards must be positive or zero")
    num_new_cards = min(num_new_cards, self.__num_new_cards)
    if self.__num_due_cards == 0:
      size = min(size, self.__card_count)
      selection = []
      def OfferCard(card):
        heap_key = self.__now - self.__hashes_to_stubs[card.Hash].DueDate
        if len(selection) < size:
          heapq.heappush(selection, (heap_key, random.random(), id(card), card))
        elif heap_key >= selection[0][0]:
          heapq.heapreplace(selection, (heap_key, random.random(), id(card), card))
      def YieldCards():
        for _, _, _, card in selection:
          yield card
    else:
      num_due_cards = max(min(size, self.__num_due_cards) - num_new_cards, 0)
      new_card_selector = TRandomSelector(num_new_cards)
      due_card_selector = TRandomSelector(num_due_cards)
      def OfferCard(card):
        stub = self.__hashes_to_stubs[card.Hash]
        if stub.IsNewCard and num_new_cards != 0:
          new_card_selector.Add(card)
        elif stub.IsDue(self.__now) and num_due_cards != 0:
          due_card_selector.Add(card)
      def YieldCards():
        return itertools.chain(new_card_selector, due_card_selector)

    # Pass through the flashcard file and randomly pick cards according
    # to the parameters.
    self.__flashcard_parser_cb(OfferCard)

    # Return the combined, shuffled results.
    combined_results = TRandomSelector(self.__card_count)
    combined_results.ConsumeSequence(YieldCards())
    return combined_results

  def Refresh(self):
    """ Parse the flashcards and their performance records again.  This
        will reset the associated Leitner buckets."""
    # First, reset the Leitner buckets' card counts and construct a map of
    # flashcard hashes to flashcard stubs.
    for bucket in self.__buckets:
      bucket.Reset()
    self.__hashes_to_stubs = CreateFlashcardStubMap(
      self.__flashcard_parser_cb,
      self.__buckets,
      self.__now
     )

    # Second, apply the stats file to the stubs.
    # This will change the Leitner buckets.
    def LogParserCrank(log_record_handler):
      try:
        self.__log_parser_cb(log_record_handler)
      except IOError as e:
        if e.errno != errno.ENOENT:
          raise e
    self.__num_new_cards, self.__num_due_cards = ApplyStatsToStubMap(
      self.__log_parser_cb,
      self.__hashes_to_stubs,
      self.__buckets,
      self.__now
     )
    assert self.__num_new_cards <= self.__num_due_cards # New cards are always due.
    self.__card_count = len(self.__hashes_to_stubs)

  def RenderConfigPage(self,
    title,
    session_token,
    post_handler_url,
    default_time=('', '', ''),
    default_max_deck_size='',
    default_max_new_cards='',
    image_settings=None
   ):
    """ Generate an HTML page that displays a deck configuration screen.
        This method has the following parameters:

          title :: str
            the generated web page's title
          session_token :: int | str
            the current session's token
          post_handler_url :: str
            the absolute or relative URL of the script that will handle POST
            results sent from the client
          default_time :: 3-tuple<str>
            the initial values of the hours, minutes, and seconds fields
            of the configuration form, respectively
          default_max_deck_size :: str
            the initial value of the input field for the maximum deck size
          default_max_new_cards :: str
            the initial value of the input field for the maximum number of
            new cards
          image_settings :: TStrokeOrderDiagramFSInfo
            the stroke order diagram image manager for 漢字 stroke order
            diagram sources or None if the user should not be allowed to
            select a remote source for stroke order diagrams"""
    fieldsets = []
    template_contents = {
      'title': title,
      'session_token': session_token,
      'handler_url': post_handler_url,
      'num_cards_due': self.NumberOfDueCards,
      'num_new_cards': self.NumberOfNewCards,
      'num_cards_total': self.NumberOfCards,
      'buckets': self.Buckets,
      'time_hours': default_time[0],
      'time_minutes': default_time[1],
      'time_seconds': default_time[2],
      'max_deck_size': default_max_deck_size,
      'max_new_cards': default_max_new_cards
     }

    if image_settings is not None:
      assert isinstance(image_settings, TStrokeOrderDiagramFSInfo)
      fieldsets.append({
        'legend': "漢字 Stroke Order Diagram Source",
        'contents': JinjaEnvironment.get_template('radiobuttonset.html').render({
          'radio_set_name': "漢字source",
          'prefix': "source",
          'remote_sources': list(image_settings.EnabledSources)
         })
       })

    template_contents['fieldsets'] = fieldsets
    return JinjaEnvironment.get_template('deckconfig.html').render(template_contents)

  @property
  def Buckets(self):
    """a list of Leitner buckets"""
    return list(self.__buckets)

  @property
  def NumberOfCards(self):
    """the total number of flashcards in the flashcard pool"""
    return self.__card_count

  @property
  def NumberOfDueCards(self):
    """the number of cards that are due for review"""
    return self.__num_due_cards

  @property
  def NumberOfNewCards(self):
    """the number of cards that have not been used in quizzes"""
    return self.__num_new_cards



################################################################################
# TFlashcard subclasses
################################################################################

class TSourcedフラッシュカード(TFlashcard):
  """ Instances of this class are Leitner flashcards with three parts: a front,
      a back, and the card's source."""

  class TFormatError(Exception):
    """ ParseSourceFile() raises this exception whenever a flashcard row is formatted incorrectly."""
    pass

  @staticmethod
  def ParseSourceFile(source_file, flashcard_cb):
    """ Parse the specified configuration file describing sources and invoke the specified unary callback for each parsed flashcard."""
    sources_and_paths = []
    settings = ConstructConfigurationParser()
    settings.read(source_file)
    source_file_dir = os.path.dirname(source_file)
    def ForEachSource(source_name, source_path):
      with open(EnsureAbsolutePath(source_path, source_file_dir), 'r') as sf:
        reader = ConstructLogParser(sf)
        for row in reader:
          if len(row) != 2:
            raise TSourcedフラッシュカード.TFormatError("illegal number of fields: " + str(len(row)))
          flashcard_cb(TSourcedフラッシュカード(row[0], row[1], source_name))
    ForEachConfigurationSetting(settings, 'sources', ForEachSource)

  def Render(self,
    title,
    post_handler_url,
    session_token,
    前cb=lambda 前: 前,
    後ろcb=lambda 後ろ: 後ろ,
    source_cb=lambda source: source,
    enable_ruby=True,
    enable_kanji_highlighting=True,
    enable_furigana_display=True,
    image_settings=None,
    image_source=None,
    timeout_secs=0,
    deck_stats=None
   ):
    """ Generate an HTML page that displays this flashcard.  This method has
        the following parameters:

          title :: str
            the generated web page's title
          post_handler_url :: str
            the absolute or relative URL of the script that will handle POST
            results sent from the client
          session_token :: int | str
            the current session's token
          前cb :: str => str
            a function that transforms the 前 content into the text that
            will be rendered as the "front" of the flashcard
          後ろcb :: str => str
            a function that transforms the 後ろ content into the text that
            will be rendered as the "back" of the flashcard
          source_cb :: str => str
            a function that transforms the Source content into the text that
            will be rendered as the flashcard's source
          enable_ruby :: boolean
            True if 振り仮名 in the strings returned by 前cb, 後ろcb, and source_cb
            should be parsed and placed inside <ruby> tags, False otherwise
          enable_kanji_highlighting :: boolean
            True if 漢字 in the strings returned by 前cb, 後ろcb, and source_cb
            should be highlighted when the user moves his mouse over them,
            False otherwise (True automatically sets enable_ruby)
          enable_furigana_display :: boolean
            True if the user should be given the option to enable and disable
            振り仮名 in the strings returned by 前cb, 後ろcb, and source_cb,
            False otherwise (True automatically sets enable_ruby)
          image_settings :: TStrokeOrderDiagramFSInfo
            the stroke order diagram image manager for 漢字 stroke order
            diagrams or None if 漢字 stroke order diagrams shouldn't be displayed
            (non-None values automatically set enable_ruby if image_source is
            also non-None)
          image_source :: str
            an enabled remote source for 漢字 stroke order diagrams or None
            if 漢字 stroke order diagrams shouldn't be displayed (non-None
            values automatically set enable_ruby if image_settings is
            also non-None)
          timeout_secs :: int
            the number of seconds remaining in the quiz; zero or negative if
            there is no timeout
          deck_stats :: TCardDeckStatistics
            the current card deck's statistics or None if statistics shouldn't
            be displayed"""
    前 = 前cb(self.前)
    後ろ = 後ろcb(self.後ろ)
    source = source_cb(self.Source)
    kanji_sods_enabled = image_settings is not None and image_source in image_settings.EnabledSources
    bottom_content = ""
    selectors = []
    css = []
    js = []

    template_contents = {
      'title': title,
      'handler_url': post_handler_url,
      'session_token': session_token,
      'rts': timeout_secs,
      'show_stats': deck_stats is not None
     }

    if deck_stats is not None:
      assert isinstance(deck_stats, TCardDeckStatistics)
      template_contents.update({
        'num_cards_passed': deck_stats.NumPassedOnFirstTry,
        'num_cards_failed': deck_stats.NumFailedOnFirstTry,
        'num_cards_seen': deck_stats.NumAttempts,
        'num_cards_left': deck_stats.NumCardsLeft,
        'num_cards_total': deck_stats.NumCards
       })

    if kanji_sods_enabled:
      enable_ruby = True
      漢字 = set(字 for 字 in 前 + 後ろ + source if ord(字) in KANJI_RANGE)
      bottom_content = "".join(
        '<img name="漢字diagram' + 字 + '" style="display: none" alt="漢字 Diagram" src="' +
         image_settings.GetStrokeOrderDiagramURL(字, image_source) + '" />' for 字 in 漢字
       )
      js.append("/static/kanjisod.js")
      selectors.append('<input type="button" name="show_kanji" value="漢字の書き方を見せて" onclick="enableKanjiView()"/>')

    if enable_furigana_display:
      enable_ruby = True
      js.append("/static/furigana.js")
      selectors.append("""<input type="button" name="振り仮名を見せて" value="振り仮名を見せて" onclick="toggle_visibility('furigana')"/>""")

    if enable_kanji_highlighting:
      enable_ruby = True

    if enable_ruby:
      def GenerateDictionaryJS(字):
        quoted = urllib.parse.quote(字)
        return """window.open('http://jisho.org/kanji/details/""" + quoted + """', '""" + quoted + """')"""
      def GenerateRuby(言葉と振り仮名):
        buf = io.StringIO()
        GenerateHTML5Ruby(言葉と振り仮名, buf,
         "kanji" if enable_kanji_highlighting else "nhlkanji",
         GenerateDictionaryJS,
         (lambda 字: "showKanjiImage('" + 字 + "')") if kanji_sods_enabled else None,
         (lambda 字: "hideKanjiImage('" + 字 + "')") if kanji_sods_enabled else None,
         "furigana", False)
        return buf.getvalue()
      producer = T言葉と振り仮名Producer()
      前 = GenerateRuby(producer.ProcessAndReset(前))
      後ろ = GenerateRuby(producer.ProcessAndReset(後ろ))
      source = GenerateRuby(producer.ProcessAndReset(source))

    template_contents['front_content'] = 前
    template_contents['back_content'] = 後ろ
    template_contents['source_content'] = source
    template_contents['bottom_content'] = bottom_content
    template_contents['css'] = css
    template_contents['js'] = js
    if selectors:
      selectors = ["<form>"] + selectors + ["</form>"]
    template_contents['selectors_content'] = ''.join(selectors)
    return JinjaEnvironment.get_template('sourcedflashcard.html').render(template_contents)

  def __init__(self, 前, 後ろ, source):
    """ Construct a new flashcard."""
    self.__前 = 前
    self.__後ろ = 後ろ
    self.__source = source
    super().__init__()

  def __bytes__(self):
    return bytes(self.前, encoding="UTF-8") + bytes(self.後ろ, encoding="UTF-8") + bytes(self.Source, encoding="UTF-8")

  @property
  def 後ろ(self):
    """the back"""
    return self.__後ろ

  @property
  def 前(self):
    """the front"""
    return self.__前

  @property
  def Source(self):
    """the card's source"""
    return self.__source




################################################################################
# Common tool functions
################################################################################

def ツールの設定ファイルを分析する(パス名, ハンドラ):
  """ Parse the configuration file whose path is パス名.  This function expects
      the following parameters:

        パス名 :: str
        This is a path to a configuration file.
      ハンドラ :: (configparser.ConfigParser, str, (str, int) => None) => None
        This specifies the handler that will process the configuration file's
        settings as stored in the specified parser object.  The handler's second
        parameter is the resolved absolute path equivalent to パス名.  The
        handler's third parameter is an error function: It prints its first
        argument as an error message and terminates the program with the
        specified numeric error code, which defaults to 2.

      This function will handle several common errors related to configuration
      file parsing, such as パス名 pointing to something that is not a file.

      """
  # Ensure that the provided configuration file is a readable file.
  if not os.path.isfile(パス名):
    sys.stderr.write("すみません、" + パス名 + "はファイルじゃありません。外のパス名を使って下さい。\n")
    sys.exit(2)
  if not os.access(パス名, os.R_OK):
    sys.stderr.write("すみません、" + パス名 + "を開けて読めません。\n")
    sys.exit(2)

  # Parse the configuration file.
  parser = ConstructConfigurationParser()
  try:
    parser.read(パス名)
  except configparser.Error as e:
    sys.stderr.write("すみません、その設定ファイルは駄目です。\n")
    sys.stderr.write(str(e) + "\n")
    sys.exit(2)
  except Exception as e:
    sys.stderr.write("unexpected error while parsing the configuration file " + パス名 + ": " + str(e) + "\n")
    sys.exit(2)
  パス名 = os.path.abspath(パス名)

  # Process the configuration file's settings.
  def PrintErrorAndExit(message, error_code=2):
    sys.stderr.write("すみません、その設定ファイルは駄目です。" + message + "\n")
    sys.exit(error_code)
  ハンドラ(parser, パス名, PrintErrorAndExit)

@get("/static/<filename>")
def ServeStaticContent(filename):
  return static_file(filename, TemplateDirectory)



