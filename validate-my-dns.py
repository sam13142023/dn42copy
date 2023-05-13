#!/usr/bin/env python3

# NOTE: for configuration see below imports

import time
import json
import subprocess
import os
import sys
import struct
import base64
import hashlib
import threading
from multiprocessing.dummy import Pool as ThreadPool

try:
    import dns.name
    import dns.query
    import dns.dnssec
    import dns.message
    import dns.resolver
    import dns.rdatatype
    import dns.rcode
except ImportError:
    print()
    print("CRITICAL: this script requires the 'dnspython' library, please install it using `python3 -m pip install dnspython`")
    print()
    exit(1)
# import exceptions so they could be try/catched
import binascii
import dns.exception

# --- start configuration

# path to the registry repo
REGISTRY_PATH = "."
# amounts of seconds to wait for a reply
TIMEOUT = 3
# amount of threads to use when scanning dns servers
THREADS = 16

# --- end configuration

# counter of errors that occured
errors = 0

# global summary object (used for final summary): {"domain": [success, dnssec-fail, wrong NS, wrong SOA, NX-DOMAIN, refused, timeout]}
summary = {}

# indexes for the summary list
class SUMMARY:
    SUCCESS = 0
    DNSSEC_FAIL = 1
    WRONG_NS = 2
    WRONG_SOA = 3
    NXDOMAIN = 4
    REFUSED = 5
    SERVFAIL = 6
    TIMEOUT = 7


# step1:


