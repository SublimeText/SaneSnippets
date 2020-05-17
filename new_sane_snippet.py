import os

import sublime
import sublime_plugin

snippet_template = """---
description: ${1:Lorizzle}
tabTrigger:  ${2:lorizzle}
scope:       ${3:%s}
---
%s"""

# Should be "SaneSnippets", but do not rely on it
SYNTAX_FILE  = 'Packages/{}/SaneSnippet.tmLanguage'.format(__package__)


class SaneSnippetsNewCommand(sublime_plugin.TextCommand):
    """Creates a new buffer and inserts a scratch snippet for .sane-snippet files
    or uses the current selections for the new snippets' contents"""

    def new_sane_snippet(self, window, content=None, scope=None):
        v = window.new_file()
        v.set_syntax_file(SYNTAX_FILE)
        content = content.replace("$", R"\$") if content else '$0'
        v.run_command('insert_snippet', {'contents': snippet_template % (scope or 'text.plain', content)})

        # Default settings
        s = v.settings()
        s.set('default_dir', os.path.join(sublime.packages_path(), 'User'))

    def run(self, edit):
        v = self.view
        w = v.window()
        if any(v.sel()):
            for region in v.sel():
                if len(region):
                    scope = v.scope_name(region.begin())
                    # Strip the last scope (if there are more than 1)
                    scope = scope.strip().rsplit(' ', 1)[0]
                    self.new_sane_snippet(w, v.substr(region), scope)
        else:
            self.new_sane_snippet(w)


class SaneSnippetsNewContextCommand(SaneSnippetsNewCommand):
    """SaneSnippetsNewCommand with is_visible()"""

    def is_visible(self):
        return any(self.view.sel())
