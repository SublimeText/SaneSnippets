import sublime
import sublime_plugin
import os
import re
import xml.etree.ElementTree as etree
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

ST2 = int(sublime.version()) < 3000
set_timeout = sublime.set_timeout if ST2 else sublime.set_timeout_async

EXT_SANESNIPPET  = ".sane-snippet"
EXT_SNIPPET_SANE = ".sane.sublime-snippet"

template = re.compile(
    r'''
        ---%(nl)s               # initial separator, newline {optional}
        (?P<header>.*?)%(nnl)s  # the header, named group for newline
        ---%(nl)s               # another separator, newline
        (?P<content>.*)         # the content - matches till the end of the string
    '''
    % dict(nl=r'(?:\r\n?|\n)', nnl=r'(?P<linesep>\r\n?|\n)'),
    re.S | re.X)
line_template = re.compile(r'^(?P<comment>#.*?)$|^(?P<key>\w+):\s*(?P<val>.*)$|^(?P<empty>\s*)$')


################################################################################
# XML dump only part

class ElementTreeCDATA(etree.ElementTree):
    """Subclass of ElementTree which handles CDATA blocks reasonably"""
    # http://stackoverflow.com/questions/174890

    def _write(self, f, node, encoding, namespaces):
        """This method is for ElementTree <= 1.2.6"""

        if node.tag == '![CDATA[':
            text = node.text.encode(encoding)
            f.write(_process_cdata(text))
        else:
            etree.ElementTree._write(self, f, node, encoding, namespaces)


def _process_cdata(cdata):
    # http://stackoverflow.com/questions/223652
    # ']]>' sequences should be escaped by wrapping them into two CDATA sections
    # However, this is not supported by ST as of 2220 and 3035. Instead, use a hack with
    # an undefined variable which ST will replace with ''.
    # See: https://github.com/SublimeText/UnofficialDocs/pull/29
    cdata = cdata.replace(']]>', ']]$UNDEFINED>')
    # cdata = cdata.replace(']]>', ']]]]><![CDATA[>')

    return "<![CDATA[%s]]>" % cdata

patched = 'sane_monkeypatched'

if hasattr(etree, '_serialize_xml') and not hasattr(etree._serialize_xml, patched):
    etree._original_serialize_xml = etree._serialize_xml

    def _serialize_xml(write, elem, qnames, namespaces):
        """This method is for ElementTree >= 1.3.0"""

        if elem.tag == '![CDATA[':
            write(_process_cdata(elem.text))
        else:
            etree._original_serialize_xml(write, elem, qnames, namespaces)

    setattr(_serialize_xml, patched, True)

    etree._serialize_xml = _serialize_xml


################################################################################
# XML helper functions

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


################################################################################
# The actual functions that do stuff

def parse_snippet(path, name, text):
    """Parse a .sane-snippet and return an dict with the snippet's data
    May raise SyntaxError (intended) or other unintended exceptions.
    @return dict() with snippet's data"""

    # Defaults
    snippet = {
        'path':        path,
        'name':        name,
        'description': name,
        'tabTrigger':  '',
        'scope':       '',
        'linesep':     os.linesep
    }

    def parse_val(text):
        return text.strip()

    match = template.match(text)
    if match is None:
        raise SyntaxError("Unable to parse SaneSnippet")
    m = match.groupdict()
    snippet['content'] = m['content']
    snippet['linesep'] = m['linesep']

    # Parse frontmatter
    for line in m['header'].splitlines():
        match = line_template.match(line)
        if match is None:
            raise SyntaxError("Unable to parse SaneSnippet header")
        m = match.groupdict()

        if not m['key']:
            # commented or empty line
            continue

        m['key'] = m['key'].strip()
        if m['key'] in ('description', 'tabTrigger', 'scope'):
            snippet[m['key']] = parse_val(m['val'])
        else:
            raise SyntaxError('Unexpected SaneSnippet property: "%s"' % m['key'])

    return snippet


