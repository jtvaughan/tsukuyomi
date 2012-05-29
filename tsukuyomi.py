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
import errno
import hashlib
import heapq
import io
import itertools
import os
import os.path
import random
import sys
import time
import urllib.parse
import urllib.request

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
# Configuration file data structures and algorithms
################################################################################

class TSection(object):
  """ Instances of this class represent sections within configuration files.
      As explained in README.md, configuration file sections are like inner
      nodes within N-ary trees.  Each section may contain settings (strings)
      or sections.  The only restriction is that the contained sections cannot
      share the same name."""

  def __init__(self, name):
    """ Construct an empty TSection with the specified name string."""
    self.__name = name
    self.__children = []      # settings and sections in order
    self.__sections = collections.OrderedDict()
    self.__settings = []
    super().__init__()

  def AddSection(self, section):
    """ Add the specified TSection to this section.  This raises
        KeyError if this section already contains a section with the specified
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
    """ Get the section with the specified name.  This raises
        KeyError if this section contains no section with the specified name."""
    return self.__sections[name]

  def HasSection(self, name):
    """ Determine whether this section contains a section with the specified name."""
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
    """a list of the section's settings and sections (read-only)"""
    return self.__children

  @property
  def HasChildren(self):
    """True if this section contains settings or sections, False otherwise"""
    return bool(self.__children)

  @property
  def HasSections(self):
    """True if this section contains sections, False otherwise"""
    return bool(self.__sections)

  @property
  def HasSettings(self):
    """True if this section has settings, False otherwise"""
    return bool(self.__settings)

  @property
  def IsAttribute(self):
    """True if this section is an attribute (it contains one setting and no sections), False otherwise"""
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

  _COMMENT_CHARS = {'#', '@'}

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
      elif char in self._COMMENT_CHARS:
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
      elif char in self._COMMENT_CHARS:
        self.__prior_state = self.__state
        self.__state = self.__LINE_COMMENT
      else:
        raise TConfigurationFormatError(self.Line, self.Column, "Unexpected character: '" + char + "'")

  def __HandleName(self, char):
    if char == '\\':
      self.__state = self.__NAME_ESCAPE
    elif char == '"':
      self.__state = self.__POST_NAME
    else:
      self.__name.write(char)

  def __HandleNameEscape(self, char):
    self.__name.write(char)
    self.__state = self.__NAME

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
      elif char in self._COMMENT_CHARS:
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

  escape_map = dict(itertools.chain(
    ((c, '\\' + c) for c in TConfigurationParser._COMMENT_CHARS),
    [('"', '\\"')]
   ))

  def WriteEncodedString(text):
    for c in text:
      fobj.write(escape_map.get(c, c))

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

  _COMMENT_CHARS = {'#', '@'}
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

  def SetRecordCb(self, callback):
    self.__entry_callback = callback

  @property
  def AbsolutePosition(self):
    return self.__absolute_position

  @property
  def RecordCb(self):
    return self.__entry_callback

  @RecordCb.setter
  def RecordCb(self, entry_callback):
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
      self.RecordCb(entry)

  def __HandlePreField(self, char):
    if not char.isspace():
      if char == '"':
        self.__state = self.__FIELD
        self.__colon_seen = False
      elif char == ':':
        self.__fields.append("")
        self.__colon_seen = True
      elif char in self._COMMENT_CHARS:
        self.__FinishEntry(self.__LINE_COMMENT)
      else:
        raise TLogFormatError(self.Line, self.Column, self.EntryNumber, "unexpected character: " + char)
    elif char == '\n':
      self.__FinishEntry(self.__PRE_FIELD)

  def __HandleField(self, char):
    if char == '\\':
      self.__state = self.__FIELD_ESCAPE
    elif char == '"':
      self.__fields.append(self.__field_buffer.getvalue())
      self.__field_buffer = io.StringIO()
      self.__state = self.__POST_FIELD_PRE_COLON
    else:
      self.__field_buffer.write(char)

  def __HandleFieldEscape(self, char):
    self.__field_buffer.write(char)
    self.__state = self.__FIELD

  def __HandlePostFieldPreColon(self, char):
    if not char.isspace():
      if char == ':':
        self.__state = self.__PRE_FIELD
        self.__colon_seen = True
      elif char in self._COMMENT_CHARS:
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

  __CHAR_TO_ESCAPE_MAP = dict(itertools.chain(
    ((c, '\\' + c) for c in TLogParser._COMMENT_CHARS),
    [('"', '\\"')]
   ))

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
      self.__stream.write(self.__CHAR_TO_ESCAPE_MAP.get(char, char))

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
 kanji_onclick_generator, kanji_onmouseover_generator,
 kanji_onmouseout_generator, 振り仮名のクラス, 振り仮名を見える=True):
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

  def Write漢字(字):
    buf.write(
      '<span class=\"' + kanji_class +
      '" onclick="' + kanji_onclick_generator(字) +
      ('" onmouseover="' + kanji_onmouseover_generator(字) if kanji_onmouseover_generator is not None else '') +
      ('" onmouseout="' + kanji_onmouseout_generator(字) + '">' if kanji_onmouseout_generator is not None else '">') +
      字 + '</span>'
     )

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
# Functions for processing stroke order diagram configuration files
################################################################################

