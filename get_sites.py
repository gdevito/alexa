#!/usr/bin/python
import argparse
import boto3
import io
import json
import locale
import logging
import multiprocessing
import operator
import pprint
import re
import requests
import sys
import time

from bs4 import BeautifulSoup

def get_alexa_sites(rank=100):
    ''' parse wiki table for top rank and collect additional info from 
    the table.  previous AWS Alexa api had not been working and found this
    to work nicely once read up on bs4 module'''

    try:
        r = requests.get('https://en.wikipedia.org/wiki/List_of_most_popular_websites')
    except requests.exceptions.RequestException as e:
        logging.error(e)
        sys.exit(1)
    html = BeautifulSoup(r.content, 'lxml')
    sites = []
    for tr in html.findAll('tr'):
        tds = tr.findAll('td')
        it = 0
        site = {}
        for td in tds:
            if td.find('sup'):
                td.find('sup').extract()
            txt = td.getText()
            if it == 0: site['co'] = txt
            elif it == 1: site['url'] = txt
            elif it == 2: site['rank'] = txt
            elif it == 3:
                txt = txt.replace('N/A', '0')
                site['prev_rank'] = txt
                jmp = int(str(site['prev_rank']).replace(',','')) - int(str(site['rank']).replace(',',''))
                site['rank_jmp'] = jmp
            elif it == 4:
                site['type'] = txt
            elif it == 5: site['country'] = txt
            it += 1

        if site:
            sites.append(site)
        if len(sites) == rank:
            break

    assert len(sites) >= rank
    logging.info(sites)
    return sites[:rank]

def get_retry(kwargs):

    result = kwargs.pop('default')
    func = kwargs.pop('func')
    tries = kwargs.pop('tries')
    logging.info(kwargs)

    while tries:
        try:
            logging.info('Trying')
            result = func(**kwargs)
            break
        except Exception as e:
            logging.warning('Retrying')
            tries -= 1
            
    return result

def get_words(url):
    
    response = None
    logging.info('GET:words ' + url)
    start = time.time()
    try:
        r = requests.get('http://www.' + url)
    except requests.exceptions.RequestException as e:
        logging.error(e)
        sys.exit(1)
    html = BeautifulSoup(r.content, 'lxml')
    refs = html.find_all('a')
    words = []
    for ref in refs:
        strings = ref.get_text().encode('utf-8').split()
        for string in strings:
            re.compile('\w+').findall(string)
            words.append(string)
    logging.info('URL: '+url)
    logging.info('LEN: '+str(len(words)))
    t_get = time.time() - start
    response = {'words':words, 'wc':len(words), 'time':t_get, 'url':url}

    #logging.info(response)
    return response

def main():

    logging.basicConfig(filename='alexa_ranks.log', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--rank', type=int, help='Rankings to get 1 to 100')
    parser.add_argument('-w', '--words', dest='words', action='store_true', default=False, help='Calculate word counts')
    args = parser.parse_args()

    metrics = {}

    start = time.time()
    if args.rank:
        sites = get_alexa_sites(args.rank)
    else:
        sites = get_alexa_sites()
        logging.info('Default get 100')

    metrics['t_sites'] = time.time() - start
    metrics['num_sites'] = len(sites)

    if args.words:
        
        start = time.time()
        pool = multiprocessing.Pool()
        par_args = []
        for site in sites:
            logging.info(site['url'])
            
            args = {'func':get_words, 'default':None, 'tries':5, 'url':site['url']}
            par_args.append(args)

        logging.info(par_args)
        results = pool.map(get_retry, par_args)

    #with io.open('results/results.txt', 'w', encoding='utf-8') as f:
    #    f.write(unicode(json.dumps(results, indent=4)))

    # rollup metrics
    metrics['avg_wc'] = sum(site['wc'] for site in results) / len(sites)
    metrics['t_lookups'] = sum(site['time'] for site in results)
    metrics['t_total_real'] = metrics['t_sites'] + time.time() - start
    with io.open('results/metrics.txt', 'w', encoding='utf-8') as f:
        logging.info('Writing metrics to json')
        f.write(unicode(json.dumps(metrics, indent=4)))

    by_wc = sorted(results, key=operator.itemgetter('wc'))
    by_rank_jump = sorted(sites, key=operator.itemgetter('rank_jmp'), reverse=True)

    with io.open('results/top_tens.txt', 'w', encoding='utf-8') as f:
        logging.info('Writing top tens')
        f.write(unicode(json.dumps(by_wc, indent=4)))
        f.write(unicode(json.dumps(by_rank_jump, indent=4)))
                          
if __name__ == "__main__":
    main()

