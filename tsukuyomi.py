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
import hashlib
import heapq
import io
import os
import os.path
import random
import sys
import time
import urllib.parse

if __name__ == "__main__":
  sys.path = [os.path.realpath(__file__)] + sys.path

from bottle import *



################################################################################
# Miscellaneous Functions
################################################################################

def EnsureAbsolutePath(path, base):
  """ Convert a path into an absolute path if it is not one already.
      If 'path' is absolute, then this function returns it untouched;
      otherwise, it joins it to 'base'.  'base' must be an absolute path."""
  assert os.path.isabs(base)
  return path if os.path.isabs(path) else os.path.join(base, path)



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
# Configuration file data structures and algorithms
################################################################################

class TSection(object):
  """ Instances of this class represent sections within configuration files.
      As explained in README.md, configuration file sections are like inner
      nodes within N-ary trees.  Each section may contain settings (strings)
      or associated (child) sections.  The only restriction is that a section's
      associated sections cannot not share the same name."""

  def __init__(self, name):
    """ Construct an empty TSection with the specified name string."""
    self.__name = name
    self.__children = []      # settings and sections in order
    self.__sections = collections.OrderedDict()
    self.__settings = []
    super().__init__()

  def AddSection(self, section):
    """ Associate the specified TSection with this section.  This raises
        KeyError if there is already an associated section with the specified
        TSection's name."""
    assert isinstance(section, TSection)
    assert section is not self
    if self.__sections.setdefault(section.Name, section) is not section:
      raise KeyError("duplicate section name: " + section.Name)
    self.__children.append(section)

  def AddSetting(self, setting):
    """Append the specified setting string to this section."""
    self.__settings.append(setting)
    self.__children.append(setting)

  def GetSection(self, name):
    """ Get the associated section with the specified name.  This raises
        KeyError if there is no such associated section."""
    return self.__sections[name]

  def HasSection(self, name):
    """ Determine whether there is an associated section with the specified name."""
    return name in self.__sections

  def YieldSections(self):
    """Get a generator that yields all of this section's sections in order."""
    for name in reversed(self.__sections):
      yield self.__sections[name]

  def YieldSectionsReversed(self):
    """Get a generator that yields all of this section's sections in reverse order."""
    for section in self.__sections.values():
      yield section

  @property
  def Children(self):
    """a list of the section's settings and associated sections (read-only)"""
    return self.__children

  @property
  def HasChildren(self):
    """True if this section has settings or associated sections, False otherwise"""
    return bool(self.__children)

  @property
  def HasSections(self):
    """True if this section has associated sections, False otherwise"""
    return bool(self.__sections)

  @property
  def HasSettings(self):
    """True if this section has settings, False otherwise"""
    return bool(self.__settings)

  @property
  def IsAttribute(self):
    """True if this section is an attribute (it has one setting and no associated sections), False otherwise"""
    return len(self.Settings) == 1 and not self.HasSections

  @property
  def Name(self):
    """this section's name string"""
    return self.__name

  @property
  def Settings(self):
    """a list of this section's settings (in order)"""
    return self.__settings

  @property
  def Value(self):
    """the value of this attribute (this section must be an attribute)"""
    assert self.IsAttribute
    return self.__settings[0]

class TConfigurationFormatError(Exception):

  def __init__(self, line, column, message):
    self.__line = line
    self.__column = column
    self.__message = message
    super().__init__(str(line) + ":" + str(column) + " " + message)

  def __str__(self):
    return str(self.Line) + ':' + str(self.Column) + ": " + self.Message

  @property
  def Column(self):
    return self.__column

  @property
  def Line(self):
    return self.__line

  @property
  def Message(self):
    return self.__message