class TStrokeOrderDiagramFSInfo(object):

  def __init__(self, 設定ファイルのパス):
    # Flags and default settings
    self.__設定ファイル = []
    self.__タイムアウト = None
    self.__ログファイル = []
    configuration_files_specified = False
    self.__enabled_sources = []
    enabled_sources_specified = False
    self.__image_directory = None
    log_files_specified = False
    self.__設定ファイルのディレクトリ = os.path.abspath(os.path.dirname(設定ファイルのパス))

    # Parse the configuration file.
    def ProcessSection(section, パス名, PrintErrorAndExit):
      nonlocal configuration_files_specified
      nonlocal enabled_sources_specified
      nonlocal log_files_specified

      if section.Name == "configuration-files":
        if section.HasSections:
          PrintErrorAndExit("configuration-files cannot have subsections.")
        if configuration_files_specified:
          PrintErrorAndExit("configuration-files must be specified once.")
        configuration_files_specified = True
        for 設定ファイルのパス名 in section.Settings:
          self.__設定ファイル.append(os.path.join(self.__設定ファイルのディレクトリ, 設定ファイルのパス名))

      elif section.Name == "enabled-sources":
        if section.HasSections:
          PrintErrorAndExit("enabled-sources cannot have subsections.")
        if enabled_sources_specified:
          PrintErrorAndExit("enabled-sources must be specified once.")
        enabled_sources_specified = True
        for source in section.Settings:
          if source not in RemoteSources:
            PrintErrorAndExit("This image source is not known: " + source)
          self.__enabled_sources.append(source)

      elif section.Name == "image-directory":
        if not section.IsAttribute:
          PrintErrorAndExit("image-directory must be an attribute.")
        if self.__image_directory is not None:
          PrintErrorAndExit("image-directory must be specified once.")
        self.__image_directory = EnsureAccessibleAbsoluteDirectoryPath(section.Value, self.__設定ファイルのディレクトリ, os.R_OK, path_title="image-directory")

      elif section.Name == "log-files":
        if section.HasSections:
          PrintErrorAndExit("log-files cannot have subsections.")
        if log_files_specified:
          PrintErrorAndExit("log-files must be specified once.")
        log_files_specified = True
        for ログファイルのパス名 in section.Settings:
          self.__ログファイル.append(os.path.join(self.__設定ファイルのディレクトリ, ログファイルのパス名))

      elif section.Name == "timeout":
        if not section.IsAttribute:
          PrintErrorAndExit("timeout must be an attribute.")
        if self.__タイムアウト is not None:
          PrintErrorAndExit("timeout must be specified once.")
        try:
          self.__タイムアウト = int(section.Value)
        except ValueError:
          PrintErrorAndExit("timeout is not a number: " + section.Value)

    ツールの設定ファイルを分析する(設定ファイルのパス, "image-settings", False, ProcessSection)

    # Validate settings.
    if not enabled_sources_specified and (self.__設定ファイル or self.__ログファイル):
      sys.stderr.write("すみません、you must enable at least one source in the 設定ファイル.")
      sys.exit(2)
    self.__image_directory = os.path.join(self.__設定ファイルのディレクトリ, self.__image_directory)
    EnsureIsImageDirectory(self.__image_directory)
    if self.__タイムアウト is None:
      self.__タイムアウト = 30
    super().__init__()

  @property
  def 設定ファイル(self):
    return self.__設定ファイル

  @property
  def 設定ファイルのディレクトリ(self):
    return self.__設定ファイルのディレクトリ

  @property
  def タイムアウト(self):
    return self.__タイムアウト

  @property
  def ログファイル(self):
    return self.__ログファイル

  @property
  def EnabledSources(self):
    return self.__enabled_sources

  @property
  def ImageDirectory(self):
    return self.__image_directory



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