def get_domain_by_mntner(mntner):
    """get a list of domains (and reverse ipv4/6) if a nserver is specified"""
    global errors

    # grep for the given mntner in the dns,inetnum,inet6num directory of the registry and split it into a list; replace // with / in case REGISTRY_PATH ends with /
    dns_files = subprocess.Popen(["grep", "-Ril", f" {mntner}", f"{REGISTRY_PATH}/data/dns/"],
                                 stdout=subprocess.PIPE).communicate()[0].decode().replace("//", "/").split("\n")[:-1]
    inetnums_files = subprocess.Popen(["grep", "-Ril", f" {mntner}", f"{REGISTRY_PATH}/data/inetnum/"],
                                      stdout=subprocess.PIPE).communicate()[0].decode().replace("//", "/").split("\n")[:-1]
    inet6nums_files = subprocess.Popen(
        ["grep", "-Ril", f" {mntner}", f"{REGISTRY_PATH}/data/inet6num/"], stdout=subprocess.PIPE).communicate()[0].decode().split("\n")[:-1]

    # domains dict containing dns objects and inet(6)nums if they have nserver specified
    domains = {}

    def _parse_nserver(line):
        global errors
        nserver = line[20:].split(" ")
        # handle edge case where
        if "\t" in nserver[0]:
            print(
                f"WARN: nserver line is not following expected schema. atempting to guess: {line}")
            errors += 1
            nserver = nserver[0].split("\t")
        # has more than one space between nserver fqdn and its ip
        if len(nserver) > 2:
            print(
                f"WARN: nserver line is not following expected schema. atempting to guess: {line}")
            errors += 1
            nserver = [nserver[0], line[20:].replace(nserver[0], "").strip()]
        # ignore registry-sync nservers
        if "registry-sync.dn42" in nserver[0]:
            # TODO: parse registry-sync ips
            nserver = nserver[0]
            if nserver.endswith("ipv4.registry-sync.dn42"):
                nserver = [nserver, ".".join(nserver.replace(
                    ".ipv4.registry-sync.dn42", "").split(".")[::-1])]
            elif nserver.endswith("ipv6.registry-sync.dn42"):
                _ip6 = nserver.replace(
                    ".ipv6.registry-sync.dn42", "").replace(".", "")[::-1]
                nserver = [nserver, ":".join(
                    a+b+c+d for a, b, c, d in zip(_ip6[::4], _ip6[1::4], _ip6[2::4], _ip6[3::4]))]
            return nserver

        # nserver should be defined in an other dns file
        if len(nserver) == 1:
            return [nserver[0], None]
        # nserver is defined in this file
        elif len(nserver) == 2:
            return nserver

    # read dns files
    for domain in dns_files:
        with open(domain) as d:
            domain_name = domain.split("/")[-1]
            # a dictionary for each domain with "nserver": {"ns1.domain.dn42": ["ns1 ipv4", "ns1 ipv6"], ...}, "ds-rdata": ["123 45 67 ...", "98 7 65 ..."]
            domains[domain_name] = {"nserver": {}, "ds-rdata": []}
            for line in d.readlines():
                line = line.replace("\n", "")
                if line.startswith("nserver"):
                    _tmp = _parse_nserver(line)
                    if _tmp == "break":
                        break
                    if _tmp[1] == None:
                        domains[domain_name]["nserver"][_tmp[0]] = None
                    elif _tmp[0] in domains[domain_name]["nserver"]:
                        domains[domain_name]["nserver"][_tmp[0]].append(
                            _tmp[1])
                    else:
                        domains[domain_name]["nserver"][_tmp[0]] = [_tmp[1]]

                elif line.startswith("ds-rdata:"):
                    ds_rdata = line[20:].lower()
                    _split = ds_rdata.split(" ")
                    if len(_split) == 5:
                        ds_rdata = f"{_split[0]} {_split[1]} {_split[2]} {_split[3] + _split[4]}"
                    domains[domain_name]["ds-rdata"].append(ds_rdata)
    # load inetnums
    for inetnum in inetnums_files:
        # temp variables in case there is no nserver
        _nserver = {}
        _ds_rdatas = []
        _domain_name = ""
        with open(inetnum) as i4:
            for line in i4.readlines():
                line = line.replace("\n", "")
                if line.startswith("cidr"):
                    line = line[20:]
                    _domain_name = ".".join(
                        line.split(".")[::-1]) + ".in-addr.arpa"
                    if int(line.split("/")[1]) == 24:
                        _domain_name = _domain_name.replace("0/24.", "")
                    elif int(line.split("/")[1]) == 16:
                        _domain_name = _domain_name.replace("0/16.0.", "")
                    elif int(line.split("/")[1]) == 8:
                        _domain_name = _domain_name.replace("0/8.0.0.", "")
                    elif int(line.split("/")[1]) <= 24:
                        # TODO: implement creation of multiple zones for every /24 within
                        print(
                            f"WARN: currently only ipv4 subnets with length >=24 or 16 or 8 are possible to be checked: relavent inetnum {line}")
                        break
                elif line.startswith("nserver"):
                    _tmp = _parse_nserver(line)
                    if _tmp == "break":
                        break
                    if _tmp[0] in _nserver:
                        print(
                            f"ERROR: nserver {_tmp[0]} was specified twice (or more) in {inetnum.split('/')[-1]} without ip")
                        errors += 1
                    else:
                        _nserver[_tmp[0]] = None

                elif line.startswith("ds-rdata:"):
                    ds_rdata = line[20:].lower()
                    _split = ds_rdata.split(" ")
                    if len(_split) == 5:
                        ds_rdata = f"{_split[0]} {_split[1]} {_split[2]} {_split[3] + _split[4]}"

                    _ds_rdatas.append(ds_rdata)
        # if nserver list is not empty add the reverse to the domain list
        if not _nserver == {}:
            domains[_domain_name] = {
                "nserver": _nserver, "ds-rdata": _ds_rdatas}
    # load inet6nums
    for inet6num in inet6nums_files:
        # temp variables in case there is no nserver
        _nserver = {}
        _ds_rdatas = []
        _domain_name = ""
        with open(inet6num) as i6:
            for line in i6.readlines():
                line = line.replace("\n", "")
                if line.startswith("inet6num"):
                    line = line[20:]

                    # generate the reverse ipv6
                    _domain_name = "ip6.arpa"
                    _lowest, _highest = line.replace(":", "").split(" - ")
                    for _digit1, _digit2 in zip(_lowest, _highest):
                        if _digit1 != _digit2:
                            break
                        _domain_name = _digit1 + "." + _domain_name
                elif line.startswith("nserver"):
                    _tmp = _parse_nserver(line)
                    if _tmp == "break":
                        break
                    if _tmp[0] in _nserver:
                        print(
                            f"ERROR: nserver {_tmp[0]} was specified twice (or more) in {inet6num.split('/')[-1]} without ip")
                        errors += 1
                    else:
                        _nserver[_tmp[0]] = None

                elif line.startswith("ds-rdata:"):
                    ds_rdata = line[20:].lower()
                    _split = ds_rdata.split(" ")
                    if len(_split) == 5:
                        ds_rdata = f"{_split[0]} {_split[1]} {_split[2]} {_split[3] + _split[4]}"

                    _ds_rdatas.append(ds_rdata)

        # if nserver list is not empty add the reverse to the domain list
        if not _nserver == {}:
            domains[_domain_name] = {
                "nserver": _nserver, "ds-rdata": _ds_rdatas}

    # add entries from main domain, if the nserver doesn't have an ip address (like in inet(6)nums)
    for domain in domains:
        for nserver in domains[domain]["nserver"]:
            # if the nserver isn't specified: ...
            if domains[domain]["nserver"][nserver] == None:
                # print(f"INFO: the nserver {nserver} isn't specified in {domain}, looking into the parent domain of it")
                for i in range(len(nserver.split(".")), 1, -1):
                    # check if the nserver is already in loaded database, starts with more specific
                    if ".".join(nserver.split(".")[-i:]) in domains:
                        try:
                            domains[domain]["nserver"][nserver] = domains[".".join(
                                nserver.split(".")[-i:])]["nserver"][nserver]
                        except KeyError:
                            # reaches here if the domain for the nserver specified in the inet{6}num/domain is found, but the nserver itself not.
                            print(
                                f"Warn: the nserver {nserver} specified in {domain} wasn't found")
                            break

    return domains