class TConfigurationParser(object):

  __START = 0
  __PRE_NAME = 1
  __NAME = 2
  __NAME_ESCAPE = 3
  __POST_NAME = 4
  __LINE_COMMENT = 5

  __COMMENT_CHARS = {'#', '@'}

  def __init__(self, section_begin_callback, section_end_callback, setting_callback):
    self.__section_begin_cb = section_begin_callback
    self.__section_end_cb = section_end_callback
    self.__setting_cb = setting_callback
    self.__state = self.__START
    self.__absolute_position = 1
    self.__line = 1
    self.__column = 1
    self.__section_stack = []

  def Finish(self):
    if self.__state != self.__PRE_NAME or self.__section_stack:
      raise TConfigurationFormatError(self.Line, self.Column, "Incomplete document")

  def ParseString(self, text):
    for char in text:
      self.__Handlers[self.__state](self, char)
      self.__absolute_position += 1
      if char == '\n':
        self.__line += 1
        self.__column = 1
      else:
        self.__column += 1

  def ParseStrings(self, text_generator):
    for line in text_generator:
      self.ParseString(line)

  def SetCallbacks(self, callback_triple):
    assert len(callback_triple) == 3
    self.__section_begin_cb, self.__section_end_cb, self.__setting_cb = callback_triple

  @property
  def AbsolutePosition(self):
    return self.__absolute_position

  @property
  def Callbacks(self):
    return (self.__section_begin_cb, self.__section_end_cb, self.__setting_cb)

  @property
  def Column(self):
    return self.__column

  @property
  def _CurrentSection(self):
    assert self.__section_stack
    return self.__section_stack[-1]

  @property
  def Line(self):
    return self.__line

  @property
  def SectionBeginCb(self):
    return self.__section_begin_cb

  @SectionBeginCb.setter
  def SectionBeginCb(self, cb):
    self.__section_begin_cb = cb

  @property
  def SectionEndCb(self):
    return self.__section_end_cb

  @SectionEndCb.setter
  def SectionEndCb(self, cb):
    self.__section_end_cb = cb

  @property
  def SettingCb(self):
    return self.__setting_cb

  @SettingCb.setter
  def SettingCb(self, cb):
    self.__setting_cb = cb

  def __HandleStart(self, char):
    if not char.isspace():
      if char == '"':
        self.__name = io.StringIO()
        self.__state = self.__NAME
      elif char == '{':
        raise TConfigurationFormatError(self.Line, self.Column, "Opening the top-level section without a name")
      elif char == '}':
        raise TConfigurationFormatError(self.Line, self.Column, "Closing the top-level section without opening it")
      elif char in self.__COMMENT_CHARS:
        self.__prior_state = self.__state
        self.__state = self.__LINE_COMMENT
      else:
        raise TConfigurationFormatError(self.Line, self.Column, "Unexpected character at the top level: '" + char + "'")

  def __HandlePreName(self, char):
    if not char.isspace():
      if char == '"':
        self.__name = io.StringIO()
        self.__state = self.__NAME
      elif char == '}':
        if not self.__section_stack:
          raise TConfigurationFormatError(self.Line, self.Column, "Closing a nonexistent section at the top level")
        else:
          self.__section_end_cb(self.__section_stack.pop())
      elif char in self.__COMMENT_CHARS:
        self.__prior_state = self.__state
        self.__state = self.__LINE_COMMENT
      else:
        raise TConfigurationFormatError(self.Line, self.Column, "Unexpected character: '" + char + "'")

  def __HandleName(self, char):
    if char == '"':
      self.__state = self.__NAME_ESCAPE
    else:
      self.__name.write(char)

  def __HandleNameEscape(self, char):
    if char == '"':
      self.__name.write(char)
      self.__state = self.__NAME
    else:
      self.__state = self.__POST_NAME
      self.__HandlePostName(char)

  def __HandlePostName(self, char):
    if not char.isspace():
      if char == ';':
        if not self.__section_stack:
          raise TConfigurationFormatError(self.Line, self.Column, "Setting found in the top level")
        else:
          self.__state = self.__PRE_NAME
          setting = self.__name.getvalue()
          self.__setting_cb(setting, self.__section_stack[-1])
      elif char == '{':
        self.__state = self.__PRE_NAME
        section = TSection(self.__name.getvalue())
        try:
          self.__section_begin_cb(section, self.__section_stack[-1] if self.__section_stack else None)
        finally:
          self.__section_stack.append(section)
      elif char == '}':
        if not self.__section_stack:
          raise TConfigurationFormatError(self.Line, self.Column, "Closing a nonexistent section")
        else:
          setting = self.__name.getvalue()
          self.__state = self.__PRE_NAME
          try:
            self.__setting_cb(setting, self.__section_stack[-1])
          finally:
            section = self.__section_stack.pop()
          self.__section_end_cb(section)
      elif char in self.__COMMENT_CHARS:
        self.__prior_state = self.__state
        self.__state = self.__LINE_COMMENT
      else:
        raise TConfigurationFormatError(self.Line, self.Column, "Unexpected character")

  def __HandleLineComment(self, char):
    if char == '\n':
      self.__state = self.__prior_state

  __Handlers = {
    __START:        __HandleStart,
    __PRE_NAME:     __HandlePreName,
    __NAME:         __HandleName,
    __NAME_ESCAPE:  __HandleNameEscape,
    __POST_NAME:    __HandlePostName,
    __LINE_COMMENT: __HandleLineComment
   }

class TConfigurationDOMParser(TConfigurationParser):
  """ Instances of this configuration file parser read entire section trees into memory.
      They are akin to XML DOM parsers."""

  def __init__(self):
    """ Construct a configuration file parser.  The client must invoke the
        regular TConfigurationParser methods (ParseString(), ParseStrings(),
        Finish(), etc.) to actually parse content."""
    self.__root = None
    def SectionBeginHandler(section, parent):
      if not self.__root:
        self.__root = section
      else:
        assert parent is not None
        try:
          parent.AddSection(section)
        except KeyError as e:
          raise RuntimeError("Duplicate section name")
    def SectionEndHandler(section):
      pass
    def SettingHandler(setting, section):
      section.AddSetting(setting)
    super().__init__(SectionBeginHandler, SectionEndHandler, SettingHandler)

  @property
  def Root(self):
    """the root section of the parsed configuration file (only valid after Finish() is invoked)"""
    return self.__root

