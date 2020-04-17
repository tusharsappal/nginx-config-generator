import re

INDENT = '    '


def bump_child_depth(obj, depth):
    children = getattr(obj, 'children', [])
    for child in children:
        child._depth = depth + 1
        bump_child_depth(child, child._depth)


class Conf(object):
    """
    Represents an nginx configuration.
    A `Conf` can consist of any number of server blocks, as well as Upstream
    and other types of containers. It can also include top-level comments.
    """

    def __init__(self, *args):
        """
        Initialize object.
        :param *args: Any objects to include in this Conf.
        """
        self.children = list(args)

    def add(self, *args):
        """
        Add object(s) to the Conf.
        :param *args: Any objects to add to the Conf.
        :returns: full list of Conf's child objects
        """
        self.children.extend(args)
        return self.children

    def remove(self, *args):
        """
        Remove object(s) from the Conf.
        :param *args: Any objects to remove from the Conf.
        :returns: full list of Conf's child objects
        """
        for x in args:
            self.children.remove(x)
        return self.children

    def filter(self, btype='', name=''):
        """
        Return child object(s) of this Conf that satisfy certain criteria.
        :param str btype: Type of object to filter by (e.g. 'Key')
        :param str name: Name of key OR container value to filter by
        :returns: full list of matching child objects
        """
        filtered = []
        for x in self.children:
            if name and isinstance(x, Key) and x.name == name:
                filtered.append(x)
            elif isinstance(x, Container) and x.__class__.__name__ == btype \
                    and x.value == name:
                filtered.append(x)
            elif not name and btype and x.__class__.__name__ == btype:
                filtered.append(x)
        return filtered

    @property
    def servers(self):
        """Return a list of child Server objects."""
        return [x for x in self.children if isinstance(x, Server)]

    @property
    def server(self):
        """Convenience property to fetch the first available server only."""
        return self.servers[0]

    @property
    def as_list(self):
        """Return all child objects in nested lists of strings."""
        return [x.as_list for x in self.children]

    @property
    def as_dict(self):
        """Return all child objects in nested dict."""
        return {'conf': [x.as_dict for x in self.children]}

    @property
    def as_strings(self):
        """Return the entire Conf as nginx config strings."""
        ret = []
        for x in self.children:
            if isinstance(x, Key):
                ret.append(x.as_strings)
            else:
                for y in x.as_strings:
                    ret.append(y)
        if ret:
            ret[-1] = re.sub('}\n+$', '}\n', ret[-1])
        return ret


class Container(object):
    """
    Represents a type of child block found in an nginx config.
    Intended to be subclassed by various types of child blocks, like
    Locations or Geo blocks.
    """

    def __init__(self, value, *args):
        """
        Initialize object.
        :param str value: Value to be used in name (e.g. regex for Location)
        :param *args: Any objects to include in this Conf.
        """
        self.name = ''
        self.value = value
        self._depth = 0
        self.children = list(args)
        bump_child_depth(self, self._depth)

    def add(self, *args):
        """
        Add object(s) to the Container.
        :param *args: Any objects to add to the Container.
        :returns: full list of Container's child objects
        """
        self.children.extend(args)
        bump_child_depth(self, self._depth)
        return self.children

    def remove(self, *args):
        """
        Remove object(s) from the Container.
        :param *args: Any objects to remove from the Container.
        :returns: full list of Container's child objects
        """
        for x in args:
            self.children.remove(x)
        return self.children

    def filter(self, btype='', name=''):
        """
        Return child object(s) of this Server block that meet certain criteria.
        :param str btype: Type of object to filter by (e.g. 'Key')
        :param str name: Name of key OR container value to filter by
        :returns: full list of matching child objects
        """
        filtered = []
        for x in self.children:
            if name and isinstance(x, Key) and x.name == name:
                filtered.append(x)
            elif isinstance(x, Container) and x.__class__.__name__ == btype \
                    and x.value == name:
                filtered.append(x)
            elif not name and btype and x.__class__.__name__ == btype:
                filtered.append(x)
        return filtered

    @property
    def locations(self):
        """Return a list of child Location objects."""
        return [x for x in self.children if isinstance(x, Location)]

    @property
    def keys(self):
        """Return a list of child Key objects."""
        return [x for x in self.children if isinstance(x, Key)]

    @property
    def as_list(self):
        """Return all child objects in nested lists of strings."""
        return [self.name, self.value, [x.as_list for x in self.children]]

    @property
    def as_dict(self):
        """Return all child objects in nested dict."""
        dicts = [x.as_dict for x in self.children]
        return {'{0} {1}'.format(self.name, self.value): dicts}

    @property
    def as_strings(self):
        """Return the entire Container as nginx config strings."""
        ret = []
        container_title = (INDENT * self._depth)
        container_title += '{0}{1} {{\n'.format(
            self.name, (' {0}'.format(self.value) if self.value else '')
        )
        ret.append(container_title)
        for x in self.children:
            if isinstance(x, Key):
                ret.append(INDENT + x.as_strings)
            elif isinstance(x, Container):
                y = x.as_strings
                ret.append('\n' + y[0])
                for z in y[1:]:
                    ret.append(INDENT + z)
            else:
                y = x.as_strings
                ret.append(INDENT + y)
        ret[-1] = re.sub('}\n+$', '}\n', ret[-1])
        ret.append('}\n\n')
        return ret


