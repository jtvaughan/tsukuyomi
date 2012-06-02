
月詠 (Tsukuyomi)
=================

Summary
-------

月詠 (Tsukuyomi) is a set of [Python](http://www.python.org/) tools for
learning [the Japanese language](http://en.wikipedia.org/wiki/Japanese_language).
It is meant to supplement individuals' learning tools, not to
function as a complete learning suite like
[Rosetta Stone](http://www.rosettastone.com/).  It is coded to be
_useful_ but not necessarily _easy to use_ for average computer users.
If you can run Python commands on a terminal, then you can use 月詠.

月詠 is [the god of the moon](http://en.wikipedia.org/wiki/Tsukuyomi-no-Mikoto)
in [Shinto](http://en.wikipedia.org/wiki/Shinto) mythology.



Introduction
------------

月詠 is a loose collection of command line and web-facing tools for learning
Japanese.  It could, in principle, be tailored to help people learn any
language, but its algorithms are specially designed for processing Japanese
text.  As mentioned above, 月詠 is designed to be useful but not necessarily
easy to use for average computer users.  However, anyone who can
run Python commands from terminals can use 月詠.


### Guiding Principles

A few principles guide 月詠:

1. _Minimalism_: Do not waste time building general-purpose frameworks
   or pretty [UI](http://en.wikipedia.org/wiki/User_interface)s for
   one-off projects: Useful abstractions can be generalized and UIs can
   be improved later.  Instead, focus on _solving problems_ with sensible,
   straightforward, correct code and ensuring that UIs are _functional_.
   Do not make applications more complex than they need to be.
2. _Transparent, Portable Data Storage_: Application and user data should be
   easy to parse and migrate to other applications.
3. _Clarity_: Code and UIs should be thoroughly documented.
4. _Freedom_: Open-source software should be truly open.  Anyone and any
   thing should be able to download, distribute, modify, and use it freely
   (as in
   ["free speech" _and_ "free beer"](http://en.wikipedia.org/wiki/Gratis_versus_libre)).

In keeping with these principles, 月詠 features the following:

1. 月詠 has no external dependencies other than the standard Python
   interpreter: You do not need to download and manage a mess of
   third-party libraries.
2. 月詠 is not an Internet-facing application.  Its web-facing tools are
   single-[threaded](http://en.wikipedia.org/wiki/Thread_(computer_science\)),
   [blocking](http://en.wikipedia.org/wiki/Blocking_(computing\)),
   single-[session](http://en.wikipedia.org/wiki/Session_(computer_science\)),
   local [web applications](http://en.wikipedia.org/wiki/Web_application).
   In fact, they are only web applications because web browsers are perfect
   front-ends for graphical applications.  In other words, is easy to
   design nice, functional UIs in
   [HTML5](http://en.wikipedia.org/wiki/HTML5),
   [CSS](http://en.wikipedia.org/wiki/CSS), and
   [Javascript](http://en.wikipedia.org/wiki/Javascript).
   ([HTML5's ruby tag](http://www.w3schools.com/html5/tag_ruby.asp) is
   especially handy.)
3. All 月詠 modules are thoroughly documented.  Undocumented functions
   and out-of-date documentation are treated as bugs.
4. All data is read from and written to plain text files with
   well-documented, easy-to-parse formats.
5. Aside from its underlying [web framework], the core
   月詠 classes and functions are organized into a single Python source file.
   Each tool has its own script file.
6. Unless noted otherwise, all of 月詠 has been released to the
   [public domain](http://en.wikipedia.org/wiki/Public_domain).
   This means that the files are not copyrighted: You can download,
   distribute, modify, and use them any way you like.


### Why Yet Another Learning Tool?

Why am I, the author, writing 月詠 even though there are other free learning
tools, such as [Anki](http://ankisrs.net/) and
[Mnemosyne](http://www.mnemosyne-proj.org/)?

1. Neither project adheres to all of the aforementioned principles.
   I used Anki and Mnemosyne for a while but thought Anki was too
   complex and Mnemosyne was too generic.  Both are designed to appeal to
   large, diverse audiences: All I need is a tool or two that I can
   use to learn Japanese.
2. Mnemosyne is almost dead.
3. Anki is split across several repositories that are rarely synchronized.
   I have tried in vain to load Anki decks created via the latest
   Anki desktop release into the latest Android release on my tablet.
   There should be one repository with synchronized updates to all
   supported platforms.
4. I despise using [SQLite](http://www.sqlite.org/) to
   store and retrieve flashcards.  I want to be able to easily edit my
   flashcard files with a text editor.
5. I want to use several different kinds of tools to aid my language studies,
   not just flashcards.
6. I want to separate flashcards from performance data.  The two are stored
   in separate files.
7. I like writing my own software.  I understand exactly how the software
   works and I can tailor it to fit my needs.  Besides, I think I can
   write decent software.



Requirements
------------

In keeping with the principle of minimalism, 月詠 has no external
dependencies other than the standard Python libraries.  At the time
this was written, 月詠 runs on the stable release of Python 3 (3.2).
It has not been tested with other versions of Python or any interpreters
other than [CPython](http://www.python.org), the standard interpreter.

For those of you who are still stuck in Python 2.x land: Get over it.
Python 3 is the present and the future.

月詠 serves HTML5 web pages, so you will need to use
[a web browser that supports HTML5](http://html5test.com/results/desktop.html).
In particular, the browser should render ruby-annotated text properly, or else
Japanese text with [furigana](http://en.wikipedia.org/wiki/Furigana) will be
difficult to read.

If the following text is rendered as a single line with a ton of
parentheses (that is, the furigana does not render properly), then you
will need to use another web browser:

> # <ruby>日<rp>(</rp><rt>に</rt><rp>)</rp></ruby><ruby>本<rp>(</rp><rt>ほん</rt><rp>)</rp></ruby><ruby>語<rp>(</rp><rt>ご</rt><rp>)</rp></ruby>を<ruby>勉<rp>(</rp><rt>べん</rt><rp>)</rp></ruby><ruby>強<rp>(</rp><rt>きょう</rt><rp>)</rp></ruby>しましょう！</ruby>

Consider using [Google's Chrome browser](https://www.google.com/chrome),
which natively supports furigana.

It should go without saying that you will need a Chinese or
[Japanese font](http://www.wazu.jp/gallery/Fonts_Japanese.html)
with [UTF-8](http://en.wikipedia.org/wiki/UTF-8) support.  If the above
line of Japanese text renders as a bunch of garbled characters, then you
do not have such a font or it is not your browser's default
[sans-serif font](http://en.wikipedia.org/wiki/Serif).



Tools
-----

月詠 provides two tools:

* **言葉 Flashcards**: This web-facing tool starts a local web server that
  serves two-sided flashcards in a simple quiz with a modified
  [Leitner card scheduler](http://en.wikipedia.org/wiki/Leitner_system).
* **漢字 Stroke Order Diagram Downloader**: This command line tool scans
  configuration files (such as flashcard files) and logs for 漢字 characters
  and downloads stroke order diagrams from one or more sources on the Internet.
  Other 月詠 tools can link to the downloaded stroke order diagrams instead of
  those served by remote Internet servers to speed up web page rendering.

Each tool is executed differently.  Please refer to each tool's README file
for instructions.

Please read the rest of this document before reading the tools' README files.
In particular, you must understand 月詠's file formats before you can use
the tools.



File Formats
------------

月詠 uses two kinds of files: configuration files and log files.


### Configuration Files

_Configuration files_ are structured UTF-8 text files that represent data
as nodes within [trees](http://en.wikipedia.org/wiki/Tree_structure).
They are similar to [XML](http://en.wikipedia.org/wiki/XML) and
[HTML](http://en.wikipedia.org/wiki/HTML) files but are
much easier to edit, parse, and read.

There are two fundamental entities in configuration files:

1. _Settings_: A _setting_ is a chunk of text.
2. _Sections_: A _section_ is a chunk of text containing zero or more
   settings and sections.

Here is a simplified [grammar](http://en.wikipedia.org/wiki/Context-free_grammar)
describing configuration files (`configuration-file` is the
[start symbol](http://en.wikipedia.org/wiki/Context-free_grammar#Formal_definitions)):

>     configuration-file = section

>     section = DOUBLE-QUOTE TEXT DOUBLE-QUOTE OPENING-BRACE section-contents CLOSING-BRACE

>     section-contents =
        EMPTY |
        section section-contents |
        setting SEMICOLON section-contents |
        setting

>     setting = DOUBLE-QUOTE TEXT DOUBLE-QUOTE

>     DOUBLE-QUOTE = '"'
>     OPENING-BRACE = '{'
>     CLOSING-BRACE = '}'
>     SEMICOLON = ';'

There are two special
[terminals](http://en.wikipedia.org/wiki/Context-free_grammar#Formal_definitions)
in the grammar.  `EMPTY` means what it
says: It is an empty string (no characters).  `TEXT` is any arbitrary
string of characters in which every occurrence of `DOUBLE-QUOTE` is
escaped by a prefixed backslash ('\').  (Any character can be escaped with a
backslash.)  For example, the string

>     Why is \"Hello, world!\" the universal first program?

is a valid `TEXT` terminal because every `DOUBLE-QUOTE` is properly
escaped.  When the escapes are removed, the text becomes:

>     Why is "Hello, world!" the universal first program?

But

>     I said, "Hello, world!"

is not a valid `TEXT` terminal because there are unescaped `DOUBLE-QUOTE`s
within the string.

Configuration files may contain comments.  A comment begins with
`@` or `#` and proceeds to the end of the line (that is, up to and
including the next newline [`\n`] in the file).  Comments cannot occur
within `TEXT` terminals.  Comments are ignored by 月詠, so they can
contain any valid UTF-8 text.

There are a few things to note about configuration files:

1. Every configuration file has exactly one top-level section called
   the _root section_ (or simple the _root_).  XML and HTML are similar in
   this respect.
2. The `TEXT` preceding a section's `OPENING-BRACE` is called the
   section's _name_.
3. A section cannot contain sections with the same name.
   In other words, if configuration files are viewed as trees with
   sections as nodes, then two sections with the same name cannot have
   the same parent.
4. A section other than the root containing no sections and at most
   one setting is called an _attribute_.  An attribute's setting is called
   the attribute's _value_.  If an attribute does not contain a setting,
   then it is said to have an _empty value_.
5. The order in which settings and sections appear within a section's
   `section-contents` might be relevant depending on how the file is
   interpreted by applications.  XML and HTML are also similar in
   this respect.
6. Configuration files do not have anything resembling XML and HTML
   DTDs, namespaces, schemas, or entities.
7. Whitespace, including line breaks, is captured in `TEXT` terminals but
   is ignored everywhere else.


### Log Files

_Log files_ are semi-structured UTF-8 text files that represent data
as fields within records.  They are similar to
[`/etc/passwd`](http://en.wikipedia.org/wiki//etc/passwd) files
in [*NIX operating systems](http://en.wikipedia.org/wiki/*NIX).

There are two fundamental entities in log files:

1. _Fields_: A _field_ is a chunk of text.
2. _Records_: A _record_ is a [tuple](http://en.wikipedia.org/wiki/Tuple)
   of one or more fields.

Here is a simplified [grammar](http://en.wikipedia.org/wiki/Context-free_grammar)
describing log files (`log-file` is the
[start symbol](http://en.wikipedia.org/wiki/Context-free_grammar#Formal_definitions)):

>     log-file = record-list

>     record-list = EMPTY | NEWLINE record-list | record record-list

>     record = field NEWLINE | possibly-empty-field COLON trailing-fields NEWLINE

>     field = TEXT

>     empty-field = EMPTY

>     possibly-empty-field = empty-field | field

>     trailing-fields = empty-field | possibly-empty-field COLON trailing-fields

>     COLON = ':'
>     NEWLINE = '\n'

There are two special
[terminals](http://en.wikipedia.org/wiki/Context-free_grammar#Formal_definitions)
in the grammar.  `EMPTY` means what it
says: It is an empty string (no characters).  `TEXT` is any arbitrary
string of characters, including whitespace.  Any character can be escaped with a
backslash.  For example, the string

>     Why is "Hello, world!" the universal first program?  This is why\:
>     it's easy.

is a valid `TEXT` terminal.

Log files may contain comments.  A comment begins with
`@` or `#` and proceeds to the end of the line (that is, up to and
including the next `NEWLINE` in the file).  Comments cannot occur
within `TEXT` terminals.  Comments are ignored by 月詠, so they can
contain any valid UTF-8 text.

Note that all whitespace except `NEWLINE` is captured in `TEXT` terminals.
`NEWLINE`s may be escaped.  Lines containing nothing but whitespace are
considered records, each containing a single `FIELD` holding the whitespace
found on the line.  Whitespace at the end of a line is considered part of that
line's record's last field.



Repository Layout
-----------------

Aside from its underlying [web framework], the core 月詠 algorithms reside
in a single Python file, `tsukuyomi.py`.  The major code sections are delimited
by wide horizontal rules.  Each tool resides in its own Python source file.



Authors
-------

I, Joodan Van, wrote 月詠 to help myself learn Japanese.  I am
[publishing it on GitHub](https://github.com/joodan-van-github/tsukuyomi)
so that others may use it.  Of course, I welcome suggestions
and contributions. (^_^)



Licenses
--------

The following text applies to all files in the repository unless
noted otherwise below:

> This is free and unencumbered software released into the public domain.

> Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

> In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

> For more information, please refer to <http://unlicense.org/>.

The file [bottle.py](http://bottlepy.org/) is governed by this license:

> Copyright (c) 2011, Marcel Hellkamp.

> Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

> The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.



[web framework]: http://bottlepy.org/ "Bottle"