def WriteConfiguration(fobj, section, pretty_print=False, tab_size=2):
  """ Write a configuration file to the specified file-like object.  'fobj' must
      be a file-like object open for writing.  'section' is the root of the
      configuration file.  'pretty_print' is a boolean specifying whether the
      configuration file should be "pretty printed" (whitespace and newlines
      added).  If 'pretty_print' is True, then 'tab_size' specifies the number
      of spaces per generated tab; otherwise, 'tab_size' is ignored."""
  assert isinstance(section, TSection)

  def WriteEncodedString(text):
    for c in text:
      fobj.write(c if c != '"' else '""')

  num_tabs = 0
  if pretty_print:
    section_open_text = '" {'
    section_close_text = '}\n'
    empty_section_text = '" {}'
    attribute_begin_text = '" { "'
    attribute_end_text = '" }\n'
    tab = ' ' * tab_size
    def WriteTabbed(text):
      fobj.write(tab * num_tabs + text)
    def WriteEndOfLine(text):
      fobj.write(text + '\n')
  else:
    section_open_text = '"{'
    section_close_text = '}'
    empty_section_text = '"{}'
    attribute_begin_text = '"{"'
    attribute_end_text = '"}'
    def WriteTabbed(text):
      fobj.write(text)
    def WriteEndOfLine(text):
      fobj.write(text)

  def CloseSection():
    nonlocal num_tabs
    num_tabs -= 1
    WriteTabbed(section_close_text)

  section_stack = [(False, 0, 0, section)]

  def WriteChildren(section, start_index):
    for child_index, child in enumerate(section.Children[start_index:], start_index):
      if isinstance(child, str):
        WriteTabbed('"')
        WriteEncodedString(child)
        if child_index != len(section.Children) - 1:
          WriteEndOfLine('";')
        else:
          WriteEndOfLine('"')
      else:
        assert isinstance(child, TSection)
        section_stack.append((True, num_tabs, child_index + 1, section))
        section_stack.append((False, num_tabs, 0, child))
        return False
    return True

  while section_stack:
    visited, num_tabs, last_child_index, section = section_stack.pop()
    if visited:
      if last_child_index == len(section.Children) or WriteChildren(section, last_child_index):
        CloseSection()
    else:
      WriteTabbed('"')
      WriteEncodedString(section.Name)
      if section.HasChildren:
        if len(section.Settings) == 1 and not section.HasSections:
          fobj.write(attribute_begin_text)
          WriteEncodedString(section.Settings[0])
          fobj.write(attribute_end_text)
        else:
          WriteEndOfLine(section_open_text)
          num_tabs += 1
          if WriteChildren(section, last_child_index):
            CloseSection()
      else:
        WriteEndOfLine(empty_section_text)



################################################################################
# Log file data structures and algorithms
################################################################################

class TLogFormatError(Exception):

  def __init__(self, line, column, entry_number, message):
    self.__line = line
    self.__column = column
    self.__entry_number = entry_number
    self.__message = message
    super().__init__(str(line) + ":" + str(column) + " " + message)

  @property
  def Column(self):
    return self.__column

  @property
  def EntryNumber(self):
    return self.__entry_number

  @property
  def Line(self):
    return self.__line

  @property
  def Message(self):
    return self.__message

class TLogParser(object):

  __PRE_FIELD = 0
  __FIELD = 1
  __FIELD_ESCAPE = 2
  __POST_FIELD_PRE_COLON = 3
  __LINE_COMMENT = 4

  __COMMENT_CHARS = {'#', '@'}
  __FINISH_STATES = {__PRE_FIELD, __POST_FIELD_PRE_COLON, __LINE_COMMENT}

  def __init__(self, entry_callback):
    self.__entry_callback = entry_callback
    self.__state = self.__PRE_FIELD
    self.__line = 1
    self.__column = 1
    self.__absolute_position = 1
    self.__entry = 1
    self.__fields = []
    self.__field_buffer = io.StringIO()
    self.__colon_seen = False
    super().__init__()

  def Finish(self):
    if self.__state not in self.__FINISH_STATES:
      raise TLogFormatError(self.Line, self.Column, self.EntryNumber, "finished in the middle of a field")
    else:
      self.__FinishEntry(self.__PRE_FIELD)

  def ParseString(self, text):
    for char in text:      
      self.__Handlers[self.__state](self, char)
      self.__absolute_position += 1
      if char == '\n':
        self.__line += 1
        self.__column = 1
      else:
        self.__column += 1

  def ParseStrings(self, text_generator):
    for line in text_generator:
      self.ParseString(line)

  @property
  def AbsolutePosition(self):
    return self.__absolute_position

  @property
  def EntryCb(self):
    return self.__entry_callback

  @EntryCb.setter
  def EntryCb(self, entry_callback):
    self.__entry_callback = entry_callback

  @property
  def EntryNumber(self):
    return self.__entry

  @property
  def Column(self):
    return self.__column

  @property
  def Line(self):
    return self.__line

  def __FinishEntry(self, new_state):
    self.__state = new_state
    if self.__colon_seen:
      self.__fields.append("")
      self.__colon_seen = False
    if self.__fields:
      entry = tuple(self.__fields)
      self.__fields = []
      self.__entry += 1
      self.EntryCb(entry)

  def __HandlePreField(self, char):
    if not char.isspace():
      if char == '"':
        self.__state = self.__FIELD
        self.__colon_seen = False
      elif char == ':':
        self.__fields.append("")
        self.__colon_seen = True
      elif char in self.__COMMENT_CHARS:
        self.__FinishEntry(self.__LINE_COMMENT)
      else:
        raise TLogFormatError(self.Line, self.Column, self.EntryNumber, "unexpected character: " + char)
    elif char == '\n':
      self.__FinishEntry(self.__PRE_FIELD)

  def __HandleField(self, char):
    if char == '"':
      self.__state = self.__FIELD_ESCAPE
    else:
      self.__field_buffer.write(char)

  def __HandleFieldEscape(self, char):
    if char == '"':
      self.__field_buffer.write(char)
      self.__state = self.__FIELD
    else:
      self.__fields.append(self.__field_buffer.getvalue())
      self.__field_buffer.truncate(0)
      if char == '\n':
        self.__FinishEntry(self.__PRE_FIELD)
      elif char.isspace():
        self.__state = self.__POST_FIELD_PRE_COLON
      elif char == ':':
        self.__state = self.__PRE_FIELD
        self.__colon_seen = True
      elif char in self.__COMMENT_CHARS:
        self.__FinishEntry(self.__LINE_COMMENT)
      else:
        raise TLogFormatError(self.Line, self.Column, self.EntryNumber, "unexpected character: " + char)

  def __HandlePostFieldPreColon(self, char):
    if not char.isspace():
      if char == ':':
        self.__state = self.__PRE_FIELD
        self.__colon_seen = True
      elif char in self.__COMMENT_CHARS:
        self.__FinishEntry(self.__LINE_COMMENT)
      else:
        raise TLogFormatError(self.Line, self.Column, self.EntryNumber, "unexpected character: " + char)
    elif char == '\n':
      self.__FinishEntry(self.__PRE_FIELD)

  def __HandleLineComment(self, char):
    if char == '\n':
      self.__state = self.__PRE_FIELD

  __Handlers = {
    __PRE_FIELD:            __HandlePreField,
    __FIELD:                __HandleField,
    __FIELD_ESCAPE:         __HandleFieldEscape,
    __POST_FIELD_PRE_COLON: __HandlePostFieldPreColon,
    __LINE_COMMENT:         __HandleLineComment
   }

