SaneSnippets for Sublime Text 2
===============================

SaneSnippets consist of text file with little bit of YAML front matter. They're
optimized for human readability, not plist parsers:

    ---
    description: Sample SaneSnippet
    tabTrigger:  sane
    scope:       text.plain
    ---
    sup_dawg:
        i_herd_you_like: yaml
        so_i:
            put: yaml
            in_your: yaml
        so_you:
            can: parse
            while_you: parse


... because nobody likes hand-coding XML.

To use, add `.sane-snippet` files to any SublimeText package. I personally keep
them in `User/Snippets`.


Installation
------------

Copy or clone SaneSnippets into your Sublime Text Packages directory:

    # cd to packages dir ...
    git clone git://github.com/bobthecow/sublime-sane-snippets.git SaneSnippets

----

The Packages directory is located at:

 * Windows:

        %APPDATA%/Sublime Text 2/Packages/

 * OS X:

        ~/Library/Application Support/Sublime Text 2/Packages/

 * Linux:

        ~/.Sublime Text 2/Packages/


Usage
-----


Create `.sane-snippet` files anywhere in your Sublime Text Packages directory


License
-------

Copyright (c) 2011 Justin Hileman

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
