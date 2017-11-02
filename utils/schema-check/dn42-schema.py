#!/usr/bin/env python3

from __future__ import print_function

import re
import os
import sys
import argparse
import log
import glob


SCHEMA_NAMESPACE = "dn42."


class SchemaDOM:
    src = None
    schema = None
    name = None
    ref = None

    def __init__(self, fn):
        self.src = fn
        f = FileDOM(fn)
        self.schema = self.__parse_schema(f)

    def __parse_schema(self, f):
        schema = {}
        for k, v, l in f.dom:
            if k == 'ref':
                self.ref = v
            elif k == 'schema':
                self.name = v

            if k != 'key':
                continue

            v = v.split()
            key = v.pop(0)
            schema[key] = set()
            for i in v:
                if i == ">":
                    break

                schema[key].add(i)

            for k, v in schema.items():
                if 'primary' in v:
                    schema[k].add("oneline")
                    if "multiline" in v:
                        schema[k].remove("multiline")
                    schema[k].add("single")
                    if "multiple" in v:
                        schema[k].remove("multiple")
                    schema[k].add("required")
                    if "optional" in v:
                        schema[k].remove("optional")
                    if "recommend" in v:
                        schema[k].remove("recommend")
                    if "deprecate" in v:
                        schema[k].remove("deprecate")

                if 'oneline' not in v:
                    schema[k].add("multiline")
                if 'single' not in v:
                    schema[k].add("multiple")

        return schema

    def check_file(self, f, lookups=None):
        status = "PASS"

        for k, v in self.schema.items():
            if 'required' in v and k not in f.keys:
                log.error(
                    "%s Line 0: Key [%s] not found and is required." % (f.src, k))
                status = "FAIL"
            elif 'recommend' in v and k not in f.keys:
                log.notice(
                    "%s Line 0: Key [%s] not found and is recommended." % (f.src, k))
                status = "NOTE"

            if 'schema' in v and SCHEMA_NAMESPACE + f.dom[0][0] != self.ref:
                log.error(
                    "%s Line 1: Key [%s] not found and is required as the first line." % (f.src, k))
                status = "FAIL"

            if 'single' in v and k in f.keys and len(f.keys[k]) > 1:
                log.warning("%s Line %d: Key [%s] first defined here and has repeated keys." % (
                    f.src, f.keys[k][0], k))
                for l in f.keys[k][1:]:
                    log.error(
                        "%s Line %d: Key [%s] can only appear once." % (f.src, l, k))
                    status = "FAIL"

            if 'oneline' in v and k in f.multi:
                for l in f.keys[k]:
                    log.error(
                        "%s Line %d: Key [%s] can not have multiple lines." % (f.src, l, k))
                    status = "FAIL"

        for k, v, l in f.dom:
            if k.startswith("x-"):
                log.info("%s Line %d: Key [%s] is user defined." % (f.src, l, k))

            elif k not in self.schema:
                log.error("%s Line %d: Key [%s] not in schema." % (f.src, l, k))
                status = "FAIL"
                continue
            else:
                if 'deprecate' in self.schema[k]:
                    log.info(
                        "%s Line %d: Key [%s] was found and is deprecated." % (f.src, l, k))
                    status = "INFO"

                if lookups is not None:
                    for o in self.schema[k]:
                        if o.startswith("lookup="):
                            refs = o.split("=", 2)[1].split(",")
                            val = v.split()[0]
                            found = False
                            for ref in refs:
                                if (ref, val) in lookups:
                                    found = True
                            if not found:
                                log.error("%s Line %d: Key %s references object %s in %s but does not exist." % (
                                    f.src, l, k, val, refs))
                                status = "FAIL"

        print("CHECK\t%-54s\t%s\tMNTNERS: %s" %(f.src, status, ','.join(f.mntner)))
        return status