class TLogWriter(object):

  def __init__(self, stream=None):
    self.__stream = stream
    super().__init__()

  def SetStream(self, stream):
    self.__stream = stream

  # TODO Remove the generator prohibition.
  def Write(self, fields):
    if len(fields) == 1:
      self.__WriteField(field, True) if fields[0] else self.__stream.write('""')
    else:
      for index, field in enumerate(fields, 1):
        self.__WriteField(field, index == len(fields))
    self.__stream.write('\n')

  def __WriteEncodedString(self, text):
    for char in text:
      self.__stream.write(char if char != '"' else '""')

  def __WriteField(self, field, is_final_field):
    data = str(field)
    if data:
      self.__stream.write('"')
      self.__WriteEncodedString(data)
      self.__stream.write('":' if not is_final_field else '"')
    elif not is_final_field:
      self.__stream.write(':')

  @property
  def Stream(self):
    return self.__stream



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

  def __init__(self, 振り仮名start, 振り仮名end):
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
 kanji_onclick_generator, kanji_onmouseover_generator, 振り仮名のクラス,
 振り仮名を見える=True):
  """ Write HTML5 ruby-annotated text from the specified iterable of
      T言葉と振り仮名 into the specified buffer.  振り仮名のクラス should be a
      valid CSS class name: It will be the value of each rt tag's
      "class" attribute.  If 振り仮名を見える is True, then the generated
      HTML5 text will ensure that the 振り仮名 is initially visible via
      the "style" tag attribute; otherwise, the generated HTML5 text
      will ensure that the 振り仮名 is hidden."""
  visible = ('" style="visibility:visible;">' if 振り仮名を見える else '" style="visibility:hidden;">')
  rt_start = '<rp class="' + 振り仮名のクラス + visible + ' (</rp><rt class="' + 振り仮名のクラス + visible
  rt_end = '<rp class="' + 振り仮名のクラス + visible + ') </rp></rt></ruby>'
  for ペア in 言葉と振り仮名sequence:
    if ペア.振り仮名:
      buf.write("""<ruby>""")
      for 字 in ペア.言葉:
        buf.write(
          '<span class=\"' + kanji_class +
          '" onclick="' + kanji_onclick_generator(字) +
          ('" onmouseover="' + kanji_onmouseover_generator(字) + '">' if kanji_onmouseover_generator is not None else '">') +
          字 + '</span>'
         )
      buf.write(rt_start)
      buf.write(ペア.振り仮名)
      buf.write(rt_end)
    else:
      for 字 in ペア.言葉:
        if ord(字) in KANJI_RANGE:
          buf.write(
            '<span class=\"' + kanji_class +
            '" onclick="' + kanji_onclick_generator(字) +
            ('" onmouseover="' + kanji_onmouseover_generator(字) + '">' if kanji_onmouseover_generator is not None else '">') +
            字 + '</span>'
           )
        else:
          buf.write(字)



################################################################################
# Utility functions for generating HTML5 code
################################################################################

def BeginHTML5(buf, title="Untitled", encoding="UTF-8"):
  """ Produce a string containing the beginning of an HTML5 document.  This
      will contain a doctype declaration, a meta charset entry for the specified
      character encoding, and the specified document title.  It will end inside
      of the HEAD tag."""
  buf.write('<!DOCTYPE html><html><head><meta charset="' +
    encoding + '" /><title>' + title + '</title>')



################################################################################
# Code designed specifically for organizing and displaying flashcards
################################################################################

class TEmptyDeckError(Exception):
  """TCardDeck raises this exception whenever clients try to draw cards when
     none are left."""
  pass

class TFlashcard(object):
  """ This is the base class for flashcards.  These flashcards use a basic
      Leitner system.  Each card has an associated zero-indexed Leitner bucket
      number.  Cards that the user answers correctly are promoted into higher
      Leitner bucket numbers, whereas incorrectly-answered cards are demoted to
      bucket zero.  The idea is that cards with higher bucket numbers are shown
      to the user after increasingly large delays.

      Subclasses should override __bytes__()."""

  def __init__(self):
    """ Construct a flashcard in Leitner bucket zero (the current deck)."""
    self.__bucket = 0
    super().__init__()

  def Demote(self):
    """ Move the flashcard into Leitner bucket zero (the current deck)."""
    self.__bucket = 0

  def Promote(self, max_bucket_number):
    """ Move the flashcard into the next Leitner bucket, if possible.  The
        parameter represents the largest Leitner bucket number.  This method
        returns True if the card was promoted; otherwise, it returns False."""
    if self.__bucket < max_bucket_number:
      self.__bucket += 1
      return True
    return False

  def SetBucket(self, bucket):
    """ Set the card's Leitner bucket number."""
    assert isinstance(bucket, int)
    self.__bucket = bucket

  @property
  def Bucket(self):
    """the card's Leitner bucket number"""
    return self.__bucket

  @property
  def Hash(self):
    """the hash digest of the flashcard as a hex string"""
    return hashlib.sha1(bytes(self)).hexdigest()

