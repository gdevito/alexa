#!/usr/bin/python

import argparse
import configparser
import base64
import hashlib
import hmac
import json
import logging
import pprint
import re
import requests
import sha
import sys
import time
import urllib

from collections import OrderedDict
from bs4 import BeautifulSoup

'''
http://ats.amazonaws.com/?
            AWSAccessKeyId=
            &Action=TopSites
            &Count=100
            &CountryCode=BR
            &ResponseGroup=Country
            &SignatureMethod=HmacSHA1
            &SignatureVersion=2
            &Start=301
            &Timestamp=2011-05-06T17%3A58%3A49.463Z
            &Url=yahoo.com
            &Signature=
'''

def sign(string_to_sign, key):

    logging.info(string_to_sign)
    h = hmac.new(key, string_to_sign, sha)
    d = h.digest()
    sig = base64.b64encode(d)
    sig = urllib.urlencode(sig)
    return sig

def get_alexa(p, sts):

    sig = sign(sts)
    p['Signature'] = sig
    e_params = urllib.urlencode(p)
    req = http + ats_url + '/?' + e_params
    try:
        r = requests.get(req)
    except requests.exceptions.RequestException as e:
        logging.error(e)
        sys.exit(1)
    logging.info(r.status_code)
    logging.info(r.content)

def call(username=None, key=None):

    p = OrderedDict()
    p['AWSAccessKeyId'] = username
    p['Action'] = 'TopSites'
    p['Count'] ='5'
    p['CountryCode'] ='US'
    p['ResponseGroup'] = 'Country'
    p['SignatureMethod'] = 'HmacSHA1'
    p['SignatureVersion'] = '2'
    p['Start'] = '1'
    p['Timestamp'] = str(time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()))
    
    e_params = urllib.urlencode(p)
    http = 'http://'
    ats_url = 'ats.amazonaws.com'
    verb = 'GET'
    sts = verb + '\n' + ats_url + '\n\n' + e_params
    get_alexa(p, string_to_sign(sts, key))

def prep_wiki(page):
    """
    cut through start of wiki page to get to table kept by 
    wikipedia
    """
    s = page.find("<tr>\n<td><a href")
    if s == -1:
        return 0
    return s-7

def get_tr(html):

    tr = html.find("tr")
    if tr == -1:
        return None, 0
    return tr

def get_ref(html):

    ref = html.find("a href")
    if ref == -1:
        return None, 0
    start = html.find('"/wiki/', ref)
    end = html.find('"', start + 1)
    ref = html[start + 7: end]
    return ref, end

def get_type(html):
    
    ref = html.find(" href")
    if ref == -1:
        return None, 0
    start = html.find('"/wiki/', ref)
    end = html.find('"', start + 1)
    type = html[start + 7: end]
    a_t = html.find("a> and <a")
    if a_t == -1:
        pass
    else:
        if a_t < html.find('"/wiki/', end):
            start = html.find('"/wiki/', a_t)
            end = html.find('"', start + 1)
            type = [type, html[start + 7: end]]
    return type, end
    
def get_url(html):
    start = html.find("<td>")
    end = html.find("</td>", start)
    url = html[start + 4: end]
    return url, end

def get_top_sites(rank_max=100):
    top_sites = {}
    r = requests.get('https://en.wikipedia.org/wiki/List_of_most_popular_websites')
    h = str(BeautifulSoup(r.content, 'lxml'))
    logging.info(h)
    n = prep_wiki(h)
    h = h[n:]
    rank = 1
    top_sites = []
    while rank < rank_max + 1:
        new_ref, n = get_ref(h)
        if new_ref:
            site = {}
            h = h[n:]
            url, n = get_url(h)
            site['url'] = url
            site['ref'] = new_ref
            site['rank'] = rank
            h = h[n:]
            type, n = get_type(h)
            site['type'] = type
            h = h[n:]
            co, n = get_ref(h)
            site['co'] = co
            h = h[n:]
            # not always co_str ref, so watch out ( misorder )
            #co_str, n = get_ref(h)
            #top_sites[url]['co_str'] = co_str
            #h = h[n:]
            print url, new_ref, rank, type, co
            rank += 1
            n = get_tr(h)
            h = h[n:]
            top_sites.append(site)
        else:
            break
    # current issue is with taoboa and vk, twitter showing up as 15, is 12
    return top_sites

pref = 'http://www.'

def main():

    cfg = ConfigParser()
    cfg.read(os.path.expanduser('~/.aws'))
    username = cfg.get('aws', 'username')
    key = cfg.get('aws', 'api_key'))

    logging.basicConfig(filename='alexa_ranks.log', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--alexa', type=bool, help='Get alexa ranking via rest api')
    parser.add_argument('-r', '--rank', type=int, help='Rankings to get 1 to 100')
    args = parser.parse_args()

    if args.rank:
        rankings = get_top_sites(args.rank)
    else:
        rankings = get_top_sites()
        logging.info('Default get 100')

    for r in rankings:
        logging.info(r)

if __name__ == "__main__":
    main()