class FileDOM:

    def __init__(self, fn):
        dom = []
        keys = {}
        multi = {}
        mntner = []
        last_multi = None
        schema = None
        src = fn

        with open(fn, "r") as f:
            for lineno, i in enumerate(f.readlines(), 1):

                if re.match(r'[ \t]', i):
                    dom[-1][1] += "\n" + i.strip()

                    if dom[-1][0] not in multi:
                        multi[dom[-1][0]] = []

                    if last_multi is None:
                        multi[dom[-1][0]].append(lineno)
                        last_multi = dom[-1][0]

                else:
                    i = i.split(":")
                    if len(i) < 2:
                        continue

                    dom.append([i[0].strip(), ':'.join(i[1:]).strip(), lineno])

                    if i[0].strip() not in keys:
                        keys[i[0].strip()] = []

                    keys[i[0].strip()].append(lineno)

                    last_multi = None

                if dom[-1][0] == 'use-schema':
                    schema = dom[-1][1]

                if dom[-1][0] == 'mnt-by':
                    mntner.append(dom[-1][1])

        self.dom = dom
        self.keys = keys
        self.multi = multi
        self.mntner = mntner
        self.schema = schema
        self.src = src

    def __str__(self):
        length = 13
        for i in self.dom:
            if len(i[0]) > length:
                length = len(i[0]) + 2
        s = ""
        for i in self.dom:
            l = i[1].split("\n")

            s += i[0] + ":" + " " * (length - len(i[0])) + l[0] + "\n"
            for m in l[1:]:
                s +=  " " * (length + 1) + m + "\n"

        return s
def main(infile, schema):

    log.debug("Check File: %s" % (infile))
    f = FileDOM(infile)

    if schema is not None:
        f.schema = schema
    else:
        f.schema = "schema/" + f.schema

    if f.schema is None:
        log.error("Schema is not defined for file")
        return False

    log.debug("Use Schema: %s" % (f.schema))

    s = SchemaDOM(f.schema)
    return s.check_file(f)


def check_schemas(path):
    schemas = {}
    for fn in glob.glob(path+"/*"):
        s = SchemaDOM(fn)
        log.info("read schema: %s" % (s.name))
        schemas[s.ref] = s

    ok = True
    c = schemas[SCHEMA_NAMESPACE + "schema"]
    for s in schemas.keys():
        ck = c.check_file(s)
        if not ck:
            ok = False

    return ok


def scan_index(infile, mntner=None):
    idx = {}
    schemas = {}

    with open(infile, 'r') as f:
        for line in f.readlines():
            line = line.split()
            idx[(line[0], line[1])] = line[2:]
            if line[0] == SCHEMA_NAMEPACE + 'schema':
                s = SchemaDOM(line[2])
                log.info("read schema: %s" % (s.name))
                schemas[s.ref] = s

    return __scan_index(idx, schemas, mntner)


def scan_files(path, mntner=None):
    arr = __index_files(path)

    idx = {}
    schemas = {}

    for line in arr:
        idx[(line[0], line[1])] = line[2:]
        if line[0] == SCHEMA_NAMESPACE + 'schema':
            s = SchemaDOM(line[2])
            log.info("read schema: %s" % (s.name))
            schemas[s.ref] = s

    return __scan_index(idx, schemas, mntner)

def __scan_index(idx, schemas, mntner):
    ok = True
    for k, v in idx.items():
        log.debug(k)
        mlist = []
        if len(v) > 1:
            mlist = v[1].split(",")

        if mntner is not None and mntner not in mlist:
            continue

        s = schemas.get(k[0], None)
        if s is None:
            log.error("No schema found for %s" % (k[1]))
            ok = False
            continue
        c = FileDOM(v[0])
        ck = s.check_file(c, idx.keys())
        if ck == "INFO" and ok != "FAIL":
            ok = ck
        if ck == "FAIL":
            ok = ck

    return ok


def __index_files(path):
    xlat = {
        "dns/":          SCHEMA_NAMESPACE + "domain",
        "inetnum/":      SCHEMA_NAMESPACE + "inetnum",
        "inet6num/":     SCHEMA_NAMESPACE + "inet6num",
        "route/":        SCHEMA_NAMESPACE + "route",
        "route6/":       SCHEMA_NAMESPACE + "route6",
        "aut-num/":      SCHEMA_NAMESPACE + "aut-num",
        "as-set/":       SCHEMA_NAMESPACE + "as-set",
        "as-block/":     SCHEMA_NAMESPACE + "as-block",
        "organisation/": SCHEMA_NAMESPACE + "organisation",
        "mntner/":       SCHEMA_NAMESPACE + "mntner",
        "person/":       SCHEMA_NAMESPACE + "person",
        "role/":         SCHEMA_NAMESPACE + "role",
        "tinc-key/":     SCHEMA_NAMESPACE + "tinc-key",
        "tinc-keyset/":  SCHEMA_NAMESPACE + "tinc-keyset",
        "schema/":       SCHEMA_NAMESPACE + "schema",
    }

    for root, dirs, files in os.walk(path):
        ignore = True
        for t in xlat.keys():
            if root+"/" == os.path.join(path, t):
               ignore = False
               break
        if ignore:
           continue

        for f in files:

            dom = FileDOM(os.path.join(root, f))

            for t, s in xlat.items():
                if dom.src.startswith(os.path.join(path, t)):
                    dom.schema = s

            yield (dom.schema, dom.src.split("/")[-1].replace("_", "/"), dom.src, ",".join(dom.mntner))


