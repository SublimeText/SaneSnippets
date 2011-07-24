import sublime, sublime_plugin, os

snippet_template = """---
description: ${1:Lorizzle}
tabTrigger:  ${2:lorizzle}
scope:       ${3:text.plain}
---
$0"""

syntax_file = os.path.join(os.getcwd(), 'SaneSnippet.tmLanguage')

class NewSaneSnippetCommand(sublime_plugin.TextCommand):
	def new_sane_snippet(self, content=None):
		v = self.view.window().new_file()
		v.settings().set('default_dir', os.path.join(sublime.packages_path(), 'User'))
		v.set_syntax_file(syntax_file)
		v.run_command('insert_snippet', { 'contents': snippet_template.replace('$0', content or '$0') })
		v.set_scratch(True)

	def run(self, edit):
		worked = False
		for region in self.view.sel():
			if (len(region)):
				self.new_sane_snippet(self.view.substr(region))
				worked = True
		if not worked:
			self.new_sane_snippet()

class NewSaneSnippetContextCommand(NewSaneSnippetCommand):
	def is_enabled(self):
		for region in self.view.sel():
			if (len(region)):
				return True