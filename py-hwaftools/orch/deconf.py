#!/usr/bin/env python
'''A descending configuration parser.

This parser provides for composing a hierarchical data structure from
a Python (ConfigParser) configuration file.  It also allows for a more
flexible string interpolation than the base parser.

The file is parsed (see parse() function) by the usual ConfigParser
module and the resulting data is interpreted (see interpret()
function) into a dictionary.  Two special sections are checked.

 - [keytype] :: a mapping of a key name to a "section type"

 - [<name>] :: the starting point of interpretation, default <name> is "start"

The [keytype] section maps a key name to a section type.  When a key
is found in a section which matches a keytype key the key is
interpreted as a comma-separated list of section names and its value
in the keytype dictionary as a section type.  A section expresses its
type and name by starting with a line that matches "[<type> <name>]".
When a matching key is encountered the keytype mapping and the list of
names are used to set a list on that key in the returned data
structure which contains the result of interpreting the referred to
sections.

This interpretation continues until all potential sections have been
loaded.  Not all sections in the file may be represented in the
resulting data structure if they have not been referenced through the
keytype mechanism described above.

After interpretation the data structure is inflated (see inflate()
function).  The result is a new dictionary in which any daughter
dictionaries now contain all scalar, string (non-list, non-dictionary)
entries from all its mothers.

Finally, each dictionary in the hierarchy has all of its scalar,
string entries interpolated (see format_any() function).  This portion
of the dictionary is itself used as a source of "{variable}"
interpolation.  Infinite loops must be avoided.

By default a scalar, string value is formatted via its string format()
function.  A "formatter(string, **kwds)" function can be provided to
provide customized formatting.

This formatting continues until all possible interpolations have been
resolved.  Any unresolved ones will be retained.  This interpolation
is done on intermediate dictionaries but it is only the ones at leafs
of the hierarchy which are likely useful to the application.

Either a single filename or a list of filenames can be given for
parsing.  The [start] section may include a special key "includes" to
specify a list of other configuration files to also parse.  The files
are searched first in the current working directory, next in the
directories holding the files already specified and next from any
colon-separated list of directories specified by a DECONF_INCLUDE_PATH
environment variable.
'''

import os

def parse(filename):
    'Parse the filename, return an uninterpreted object'
    try:                from ConfigParser import SafeConfigParser
    except ImportError: from configparser import SafeConfigParser
    cfg = SafeConfigParser()
    cfg.optionxform = str       # want case sensitive
    cfg.read(filename)
    if isinstance(filename, type("")):
        filename = [filename]
    cfg.files = filename
    return cfg

def to_list(lst):
    return [x.strip() for x in lst.split(',')]

def get_first_typed_section(cfg, typ, name):
    target = '%s %s' % (typ, name)
    for sec in cfg.sections():
        if sec.startswith(target):
            return sec
    raise ValueError('No section: <%s> %s' % (typ,name))


def find_file(fname, others = None):
    '''Find file <fname> in current working directory, in the "others"
    directories and finally in a environment path variable
    DECONF_INCLUDE_PATH.'''

    dirs = ['.'] 
    if others:
        dirs += others
    dirs += os.environ.get('DECONF_INCLUDE_PATH','').split(':')

    for check in dirs:
        maybe = os.path.join(check, fname)
        if os.path.exists(maybe):
            return maybe
    return
    

def add_includes(cfg, sec):
    '''
    Resolves any "includes" item in section <sec> by reading the
    specified files into the cfg object.
    '''
    if not cfg.has_option(sec,'includes'):
        return

    inc_val = cfg.get(sec,'includes')
    inc_list = to_list(inc_val)
    if not inc_list:
        raise ValueError('Not includes: "%s"' % inc_val)
        return

    to_check = ['.']
    if hasattr(cfg, 'files') and cfg.files:
        already_read = cfg.files
        if isinstance(already_read, type('')):
            already_read = [already_read]
        other_dirs = map(os.path.realpath, map(os.path.dirname, already_read))
        to_check += other_dirs
    to_check += os.environ.get('DECONF_INCLUDE_PATH','').split(':')

    for fname in inc_list:
        fpath = find_file(fname, other_dirs)
        if not fpath:
            raise ValueError(
                'Failed to locate file: %s (%s)' % 
                (fname, ':'.join(other_dirs))
                )
        cfg.read(fpath)
        if hasattr(cfg, 'files'):
            cfg.files.append(fpath)
    return

