import sublime
import sublime_plugin
import os

snippet_template = """---
description: ${1:Lorizzle}
tabTrigger:  ${2:lorizzle}
scope:       ${3:%s}
---
%s"""

# Should be "SaneSnippets", but do not rely on it
PACKAGE_NAME = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
SYNTAX_FILE  = 'Packages/%s/SaneSnippet.tmLanguage' % PACKAGE_NAME


def view_has_selection(view):
    return any(len(region) for region in view.sel())


class NewSaneSnippetCommand(sublime_plugin.TextCommand):
    """Creates a new buffer and inserts a scratch snippet for .sane-snippet files
    or uses the current selections for the new snippets' contents"""

    def new_sane_snippet(self, window, content=None, scope=None):
        v = window.new_file()
        v.set_syntax_file(SYNTAX_FILE)
        content = content.replace("$", "\$") if content else '$0'
        v.run_command('insert_snippet', {'contents': snippet_template % (scope or 'text.plain', content)})

        # Default settings
        s = v.settings()
        s.set('default_dir', os.path.join(sublime.packages_path(), 'User'))
        s.set('translate_tabs_to_spaces', False)  # Use tabs because they are translated if necessary

    def run(self, edit):
        v = self.view
        w = v.window()
        if view_has_selection(v):
            for region in v.sel():
                if len(region):
                    scope = v.scope_name(region.begin())
                    # Strip the last scope (if there are more than 1)
                    scope = scope.rsplit(' ', 1)[0]
                    self.new_sane_snippet(w, v.substr(region), scope)
        else:
            self.new_sane_snippet(w)


class NewSaneSnippetContextCommand(NewSaneSnippetCommand):
    """NewSaneSnippetCommand for menus (here: context menu), with is_enabled()"""

    def is_enabled(self):
        return view_has_selection(self.view)