class TCardDeckStatistics(object):
  """Instances of this class record information about decks of cards and
     how well users perform with the decks."""

  def __init__(self, cards):
    """Construct a new stats object that records information about the
       specified collection of cards.  NOTE: 'cards' must have a
       __len__() method."""
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

  def CardPassed(self, card):
    """Note that the user successfully answered the specified card."""
    self.__num_attempts += 1
    if card not in self.__retry_map:
      self.__num_passed_on_first_try += 1
    self.__cards.add(card)
    self.__num_left -= 1

  # Log format:
  #
  #   <date-stamp>:<card-hash>:<num-retries>
  def Log(self, stream):
    """ Write statistics about cards that the user has seen to the specified
        file-like object.  The data is stored as log entries.  Each entry has
        the following fields (in order):

          1. the current timestamp as returned by time.time();
          2. the SHA-1 hash of the byte representation of the card (that is,
             the SHA-1 hash of the result of constructing a bytes object from
             the card); and
          3. the number of times the user had to retry the card before he
             successfully answered it."""
    writer = TLogWriter(stream)
    cur_time = time.time()
    for card in self.__cards:
      writer.Write((cur_time, card.Hash, self.__retry_map.get(card, 0)))

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
      be of any type.

      Clients typically use this class as follows:

        1. Construct a deck of cards.
        2. If there are any cards left (HasCards), then draw a card (GetCard());
           otherwise, the test is over.
        3. If the user answers the card correctly, then invoke MarkSucceeded();
           otherwise, invoke MarkFailed().
        4. Go to step (2).

      Decks automatically recycle failed cards."""

  def __init__(self, cards, max_leitner_bucket_number):
    """ Construct a deck from the specified sequence of flashcards and the specified maximum Leitner bucket number."""
    self.__cards = list(cards)
    self.__failed_cards = []
    self.__current_card = None
    self.__current_card_marked = False
    self.__statistics = TCardDeckStatistics(self.__cards)
    self.__max_leitner_bucket_number = max_leitner_bucket_number
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
    self.__current_card.Demote()

  def MarkSucceeded(self):
    """ Mark the current card (that is, the card that was last drawn) as
        "succeeded" (that is, the user answered it correctly).  This method
        will remove the card from the deck."""
    assert self.__current_card is not None
    assert not self.__current_card_marked
    self.__current_card_marked = True
    self.Statistics.CardPassed(self.__current_card)
    self.__current_card.Promote(self.MaximumLeitnerBucketNumber)

  @property
  def CurrentCard(self):
    """the current card (that is, the card that was last drawn from the deck)"""
    return self.__current_card

  @property
  def HasCards(self):
    """True if the deck is not empty, False otherwise"""
    return bool(self.__cards) or bool(self.__failed_cards)

  @property
  def MaximumLeitnerBucketNumber(self):
    """the maximum Leitner bucket number that a card can achieve"""
    return self.__max_leitner_bucket_number

  @property
  def Statistics(self):
    """the TCardDeckStatistics object associated with this deck"""
    return self.__statistics

# TODO Make the callbacks take a buffer parameter.
def GenerateCardHTML(handler_url, session_token, title, remaining_time_secs,
 head_creator, front_content_creator, back_content_creator, selectors_creator,
 stats_creator, bottom_creator):
  """ Construct a string containing a complete HTML document for displaying a
      flashcard.  The parameters are:

        handler_url :: str -- the URL that will handle form submissions
        session_token :: str -- some value identifying the session
        title :: string -- the HTML document's title
        remaining_time_secs :: int -- the number of seconds left in the quiz or
                                      0 if there is no timeout
        head_creator :: () => string -- nullary function that returns HTML
                                        content to go in the document's
                                        head section (can be None)
        front_content_creator :: () => string -- nullary function that returns
                                                 HTML content for the front
                                                 of the card
        back_content_creator :: () => string -- nullary function that returns
                                                HTML content for the back of
                                                the card
        selectors_creator :: () => string -- nullary function that returns
                                             HTML content producing additional
                                             buttons or content to appear
                                             below the back of the card but
                                             above the answer buttons (may
                                             be None)
        stats_creator :: () => string -- nullary function that returns HTML
                                         content to appear in the stats area
                                         of the card

      The produced document will send POSTs to handler in these situations:

        * The user selects the "やった！" button (answered the card correctly).
          In this case, there will be two form values: "successful", which will
          be "1", and "secs_left", which contains an integer representing the
          number of seconds left in the quiz.  (This is meaningless if there
          is no timeout.)  There is also a field named "method" whose value
          will be "success".

        * The user selects the "駄目だ" button (answered the card incorrectly).
          In this case, there will be two form values as in the above case
          except that the "successful" value will be "0".  There is also a
          field named "method" whose value will be "failure".

        * The quiz times out.  In this case, there will be one form value,
          "timed_out", which will be "1".  There will also be a field named
          "method" whose value will be "timeout".

      All three POST scenarios will include a form value, "session_token",
      containing the value of the 'session_token' parameter.

"""
  buf = io.StringIO()
  BeginHTML5(buf, title=title)
  buf.write("""<style type="text/css">

.toplevel {
  text-align: center;
  background: #c0c0c0;
  padding: 10px 15px;
}

.toplevel:before {
  content: '';
  display: inline-block;
  height: 100%;
  vertical-align: middle;
  margin-right: -0.25em;  /* adjusts for spacing */
  /* For visualization */
  /* background: #808080; width: 5px; */
}

div.card {
  display: inline-block;
  vertical-align: middle;
  padding: 10px 15px;
  border: #a0a0a0 solid 1px;
  background: #f5f5f5;
}

