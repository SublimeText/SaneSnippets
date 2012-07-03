import sublime
import sublime_plugin
import os
import re
import xml.etree.ElementTree as etree
from tempfile import mkstemp

template      = re.compile(r'''
                                ---%(nl)s               # initial separator, newline
                                (?P<header>.*?)%(nnl)s  # the header, named group for newline
                                ---%(nl)s               # another separator, newline
                                (?P<content>.*)         # the content - matches till the end of the string
                           ''' % dict(nl=r'(?:\r\n?|\n)', nnl=r'(?P<linesep>\r\n?|\n)'),
                           re.S | re.X)
line_template = re.compile(r'^(?P<key>.*?):\s*(?P<val>.*)$')


class ElementTreeCDATA(etree.ElementTree):
    """Subclass of ElementTree which handles CDATA blocks reasonably"""

    def __init__(self, elem, linesep='\n', *args, **kwargs):
        etree.ElementTree.__init__(self, elem, *args, **kwargs)
        self.linesep = linesep

    def _write(self, f, node, encoding, namespaces):
        """This method is for ElementTree <= 1.2.6"""

        if node.tag == '![CDATA[':
            text = node.text.encode(encoding)
            # escape ']]>' sequences by wrapping them into two CDATA sections
            # http://stackoverflow.com/questions/223652
            text = text.replace(']]>', ']]]]><![CDATA[>')
            # Windows seems to replace '\r\n' by '\n' when parsing the regexp (but using only '\n' in the regexp will fail).
            # Also, Windows replaces any '\n' write-time by '\r\n'. '\r' works as it should.
            f.write("%(ls)s<![CDATA[%(text)s]]>%(ls)s" % dict(text=text, ls=self.linesep))
        else:
            etree.ElementTree._write(self, f, node, encoding, namespaces)


def xml_append_node(s, tag, text, **kwargs):
    """This one is tough ..."""

    c = etree.Element(tag, **kwargs)
    c.text = text
    s.append(c)
    return s


def snippet_to_xml(snippet):
    """This one is tougher (btw I'm talking about etree.Elements here) ..."""

    s = etree.Element('snippet')
    for key in ['description', 'tabTrigger', 'scope']:
        xml_append_node(s, key, snippet[key])

    s.append(xml_append_node(etree.Element('content'), '![CDATA[', snippet['content']))
    return s


def parse_snippet(path, name, text):
    """Parse a .sane-snippet and return an dict with the snippet's data
    May raise SyntaxError (intended) or other unintended exceptions."""

    snippet = {
        'path':        path,
        'name':        name,
        'description': name,
        'tabTrigger':  '',
        'scope':       '',
        'linesep':     os.linesep
    }

    def parse_val(text):
        # TODO: handle quoted strings.
        return text.strip()

    match = template.match(text)
    if match is None:
        raise SyntaxError("Unable to parse SaneSnippet")
    m = match.groupdict()
    snippet['content'] = m['content']
    snippet['linesep'] = m['linesep']

    for line in m['header'].splitlines():
        match = line_template.match(line)
        if match is None:
            raise SyntaxError("Unable to parse SaneSnippet header")
        m = match.groupdict()
        m['key'] = m['key'].strip()
        if m['key'] in ('description', 'tabTrigger', 'scope'):
            snippet[m['key']] = parse_val(m['val'])
        else:
            raise SyntaxError('Unexpected SaneSnippet property: "%s"' % m['key'])

    return snippet


def regenerate_snippet(path, onload=False):
    "Call parse_snippet() and be proud of it (and catch some exceptions)"

    (name, ext) = os.path.splitext(os.path.basename(path))
    try:
        f = open(path, 'r')
        snippet = parse_snippet(path, name, f.read())

    except Exception as e:
        msg  = isinstance(e, SyntaxError) and str(e) or "Error parsing SaneSnippet"
        msg += ' in file "%s"' % path
        if onload:
            # Sublime Text likes "hanging" itself when an error_message is pushed at initialization
            print "Error: " + msg
        else:
            sublime.error_message(msg)
        if not isinstance(e, SyntaxError):
            print e  # print the error only if it's not raised intentionally

        return

    finally:
        f.close()

    try:
        (fd, path) = mkstemp(prefix=".%s." % snippet['description'],
                            suffix='.sane.sublime-snippet',
                            dir=os.path.dirname(snippet['path']),
                            text=True)
        f = os.fdopen(fd, 'w')

        # print 'Writing SaneSnippet "%s" to "%s"' % (snippet['description'], path)
        # TODO: Prettify the XML structure before writing
        ElementTreeCDATA(snippet_to_xml(snippet), linesep=snippet['linesep']).write(f)

    finally:
        f.close()


def regenerate_snippets(root=sublime.packages_path(), onload=False):
    "Check the `root` dir for .sane-snippets and regenerate them while deleting .sane.sublime-snippets"

    for root, dirs, files in os.walk(root):
        for basename in files:
            # Remove old snippets
            # TODO: Only regenerate if "previous" file's contents are not equal
            if basename.endswith('.sane.sublime-snippet'):
                path = os.path.join(root, basename)
                try:
                    os.remove(path)
                except:
                    print "SaneSnippet: Unable to delete `%s`, file is probably in use" % path
                    pass

            # Create new snippets
            if basename.endswith('.sane-snippet'):
                regenerate_snippet(os.path.join(root, basename), onload=onload)

# Go go gadget snippets! (run async?)
regenerate_snippets(onload=True)


# And watch for updated snippets
class SaneSnippet(sublime_plugin.EventListener):
    """Rechecks the view's directory for .sane-snippets and regenerates them,
    if the saved file is a .sane-snippet

    Implements:
        on_post_save"""

    def on_post_save(self, view):
        fn = view.file_name()
        if (fn.endswith('.sane-snippet')):
            regenerate_snippets(os.path.dirname(fn))