def get_soa(domain_name, nserver):
    """query dns server for SOA"""
    global errors, summary

    try:
        request = dns.message.make_query(
            domain_name, dns.rdatatype.SOA, want_dnssec=False)
        response = dns.query.udp_with_fallback(
            request, nserver, timeout=TIMEOUT)
    except dns.exception.Timeout:
        print(f"WARN: querying {nserver} for SOA on {domain_name} timed out")
        summary[domain_name][SUMMARY.TIMEOUT] += 1
        errors += 1
        return False
    except dns.query.UnexpectedSource as e:
        print(
            f"ERROR: server replied with different ip than requested: error: {e}")
        errors += 1
        summary[domain_name][SUMMARY.SERVFAIL] += 1
        return False
    except Exception as e:
        print(
            f"ERROR: unknown error occured while querying {nserver} for {domain_name}: '{e}'")
        errors += 1
        time.sleep(3)
        return False
        # raise e
    if response[0].rcode() != 0:
        # HANDLE QUERY FAILED (SERVER ERROR OR NO SOA RECORD)
        print(
            f"WARN: query for a SOA on {domain_name} failed on {nserver}, returncode: {dns.rcode.to_text(response[0].rcode())}")
        errors += 1
        if dns.rcode.to_text(response[0].rcode()) == "REFUSED":
            summary[domain_name][SUMMARY.REFUSED] += 1
            errors += 1
        elif dns.rcode.to_text(response[0].rcode()) == "NXDOMAIN":
            summary[domain_name][SUMMARY.NXDOMAIN] += 1
            errors += 1
        elif dns.rcode.to_text(response[0].rcode()) == "SERVFAIL":
            summary[domain_name][SUMMARY.SERVFAIL] += 1
            errors += 1
        else:
            print(
                f"DEBUG: rcode not iplemented '{dns.rcode.to_text(response[0].rcode())}'")
            errors += 1
        return False
    _out = []
    for dnskey in response[0].answer:
        for key in dnskey.to_text().split("\n"):
            if not "IN SOA " in key:
                print(f"ERROR: CNAME returned for SOA: THIS SHOULD NOT BE USED")
                summary[domain_name][SUMMARY.WRONG_NS] += 1
                errors += 1
                break
            else:
                _out.append(key.split("IN SOA ")[1])

    # print(f"DEBUG: response: {response[0].answer[0].to_text()}")
    # print(f"DEBUG:{_out}")
    return _out