"""a dictionary mapping stroke order diagram sources to their download handlers and file extensions"""
RemoteSources = {
  "jisho.org": (DownloadJishoDotOrgDiagram, GetJishoDotOrgURL, "jpg"),
  "saiga-jp.com": (DownloadSaigaJPDiagram, GetSaigaJPURL, "gif"),
  "sljfaq.org": (DownloadSLJFAQDiagram, GetSLJFAQURL, "png")
 }



################################################################################
# Functions for accessing 漢字 stroke order diagrams locally
################################################################################

""" This is the start of URL paths for 漢字 stroke order diagrams.  Clients that
    need to access locally-stored stroke order diagrams should access the
    diagrams through this path.  See GetStrokeOrderDiagramURL()."""
StrokeOrderDiagramURLBase = "/images/"

def ConstructStrokeOrderDiagramPath(漢字, image_directory, source):
  """ Get a string representing the path to the stroke order diagram for the specified 漢字 from the specified source.
      The file might not exist."""
  assert source in RemoteSources
  return os.path.join(image_directory, source, 漢字 + os.extsep + RemoteSources[source][2])

def EnsureIsImageDirectory(image_directory):
  """ Terminate the program if the specified path does not refer to an image directory."""
  if not os.path.isdir(image_directory):
    sys.stderr.write("image directory path does not refer to a directory: " + image_directory + "\n")
    sys.exit(3)

def GetStrokeOrderDiagramSources(image_directory):
  """ Get a list of sources from which 漢字 stroke order diagrams were downloaded.
      'image_directory' must be a path to a root image directory that was
      previously managed by the download-kanji-images.py tool."""
  EnsureIsImageDirectory(image_directory)
  sources = os.listdir(image_directory)
  for source in sources:
    if not os.path.isdir(os.path.join(image_directory, source)):
      sys.stderr.write("image directory is corrupted: " + image_directory + ": " + source + " is not a directory\n")
      sys.exit(3)
    if source not in RemoteSources:
      sys.stderr.write("image directory is corrupted: " + image_directory + ": " + source + " is not a recognized remote source\n")
      sys.exit(3)
  return sources

def GetLocalStrokeOrderDiagramPaths(漢字, image_directory, enabled_sources):
  """ Get a list of paths to locally-stored stroke order diagrams for the specified 漢字 character.
      This function expects the following parameters:

        漢字 :: str
          A single-character string containing a 漢字 character.
        image_directory :: str
          A path to the root image directory.  This directory must have been
          managed by the download-kanji-images.py tool.
        enabled_sources :: list<str>
          A list of enabled image sources.  This function will only look for
          kanji stroke order diagrams downloaded from these sources.

  """
  assert len(漢字) == 1
  assert ord(漢字) in KANJI_RANGE
  local_sources = set(GetStrokeOrderDiagramSources(image_directory)) ^ set(enabled_sources)
  漢字 = 漢字 + os.extsep
  パス名 = []
  for source in local_sources:
    パス = GetStrokeOrderDiagramPath(漢字, image_directory, source)
    if パス is not False:
      パス名.append(パス)
  return パス名

def GetStrokeOrderDiagramPath(漢字, image_directory, source):
  """ Get the path to a stroke order diagram from the specified source for the specified 漢字.
      This function expects the following parameters:

        漢字 :: str
          A single-character string containing a 漢字 character.
        image_directory :: str
          A path to the root image directory.  This directory must have been
          managed by the download-kanji-images.py tool.
        source :: str
          A stroke order diagram source.

      This function returns the path to the stroke order diagram if it is found.
      Otherwise, this function returns False.
  """
  assert len(漢字) == 1
  assert ord(漢字) in KANJI_RANGE
  assert source in RemoteSources

  パス = ConstructStrokeOrderDiagramPath(漢字, image_directory, source)
  return パス if os.path.isfile(パス) else False

