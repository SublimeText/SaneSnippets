import sublime
import sublime_plugin
import os
import re
from xml.etree import ElementTree as etree
from tempfile import mkstemp

template      = re.compile('^---%(n)s(.*?)%(n)s---%(n)s(.*)$' % {'n': os.linesep}, re.S)
line_template = re.compile('^(.*?):\s*(.*)$')


def CDATA(text=None):
    element = etree.Element(CDATA)
    element.text = text
    return element


class TreeDumper(etree.ElementTree):
    def _write(self, file, node, encoding, namespaces):
        if node.tag is CDATA:
            text = node.text.encode(encoding)
            file.write("<![CDATA[%s]]>" % text)
        else:
            etree.ElementTree._write(self, file, node, encoding, namespaces)


def snippet_to_xml(snippet):
    s = etree.Element('snippet')
    for key in ['description', 'tabTrigger', 'scope']:
        c = etree.Element(key)
        c.text = snippet[key]
        s.append(c)
    c = etree.Element('content')
    c.append(CDATA(snippet['content']))
    s.append(c)
    return s


def parse_snippet(path, name, text):
    snippet = {
        'path':        path,
        'name':        name,
        'description': name,
        'tabTrigger':  None,
        'scope':       None,
    }

    def parse_val(text):
        # TODO: handle quoted strings.
        return text.strip()

    try:
        (frontmatter, content) = template.match(text).groups()
        snippet['content'] = content
        for line in frontmatter.split(os.linesep):
            (key, val) = line_template.match(line).groups()
            key = key.strip()
            if key in ['description', 'tabTrigger', 'scope']:
                snippet[key] = parse_val(val)
            else:
                sublime.error_message('Unexpected SaneSnippet property: "%s" in file "%s"' % (key, path))
                return
    except Exception:
        sublime.error_message("Error parsing SaneSnippet in file \"%s\"" % path)

    return snippet


def regenerate_snippets():
    snippets = []

    # Check Packages folder
    for root, dirs, files in os.walk(sublime.packages_path()):

        # Unlink old snippets
        for name in files:
            try:
                if name.endswith('.sane.sublime-snippet'):
                    os.unlink(os.path.join(root, name))
            except:
                pass

        # Create new snippets
        for name in files:
            try:
                if name.endswith('.sane-snippet'):
                    path = os.path.join(root, name)
                    f = open(path, 'rb')
                    snippets.append(parse_snippet(path, os.path.splitext(name)[0], f.read()))
                    f.close()

            except:
                pass

    # Dump new snippets
    for snippet in snippets:
        (f, path) = mkstemp(prefix=".%s." % snippet['description'], suffix='.sane.sublime-snippet', dir=os.path.dirname(snippet['path']))
        # print 'Writing SaneSnippet "%s" to "%s"' % (snippet['description'], path)
        TreeDumper(snippet_to_xml(snippet)).write(path)

# Go go gadget snippets!
regenerate_snippets()


# And watch for updated snippets
class SaneSnippet(sublime_plugin.EventListener):
    def on_post_save(self, view):
        if (view.file_name().endswith('.sane-snippet')):
            regenerate_snippets()
