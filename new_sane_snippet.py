import sublime, sublime_plugin, os

snippet_template = """---
description: ${1:Lorizzle}
tabTrigger:  ${2:lorizzle}
scope:       ${3:text.plain}
---
$0"""

syntax_file = os.path.join(os.getcwd(), 'SaneSnippet.tmLanguage')

class NewSaneSnippetCommand(sublime_plugin.TextCommand):
	def has_selection(self):
		return any(len(region) for region in self.view.sel())

	def new_sane_snippet(self, window, content=None):
		v = window.new_file()
		v.settings().set('default_dir', os.path.join(sublime.packages_path(), 'User'))
		v.set_syntax_file(syntax_file)
		v.run_command('insert_snippet', { 'contents': snippet_template.replace('$0', content or '$0') })
		v.set_scratch(True)

	def run(self, edit):
		w = self.view.window()
		if self.has_selection():
			for region in self.view.sel():
				if (len(region)):
					self.new_sane_snippet(w, self.view.substr(region))
		else:
			self.new_sane_snippet(w)

class NewSaneSnippetContextCommand(NewSaneSnippetCommand):
	def is_enabled(self):
		return self.has_selection()
