#!/usr/bin/python
import argparse
import boto3
import io
import json
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
    top_sites = []

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
                site['prev_rank'] = txt
                #site['rank_hop'] = int(site['rank']) - int(site['prev_rank'])
            elif it == 4:
                site['type'] = txt
            #refs = td.find_all('a', href=True)
            #for r in refs:
            #    print site['type']
            #    print r.text
                #site['type'] = [site['type'] + r.text]
            elif it == 5: site['country'] = txt
            it += 1
        if site:
            top_sites.append(site)
    assert len(top_sites) >= rank
    return top_sites[:rank]

def get_words(url):
    
    try:
        r = requests.get('http://www.' + url)
    except requests.exceptions.RequestException as e:
        logging.error(e)
        sys.exit(1)
    html = BeautifulSoup(r.content, 'lxml')
    #text = html.findAll(text=True)
    refs = html.find_all('a')
    words = []
    for ref in refs:
        strings = ref.get_text().encode('utf-8').split()
        for string in strings:
            string = re.sub('[^a-zA-Z0-9-_*.]', '', string)
            #for c in string:
                # very restrictive
                #if not c.isalphanum():
                #    string = None
            words.append(string)
    logging.info('URL: '+url)
    logging.info('LEN: '+str(len(words)))
         
    return words, len(words)

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

    metrics['t_sites'] = start - time.time()
    metrics['num_sites'] = len(sites)
    t_num = 0
    t_get_words = 0
    num_words = 0

    if args.words:
        for site in sites:
            logging.info(site)
            start = time.time()
            # use thread pool to parallelize calls
            words, num = get_words(site['url'])
            site['wc'] = num
            num_words += num
            site['words'] = words
            site['time'] = time.time() - start
            t_get_words += site['time']
            logging.info('Time: ', site['time'])
            with io.open('results/word_counts.txt', 'a', encoding='utf-8') as f:
                logging.info('Writing json out to word_counts.txt')
                f.write(unicode(json.dumps(site, indent=4, ensure_ascii=False)))

    # rollup metrics
    metrics['avg_wc'] = num_words / metrics['num_sites']
    metrics['t_lookup'] = t_get_words
    metrics['t_avg_lookup'] = t_get_words / metrics['num_sites']
    metrics['t_total'] = metrics['t_sites'] + metrics['t_lookup']
    with io.open('results/metrics.txt', 'w', encoding='utf-8') as f:
        logging.info('Writing metrics to json')
        f.write(unicode(json.dumps(metrics, indent=4)))

    by_wc = sorted(sites, key=operator.itemgetter('wc'))
    #by_rank_jump = sorted(sites, key=(operator.itemgetter('rank_hop')))
    
    top = 10 if len(sites) >= 10 else len(sites)
    with io.open('results/top_tens.txt', 'w', encoding='utf-8') as f:
        logging.info('Writing top tens')
        f.write(unicode(json.dumps(by_wc[:top])))
        #f.write(unicode(json.dumps(by_rank_jump[:top])))
                          

if __name__ == "__main__":
    main()