div.card div.stats {
  display: inline-block;
  font-size: medium;
  text-align: center;
  margin: 0.5em 0.5em;
}

div.front {
  font-size: xx-large;
  text-align: center;
  border: black solid 1px;
  margin: 1em 1em;
}

div.back {
  display: inline;
  font-size: large;
  text-align: center;
}

div.selectors {
  font-size: medium;
  text-align: center;
  margin: 1em 2em;
  padding: 0.5em 0.5em;
}
</style>""")
  if head_creator is not None:
    buf.write(head_creator())
  if remaining_time_secs > 0:
    buf.write("""<script type="text/javascript">var secs_left = """)
    buf.write(str(remaining_time_secs))
    buf.write("""; var t = setTimeout("UpdateSecondsDisplay();", 1000);
        function UpdateSecondsDisplay() {{
          secs_left = secs_left - 1
          if (secs_left <= 0) {{
            document.forms["timeout"].submit()
          }}
          var secs_left_fields = document.getElementsByTagName("input");
          var i = 0;
          for (i = 0; i < secs_left_fields.length; i++) {{
            var elem = secs_left_fields.item(i);
            if (elem.getAttribute("name") == "secs_left") {{
              elem.setAttribute("value", secs_left.toString());
            }}
          }}
          var timefield = document.getElementById("time_left");
          while (timefield.childNodes.length >= 1) {{
            timefield.removeChild(timefield.firstChild);
          }}
          timefield.appendChild(timefield.ownerDocument.createTextNode(
            Math.floor(secs_left / 3600).toString() + "時" + Math.floor((secs_left % 3600) / 60).toString() + "分" + ((secs_left % 3600) % 60).toString() + "秒"
           ));
          t = setTimeout("UpdateSecondsDisplay();", 1000);
        }}</script>""")
  buf.write("""<body><div class="toplevel" height="100%"><div class="card"><div class="front">""")
  buf.write(front_content_creator())
  buf.write('</div><div id="hidden_portion" style="visibility:hidden;"><div class="back">')
  buf.write(back_content_creator())
  buf.write('</div><div class="selectors">')
  if selectors_creator is not None:
    buf.write(selectors_creator())
  buf.write("""<form accept-charset="UTF-8" style="display:inline" action=\"""")
  buf.write(handler_url)
  buf.write("""\" method="post">
      <input type="submit" value="駄目だ" />
      <input type="hidden" name="method" value="failure" />
      <input type="hidden" name="session_token" value=\"""")
  buf.write(str(session_token))
  buf.write("""\" />
      <input type="hidden" name="successful" value="0" />
      <input type="hidden" name="secs_left" value=\"""")
  rts_string = str(remaining_time_secs)
  buf.write(rts_string)
  buf.write("""\" /></form><form accept-charset="UTF-8" style="display:inline" action=\"""")
  buf.write(handler_url)
  buf.write("""\" method="post">
      <input type="submit" value="やった！" />
      <input type="hidden" name="method" value="success" />
      <input type="hidden" name="session_token" value=\"""")
  buf.write(str(session_token))
  buf.write("""\" />
      <input type="hidden" name="successful" value="1" />
      <input type="hidden" name="secs_left" value=\"""")
  buf.write(rts_string)
  buf.write("""\" /></form></div></div><div class="stats">""")
  buf.write(stats_creator())
  buf.write("""</div></div>""")
  if bottom_creator is not None:
    buf.write(bottom_creator())
  buf.write("""<form id="show_form" style="visibility:visible;">
      <input type="button" value="Show Answer"
        onclick="document.getElementById('show_form').setAttribute('style', 'visibility:hidden'); document.getElementById('hidden_portion').setAttribute('style', 'visibility:visible');" />
    </form></div>
    <form accept-charset="UTF-8" action=\"""")
  buf.write(handler_url)
  buf.write("""\" method="post" id="timeout" style="visibility:hidden;">
    <input type="hidden" name="method" value="timeout" />
    <input type="hidden" name="session_token" value=\"""")
  buf.write(str(session_token))
  buf.write("""\" />
    <input type="hidden" name="timed_out" value="1" /></form></body></html>""")

  return buf.getvalue()



################################################################################
# Code for the 言葉 flashcards application
################################################################################

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
        on_flashcard_handler(T言葉のフラッシュカード(self.__日本語, self.__英語, self.__source))
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



################################################################################
# The main server code
################################################################################

QuizURL = "/"
CurrentDeck = None
CardCount = 0
CurrentSession = None
FlashcardsFile = None
FlashcardsStatsLog = None
MaxLeitnerBucket = None
RemainingTimeSecs = 0

ReversedCardOrientation = False

@get(QuizURL)
def Config():
  global CardCount
  global CurrentSession
  CurrentSession = str(random.random())

  if not CardCount:
    def Handleカード(カード):
      global CardCount
      CardCount += 1
    parser = T言葉のフラッシュカードのパーサ(Handleカード)
    with open(FlashcardsFile, "r") as f:
      parser.ParseStrings(f)
    parser.Finish()

  buf = io.StringIO()
  BeginHTML5(buf, title="言葉の試験 Setup")
  buf.write("""</head><body><p><h1>言葉の試験 Setup</h1></p>
<p>Card Count: {0}</p>
<p><form method="post" action="{1}">
<fieldset><legend>Limits</legend><p>
<label>Time:</label>
<input type="text" id="時" name="hours" /><label for="時">時</label>
<input type="text" id="分" name="minutes" /><label for="分">分</label>
<input type="text" id="秒" name="seconds" /><label for="秒">秒</label>
</p><p>
<label>Maximum Cards:</label><input type="text" name="max_cards" />
</p></fieldset>
<fieldset><legend>Deck Options</legend><p>
<label>Card Orientation:</label><br />
<input type="radio" id="orientation_regular" name="card_orientation" value="regular" checked="checked" /><label for="orientation_regular">前は日本語、後ろは英語</label><br />
<input type="radio" id="orientation_reversed" name="card_orientation" value="reversed" /><label for="orientation_reversed">前は英語、後ろは日本語</label>
</p></fieldset>
<input type="submit" value="始めましょう！" />
<input type="hidden" name="method" value="configure" />
<input type="hidden" name="session_token" value="{2}" />
</form></p></body></html>""".format(CardCount, QuizURL, CurrentSession))
  return buf.getvalue()

