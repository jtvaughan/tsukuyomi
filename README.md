
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

1. _Transparent, Portable Data Storage_: Application and user data should be
   easy to parse and migrate to other applications.
2. _Clarity_: Code and UIs should be thoroughly documented.
3. _Freedom_: Open-source software should be truly open.  Anyone and any
   thing should be able to download, distribute, modify, and use it freely
   (as in
   ["free speech" _and_ "free beer"](http://en.wikipedia.org/wiki/Gratis_versus_libre)).

In keeping with these principles, 月詠 features the following:

1. 月詠 has only a few third-party dependencies.  (See the next section
   for details.)
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
   standard, well-documented, easy-to-parse formats.
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

月詠 depends on these third-party libraries:

* [Jinja2](http://jinja.pocoo.org), a templating engine

At the time this was written, 月詠 runs on the stable release of Python 3 (3.2).
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

月詠 provides three tools:

* **言葉 Flashcards**: This web-facing tool starts a local web server that
  serves two-sided flashcards in a simple quiz with a modified
  [Leitner card scheduler](http://en.wikipedia.org/wiki/Leitner_system).
* **漢字 Stroke Order Diagram Downloader**: This command line tool scans
  configuration files (such as flashcard files) and logs for 漢字 characters
  and downloads stroke order diagrams from one or more sources on the Internet.
  Other 月詠 tools can link to the downloaded stroke order diagrams instead of
  those served by remote Internet servers to speed up web page rendering.
* **Two-Sided Flashcard Generator**: This command line tool transforms one
  or more strings of Japanese text into two-sided flashcards suitable for
  言葉 Flashcards flashcard files.  Each card's front is the unaltered
  Japanese text and its back is the text with kanji replaced by furigana
  wherever there are furigana annotations.
* **Furigana Delimiter Adder**: This command line tool copies standard input
  to standard output but adds a matching pair of furigana delimiters (the square
  brackets '[' and ']') after each kanji character.

Each tool is executed differently.  Please refer to each tool's README file
for instructions.

Please read the rest of this document before reading the tools' README files.
In particular, you must understand 月詠's file formats before you can use
the tools.



File Formats
------------

月詠 uses two kinds of files: configuration files and log files.
_Configuration files_ use the format parsed by Python's standard
[configparser](http://docs.python.org/py3k/library/configparser.html)
library.  Interpolation is disabled by default and settings with empty
values are permitted.  _Log files_ use the "unix" CSV dialect as
described by Python's standard
[csv](http://docs.python.org/py3k/library/csv.html) library.



Repository Layout
-----------------

Aside from its underlying [web framework], the core 月詠 algorithms reside
in a single Python file, `tsukuyomi.py`.  The major code sections are delimited
by wide horizontal rules.  Each tool resides in its own Python source file.
Web page templates, CSS, and JS files reside in the "templates" subdirectory.



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