def get_ns(domain_name, nserver):
    """query dns server for NS"""
    global errors, summary

    try:
        request = dns.message.make_query(
            domain_name, dns.rdatatype.NS, want_dnssec=False)
        response = dns.query.udp_with_fallback(
            request, nserver, timeout=TIMEOUT)
    except dns.exception.Timeout:
        print(f"WARN: querying {nserver} for NS on {domain_name} timed out")
        summary[domain_name][SUMMARY.TIMEOUT] += 1
        errors += 1
        return False
    except dns.query.UnexpectedSource as e:
        print(
            f"ERROR: server replied with different different ip than requested: error: {e}")
        errors += 1
        return False
    if response[0].rcode() != 0:
        # HANDLE QUERY FAILED (SERVER ERROR OR NO NS RECORD)
        print(
            f"WARN: query for a NS on {domain_name} failed on {nserver}, returncode: {dns.rcode.to_text(response[0].rcode())}")
        errors += 1
        if dns.rcode.to_text(response[0].rcode()) == "REFUSED":
            summary[domain_name][SUMMARY.REFUSED] += 1
            errors += 1
        elif dns.rcode.to_text(response[0].rcode()) == "NXDOMAIN":
            summary[domain_name][SUMMARY.NXDOMAIN] += 1
            errors += 1
        else:
            print(
                f"DEBUG: rcode not iplemented '{dns.rcode.to_text(response[0].rcode())}'")
        return False
    _out = []
    for dnskey in response[0].answer:
        for key in dnskey.to_text().split("\n"):
            if not "IN NS " in key:
                print(f"ERROR: CNAME returned for NS: THIS SHOULD NOT BE USED")
                summary[domain_name][SUMMARY.WRONG_NS] += 1
                errors += 1
                break
            else:
                _out.append(key.split("IN NS ")[1])

    # print(f"DEBUG: response: {response[0].answer[0].to_text()}")
    # print(f"DEBUG:{_out}")
    return _out


def get_dnskey(domain_name, nserver):
    """query dns server for DNSKEY"""
    global errors, summary
    if nserver == None:
        print("WARN: nserver specified was 'None'")
        errors += 1
        return False
    try:
        request = dns.message.make_query(
            domain_name, dns.rdatatype.DNSKEY, want_dnssec=False)
        response = dns.query.udp_with_fallback(
            request, nserver, timeout=TIMEOUT)
    except dns.exception.Timeout:
        print(
            f"WARN: querying {nserver} for DNSKEY on {domain_name} timed out")
        summary[domain_name][SUMMARY.TIMEOUT] += 1
        errors += 1
        return False
    except dns.query.UnexpectedSource as e:
        print(
            f"ERROR: server replied with different different ip than requested: error: {e}")
        errors += 1
        return False
    except ConnectionRefusedError:
        print(
            f"WARN: {nserver} refused the connection")
        summary[domain_name][SUMMARY.REFUSED] += 1
        errors += 1
        return False

    if response[0].rcode() != 0:
        # HANDLE QUERY FAILED (SERVER ERROR OR NO DNSKEY RECORD)
        print(
            f"WARN: query for a DNSKEY on {domain_name} failed on {nserver}, returncode: {dns.rcode.to_text(response[0].rcode())}")
        errors += 1
        if dns.rcode.to_text(response[0].rcode()) == "REFUSED":
            summary[domain_name][SUMMARY.REFUSED] += 1
        elif dns.rcode.to_text(response[0].rcode()) == "NXDOMAIN":
            summary[domain_name][SUMMARY.NXDOMAIN] += 1
        else:
            print(
                f"DEBUG: rcode not iplemented '{dns.rcode.to_text(response[0].rcode())}'")
        return False

    _out = []
    for dnskey in response[0].answer:
        for key in dnskey.to_text().split("\n"):
            _out.append(key.split("IN DNSKEY ")[1])

    # print(f"DEBUG: response: {response[0].answer[0].to_text()}")
    # print(f"DEBUG:{_out}")
    return _out

# end_step1


# step 2: <start dnskey_to_DS.py based on https://gist.github.com/wido/4c6288b2f5ba6d16fce37dca3fc2cb4a >
"""
Generate a DNSSEC DS record based on the incoming DNSKEY record
The DNSKEY can be found using for example 'dig':
$ dig DNSKEY secure.widodh.nl
The output can then be parsed with the following code to generate a DS record
for in the parent DNS zone
Author: Wido den Hollander <wido@widodh.nl>
Many thanks to this blogpost: https://www.v13.gr/blog/?p=239
"""