@post(QuizURL)
def HandlePost():
  global CardCount
  global ReversedCardOrientation
  global CurrentDeck
  global CurrentSession
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
    if request.forms.max_cards:
      selector = TRandomSelector(StrToInt(request.forms.max_cards, "max_cards"))
    else:
      class TUnboundedSelector(list):
        def Add(self, カード):
          self.append(カード)
      selector = TUnboundedSelector()

    # Determine the card orientation.
    if not request.forms.card_orientation:
      abort(400, "no card orientation")
    ReversedCardOrientation = (request.forms.card_orientation == "reversed")

    # Parse the flashcards file and create a deck from some of the cards.
    local_card_count = 0
    def Handleカード(カード):
      nonlocal local_card_count
      selector.Add(カード)
      local_card_count += 1
    parser = T言葉のフラッシュカードのパーサ(Handleカード)
    with open(FlashcardsFile, "r") as f:
      parser.ParseStrings(f)
    parser.Finish()
    if local_card_count != CardCount:
      CardCount = local_card_count
    if not isinstance(selector, TRandomSelector):
      random.shuffle(selector)
    CurrentDeck = TCardDeck(selector, MaxLeitnerBucket)

    # Finally, render the first card.
    return RenderCard()

  assert CurrentDeck
  RemainingTimeSecs = StrToInt(request.forms.secs_left, "secs_left")
  if method == "success":
    CurrentDeck.MarkSucceeded()
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
  global MaxLeitnerBucket

  parser = argparse.ArgumentParser(description="月詠は日本語を勉強するツールです。")
  parser.add_argument(
    "ポート番号",
    help="サーバのポート番号です。"
   )
  parser.add_argument(
    "サーバの設定ファイル",
    help="path to the file containing the server's settings"
   )

  args = parser.parse_args(sys.argv[1:])
  try:
    ポート番号 = int(args.ポート番号)
  except ValueError:
    sys.stderr.write("すみません、サーバのポート番号は駄目です。外のポート番号を使って下さい。\n")
    sys.exit(2)

  # Ensure that the provided server configuration file is a readable file.
  if not os.path.isfile(args.サーバの設定ファイル):
    sys.stderr.write("すみません、" + args.サーバの設定ファイル + "はファイルじゃありません。外のパス名を使って下さい。\n")
    sys.exit(2)
  if not os.access(args.サーバの設定ファイル, os.R_OK):
    sys.stderr.write("すみません、" + args.サーバの設定ファイル + "を開けて読めません。\n")
    sys.exit(2)

  # Parse the configuration file.
  parser = TConfigurationDOMParser()
  try:
    with open(args.サーバの設定ファイル, "r") as f:
      parser.ParseStrings(f)
    parser.Finish()
  except TConfigurationFormatError as e:
    sys.stderr.write("すみません、その設定ファイルは駄目です。\n")
    sys.stderr.write(str(e) + "\n")
    sys.exit(2)
  except Exception as e:
    sys.stderr.write("Unexpected error: " + str(e) + "\n")
    sys.exit(2)
  args.サーバの設定ファイル = os.path.abspath(os.path.dirname(args.サーバの設定ファイル))

  # Extract server settings from the configuration file.
  # Check for errors.
  def PrintErrorAndExit(message):
    sys.stderr.write("すみません、その設定ファイルは駄目です。" + message + "\n")
    sys.exit(2)
  if parser.Root.Name != "server-configuration":
    PrintErrorAndExit("The root's name should be 'server-configuration'.")
  if parser.Root.HasSettings:
    PrintErrorAndExit("The root node cannot have settings.")
  for section in parser.Root.YieldSections():
    if not section.IsAttribute:
      PrintErrorAndExit("Settings must be attributes.")
    if section.Name == "kotoba-flashcards-file":
      if FlashcardsFile is not None:
        PrintErrorAndExit("It has two 'kotoba-flashcards-file' attributes.")
      FlashcardsFile = EnsureAbsolutePath(section.Value, args.サーバの設定ファイル)
      if not os.path.isfile(FlashcardsFile):
        PrintErrorAndExit("The kotoba-flashcards-file '" + FlashcardsFile + "' is not a file.")
      if not os.access(FlashcardsFile, os.R_OK):
        PrintErrorAndExit("The kotoba-flashcards-file '" + FlashcardsFile + "' cannot be read.")
    elif section.Name == "kotoba-flashcards-stats-log":
      if FlashcardsStatsLog is not None:
        PrintErrorAndExit("It has two 'kotoba-flashcards-stats-log' attributes.")
      FlashcardsStatsLog = EnsureAbsolutePath(section.Value, args.サーバの設定ファイル)
      if os.path.exists(FlashcardsStatsLog):
        if not os.path.isfile(FlashcardsStatsLog):
          PrintErrorAndExit("The kotoba-flashcards-file '" + FlashcardsStatsLog + "' is not a file.")
        if not os.access(FlashcardsStatsLog, os.R_OK):
          PrintErrorAndExit("The kotoba-flashcards-file '" + FlashcardsStatsLog + "' cannot be read.")
    elif section.Name == "kotoba-flashcards-max-leitner-bucket":
      if MaxLeitnerBucket is not None:
        PrintErrorAndExit("It has two 'kotoba-flashcards-max-leitner-bucket' attributes.")
      try:
        MaxLeitnerBucket = int(section.Value)
      except ValueError:
        PrintErrorAndExit("It has a non-numeric 'kotoba-flashcards-max-leitner-bucket' value: " + section.Value)
      if MaxLeitnerBucket < 0:
        PrintErrorAndExit("'kotoba-flashcards-max-leitner-bucket' is less than zero.")
    else:
      PrintErrorAndExit("One setting has an invalid name: " + section.Name)

  # Set defaults.
  if MaxLeitnerBucket is None:
    MaxLeitnerBucket = 6

  # Start the server.
  run(host='localhost', port=ポート番号, debug=True)