def GetStrokeOrderDiagramURL(漢字, image_directory, source):
  """ Get a URL to the stroke order diagram from the specified source for the specified 漢字.
      This function expects the following parameters:

        漢字 :: str
          A single-character string containing a 漢字 character.
        image_directory :: str
          A path to the root image directory.  This directory must have been
          managed by the download-kanji-images.py tool.
        source :: str
          A stroke order diagram source.

      This function returns a string representing a URL.  The URL will be the
      contatenation of the string "/images/", the source (URL quoted,
      UTF-8 encoding), a "/", and the string representation of the integral
      value of 漢字 (UTF-8 encoding) if there is a local stroke order diagram
      for the 漢字.  If no local stroke order diagram exists for the specified
      漢字 from the specified source, then the returned URL will refer to a
      remote stroke order diagram from the specified source.
  """
  assert len(漢字) == 1
  assert ord(漢字) in KANJI_RANGE
  assert source in RemoteSources

  パス = GetStrokeOrderDiagramPath(漢字, image_directory, source)
  return (
    RemoteSources[source][1](漢字)
     if パス is False
     else "/images/" + urllib.parse.quote(source) + "/" + str(ord(漢字))
   )

def ServeStrokeOrderDiagram(漢字, image_directory, source):
  """ Serve the locally-stored stroke order diagram for the specified 漢字.
      This function expects these parameters:

        漢字 :: str
          This is a string representation of the Unicode code point for the
          漢字 whose stroke order diagram will be served.
        image_directory :: str
          A path to the root image directory.  This directory must have been
          managed by the download-kanji-images.py tool.  This can be None.
        source :: str
          A stroke order diagram source.  This can be None.

      This function must be invoked while handling a GET request.

      If all of the parameters are valid, then this will serve the stroke
      order diagram for the specified 漢字: The return value will be the
      value returned by Bottle's static_file() function.  If either
      'image_directory' or 'source' is None but 漢字 is valid, then this
      function will return the empty string.  Otherwise, an HTTP error will
      be generated.
  """
  try:
    漢字 = chr(int(漢字))
  except Exception as e:
    abort(400, "invalid 漢字 encoding")
  if len(漢字) != 1:
    abort(400, "not a single-character 漢字")
  if ord(漢字) not in KANJI_RANGE:
    abort(400, "not 漢字")
  data = ""
  if image_directory is not None and source is not None:
    local_path = GetStrokeOrderDiagramPath(漢字, image_directory, source)
    if local_path is not False:
      data = static_file(os.path.basename(local_path), os.path.dirname(local_path))
  return data



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
    self.__num_cards = 0
    self.__num_due_cards = 0
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

  def CardPassed(self, card, log_writer):
    """ Note that the user successfully answered the specified card.
        Additionally, the user's performance with the card will be recorded
        via the specified log file writer.  A card's performance record has
        the following fields (in order):

          1. the current timestamp as returned by time.time();
          2. the SHA-1 hash of the byte representation of the card (that is,
             the SHA-1 hash of the result of constructing a bytes object from
             the card); and
          3. the number of times the user had to retry the card before he
             successfully answered it.

        If log_writer is None, then no performance data will be recorded."""
    self.__num_attempts += 1
    if card not in self.__retry_map:
      self.__num_passed_on_first_try += 1
    self.__cards.add(card)
    self.__num_left -= 1
    if log_writer is not None:
      log_writer.Write((time.time(), card.Hash, self.__retry_map.get(card, 0)))

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

  def MarkSucceeded(self, log_writer):
    """ Mark the current card (that is, the card that was last drawn) as
        "succeeded" (that is, the user answered it correctly).  This method
        will remove the card from the deck.  Additionally, it will record
        the user's performance with the card via the specified log
        file writer."""
    assert self.__current_card is not None
    assert not self.__current_card_marked
    self.__current_card_marked = True
    self.Statistics.CardPassed(self.__current_card, log_writer)

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

def CreateFlashcardStubMap(handler_setter_function, parser_crank_function, buckets, now):
  """ Parse flashcards and construct a dictionary mapping flashcard hashes to TFlashcardStubs.
      "Flashcards" are objects that have Hash() functions that return
      hexadecimal hash codes as strings.

      This method expects these parameters:

        handler_setter_function :: (TFlashcard -> None) -> None
          a function that takes its function parameter and makes it the function
          that the flashcard parser invokes to process parsed flashcards
        parser_crank_function :: None -> None
          a nullary function that completely executes the parser
        buckets :: [TLeitnerBucket]
          a list of TLeitnerBuckets
        now :: numeric
          a timestamp representing the present

  """
  hashes_to_stubs = {}
  def Handleカード(カード):
    stub = TFlashcardStub(カード.Hash)
    hashes_to_stubs[stub.Hash] = stub
    buckets[0].AddStub(stub, TFlashcardStub._NEVER_TOUCHED, now)
  handler_setter_function(Handleカード)
  parser_crank_function()
  return hashes_to_stubs

