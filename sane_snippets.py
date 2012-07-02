import sublime
import sublime_plugin
import os
import re
import xml.etree.ElementTree as etree
from tempfile import mkstemp

template      = re.compile('^---$.^(.*?)^---$.^(.*)$', re.S | re.M)
line_template = re.compile('^(.*?):\s*(.*)$')


class ElementTreeCDATA(etree.ElementTree):
    """Subclass of ElementTree which handles CDATA blocks reasonably"""

    def _write(self, file, node, encoding, namespaces):
        """This method is for ElementTree <= 1.2.6"""

        if node.tag == '![CDATA[':
            text = node.text.encode(encoding)
            # escape ']]>' sequences by wrapping them into two CDATA sections
            # http://stackoverflow.com/questions/223652
            text = text.replace(']]>', ']]]]><![CDATA[')
            file.write("\n<![CDATA[%s]]>\n" % text)
        else:
            etree.ElementTree._write(self, file, node, encoding, namespaces)


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
    """Parse a .sane-snippet and return an dict with the snippet's data"""

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
            print msg
        else:
            sublime.error_message(msg)

        print e
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
        ElementTreeCDATA(snippet_to_xml(snippet)).write(f)

    finally:
        f.close()


def regenerate_snippets(root=sublime.packages_path(), onload=False):
    "Check the `root` dir for .sane-snippets and regenerate them while deleting .sane.sublime-snippets"

    for root, dirs, files in os.walk(root):
        for basename in files:
            # Remove old snippets
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
    """Rechecks the view's directory for .sane-snippets and regenerates them,
    if the saved file is a .sane-snippet

    Implements:
        on_post_save"""

    def on_post_save(self, view):
        fn = view.file_name()
        if (fn.endswith('.sane-snippet')):
            regenerate_snippets(os.path.dirname(fn))