# TODO Download kanji stroke order diagrams automatically or via a separate program.
#      Don't rely on external sources for every image.
def RenderCard():
  カード = CurrentDeck.GetCard()
  振り仮名がある = False
  振り仮名producer = T言葉と振り仮名Producer('(', ')')
  def KanjiOnClickGenerator(字):
    quoted = urllib.parse.quote(字)
    return """window.open('http://jisho.org/kanji/details/""" + quoted + """', '""" + quoted + """')"""
  def KanjiOnMouseoverGenerator(字):
    return ("setKanjiImage('http://jisho.org/static/images/stroke_diagrams/" +
     str(ord(字)) + "_frames.png')")

  def GenerateHead():
    return """<style type="text/css">
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
kanji_diagram_src_set = false;

function showKanjiDiagram() {
  kanji_image = document.getElementsByName('漢字diagram')[0];
  kanji_image.setAttribute('style', 'display: block; max-width: 100%; margin-left: auto; margin-right: auto');
}

function enableKanjiView() {
  kanji_diagram_enabled = true;
  kanji_image = document.getElementsByName('漢字diagram')[0];
  show_kanji = document.getElementsByName('show_kanji')[0];
  show_kanji.setAttribute('style', 'display: none');
  if (kanji_diagram_src_set) {
    showKanjiDiagram();
  }
}

function setKanjiImage(url_text) {
  kanji_diagram_src_set = true;
  kanji_image = document.getElementsByName('漢字diagram')[0];
  if (kanji_image.getAttribute('src') != url_text) {
    kanji_image.setAttribute('src', url_text);
  }
  if (kanji_diagram_enabled) {
    showKanjiDiagram();
  }
}

</script>"""
  def GenerateFront():
    buf = io.StringIO()
    nonlocal 振り仮名がある
    振り仮名producer.Reset()
    振り仮名producer.Process(カード.日本語)
    振り仮名producer.Finish()
    GenerateHTML5Ruby(振り仮名producer.Results, buf, "kanji", KanjiOnClickGenerator, KanjiOnMouseoverGenerator, "furigana", False)
    振り仮名がある = any(ペア.振り仮名 for ペア in 振り仮名producer.Results)
    return buf.getvalue()
  def GenerateBack():
    buf = io.StringIO()
    振り仮名producer.Reset()
    振り仮名producer.Process(カード.英語)
    振り仮名producer.Finish()
    GenerateHTML5Ruby(振り仮名producer.Results, buf, "kanji", KanjiOnClickGenerator, KanjiOnMouseoverGenerator, "furigana", False)
    buf.write("<br />(Source: ")
    振り仮名producer.Reset()
    振り仮名producer.Process(カード.Source)
    振り仮名producer.Finish()
    GenerateHTML5Ruby(振り仮名producer.Results, buf, "kanji", KanjiOnClickGenerator, KanjiOnMouseoverGenerator, "furigana", False)
    buf.write(")")
    return buf.getvalue()
  def GenerateSelectors():
    buf = io.StringIO()
    buf.write("<form><input type='button' name='show_kanji' value='漢字の書き方を見せて' onclick='enableKanjiView()'/>")
    if 振り仮名がある:
      buf.write("""<input type="button" name="振り仮名を見せて" value="振り仮名を見せて" onclick="toggle_visibility('furigana')"/>""")
    buf.write("</form>")
    return buf.getvalue()
  def GenerateStats():
    buf = io.StringIO()
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
    return buf.getvalue()
  def GenerateBottom():
    return """<img name="漢字diagram" style="display: none" alt="漢字 Stroke Diagram" src="" />"""

  # If we should reverse the card orientation, then swap the front and
  # back generators.
  if ReversedCardOrientation:
    GenerateFront, GenerateBack = GenerateBack, GenerateFront

  return GenerateCardHTML("/", CurrentSession, "言葉の試験", RemainingTimeSecs,
   GenerateHead, GenerateFront, GenerateBack, GenerateSelectors, GenerateStats,
   GenerateBottom)

def RenderFinishPage(timed_out):
  assert CurrentDeck is not None
  buf = io.StringIO()
  if FlashcardsStatsLog is not None:
    try:
      with open(FlashcardsStatsLog, "a") as logf:
        CurrentDeck.Statistics.Log(logf)
    except IOError as e:
      buf.write("WARNING: Failed to open or write to the stats log: " + str(e) + "\n")
  buf.write("Timed out!" if timed_out else "Done!")
  return buf.getvalue()

def StrToInt(text, name):
  try:
    return int(text) if text else 0
  except ValueError:
    abort(400, name + " is not an integer: " + str(text))

if __name__ == "__main__":
  Main()



