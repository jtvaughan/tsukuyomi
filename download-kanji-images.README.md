
月詠 (Tsukuyomi): 漢字 (Kanji) Stroke Order Diagram Downloader
===============================================================

Summary
-------

This command line tool scans 月詠 configuration and log files for 漢字 (kanji)
characters and downloads their stroke order diagrams (SODs) from one or more
sources on the Internet.  The tool organizes downloaded images into a simple
directory structure.  Other 月詠 tools can use the downloaded SODs instead
of linking to remote SODs provided through the Internet.  This sacrifices
disk space to reduce bandwidth consumption and the risk of inaccessible SODs
due to failed Internet connections or unavailable servers.

Note that it is your responsibility to ensure that you have permission to
download and use SODs.  Many of the images are copyrighted; please contact
their authors or maintainers and obtain their permission to download and use
the SODs before using this tool.



Running
-------

1. Download 月詠 if you have not already done so.

2. Open a console or terminal.

3. Navigate to the directory containing the downloaded code.  (You could
   execute the tool from any directory, but these instructions assume that
   you will execute the tool from within the directory in which the tool
   resides.  This simplifies the instructions.)

4. Run the following command:

   > `./download-kanji-images.py <config-file>`

   where `<config-file>` is the path to a configuration file describing
   the directory structure that will contain the downloaded SODs.  (See the
   Configuration Files section below for more information.)

   The tool will limit the number of simultaneous SOD downloads to the number
   of processors on your machine.  You can override this behavior through the
   `max-simultaneous-downloads` command line option:

   > `./download-kanji-images.py --max-simultaneous-downloads <max> <config-file>`

   where `<max>` is a positive number representing the maximum number
   of simultaneous SOD downloads.

   You should see something like this on your terminal:

         Found 138 漢字
         Finished downloading 言 from jisho.org
         Finished downloading 一 from jisho.org
         Finished downloading 頭 from jisho.org
         Finished downloading 事 from jisho.org
         Finished downloading 頭 from saiga-jp.com
         Finished downloading 言 from saiga-jp.com
         Finished downloading 同 from jisho.org
         Finished downloading 事 from saiga-jp.com
         [...]

   The terminal will display a "finished downloading" message for each SOD
   it downloads.  It might also display error messages for downloads that
   fail.  If an SOD is not available (e.g., the HTTP request for the SOD
   resulted in a 403 or 404 error), then nothing will be displayed for
   that SOD.

5. The tool will print "Done" on the terminal when it finishes.



Configuration Files
-------------------

The SOD downloader expects the user to provide a special configuration file
describing the tool's behavior and the structure of the directory containing
the downloaded SODs.  The configuration file's root must be named
"image-settings" and may contain the following attributes:

1. _image-directory_: This attribute specifies a path to the directory that
   will contain downloaded SODs.  (See the Image Directories section for
   information about the layouts of image directories.)  The directory
   must exist.
2. _configuration-files_ (optional): This section specifies zero or more
   paths to configuration files that will be scanned for 漢字.  漢字 within
   comments will be ignored.  This section must not contain subsections.
3. _log-files_ (optional): This section specifies zero or more paths to
   log files that will be scanned for 漢字.  漢字 within comments will be
   ignored.  This section must not contain subsections.
4. _enabled-sources_: This section specifies zero or more sources from which
   SODs will be downloaded.  See the Available Sources section for a list
   of recognized sources.
5. _timeout_ (optional): This attribute specifies a positive integral
   timeout (in seconds) for downloads.  The default value is thirty seconds.

All paths in the configuration file are either absolute or relative to
the directory containing the configuration file.

Here is a sample configuration file:

>     "image-settings" {
        "configuration-files" {
          "./flashcards.txt";
          "./config.txt"
        }
        "log-files" {
          "./flashcards.log"
        }
        "enabled-sources" {
          "jisho.org";
          "saiga-jp.com"
        }
        "image-directory" { "/home/tsukuyomi/img" }
        "timeout" { "45" }
    }



Available Sources
-----------------

The following strings are recognized sources for SODs and may appear within
configuration files' "enabled-sources" sections:

* [jisho.org](http://www.jisho.org)

* [saiga-jp.com](http://www.saiga-jp.com/kanji_dictionary.html)

* [sljfaq.org](http://kanji.sljfaq.org/kanjivg.html)

Remember, it is your responsibility to ensure that you have permission to
download and use the SODs from these sources.  Many of the images are
copyrighted; please contact the authors or maintainers of the sources
you would like to use and seek their permission before downloading any of
their SODs.

Also note that some of the sources might limit the number of SODs you may
download or the rate at which you may download them.  For example,
sljfaq.org usually returns single-byte image files when you exceed the
rate at which you may download its SODs.



Image Directories
-----------------

Each image directory contains one subdirectory for each source of its SODs.
A source subdirectory's name is the name of the source.  SODs from a particular
source are stored within the source's subdirectory.  Each SOD has the format

> `<字>.<extension>`

where `<字>` is the 漢字 character that the SOD describes and
`<extension>` is the SOD's file extension (e.g., "jpg" or "png").

For example, an image directory named "img" containing SODs for 漢 and 字 from
jisho.org and SODs for 日 and 本 from saiga-jp.com might look like this:

     img/
       jisho.org/
         漢.jpg
         字.jpg
       saiga-jp.com/
         日.png
         本.png



License
-------

See LICENSE for the license governing this tool.