def ApplyStatsToStubMap(handler_setter_function, parser_crank_function, hashes_to_stubs, buckets, now):
  """ Parse flashcard performance log entries and adjust the TFlashcardStubs in the specified stub map accordingly.
      "Flashcards" are objects that have Hash() functions that return
      hexadecimal hash codes as strings.

      This method expects these parameters:

        handler_setter_function :: (stats-log-record -> None) -> None
          a function that takes its function parameter and makes it the function
          that the stats log parser invokes to process parsed stats records
        parser_crank_function :: None -> None
          a nullary function that completely executes the parser
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
      invalid flashcard stats record.

  """
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
  handler_setter_function(HandleLogEntry)
  parser_crank_function()
  return (num_new_cards, sum(bucket.DueCardCount for bucket in buckets))

class TCardDeckFactory(object):
  """ Instances of this class construct flashcard decks (TCardDeck objects).
      The cards are selected randomly from a flashcard file (usually a
      configuration file) after the pool of cards is decorated with performance
      data from a stats log file.

      This class relies heavily on CreateFlashcardHashToLeitnerBucketMap() and
      ApplyStatsLogToFlashcards()."""

  def __init__(self, flashcard_cf_file, new_cf_parser_cb, set_cf_handler_cb, stats_log_file, new_log_parser_cb, set_record_handler_cb, buckets):
    """ Construct a new factory.  'flashcard_cf_file' is the path to the
        flashcard file.  'new_cf_parser_cb' is a function (() -> Parser)
        that constructs a new parser to parse flashcards in 'flashcard_cf_file'.
        'set_cf_handler_cb' is a function ((Parser, (TFlashcard -> ())) -> ())
        that sets the specified parser's flashcard handler to the specified
        function.  'stats_log_file' is the path to the stats log file.
        'new_log_parser_cb' and 'set_record_handler_cb' are similar to
        'new_cf_parser_cb' and 'set_cf_handler_cb' except that they operate
        on log parsers.  'buckets' is a list of TLeitnerBuckets."""
    self.__flashcard_cf_file = flashcard_cf_file
    self.__new_cf_parser_cb = new_cf_parser_cb
    self.__set_cf_handler_cb = set_cf_handler_cb
    self.__new_log_parser_cb = new_log_parser_cb
    self.__leitner_buckets = buckets
    self.__now = time.time()

    # First, construct a map of flashcard hashes to flashcard stubs.
    parser = new_cf_parser_cb()
    def SetHandler(flashcard_handler):
      set_cf_handler_cb(parser, flashcard_handler)
    def ParserCrank():
      with open(flashcard_cf_file, "r") as f:
        parser.ParseStrings(f)
      parser.Finish()
    hashes_to_stubs = CreateFlashcardStubMap(SetHandler, ParserCrank, buckets, self.__now)
    self.__card_count = len(hashes_to_stubs)

    # Second, apply the stats file to the stubs.
    # This will change the Leitner buckets.
    parser = new_log_parser_cb()
    def SetHandler(record_handler):
      set_record_handler_cb(parser, record_handler)
    def ParserCrank():
      try:
        with open(stats_log_file, "r") as f:
          parser.ParseStrings(f)
        parser.Finish()
      except IOError as e:
        if e.errno != errno.ENOENT:
          raise e
    self.__num_new_cards, self.__num_due_cards = ApplyStatsToStubMap(SetHandler, ParserCrank, hashes_to_stubs, buckets, self.__now)
    assert self.__num_new_cards <= self.__num_due_cards # New cards are always due.
    self.__hashes_to_stubs = hashes_to_stubs
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
    parser = self.__new_cf_parser_cb()
    self.__set_cf_handler_cb(parser, OfferCard)
    with open(self.__flashcard_cf_file, "r") as f:
      parser.ParseStrings(f)
    parser.Finish()

    # Return the combined, shuffled results.
    combined_results = TRandomSelector(self.__card_count)
    combined_results.ConsumeSequence(YieldCards())
    return combined_results

  @property
  def Buckets(self):
    """a list of Leitner buckets"""
    return list(self.__leitner_buckets)

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

