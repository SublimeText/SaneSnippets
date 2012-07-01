import sublime
import sublime_plugin
import os

snippet_template = """---
description: ${1:Lorizzle}
tabTrigger:  ${2:lorizzle}
scope:       ${3:text.plain}
---
%s"""

# Should be "SaneSnippets", but do not rely on it
package_name = os.path.relpath(os.getcwd(), sublime.packages_path())
syntax_file = 'Packages/%s/SaneSnippet.tmLanguage' % package_name


def view_has_selection(view):
    return any(len(region) for region in view.sel())


class NewSaneSnippetCommand(sublime_plugin.TextCommand):
    """Creates a new buffer and inserts a scratch snippet for .sane-snippet files"""

    def new_sane_snippet(self, window, content=None):
        v = window.new_file()
        v.settings().set('default_dir', os.path.join(sublime.packages_path(), 'User'))
        v.set_syntax_file(syntax_file)
        v.run_command('insert_snippet', { 'contents': snippet_template % (content or '$0') })
        v.set_scratch(True)

    def run(self, edit):
        w = self.view.window()
        if view_has_selection(self.view):
            for region in self.view.sel():
                if len(region):
                    self.new_sane_snippet(w, self.view.substr(region))
        else:
            self.new_sane_snippet(w)


class NewSaneSnippetContextCommand(NewSaneSnippetCommand):
    """The NewSaneSnippetCommand for menus (here: context menu), with is_enabled()"""

    def is_enabled(self):
        return self.has_selection()