def regenerate_snippet(path, onload=False):
    """Call parse_snippet() and be proud of it (and catch some exceptions)
    @return generated XML string or None"""

    (name, ext) = os.path.splitext(os.path.basename(path))
    try:
        with open(path, 'r') as f:
            read = f.read()
    except:
        print("SaneSnippet: Unable to read `%s`" % path)
        return None

    try:
        snippet = parse_snippet(path, name, read)
    except Exception as e:
        msg  = isinstance(e, SyntaxError) and str(e) or "Error parsing SaneSnippet"
        msg += " in file `%s`" % path
        if onload:
            # Sublime Text likes "hanging" itself when an error_message is pushed at initialization
            print("Error: " + msg)
        else:
            sublime.error_message(msg)
        if not isinstance(e, SyntaxError):
            print(e)  # print the error only if it's not raised intentionally

        return None

    # Leading and trailing newlines are ignored when inserting in ST, so we prettify here
    snippet['content'] = "{1}{0}{1}".format(snippet['content'].strip("\r\n"), snippet['linesep'])

    sio = StringIO()
    try:
        et = ElementTreeCDATA(snippet_to_xml(snippet))
        # TODO: Prettify the XML
        if ST2:
            et.write(sio)
        else:
            et.write(sio, encoding='unicode')
    except:
        print("SaneSnippet: Could not write XML data into stream for file `%s`" % path)
        raise
    else:
        return sio.getvalue()
    finally:
        sio.close()


def regenerate_snippets(root=None, onload=False, force=False):
    """Check the `root` dir for EXT_SANESNIPPETs and regenerate them; write only if necessary
    Also delete parsed snippets that have no raw equivalent"""

    if not root:
        root = sublime.packages_path()

    for root, dirs, files in os.walk(root):
        for basename in files:
            path = os.path.join(root, basename)
            (name, ext) = os.path.splitext(basename)

            # Remove parsed snippets that have no raw equivalent
            if basename.endswith(EXT_SNIPPET_SANE):
                sane_path = swap_extension(path)
                if not os.path.exists(sane_path):
                    try:
                        os.remove(path)
                    except:
                        print("SaneSnippet: Unable to delete `%s`, file is probably in use" % path)

                continue

            # Create new snippets
            if basename.endswith(EXT_SANESNIPPET):
                (sane_path, path) = (path, swap_extension(path))
                # Generate XML
                generated = regenerate_snippet(sane_path, onload=onload)
                if generated is None:
                    continue  # errors already printed

                # Check if snippet should be written
                write = force or not os.path.exists(path)
                # TODO: Check last modified date first, should be faster
                if not write:
                    try:
                        with open(path, 'r') as f:
                            read = f.read()
                    except:
                        print("SaneSnippet: Unable to read `%s`" % path)
                        continue

                    if read != generated:
                        write = True

                # Write the file
                if write:
                    try:
                        with open(path, 'w') as f:
                            f.write(generated)
                    except:
                        print("SaneSnippet: Unable to open `%s`" % path)


def swap_extension(path):
    "Swaps `path`'s extension between `EXT_SNIPPET_SANE` and `EXT_SANESNIPPET`"

    if path.endswith(EXT_SNIPPET_SANE):
        return path.replace(EXT_SNIPPET_SANE, EXT_SANESNIPPET)
    else:
        return path.replace(EXT_SANESNIPPET, EXT_SNIPPET_SANE)


################################################################################
# ST interface (event listeners, commands)

class SaneSnippet(sublime_plugin.EventListener):
    """Rechecks the view's directory for .sane-snippets and regenerates them,
    if the saved file is a .sane-snippet

    Implements:
        on_post_save"""

    def on_post_save(self, view):
        fn = view.file_name()
        if fn.endswith('.sane-snippet'):
            regenerate_snippets(os.path.dirname(fn))


# A command interface
class RegenerateSaneSnippetsCommand(sublime_plugin.WindowCommand):
    """Rechecks the packages directory for .sane-snippets and regenerates them
    If `force = True` it will regenerate all the snippets even if they weren't updated"""
    def run(self, force=True):
        regenerate_snippets(force=force)


################################################################################
# Init

def plugin_loaded():
    # Go go gadget snippets!
    set_timeout(regenerate_snippets(onload=True), 0)


def plugin_unloaded():
    if hasattr(etree, '_original_serialize_xml'):
        etree._serialize_xml = etree._original_serialize_xml
        del etree._original_serialize_xml


if ST2:
    plugin_loaded()

# ST2 backwards (and don't call it twice in ST3)
unload_handler = plugin_unloaded if ST2 else lambda: None
