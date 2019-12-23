#!/usr/bin/env python3
import subprocess
import sys
import re
import math
import os 
import config
import time


class Search_Episode:
    def __init__(self, title, subtitle, id):
        self.subtitle = subtitle
        self.title = title
        self.id = id

    def __str__(self):
        return self.title + " - " + self.subtitle

def execute_search(command):
    results = []
    process = subprocess.check_output(command, stdin=None, stderr=None, shell=True, universal_newlines=False)

    for line in process.split(b'\n'):
        try:
            if re.match(r'^[0-9]{4}:', line.decode('ASCII')):
                line = line.decode('ASCII').replace('\t',' ').split(',')
                line[0] = re.sub(r'[0-9]{4}: ', '', line[0])
                se = Search_Episode(line[0], line[1], line[2])
                results.append(se)
        except Exception as e:
            log(e)

    return results

def log(input):
    with open(config.LOG_LOCATION, 'a') as f:
        f.write( str( input ) )
        f.write('\n')

def print_out_menu_options(options, multi_choice=False, func=None):
    if len(options) == 0:
        print('No results found')
        time.sleep(2)
        return None
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
            dashed_option_choices = re.findall(r'[0-9]{1,2}\ ?\-\ ?[0-9]{1,2}', result)
            result = re.sub(r'[0-9]{1,2}\ ?\-\ ?[0-9]{1,2}', '', result)
            result_list = result.split(' ')
            result_list = list(filter(None, result_list))

            for choice in dashed_option_choices:
                choice_list = choice.split('-')
                try:
                    for i in range(int(choice_list[0]), int(choice_list[1])+1):
                        result_list.append(i)
                except ValueError:
                    pass

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

def search_by_keyword():
    try:
        os.system('clear')
        result = input('enter keywords: ')
        command = "get_iplayer --field=name,episode {}".format(result)
        return print_out_menu_options( execute_search(command), True, add_to_download_queue )
    except KeyboardInterrupt:
        return None

def list_channels():
    try:
        list_of_channels =["BBC One","BBC Two","BBC Three","BBC Four","BBC Radio 1","CBBC","CBeebies","BBC Scotland","BBC News","BBC Parliament","BBC Alba","S4C"]
        while True:
            os.system('clear')
            for itx,channel in enumerate(list_of_channels):
                print("{}. {}".format(itx+1,channel))
            result = input('choose channel: ')
            if result == 'q':
                break
            try:
                result = int(result)
                if (result - 1) <= len(list_of_channels):
                    command = "get_iplayer --channel='{}' '.*'".format(list_of_channels[result-1])
                    return print_out_menu_options( execute_search(command), True, add_to_download_queue )
            except ValueError:
                log('valueError')
    except KeyboardInterrupt:
        return None


    

def add_to_download_queue(episode):
    download_queue.append(episode)

def main():
    os.system('clear')
    while True:
        os.system('clear')
        print('number 1 search by keywords')
        print('number 2 results by channel')
        print('number 3 begin downloads')
        try:
            result = input('choice ')
        except KeyboardInterrupt:
            break
        try:
            result = int( result )
            if result == 1:
                search_by_keyword()
            elif result == 2:
                list_channels()
            elif result == 3:
                if len( download_queue ) > 0:
                    output_path = os.getcwd() + ':/save-here'
                    command = """docker run --privileged=true --cap-add=NET_ADMIN --device /dev/net/tun:/dev/net/tun -v """ + output_path + """ -w=/save-here -it iget:latest bash -c '/quick.sh """
                    for each in download_queue:
                        command += each.id + " "
                    command += "'"
                    log(command)
                    subprocess.run(command, shell=True)
                    # pids = []
                    # for each in download_queue:
                    #     pids.append(each.id.strip())
                    # command = ['get-iplayer','---pid={}'.format( ','.join(pids) )]
                    # log(command)
                    # subprocess.run(command, shell=True)
                    download_queue.clear()
            elif result == 99:
                log(len(download_queue))

        except ValueError:
            if result == 'q':
                break



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--help' or sys.argv[1] == '-h':
        print('Usage: bbc')
        print('Usage: Script to inteact with get_iplayer script')
        print("Usage: Allows user to interact and search BBC's iplayer for shows to download. It gets the PID of each episdoe and passes that as arguments to a docker container that uses a VPN to the UK to get around the geo-fencing.")
    else:
        width = int( subprocess.check_output(['tput','cols']) )
        height = int( subprocess.check_output(['tput','lines']) ) -1
        download_queue = []
        main()
