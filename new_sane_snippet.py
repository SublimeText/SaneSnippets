import sublime_plugin

snippet_template = """---
description: ${1:Lorizzle}
tabTrigger:  ${2:lorizzle}
scope:       ${3:text.plain}
---
$0"""

# And a command :)
class NewSaneSnippetCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir', 'Packages/User')
        v.settings().set('syntax', 'Packages/SaneSnippets/SaneSnippet.tmLanguage')
        v.run_command('insert_snippet', { 'contents': snippet_template })
        v.set_scratch(True)