def _calc_keyid(flags, protocol, algorithm, dnskey):
    st = struct.pack('!HBB', int(flags), int(protocol), int(algorithm))
    st += base64.b64decode(dnskey)

    cnt = 0
    for idx in range(len(st)):
        s = struct.unpack('B', st[idx:idx+1])[0]
        if (idx % 2) == 0:
            cnt += s << 8
        else:
            cnt += s

    return ((cnt & 0xFFFF) + (cnt >> 16)) & 0xFFFF


def _calc_ds(domain, flags, protocol, algorithm, dnskey):
    if domain.endswith('.') is False:
        domain += '.'

    signature = bytes()
    for i in domain.split('.'):
        signature += struct.pack('B', len(i)) + i.encode()

    signature += struct.pack('!HBB', int(flags), int(protocol), int(algorithm))
    signature += base64.b64decode(dnskey)

    return {
        'sha1':    hashlib.sha1(signature).hexdigest().upper(),
        'sha256':  hashlib.sha256(signature).hexdigest().upper(),
    }


def dnskey_to_ds(domain, dnskey):
    dnskeylist = dnskey.split(' ', 3)

    flags = dnskeylist[0]
    protocol = dnskeylist[1]
    algorithm = dnskeylist[2]
    key = dnskeylist[3].replace(' ', '')

    keyid = _calc_keyid(flags, protocol, algorithm, key)
    ds = _calc_ds(domain, flags, protocol, algorithm, key)

    ret = list()
    ret.append(str(keyid) + ' ' + str(algorithm) + ' ' + str(1) + ' '
               + ds['sha1'].lower())
    ret.append(str(keyid) + ' ' + str(algorithm) + ' ' + str(2) + ' '
               + ds['sha256'].lower())
    return ret

# step2: <end dnskey_to_DS.py>

# step3: start: partially stolen from: https://stackoverflow.com/questions/26137036/programmatically-check-if-domains-are-dnssec-protected


def check_dnssec(domain_name, domain_data):
    global errors, summary
    success = False

    no_ds_rdatas = domain_data["ds-rdata"] == []
    # if no_ds_rdatas:
    #    print(
    #        f"NOTE: {domain_name} doesn't have ds-rdata configured, not checking it")
    #    return True

    for nserver in domain_data["nserver"]:

        # if the nserver is not set (i.e. not loaded from other dns file or "wrong" fqdn)
        if domain_data["nserver"][nserver] == None:
            print(
                f"INFO: ip address(es) for nserver '{nserver}' in '{domain_name}' isn't specified/loaded")
            continue
        for nsaddr in domain_data["nserver"][nserver]:

            # get SOA
            request = dns.message.make_query(
                domain_name, dns.rdatatype.SOA, want_dnssec=False)
            try:
                # send the query
                dns.query.udp_with_fallback(request, nsaddr, timeout=TIMEOUT)
            # if it timed out: tell the user
            except dns.exception.Timeout:
                print(
                    f"WARN: querying {nserver} ({nsaddr}) for {domain_name} timed out")
                summary[domain_name][SUMMARY.TIMEOUT] += 1
                continue

            if no_ds_rdatas:
                print(
                    f"INFO: query for {domain_name} SOA on {nserver} ({nsaddr}) succeded, not checking DNSSEC")
                continue
            # get DNSKEY for zone
            request = dns.message.make_query(
                domain_name, dns.rdatatype.DNSKEY, want_dnssec=True)
            response = dns.query.udp_with_fallback(
                request, nsaddr, timeout=TIMEOUT)

            if response[0].rcode() != 0:
                # HANDLE QUERY FAILED (SERVER ERROR OR NO DNSKEY RECORD)
                print(
                    f"WARN: query for a DNSKEY on {domain_name} failed on {nserver} ({nsaddr}), returncode: {response[0].rcode()}")
                errors += 1
                continue
            # answer should contain two RRSET: DNSKEY and RRSIG(DNSKEY)
            answer = response[0].answer
            if len(answer) != 2:
                # SOMETHING WENT WRONG
                print(
                    f"ERROR: query for a DNSKEY on {domain_name} failed on {nserver} ({nsaddr}), invalid answer length: {len(answer)}")
                errors += 1
                continue
            # the DNSKEY should be self signed, validate it
            name = dns.name.from_text(domain_name)
            try:
                # print(f"DEBUG: answer[0]: {answer[0]}")
                # print(f"DEBUG: answer[1]: {answer[1]}")
                try:
                    dns.dnssec.validate(
                        answer[0], answer[1], {name: answer[0]})
                # it raises an AttributeError if the records are in the wrong order
                except AttributeError as e:
                    dns.dnssec.validate(
                        answer[1], answer[0], {name: answer[0]})

            except dns.dnssec.ValidationFailure:
                # BE SUSPICIOUS
                print(
                    f"WARN: DNSSEC validation failed on {domain_name} failed on {nserver} ({nsaddr}), answer: {answer}")
                summary[domain_name][SUMMARY.DNSSEC_FAIL] += 1
                errors += 1
            except AttributeError as e:
                print(f"ERROR: {e}")
                errors += 1
            else:
                # WE'RE GOOD, THERE'S A VALID DNSSEC SELF-SIGNED KEY FOR example.com
                print(
                    f"INFO: DNSSEC validation succeded on {domain_name} failed on {nserver} ({nsaddr})")
                summary[domain_name][SUMMARY.SUCCESS] += 1
                success = True

        return success