def resolve(cfg, sec, **kwds):
    'Recursively load the configuration starting at the given section'

    add_includes(cfg, sec)

    secitems = dict(cfg.items(sec))

    secitems.update(kwds)
    # get special keytype section governing the hierarchy schema
    keytype = dict(cfg.items('keytype'))

    ret = {}
    for k,v in secitems.items():
        typ = keytype.get(k)
        if not typ:
            ret[k] = v
            continue
        lst = []
        for name in to_list(v):
            other_sec = get_first_typed_section(cfg, typ, name)
            other = resolve(cfg, other_sec)
            other.setdefault(typ,name)
            lst.append(other)
        ret[k] = lst
    return ret

def interpret(cfg, start = 'start', **kwds):
    '''
    Interpret a parsed file by following any keytypes, return raw data
    structure.

    The <start> keyword can select a different section to start the
    interpretation.  Any additional keywords are override or otherwise
    added to the initial section.
    '''
    return resolve(cfg, start, **kwds)

def format_flat_dict(dat, formatter = str.format, **kwds):
    kwds = dict(kwds)
    unformatted = dict(dat)
    formatted = dict()

    while unformatted:
        changed = False
        for k,v in list(unformatted.items()):
            try:
                new_v = formatter(v, **kwds)
            except KeyError:
                continue        # maybe next time
            except TypeError:   # can't be formatted
                new_v = v       # pretend we just did

            changed = True
            formatted[k] = new_v
            kwds[k] = new_v
            unformatted.pop(k)
            continue
        if not changed:
            break
        continue
    if unformatted:
        formatted.update(unformatted)
    return formatted

def format_any(dat, formatter = str.format, **kwds):
    if dat is None:
        return dat
    if isinstance(dat, type("")):
        try:
            return formatter(dat, **kwds)
        except KeyError:
            return dat
    if isinstance(dat, list):
        return [format_any(x, formatter=formatter, **kwds) for x in dat]
    flat = dict()
    other = dict()
    for k,v in dat.items():
        if isinstance(v, type("")):
            flat[k] = v
        else:
            other[k] = v
    ret = format_flat_dict(flat, formatter=formatter, **kwds)
    for k,v in other.items():
        v = format_any(v, formatter=formatter, **kwds)
        ret[k] = v
    return ret


def inflate(src, defaults = None):
    '''
    Copy scalar dictionary entries down the hierarchy to other
    dictionaries.
    '''
    if not defaults: defaults = dict()
    ret = dict()
    ret.update(defaults)
    ret.update(src)

    flat = dict()
    other = dict()
    for k,v in ret.items():
        if isinstance(v, type("")):
            flat[k] = v
        else:
            other[k] = v
    for key,lst in other.items():
        ret[key] = [inflate(x, flat) for x in lst]

    return ret

def load(filename, start = 'start', formatter = str.format, **kwds):
    '''
    Return the fully parsed, interpreted, inflated and formatted suite.
    '''
    cfg = parse(filename)
    data = interpret(cfg, start, **kwds)
    data2 = inflate(data)
    if not formatter:
        return data2
    data3 = format_any(data2, formatter=formatter, **kwds)
    return data3



### testing

def extra_formatter(string, **kwds):
    tags = kwds.get('tags')
    if tags:
        tags = [x.strip() for x in tags.split(',')]
        kwds.setdefault('tagsdashed',  '-'.join(tags))
        kwds.setdefault('tagsunderscore', '_'.join(tags))
    
    version = kwds.get('version')
    if version:
        kwds.setdefault('version_2digit', '.'.join(version.split('.')[:2]))
        kwds.setdefault('version_underscore', version.replace('.','_'))
        kwds.setdefault('version_nodots', version.replace('.',''))

    return string.format(**kwds)
    

def example_formatter(string, **kwds):
    '''
    Example to add extra formatting
    '''
    kwds.setdefault('prefix','/tmp/simple')
    kwds.setdefault('PREFIX','/tmp/simple')
    ret = extra_formatter(string, **kwds)

    return ret


def test():
    from pprint import PrettyPrinter
    pp = PrettyPrinter(indent=2)

    cfg = parse('deconf.cfg')
    data = interpret(cfg)
    data2 = inflate(data)
    data3 = format_any(data2)

    data4 = load('deconf.cfg')
    assert data3 == data4

    print ('INTERPRETED:')
    pp.pprint(data)
    print ('INFLATED:')
    pp.pprint(data2)
    print ('FORMATTED:')
    pp.pprint(data3)

def dump(filename, start='start', formatter=str.format):
    from pprint import PrettyPrinter
    pp = PrettyPrinter(indent=2)
    data = load(filename, start=start, formatter=example_formatter)
    print ('Starting from "%s"' % start)
    pp.pprint(data)

if '__main__' == __name__:
    import sys
    dump(sys.argv[1:])