def index_files(path):
    idx = __index_files(path)
    for i in idx:
        print("%s\t%s\t%s\t%s" % i)


def get_args():
    """Get and parse command line arguments"""

    parser = argparse.ArgumentParser(
        description='Check Schema. Checks Schema of file for validity')
    parser.add_argument('--merge-output',
                        help="Merge stderr into stdout (helps when reading output with pagers) [Default OFF]",     action="store_true")
    parser.add_argument('-v',  '--verbose',
                        help="Enable verbose output [Default OFF]",        action="store_true")
    parser.add_argument('-vv', '--doubleVerbose',
                        help="Enable full verbose output [Default OFF]",   action="store_true")

    subparsers = parser.add_subparsers(help='sub-command help', dest="command")

    parser_file = subparsers.add_parser(
        'check-file', help='Process a specific file')
    parser_file.add_argument('-s',  '--use-schema',    nargs='?',
                             help="Override schema to validate [Default None]", action="store")
    parser_file.add_argument(
        'infile',                 nargs="?", help="File to check", type=str)

    parser_schema = subparsers.add_parser(
        'check-schemas', help='Validate all schemas')
    parser_schema.add_argument(
        'path',          nargs="?", help="Path for schemas", type=str)

    parser_index = subparsers.add_parser('index', help='Generate index')
    parser_index.add_argument(
        'path',  nargs="?", help="Path for dn42 data", type=str)

    parser_scanindex = subparsers.add_parser(
        'scan-index', help='Validate files in index')
    parser_scanindex.add_argument(
        'infile',  nargs="?", help="Index file to scan", type=str)
    parser_scanindex.add_argument('-m',  '--use-mntner', nargs='?',
                                  help="Only scan files that has MNT [Default None]", action="store")

    parser_scan = subparsers.add_parser('scan', help='Validate files in index')
    parser_scan.add_argument(
        'path',  nargs="?", help="Path for dn42 data", type=str)
    parser_scan.add_argument('-m',  '--use-mntner', nargs='?',
                             help="Only scan files that has a matching MNT [Default None]", action="store")

    parser_fmt = subparsers.add_parser('fmt', help='Format file')
    parser_fmt.add_argument(
        'infile',  nargs="?", help="Path for dn42 data file", type=str)
    parser_fmt.add_argument('-i',  '--in-place',
                             help="Format file in place", action="store_true")

    return vars(parser.parse_args())


if __name__ == '__main__':
    args = get_args()

    if args["merge_output"]:
        log.OUTPUT = sys.stdout

    if args["doubleVerbose"]:
        log.default.level_console = log.VERB_DEBUG
        log.default.level_full = True

    if args["verbose"]:
        log.default.level_console = log.VERB_INFO

    log.debug(args)

    valid = True
    if args["command"] == "check-file":
        valid = main(args["infile"], args["use_schema"])
        if valid:
            log.notice("Check %s: PASS" % (args["infile"]))
        else:
            log.fatal("Check %s: FAIL" % (args["infile"]))

    elif args["command"] == "check-schemas":
        valid = check_schemas(args["path"])

    elif args["command"] == "index":
        index_files(args["path"])

    elif args["command"] == "scan-index":
        scan_index(args["infile"], args["use_mntner"])

    elif args["command"] == "scan":
        import time
        log.notice("## Scan Started at %s" %(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())))
        ck = scan_files(args["path"], args["use_mntner"])
        log.notice("## Scan Completed at %s" %(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())))

        if ck == "INFO":
            sys.exit(2)
        elif ck == "FAIL":
            sys.exit(1)

    elif args["command"] == "fmt":
        dom = FileDOM(args["infile"])
        if args["in_place"]:
            with open(args["infile"], 'w+') as f:
                f.write(str(dom))

        print(str(dom))
