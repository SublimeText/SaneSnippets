import sublime, sublime_plugin, os

snippet_template = """---
description: ${1:Lorizzle}
tabTrigger:  ${2:lorizzle}
scope:       ${3:text.plain}
---
$0"""

syntax_file = os.path.join(os.getcwd(), 'SaneSnippet.tmLanguage')

# And a command :)
class NewSaneSnippetCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir', os.path.join(sublime.packages_path(), 'User'))
        v.set_syntax_file(syntax_file)
        v.run_command('insert_snippet', { 'contents': snippet_template })
        v.set_scratch(True)
