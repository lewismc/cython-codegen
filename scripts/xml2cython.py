#!/usr/bin/python

"""\
xml2cython: process xml files generated by gccxml and generate cython code

Usage:
    xml2cython header xmlfile

By default, xml2cython pull out every function available in the xmlfile. There
are some basic filter you can use to limit the functions pulled out:
    - -f/--filter-function-name: only pull out functions whose name match the
      given string.
    - -l/--location-filter: only pull out function which are declared in a file
      whose name matches the given string.

Example:
    xml2cython -f 'foo_' -l 'foo' header xmlfile

    Will only pull out functions whose name match foo_ and which are declared
    in file whose name match foo. Using regular expression instead of simple
    strings should work"""
import getopt
import sys
import re
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import cycodegenlib
from cycodegenlib.tp_puller import TypePuller
from cycodegenlib.misc import classify, query_items
from cycodegenlib.cycodegen import generate_cython

def generate_main(header, xml, output, lfilter=None, ffilter=None, funcs_list=None):
    items, named, locations = query_items(xml)

    output.write("cdef extern from '%s':\n" % header)

    funcs, tpdefs, enumvals, enums, structs, vars, unions = \
            classify(items, locations, lfilter=lfilter)

    if ffilter is None:
        ffilter = lambda x: True

    if funcs_list:
        kept_funcs = [i for i in funcs.values() if ffilter(i.name)  \
                                                   and i.name in funcs_list]
    else:
        kept_funcs = [i for i in funcs.values() if ffilter(i.name)]

    puller = TypePuller(items)
    for f in kept_funcs:
        puller.pull(f)

    needed = puller.values()

    # Order 'anonymous' enum values alphabetically
    def cmpenum(a, b):
        return cmp(a.name, b.name)
    anoenumvals = enumvals.values()
    anoenumvals.sort(cmpenum)

    # List of items to generate code for
    gen = list(needed) #+ kept_funcs
    generate_cython(output, gen, anoenumvals)

class Usage(Exception):
    def __init__(self, msg):
        self.msg = """\
usage: xml2cython [options] headerfile xmlfile

%s""" % msg

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # parse command line options
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "ho:l:f:i:V",
                                       ["help", "output", "location-filter",
                                        "function-name-filter",
                                        "input-file-filter", "--version"])
        except getopt.error, msg:
            raise Usage(msg)
    except Usage, e:
        print >>sys.stderr, e.msg
        print >>sys.stderr, "for help use --help"
        return 2

    # process options
    output = None
    lfilter_str = None
    ffilter_str = None
    ifilter = None
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            return 0
        elif o in ("-o", "--output"):
            output = a
        elif o in ("-l", "--location-filter"):
            lfilter_str = a
        elif o in ("-f", "--function-name-filter"):
            ffilter_str = a
        elif o in ("-i", "--input-file-filter"):
            ifilter = a
        elif o in ("-V", "--version"):
            print "xml2cython: use cycodegenlib version", cycodegenlib.version
            return 0

    if len(args) != 2:
        print >>sys.stderr, "Error, exactly one input file must be specified"
        print >>sys.stderr, "for help use --help"
        return 2

    header_input = args[0]
    xml_input = args[1]

    lfilter = None
    if lfilter_str:
        lfilter = re.compile(lfilter_str).search

    ffilter = None
    if ffilter_str:
        ffilter = re.compile(ffilter_str).search

    # Input file filter
    funcs = []
    if ifilter:
        a = open(ifilter, 'r')
        try:
            funcs.extend(a.read().splitlines())
        finally:
            a.close()

    # Generate cython code
    out = StringIO()
    try:
        generate_main(header_input, xml_input, out, lfilter=lfilter,
                      ffilter=ffilter, funcs_list=funcs)
        if output:
            f = open(output, 'w')
            try:
                f.write(out.getvalue())
            finally:
                f.close()
        else:
            print out.getvalue()
    finally:
        out.close()

if __name__ == '__main__':
    sys.exit(main())


# #root = 'asoundlib'
# #root = 'CoreAudio_AudioHardware'
# root = 'foo'
# header_name = '%s.h' % root
# #header_matcher = re.compile('alsa')
# header_matcher = re.compile(header_name)
# #header_matcher = re.compile('AudioHardware')
# xml_name = '%s.xml' % root
# pyx_name = '_%s.pyx' % root
# if sys.platform[:7] == 'darwin':
#     so_name = root
# else:
#     so_name = 'lib%s.so' % root
#
# items, named, locations = query_items(xml_name)
# funcs, tpdefs, enumvals, enums, structs, vars, unions = \
#         classify(items, locations, lfilter=header_matcher.search)
#
# #arguments = signatures_types(funcs.values())
# #print "Need to pull out arguments", [named[i] for i in arguments]
#
# puller = TypePuller(items)
# for f in funcs.values():
#     puller.pull(f)
#
# needed = puller.values()
# #print "Pulled out items:", [named[i] for i in needed]
#
# # Order 'anonymous' enum values alphabetically
# def cmpenum(a, b):
#     return cmp(a.name, b.name)
# anoenumvals = enumvals.values()
# anoenumvals.sort(cmpenum)
#
# # List of items to generate code for
# #gen = enumvals.values() + list(needed) + funcs.values()
# gen = list(needed) + funcs.values()
#
# #gen_names = [named[i] for i in gen]
#
# cython_code = [cy_generate(i) for i in gen]
#
# output = open(pyx_name, 'w')
# output.write("cdef extern from '%s':\n" % header_name)
# output.write("\tcdef enum:\n")
# for i in anoenumvals:
#     output.write("\t\t%s = %d\n" % (i.name, int(i.value)))
# for i in cython_code:
#     if not i:
#         continue
#     if len(i) > 1:
#         output.write("\t%s\n" % i[0])
#         for j in i[1:]:
#             output.write("\t%s\n" % j)
#     else:
#         output.write("\t%s\n" % i[0])
# output.close()