# step3: end


def main(mntner):
    global errors
    global summary
    # get all domains/inet(6)nums of the mntner
    domains = get_domain_by_mntner(mntner=mntner)

    # global _tmp_continue, _tmp_found
    # _tmp_found = False
    # _tmp_continue = "10.in-addr.arpa"
    def threaded_check_dns(domain_name):
        global errors, summary
        # global _tmp_found, _tmp_continue
        # if domain_name == _tmp_continue:
        #     _tmp_found = True
        # if not _tmp_found:
        #     return
        summary[domain_name] = [0, 0, 0, 0, 0, 0, 0, 0]
        # check if the domain doesn't have DS data
        if domains[domain_name]["ds-rdata"] == []:
            print(f"NOTE: {domain_name} doesn't have any ds-rdata specified")
            # continue

        for nserver in domains[domain_name]["nserver"]:
            # check for unset nserver ips -> dont check them
            if domains[domain_name]["nserver"][nserver] == None:
                continue
            for ip in domains[domain_name]["nserver"][nserver]:
                if ip == "":
                    print(
                        f"ERROR: nserver value for {nserver} is empty. Maybe the line ends with space?")
                    errors += 1
                    continue
                _soa = get_soa(domain_name, ip)
                if _soa == False:
                    continue
                # print(f"DEBUG: response {_soa}")
                if _soa == []:
                    print(
                        f"ERROR: empty SOA record for {domain_name} returned by {ip}({nserver})")
                    errors += 1
                    summary[domain_name][SUMMARY.WRONG_SOA] += 1
                    continue
                soa = _soa[0].split(" ")
                # check if Serial, TTL, etc. are numbers:
                try:
                    int(soa[2]) + int(soa[3]) + \
                        int(soa[4]) + int(soa[5]) + int(soa[6])
                except ValueError:
                    print(
                        f"ERROR: invalid SOA record from {ip} ({nserver}) for {domain_name}")
                    summary[domain_name][SUMMARY.WRONG_SOA] += 1
                    errors += 1
                    continue

                master_ns, _e_mail, _serial, _, _, _, _ = soa
                _found = False
                for _nserver in domains[domain_name]["nserver"]:
                    #
                    if master_ns == f"{_nserver}.":
                        _found = True
                        break
                else:
                    print(
                        f"WARN: master nserver '{master_ns}' returned by {ip}({nserver}) not in the list of the specified nservers of {domain_name}")
                    summary[domain_name][SUMMARY.WRONG_SOA] += 1
                    errors += 1
                    continue

                _ns = get_ns(domain_name, ip)
                if _ns == False:
                    continue
                # print(f"DEBUG: response {_ns}")
                if not f"{nserver}." in _ns:
                    print(
                        f"WARN: returned nservers returned by {ip}({nserver}) for {domain_name} does not include it self")
                    summary[domain_name][SUMMARY.WRONG_NS] += 1
                    errors += 1
                    continue

                for _nserver in domains[domain_name]["nserver"]:
                    for _server in _ns:
                        if f"{_nserver}." == _server:
                            # remove matches
                            _ns.remove(_server)
                            break
                    else:
                        print(
                            f"INFO: {_nserver} was not listed in the NS records by {ip}({nserver}) for {domain_name}")
                        summary[domain_name][SUMMARY.WRONG_NS] += 1
                # check if there are any left
                if len(_ns) > 0:
                    for _server in _ns:
                        print(
                            f"INFO: {_server} in response for NS records by {ip}({nserver}) for {domain_name} but not in the dns/inet(6)num file")
                        summary[domain_name][SUMMARY.WRONG_NS] += 1

                # don't check dnssec if not configured
                if domains[domain_name]["ds-rdata"] == []:
                    summary[domain_name][SUMMARY.SUCCESS] += 1
                    continue

                ds_candidates = []
                # load DNSKEYs from nserver: if False something failed (i.e. timeout)
                _keys = get_dnskey(domain_name, ip)
                if _keys == False:
                    continue
                # convert all found keys to DS
                for key in _keys:
                    try:
                        _ds_s = dnskey_to_ds(domain_name, key)
                    except binascii.Error as e:
                        print(
                            f"ERROR: trying to convert '{key}' to DS failed: {e}")
                        summary[domain_name][SUMMARY.DNSSEC_FAIL] += 1
                        continue
                    ds_candidates.extend(_ds_s)
                found = False
                # iterate over DS-rdata from the registry and check if they are found on the nserver
                for ds in domains[domain_name]["ds-rdata"]:
                    # print(ds)
                    if ds in ds_candidates:
                        found = True
                # print(f"DEBUG: available: {domains[domain_name]['ds-rdata']}")
                # print(f"DEBUG: generated: {ds_candidates}")
                if found:
                    print(
                        f"INFO: correct ds-rdata specified and matching DNSKEY returned by {ip} for {domain_name}")
                    summary[domain_name][SUMMARY.SUCCESS] += 1
                else:
                    print(
                        f"ERROR: invalid ds-rdata specified or non-matching DNSKEY returned by {ip} for {domain_name}")
                    summary[domain_name][SUMMARY.DNSSEC_FAIL] += 1
                    errors += 1
            # break

    # create ThreadPool and run threaded_check_dns against all domains
    pool = ThreadPool(processes=THREADS)
    results = pool.map(threaded_check_dns, domains)
    pool.close()
    pool.join()

    # --- show a summary as a table ---

    # sort summary
    _summary = {}
    for domain in domains:
        _summary[domain] = summary[domain]

    summary = _summary

    # get length of longest domain name
    _max_domain_length = 9
    for _domain in summary:
        if len(_domain) > _max_domain_length:
            _max_domain_length = len(_domain)

    print("\n\nSummary:\n")
    print(f"{'domain name'.ljust(_max_domain_length)}  | success | dnssec fail | wrong NS | wrong SOA | NXDOMAIN | REFUSED | SERVFAIL | timeout")
    print(f"-{'-'.rjust(_max_domain_length, '-')     }-|---------|-------------|----------|-----------|----------|---------| -------- | -------")
    for domain in summary:
        print(f" {domain.rjust(1).ljust(_max_domain_length)} | {str(summary[domain][SUMMARY.SUCCESS]).rjust(7)} | {str(summary[domain][SUMMARY.DNSSEC_FAIL]).rjust(11)} | {str(summary[domain][SUMMARY.WRONG_NS]).rjust(8)} | {str(summary[domain][SUMMARY.WRONG_SOA]).rjust(9)} | {str(summary[domain][SUMMARY.NXDOMAIN]).rjust(8)} | {str(summary[domain][SUMMARY.REFUSED]).rjust(7)} | {str(summary[domain][SUMMARY.SERVFAIL]).rjust(8)} | {str(summary[domain][SUMMARY.TIMEOUT]).rjust(7)}")

    # print(summary)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("please specify your mntner")
        print(f'   `{sys.argv[0]} YOU-MNT` to scan your dns and inet(6)num zones')
        print(f'   `{sys.argv[0]} ""` to scan everything (takes a long time)')
        exit(1)
    main(sys.argv[1])
    exit(errors)


# commands to run:
# 1. drill -D <domain>.dn42 @ns1.<domain>.dn42 NS
# 2. dnskey_to_ds("<domain>.dn42"
# #<TTL> IN DNSKEY
# "257 3 13 <base64 ...>")
# 3. write dnskey to "trust-anchor"
# 4.delv @ns1.<domain.dn42 +root=<domain>.dn42 -a ./trust-anchor.tmp SOA <domain>.dn42