def GenerateCardHTML(handler_url, session_token, title, remaining_time_secs,
 head_creator, front_content_creator, back_content_creator, selectors_creator,
 stats_creator, bottom_creator):
  """ Construct a string containing a complete HTML document for displaying a
      flashcard.  The parameters are:

        handler_url :: str
          This is the URL that will handle form submissions.
        session_token :: str
          This is some value identifying the session.
        title :: string
          This is the HTML document's title.
        remaining_time_secs :: int
          This is the number of seconds left in the quiz or 0 if there is
          no timeout.
        head_creator :: (StringIO) => None
          This is a unary function that writes HTML to the specified StringIO
          buffer.  The HTML will show up in the generated page's <head> section.
          This can be None.
        front_content_creator :: (StringIO) => None
          This is a unary function that writes HTML to the specified StringIO
          buffer.  The HTML will show up in the <div> representing the front
          of the card.
        back_content_creator :: (StringIO) => None
          This is a unary function that writes HTML to the specified StringIO
          buffer.  The HTML will show up in the <div> representing the back
          of the card.
        selectors_creator :: (StringIO) => None
          This is a unary function that writes HTML to the specified StringIO
          buffer.  The HTML will appear after the back of the card but before
          the answer buttons.  This can be None.
        stats_creator :: (StringIO) => None
          This is a unary function that writes HTML to the specified StringIO
          buffer.  The HTML will appear in the <div> representing the
          stats area.
        bottom_creator :: (StringIO) => None
          This is a unary function that writes HTML to the specified StringIO
          buffer.  The HTML will appear after the card.  This can be None.

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

body {
  margin: 0px;
  padding: 0px;
  width: 100%;
  height: 100%;
}

div.toplevel {
  position: absolute;
  margin: auto;
  top: 0px;
  bottom: 0px;
  left: 0px;
  right: 0px;
  text-align: center;
  background: #c0c0c0;
  padding: 10px 15px;
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
  padding: 0.5em 0.5em;
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
    head_creator(buf)
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
  buf.write("""<body><div class="toplevel"><div class="card"><div class="front">""")
  front_content_creator(buf)
  buf.write('</div><div id="hidden_portion" style="visibility:hidden;"><div class="back">')
  back_content_creator(buf)
  buf.write('</div><div class="selectors">')
  if selectors_creator is not None:
    selectors_creator(buf)
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
  stats_creator(buf)
  buf.write("""</div></div>""")
  if bottom_creator is not None:
    bottom_creator(buf)
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
# Common tool functions
################################################################################

def ツールの設定ファイルを分析する(パス名, ルートの名前, settings_okay, ハンドラ):
  """ Parse the configuration file whose path is パス名.  This function expects
      the following parameters:

        パス名 :: str
        This is a path to a configuration file.
      ルートの名前 :: str
        This specifies the expected root name.
      settings_okay :: bool
        If this is True, then the root may contain settings; otherwise, this
        method will print an error message and terminate the program if the
        configuration file's root contains any settings.
      ハンドラ :: (section | setting, str, (str, int) => None) => None
        This specifies the handler that will process the configuration file's
        root's settings and sections.  The handler's second parameter is
        the resolved absolute path equivalent to パス名.  The handler's third
        parameter is an error function: It prints its first argument as an error
        message and terminates the program with the specified numeric error
        code, which defaults to 2.

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
  parser = TConfigurationDOMParser()
  try:
    with open(パス名, "r") as f:
      parser.ParseStrings(f)
    parser.Finish()
  except TConfigurationFormatError as e:
    sys.stderr.write("すみません、その設定ファイルは駄目です。\n")
    sys.stderr.write(str(e) + "\n")
    sys.exit(2)
  except Exception as e:
    sys.stderr.write("unexpected error while parsing the configuration file: " + str(e) + "\n")
    sys.exit(2)
  パス名 = os.path.abspath(os.path.dirname(パス名))

  # Extract sections and settings from the configuration file.
  # Check for errors.
  def PrintErrorAndExit(message, error_code=2):
    sys.stderr.write("すみません、その設定ファイルは駄目です。" + message + "\n")
    sys.exit(error_code)
  if parser.Root.Name != ルートの名前:
    PrintErrorAndExit("The root's name should be '" + ルートの名前 + "'.")
  if parser.Root.HasSettings and not settings_okay:
    PrintErrorAndExit("The root node cannot have settings.")

  # Process the configuration file's root's settings and sections.
  for child in parser.Root.Children:
    ハンドラ(child, パス名, PrintErrorAndExit)



