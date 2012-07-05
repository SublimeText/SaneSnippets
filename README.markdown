SaneSnippets for Sublime Text 2
===============================

SaneSnippets consist of text files with little bit of YAML front matter. They're
optimized for human readability, not XML parsers:

    ---
    description: Lorizzle
    tabTrigger:  lorizzle
    scope:       text.plain
    ---
    Lorizzle sure dolizzle sit amizzle, pot adipiscing shizznit. Nullizzle check
    out this velit, fo shizzle volutpizzle, suscipit quizzle, doggy vizzle,
    yippiyo. Pellentesque tellivizzle tortizzle. Sizzle erizzle. Mah nizzle
    izzle shizzle my nizzle crocodizzle sizzle dang tempizzle bizzle. Maurizzle
    pellentesque nibh et turpizzle. Shiz izzle gizzle. Pellentesque nizzle
    rhoncus i saw beyonces tizzles and my pizzle went crizzle. In daahng dawg
    habitasse cool boom shackalack. Brizzle dapibizzle. Curabitur nizzle
    pimpin', pretizzle da bomb, mattizzle ac, eleifend vitae, nunc. Mofo
    suscipizzle. We gonna chung sempizzle go to hizzle phat gizzle.


... because nobody likes hand-coding XML.

To use, add `.sane-snippet` files to any Sublime Text package. I personally keep
them in `User/Snippets`.


Installation
------------

### Using Sublime Package Control

Pick this option. Install via [Sublime Package Control](http://wbond.net/sublime_packages/package_control),
using the `Package Control: Install Package` menu item. Look for `SaneSnippets`
in the package list.

### Using Git

Clone SaneSnippets into your `Packages` directory:

    # cd to packages dir ...
    git clone https://github.com/bobthecow/sublime-sane-snippets.git SaneSnippets

### Download manually

 1. [Download the latest version](https://github.com/bobthecow/sublime-sane-snippets/zipball/master)
 2. Unzip and rename the folder to `SaneSnippets`
 3. Move the folder into your `Packages` directory.

----

The Packages directory is located at:

 * **Linux**:   `~/.Sublime Text 2/Packages/`
 * **OS X**:    `~/Library/Application Support/Sublime Text 2/Packages/`
 * **Windows**: `%APPDATA%/Sublime Text 2/Packages/`

Or type `sublime.packages_path()` into the console (`` Ctrl-` ``).


Usage
-----

Create `.sane-snippet` files anywhere in your Sublime Text Packages directory.
SaneSnippets (`sane.sublime-snippet`) will be regenerated every time you start
Sublime Text and their contents have changed. When you save a `.sane-snippet`
file using Sublime Text its containing directory will be rescaned for changed
SaneSnippets. This allows you to rename your snippets while still detecting and
deleting the old unused snippet (with no corresponding `.sane-snippet` file).

You can manually regenerate all SaneSnippets in the whole packages directory
with the `SaneSnippets: Regenerate SaneSnippets` command from the command
palette (`Ctrl+Shift+p`, `Cmd+Shift+p`) or the menu (*Tools > Packages >
SaneSnippets > Regenerate SaneSnippets*).


Contributors
------------

 * [FichteFoll](https://github.com/FichteFoll/)


License
-------

Copyright (c) 2011 Justin Hileman

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
