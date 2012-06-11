
月詠 (Tsukuyomi): 漢字 (Kanji) Stroke Order Diagram Downloader
===============================================================

Summary
-------

This command line tool scans text files for 漢字 (kanji) characters and
downloads their stroke order diagrams (SODs) from one or more sources on the
Internet.  The tool organizes downloaded images into a simple directory
structure.  Other 月詠 tools can use the downloaded SODs instead of linking
to remote SODs provided through the Internet.  This sacrifices disk space to
reduce bandwidth consumption and the risk of inaccessible SODs due to failed
Internet connections or unavailable servers.

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
the downloaded SODs.  The configuration file should contain three sections:

1. _enabled-sources_: Each setting in this section specifies a remote source
   of 漢字 stroke order diagrams.  The downloader will only check and use
   these sources.  See the "Available Sources" section below for a list of
   acceptable sources.
2. _files_: Each setting in this section is the path to a file or directory
   that will be scanned for 漢字.  If a path refers to a directory, then all
   files in the directory's subtree will be scanned.
3. _general_: This section contains general downloader settings.

The _general_ section's settings are:

1. _image-directory_: This setting specifies a path to the directory that
   will contain downloaded SODs.  (See the Image Directories section for
   information about the layouts of image directories.)  The directory
   must exist.
2. _timeout_ (optional): This attribute specifies a positive integral
   timeout (in seconds) for downloads.  The default value is thirty seconds.

All paths in the configuration file are either absolute or relative to
the directory containing the configuration file.

Here is a sample configuration file:

>     [enabled-sources]
>     jisho.org
>     saiga-jp.com
>     
>     [files]
>     kotoba-flashcards
>     
>     [general]
>     image-directory: 漢字



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

