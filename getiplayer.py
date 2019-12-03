#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import os
import subprocess
import math
import json
import pprint as pp
import time
import sys
import urllib.parse

class Channel:
    def __init__(self, title, href, liveHref):
        self.title = title
        self.href = href
        self.liveHref = liveHref
    
    def __str__(self):
        return self.title


class Category:
    def __init__(self,title,href):
        self.title = title
        self.href = href

    def __str__(self):
        return self.title

class Show:
    def __init__(self,title, id, synopsis):
        self.title = title
        self.id = id
        self.synopsis = synopsis
    
    def __str__(self):
        return self.title

class Search_Episode:
    def __init__(self,durationSubLabel, href, subtitle, synopsis, title, episode_type, id):
        self.durationSubLabel = durationSubLabel
        self.href = href 
        self.subtitle = subtitle
        self.synopsis = synopsis
        self.title = title
        self.episode_type = episode_type
        self.id = id

    def __str__(self):
        return self.title + " - " +self.subtitle

def log(input):
    with open('log.txt', 'a') as f:
        f.write( str( input ) )

def print_out_menu_options(options, multi_choice=False, func=None):
    choices = []
    full = int( math.floor(len(options) / height ) )
    remainder = len(options) - (full * height)


    display_control = []
    counter = 0
    for each in range(full):
        temp = []
        for itr in range(height):
            temp.append(counter)
            counter+=1

        display_control.append(temp)
    temp = []
    for each in range(remainder):
        temp.append(counter)
        counter+=1
    
    display_control.append(temp)
    
    page_itr = 0

    while True:
        os.system('clear')
        for each in display_control[page_itr]:
            # print( 'number {} {}'.format(each+1, options[each].title) )
            print( 'number {} {}'.format(each+1, options[each]) )

        result = input('choice ')
        if result == 'n':
            if page_itr < len(display_control) -1:
                page_itr +=1
        elif result =='p':
            if page_itr > 0:
                page_itr -=1
        elif result =='q':
            return choices
        else: 
            result_list = result.split(' ')
            for item in result_list:
                try:
                    item = int(item)
                    if item <= len(options):
                        if multi_choice and func:
                            func( options[ item - 1 ] )
                        elif multi_choice:
                            choices.append(options[item-1])
                        elif func:
                            func( options[ item-1 ] )
                        else:
                            return options[item-1]
                except ValueError:
                    pass

def add_to_download_queue(episode):
    download_queue.append(episode)

def get_items(soup):
    results = []
    items = soup.find_all('div', class_='content-item')
    for each in items:

        content_item_link = each.find('a', class_='content-item__link')
        content = content_item_link['aria-label'].split('Description: ')
        link = 'https://www.bbc.co.uk' + content_item_link['href']
        show = Show(content[0], link.replace('featured', 'a-z'))
        log(show)
        multiple = each.find('a', class_='lnk')
        if multiple != None:
            show.multiple_episodes = True
        results.append(show)
    return results

def parse_page(url,search=False):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    number = soup.find('ol', class_='pagination__list').find('span', class_='tvip-hide').text.split('of')[1].strip()

    results = []

    results.extend(get_items(soup))

    list_of_pages = []

    if int(number) > 2:
        list_of_pages = list(range(2, int(number)+1))
    else:
        list_of_pages.append(2)

    page_token = ''
    if search:
        page_token = '&'
    else:
        page_token = '?'

    for page in list_of_pages:
        url_temp = url + page_token +'page={}'.format(page)
        temp_page = requests.get(url_temp)
        temp_soup = BeautifulSoup(temp_page.content, 'html.parser')
        results.extend(get_items(temp_soup))

        


    return results

def search_by_keyword2(search_term=None):
    os.system('clear')
    result =''
    if search_term == None:
        result = input('enter keywords separated by space ')
        result = result.replace(' ', '+')
    else:
        result = search_term
    url = 'https://www.bbc.co.uk/iplayer/search?q=' + urllib.parse.quote( result )
    return parse_search(url)

def parse_search(url):
    return_results = []
    python_obj = get_script(url)
    currentPage =  int( python_obj['pagination']['currentPage'] )
    totalPages = int( python_obj['pagination']['totalPages'] )
    print('checking {} of {} pages'.format(currentPage, totalPages))
    search_episodes = get_search_episodes_from_json(python_obj)


    return_results.extend(search_episodes)
    while currentPage < totalPages:
        currentPage += 1
        t0 = time.time()
        new_url = url + '&page={}'.format(currentPage)
        obj = get_script(new_url)
        t1 = time.time() - t0
        temp = get_search_episodes_from_json(obj)
        return_results.extend( temp )
        print('checking {} of {} pages'.format(currentPage, totalPages))
        time.sleep(t1*2)
    return return_results

def get_search_episodes_from_json(python_obj):
    log('*****************************************\n')
    results = []
    if 'entities' in python_obj:
        entities = python_obj['entities']
        for entity in entities:
            if 'meta' in entity and 'secondaryHref' in entity['meta']:
                temp_url = base + entity['meta']['secondaryHref']
                temp_result = parse_search(temp_url)
                for each in temp_result:
                    results.append(each)
            else:
                if 'durationSubLabel' not in entity['props']:
                    entity['props']['durationSubLabel'] = None
                if 'synopsis' not in entity['props']:
                    entity['props']['synopsis'] = None
                if 'subtitle' not in entity['props']:
                    entity['props']['subtitle'] = None
                if 'type'  not in entity['props']:
                    entity['props']['type'] = None
                if 'meta' in entity and 'id' not in entity['meta']:
                    entity['meta']['id'] = None
                else:
                    entity['meta'] = {}
                    entity['meta']['id'] = None
                search_episode = Search_Episode(
                    entity['props']['durationSubLabel'],
                    entity['props']['href'],
                    entity['props']['subtitle'],
                    entity['props']['synopsis'],
                    entity['props']['title'],
                    entity['props']['type'],
                    entity['meta']['id'])
                if 'meta' in entity and 'programmeId' in entity['meta']:
                    search_episode.id = entity['meta']['programmeId']
                results.append(search_episode)
    else:
        return None
    return results

