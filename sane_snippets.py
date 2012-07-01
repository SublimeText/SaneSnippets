import sublime
import sublime_plugin
import os
import re
from xml.etree import ElementTree as etree
from tempfile import mkstemp

template      = re.compile('^---$.^(.*?)^---$.^(.*)$', re.S | re.M)
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

    match = template.match(text)
    if match is None:
        raise SyntaxError("Unable to parse SaneSnippet")
    (header, content) = match.groups()
    snippet['content'] = content

    for line in header.splitlines():
        match = line_template.match(line)
        if match is None:
            raise SyntaxError("Unable to parse SaneSnippet header")
        (key, val) = match.groups()
        key = key.strip()
        if key in ('description', 'tabTrigger', 'scope'):
            snippet[key] = parse_val(val)
        else:
            raise SyntaxError('Unexpected SaneSnippet property: "%s"' % key)

    return snippet


def regenerate_snippet(path, onload=False):
    (name, ext) = os.path.splitext(os.path.basename(path))

    try:
        f = open(path, 'rb')
        snippet = parse_snippet(path, name, f.read())

    except Exception as e:
        msg  = isinstance(e, SyntaxError) and str(e) or "Error parsing SaneSnippet"
        msg += ' in file "%s"' % path
        if onload:
            # Sublime Text likes "hanging" itself when an error_message is pushed at initialization
            print msg
        else:
            sublime.error_message(msg)

        print e
        return

    finally:
        f.close()

    (f, path) = mkstemp(prefix=".%s." % snippet['description'],
                        suffix='.sane.sublime-snippet',
                        dir=os.path.dirname(snippet['path']))

    # print 'Writing SaneSnippet "%s" to "%s"' % (snippet['description'], path)
    # TODO: Prettify the XML structure before writing
    TreeDumper(snippet_to_xml(snippet)).write(path)


def regenerate_snippets(root=sublime.packages_path(), onload=False):
    # Check Packages folder
    for root, dirs, files in os.walk(root):

        # Unlink old snippets
        for basename in files:
            # TODO: Only regenerate if "previous" file's contents are equal
            if basename.endswith('.sane.sublime-snippet'):
                path = os.path.join(root, basename)
                try:
                    # TODO: Does not work on windows since Sublime Text ist "using" the file
                    os.remove(path)
                except:
                    # print "SaneSnippet: Unable to delete `%s`, file is probably in use (by Sublime Text)" % path
                    pass

            # Create new snippets
            if basename.endswith('.sane-snippet'):
                regenerate_snippet(os.path.join(root, basename), onload=onload)

# Go go gadget snippets! (run async?)
regenerate_snippets(onload=True)


# And watch for updated snippets
class SaneSnippet(sublime_plugin.EventListener):
    def on_post_save(self, view):
        fn = view.file_name()
        if (fn.endswith('.sane-snippet')):
            regenerate_snippets(os.path.dirname(fn))