class Server(Container):
    """Container for server block configurations."""

    def __init__(self, *args):
        """Initialize."""
        super(Server, self).__init__('', *args)
        self.name = 'server'

    @property
    def as_dict(self):
        """Return all child objects in nested dict."""
        return {'server': [x.as_dict for x in self.children]}


class Location(Container):
    """Container for Location-based options."""

    def __init__(self, value, *args):
        """Initialize."""
        super(Location, self).__init__(value, *args)
        self.name = 'location'


class Upstream(Container):
    """Container for upstream configuration (reverse proxy)."""

    def __init__(self, value, *args):
        """Initialize."""
        super(Upstream, self).__init__(value, *args)
        self.name = 'upstream'


class Key(object):
    """Represents a simple key/value object found in an nginx config."""

    def __init__(self, name, value):
        """
        Initialize object.
        :param *args: Any objects to include in this Server block.
        """
        self.name = name
        self.value = value

    @property
    def as_list(self):
        """Return key as nested list of strings."""
        return [self.name, self.value]

    @property
    def as_dict(self):
        """Return key as dict key/value."""
        return {self.name: self.value}

    @property
    def as_strings(self):
        """Return key as nginx config string."""
        if self.value == '' or self.value is None:
            return '{0};\n'.format(self.name)
        if '"' not in self.value and (';' in self.value or '#' in self.value):
            return '{0} "{1}";\n'.format(self.name, self.value)
        return '{0} {1};\n'.format(self.name, self.value)


def loads(data, conf=True):
    """
    Load an nginx configuration from a provided string.
    :param str data: nginx configuration
    :param bool conf: Load object(s) into a Conf object?
    """
    f = Conf() if conf else []
    lopen = []
    index = 0

    while True:
        m = re.compile(r'^\s*server\s*{', re.S).search(data[index:])
        if m:
            s = Server()
            lopen.insert(0, s)
            index += m.end()
            continue

        m = re.compile(r'^\s*location\s*([^;]*?)\s*{', re.S).search(data[index:])
        if m:
            l = Location(m.group(1))
            lopen.insert(0, l)
            index += m.end()
            continue

        m = re.compile(r'^\s*upstream\s*([^;]*?)\s*{', re.S).search(data[index:])
        if m:
            u = Upstream(m.group(1))
            lopen.insert(0, u)
            index += m.end()
            continue

        m = re.compile(r'^\s*}', re.S).search(data[index:])
        if m:
            if isinstance(lopen[0], Container):
                c = lopen[0]
                lopen.pop(0)
                if lopen and isinstance(lopen[0], Container):
                    lopen[0].add(c)
                else:
                    f.add(c) if conf else f.append(c)
            index += m.end()
            continue

        double = r'\s*"[^"]*"'
        single = r'\s*\'[^\']*\''
        normal = r'\s*[^;\s]*'
        s1 = r'{}|{}|{}'.format(double, single, normal)
        s = r'^\s*({})\s*((?:{})+);'.format(s1, s1)
        m = re.compile(s, re.S).search(data[index:])
        if m:
            k = Key(m.group(1), m.group(2))
            if lopen and isinstance(lopen[0], (Container, Server)):
                lopen[0].add(k)
            else:
                f.add(k) if conf else f.append(k)
            index += m.end()
            continue

        m = re.compile(r'^\s*(\S+);', re.S).search(data[index:])
        if m:
            k = Key(m.group(1), '')
            if lopen and isinstance(lopen[0], (Container, Server)):
                lopen[0].add(k)
            else:
                f.add(k) if conf else f.append(k)
            index += m.end()
            continue

        break

    return f


def dumps(obj):
    """
    Dump an nginx configuration to a string.
    :param obj obj: nginx object (Conf, Server, Container)
    :returns: nginx configuration as string
    """
    return ''.join(obj.as_strings)


def dump(obj, fobj):
    """
    Write an nginx configuration to a file-like object.
    :param obj obj: nginx object (Conf, Server, Container)
    :param obj fobj: file-like object to write to
    :returns: file-like object that was written to
    """
    fobj.write(dumps(obj))
    return fobj


def dumpf(obj, path):
    """
    Write an nginx configuration to file.
    :param obj obj: nginx object (Conf, Server, Container)
    :param str path: path to nginx configuration on disk
    :returns: path the configuration was written to
    """
    with open(path, 'w') as f:
        dump(obj, f)
    return path
