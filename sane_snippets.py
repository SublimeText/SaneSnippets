from io import StringIO
import logging
from pathlib import Path
import re

import sublime
import sublime_plugin

from sublime_lib import ResourcePath


# Set up logging for console output
logger = logging.getLogger(__package__)  # instead of __name__
formatter = logging.Formatter('[{name}] {levelname}: {message}', style='{')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


################################################################################
# XML helpers

# XML libraries suck and especially so the Python stdlib ones.
# Since we only use a very limited set of XML and don't need parsing,
# we implement a custom dumper

def _escape_xml(text):
    # copied from ElementTree._escape_cdata
    # it's worth avoiding do-nothing calls for strings that are
    # shorter than 500 characters, or so.  assume that's, by far,
    # the most common case in most applications.
    if "&" in text:
        text = text.replace("&", "&amp;")
    if "<" in text:
        text = text.replace("<", "&lt;")
    if ">" in text:
        text = text.replace(">", "&gt;")
    return text


def _escape_cdata(text):
    if "]]>" in text:
        text = text.replace(']]>', ']]$UNDEFINED>')
    return text


################################################################################
# XML helpers

class SaneSnippet:
    """Represent a sane snippet and define operations on it."""

    EXT_SANE = ".sane-snippet"
    EXT_SUBLIME = ".sane.sublime-snippet"

    HEADER_REGEX = re.compile(r'^(?P<key>\w+):\s*(?P<value>.*)$'
                              r'|^(?P<comment>#.*?)$|^(?P<empty>\s*)$')

    newline = "\n"

    def __init__(self, path):
        if not self.is_sane(path):
            raise ValueError("Unexpected extension", path)
        self.sane_path = path
        self.data = {}

    @property
    def sublime_path(self):
        return self.sane_path.with_suffix(self.EXT_SUBLIME)

    @classmethod
    def sane_path_for(cls, path):
        # cls.EXT_SUBLIME are two suffixes
        if not path.name.endswith(cls.EXT_SUBLIME):
            raise ValueError("Unexpected extension", path)
        return path.with_name(path.name.replace(cls.EXT_SUBLIME, cls.EXT_SANE))

    @classmethod
    def is_sane(cls, path):
        return path.suffix == cls.EXT_SANE

    @classmethod
    def is_sublime(cls, path):
        return path.suffix == cls.EXT_SUBLIME

    def write(self):
        """Write the snippet to its sublime_path."""
        if not self.data:
            logger.warning("Snippet wasn't loaded; loading now")
            self.read()

        with self.sublime_path.open('w', encoding='utf-8', newline=self.newline) as f:
            self.dump(f)

    def dump(self, file):
        """Write the snippet to the given file-like object."""
        print("<snippet>", file=file)
        for k, v in sorted(self.data.items()):  # order must be deterministic
            if k == 'content':
                # Leading and trailing newlines are ignored for content when inserting in ST
                print("\t<content><![CDATA[\n", _escape_cdata(v), "\n]]></content>", 
                      sep="", file=file)
            else:
                print("\t<", k, ">", _escape_xml(v), "</", k, ">", 
                      sep="", file=file)
        print("</snippet>", file=file)

    def read(self):
        """Read and parse the .sane-snippet file.

        Raise ValueError on parse errors and IOError on read errors.
        """
        with self.sane_path.open('r', encoding='utf-8') as f:
            text = f.read()
        lines = iter(text.splitlines())

        line = next(lines, None)
        if line == "---":
            line = next(lines, None)
        if line is None:
            raise ValueError("File is empty")

        # Parse frontmatter
        data = {}
        while line != "---":
            m = self.HEADER_REGEX.match(line)
            if m is None:
                raise ValueError("Unable to parse header {!r}".format(line))

            key, value = m.group('key').strip(), m.group('value').strip()
            if key:
                if key in {'description', 'tabTrigger', 'scope'}:
                    data[key] = value
                else:
                    raise ValueError("Unexpected SaneSnippet property: {!r}".format(key))

            line = next(lines, None)
            if line is None:
                raise ValueError("Header not terminated before EOF")

        with StringIO() as sio:
            line = next(lines, None)
            while line is not None:
                print(line, file=sio)
                line = next(lines, None)
            data['content'] = sio.getvalue().strip("\n")

        # Store in instance
        self.data = data
        if f.newlines:  # provided by io.TextIOBase
            if isinstance(f.newlines, str):
                self.newline = f.newlines
            else:
                self.newline = f.newlines[0]

    def has_changed(self):
        """Check the source and target files' mtimes."""
        try:
            return self.sane_path.stat().st_mtime > self.sublime_path.stat().st_mtime
        except OSError:
            return True


def regenerate_snippet(path, onload=False, force=False):
    snippet = SaneSnippet(path)
    if not (force or snippet.has_changed()):
        logger.debug("Skipping '%s'", path)
        return

    try:
        snippet.read()
    except IOError as e:
        logger.error("Error reading '%s'", path, exc_info=e)
        return
    except ValueError as e:
        msg = "Error parsing '{}'".format(path)
        logger.error(msg, exc_info=e)
        if not onload:
            sublime.error_message("SaneSnippets: {}\n\n{}".format(msg, e))
        return

    logger.info("Writing %s", snippet.sublime_path)
    try:
        snippet.write()
    except IOError as e:
        logger.error("Error writing '%s'", snippet.sublime_path, exc_info=e)


def glob_writable_resources(glob):
    """Find paths to resources that exist on the file system."""
    for res_path in ResourcePath.glob_resources(glob):
        path = res_path.file_path()
        if path.exists():
            yield path


def regenerate_snippets(onload=False, force=False):
    """Check the packages dir for EXT_SANESNIPPETs and regenerate them; write only if necessary

    Also delete parsed snippets that have no raw equivalent.
    """
    clean_snippets()

    for path in glob_writable_resources("*" + SaneSnippet.EXT_SANE):
        regenerate_snippet(path, onload, force)


def clean_snippets(all_=False):
    for path in glob_writable_resources("*" + SaneSnippet.EXT_SUBLIME):
        if all_ or not SaneSnippet.sane_path_for(path).exists():
            try:
                path.unlink()
                logger.info("Removed orphaned snippet '%s'", path)
            except IOError:
                logger.error("Unable to delete '%s', file is probably in use", path)


################################################################################
# ST interface

class SaneSnippetsListener(sublime_plugin.EventListener):
    """Regenerate the sane snippet of the currently saved source file."""
    def on_post_save(self, view):
        str_path = view.file_name()
        if not str_path:
            return
        path = Path(str_path)
        if SaneSnippet.is_sane(path):
            regenerate_snippet(path, force=True)


class SaneSnippetsRemoveCommand(sublime_plugin.WindowCommand):
    """Remove compiled sane snippet files."""
    def run(self):
        clean_snippets(all_=True)


class SaneSnippetsRegenerateCommand(sublime_plugin.WindowCommand):
    """Recheck the packages directory for .sane-snippets and regenerate them.

    If `force = True`, regenerate all snippets even if they weren't updated.
    """
    def run(self, force=False):
        regenerate_snippets(force=force)


def plugin_loaded():
    sublime.set_timeout_async(lambda: regenerate_snippets(onload=True), 0)


def plugin_unloaded():
    logger.removeHandler(handler)
