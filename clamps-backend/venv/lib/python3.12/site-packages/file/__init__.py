import sys

from ._libmagic import ffi as _ffi
from ._libmagic import lib as _lib

__version__ = "__version__ = '0.3.0'"

MAGIC_NONE = 0x000000  # No flags
MAGIC_DEBUG = 0x000001  # Turn on debugging
MAGIC_SYMLINK = 0x000002  # Follow symlinks
MAGIC_COMPRESS = 0x000004  # Check inside compressed files
MAGIC_DEVICES = 0x000008  # Look at the contents of devices
MAGIC_MIME_TYPE = 0x000010  # Return the MIME type
MAGIC_CONTINUE = 0x000020  # Return all matches
MAGIC_CHECK = 0x000040  # Print warnings to stderr
MAGIC_PRESERVE_ATIME = 0x000080  # Restore access time on exit
MAGIC_RAW = 0x000100  # Don't translate unprintable chars
MAGIC_ERROR = 0x000200  # Handle ENOENT etc as real errors
MAGIC_MIME_ENCODING = 0x000400  # Return the MIME encoding
MAGIC_MIME = MAGIC_MIME_TYPE | MAGIC_MIME_ENCODING
MAGIC_APPLE = 0x000800  # Return the Apple creator and type

MAGIC_NO_CHECK_COMPRESS = 0x001000  # Don't check for compressed files
MAGIC_NO_CHECK_TAR = 0x002000  # Don't check for tar files
MAGIC_NO_CHECK_SOFT = 0x004000  # Don't check magic entries
MAGIC_NO_CHECK_APPTYPE = 0x008000  # Don't check application type
MAGIC_NO_CHECK_ELF = 0x010000  # Don't check for elf details
MAGIC_NO_CHECK_TEXT = 0x020000  # Don't check for text files
MAGIC_NO_CHECK_CDF = 0x040000  # Don't check for cdf files
MAGIC_NO_CHECK_TOKENS = 0x100000  # Don't check tokens
MAGIC_NO_CHECK_ENCODING = 0x200000  # Don't check text encodings

MAGIC_NO_CHECK_FORTRAN = 0x000000  # Don't check ascii/fortran
MAGIC_NO_CHECK_TROFF = 0x000000  # Don't check ascii/troff


class cached_property(object):
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


class Magic(object):
    _cookie = None

    def __init__(self, flags=MAGIC_MIME_TYPE, database=None):
        self._flags = flags
        self._database = database
        self._lib = _lib

    @cached_property
    def _cookie(self):
        return magic_open(self._flags)

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, *exc_info):
        if self._cookie is not None:
            self._lib.magic_close(self._cookie)
            self._cookie = None

    def __del__(self):
        self.__exit__()

    def setflags(self, flags):
        return magic_setflags(self._cookie, flags)

    def file(self, path):
        return magic_file(self._cookie, path)

    def buffer(self, value):
        return magic_buffer(self._cookie, value)

    def load(self, database=None):
        if database is None:
            database = self._database
        magic_load(self._cookie, database)


def magic_setflags(cookie, flags):
    status = _lib.magic_setflags(cookie, flags)
    if status != 0:
        raise ValueError(magic_error(cookie))


def magic_error(cookie):
    return _ffi.string(_lib.magic_error(cookie))


def magic_open(flags):
    cookie = _lib.magic_open(flags)
    if cookie == _ffi.NULL:
        raise RuntimeError(magic_error(cookie))
    else:
        return cookie


def magic_close(cookie):
    _lib.magic_close(cookie)


def magic_load(cookie, path=None):
    if path is None:
        path = _ffi.NULL
    status = _lib.magic_load(cookie, path)
    if status != 0:
        raise ValueError(magic_error(cookie))


def magic_file(cookie, path):
    if not isinstance(path, bytes):
        path = path.encode(sys.getfilesystemencoding())
    result = _lib.magic_file(cookie, path)
    if result == _ffi.NULL:
        raise ValueError(magic_error(cookie))
    else:
        return _ffi.string(result).decode('utf8')


def magic_buffer(cookie, value):
    result = _lib.magic_buffer(cookie, value, len(value))
    if result == _ffi.NULL:
        raise ValueError(magic_error(cookie))
    else:
        return _ffi.string(result).decode('utf8')