def get_search_episodes_from_json_old(python_obj):
    results = []
    if 'entities' in python_obj:
        entities = python_obj['entities']
        for entity in entities:
            if 'type' in entity['props'] and entity['props']['type'] == 'tleo-available':
                if 'durationSubLabel' not in entity['props']:
                    entity['props']['durationSubLabel'] = None
                if 'synopsis' not in entity['props']:
                    entity['props']['synopsis'] = None
                if 'subtitle' not in entity['props']:
                    entity['props']['subtitle'] = None
                if 'id' not in entity['meta']:
                    entity['meta']['id'] = None
                search_episode = Search_Episode(
                    entity['props']['durationSubLabel'],
                    entity['props']['href'],
                    entity['props']['subtitle'],
                    entity['props']['synopsis'],
                    entity['props']['title'],
                    entity['props']['type'],
                    entity['meta']['id'])
                if 'programmeId' in entity['meta']:
                    search_episode.id = entity['meta']['programmeId']
                results.append(search_episode)
    elif 'groups' in python_obj:
        groups = python_obj['groups']
        entities = []
        for each in groups:
            for entity in each['entities']:
                if 'type' in entity['props'] and entity['props']['type'] == 'tleo-available':
                    if 'durationSubLabel' not in entity['props']:
                        entity['props']['durationSubLabel'] = None
                    if 'synopsis' not in entity['props']:
                        entity['props']['synopsis'] = None
                    if 'subtitle' not in entity['props']:
                        entity['props']['subtitle'] = None
                    if 'id' not in entity['meta']:
                        entity['meta']['id'] = None 
                    search_episode = Search_Episode(
                        entity['props']['durationSubLabel'],
                        entity['props']['href'],
                        entity['props']['subtitle'],
                        entity['props']['synopsis'],
                        entity['props']['title'],
                        entity['props']['type'],
                        entity['meta']['id'])
                    results.append(search_episode)
    return results

def get_script(url):
    page = requests.get( url )
    soup = BeautifulSoup(page.content, 'html.parser')
    scripts = soup.find_all('script')
    res2 = ''
    for each in scripts:
        if 'window.__IPLAYER_REDUX_STATE__ = ' in each.text:
            res2 = each.text.replace('window.__IPLAYER_REDUX_STATE__ = ','')
            res2 = res2.replace(';','')

    return json.loads(res2)

def list_episodes(obj):
    episode_url = base + obj.href.replace('/featured','')
    episode_url += '/a-z'
    log( episode_url )
    script = get_script(episode_url)
    episodes = get_search_episodes_from_json(script)
    for each in episodes:
        log(each.title)



    page = 1
    totalPages = 0
    checking = "checking {} of {} pages" 
    if 'pagination' in script:
        if 'totalPages' in script['pagination']:
            totalPages = int( script['pagination']['totalPages'] )
            if totalPages > 1:
                print(checking.format(page, totalPages))
                page = 2

    while page < totalPages:
        print(checking.format(page, totalPages))
        script = get_script(episode_url + "?page={}".format(page))
        episodes.extend( get_search_episodes_from_json( script ) )
        page +=1

    print_out_menu_options(episodes, True, list_available_episodes)

def list_available_episodes(obj):
    script = get_script(base + obj.href)['relatedEpisodes']
    if int( script['count'] ) > 0:
        shows = []
        episodes = script['episodes']
        for each in episodes:
            show = Show(each['title'] +" - " + each['subtitle'], each['id'], each['synopses']['small'])
            shows.append(show)
        print_out_menu_options(shows, True, add_to_download_queue)
    else:
        print('no episodes found')
        time.sleep(3)

def main():
    print('retrieving data')
    python_obj = get_script(base + "/iplayer")
    
    channels = []
    categories = []
    for each in python_obj['navigation']['items']:
        if 'id' in each and each['id'] == 'channels':
            for e in each['subItems']:
                channel = Channel(e['title'], e['href'], e['liveHref'])
                channels.append(channel)
        if 'id' in each and each['id'] == 'categories':
            for e in each['subItems']:
                category = Category(e['title'], e['href'])
                categories.append(category)

    while True:
        os.system('clear')
        print('number 1 search by keywords')
        print('number 2 search by category')
        print('number 3 search by channel')
        print('number 4 begin downloads')
        result = input('choice ')
        try:
            result = int( result )
            if result == 1:
                print_out_menu_options( search_by_keyword2(), True, add_to_download_queue )
            elif result == 2:
                print_out_menu_options( categories, False, list_episodes)
            elif result == 3:
                print_out_menu_options( channels, False, list_episodes)
            elif result == 4:
                if len( download_queue ) > 0: 
                    output_path = os.getcwd() + ':/save-here'
                    command = """docker run --privileged=true --cap-add=NET_ADMIN --device /dev/net/tun:/dev/net/tun -v """ + output_path + """ -w=/save-here -it iget:latest bash -c '/quick.sh """
                    for each in download_queue:
                        log(type(each))
                        command += each.id + " "
                    command += "'"
                    # subprocess.run(command, shell=True)
                    download_queue.clear()

        except ValueError:
            if result == 'q':
                break


if __name__ == "__main__":
    base = 'https://www.bbc.co.uk'
    download_queue =[]
    width = int( subprocess.check_output(['tput','cols']) )
    height = int( subprocess.check_output(['tput','lines']) ) -1
    main()
