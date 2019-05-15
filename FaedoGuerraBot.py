import numpy as np
import pickle
import time
import shutil
import os
import random

from constants import *
import game_engine, game_graphics, telegram_bot, report

import copy

channel_name = '@FaedoGuerraBotTestChannel'

def send_all_floors(state):
    for i, f in state['floors'].items():
        img = game_graphics.draw_floor(i, f, state['rooms'], fake_description, True)
        img.save('img%s.png' % i, 'PNG')
    telegram_bot.send_photo_group(channel_name, [open('img%s.png' % i, 'rb')
        for i in sorted(state['floors'].keys(), key = lambda i: state['floors'][i]['altitude'])])
    for i in state['floors']:
        os.remove('img%s.png' % i)
        
def begin_func(state):
    telegram_bot.send_message(channel_name, 'Sta per cominciare la Grande Guerra del Faedo: tenetevi pronti!')
    telegram_bot.send_message(channel_name, 'Ecco l\'elenco dei prodi combattenti')
    img = game_graphics.draw_players_list(state['rooms'])
    img.save('ProdiCombattenti.png', 'PNG')
    telegram_bot.send_document(channel_name, open('ProdiCombattenti.png', 'rb'))
    os.remove('ProdiCombattenti.png')
    send_all_floors(state)
    b_time = time.localtime(state['next_iteration'])
    telegram_bot.send_message(channel_name,
        'Le ostilità si apriranno ufficialmente il %s alle ore %s'
        % (time.strftime('%d/%m/%y', b_time), time.strftime('%H:%M', b_time)))

def end_func(state, survivor):
    telegram_bot.send_message(channel_name, 'La Grande Guerra del Faedo è terminata')
    send_all_floors(state)
    telegram_bot.send_message(channel_name, '%s è Campione del Faedo!' % state['rooms'][survivor]['person'])

def save_func(state):
    shutil.copy(save_file, save_backup_file)
    pickle.dump(state, open(save_file, 'wb'))

def prep_func(state, description):
    img = game_graphics.draw_full_image(state, description)
    img.save('img.png', 'PNG')

def main_func(state, description):
    rep = report.pretty_report(state['rooms'], description)
    telegram_bot.send_photo(channel_name, open('img.png', 'rb'), caption = rep)
    os.remove('img.png')
    print('Turno %d' % state['iterations'])
    print(rep)

state0 = pickle.load(open(save_file, 'rb'))
while True:
    if 'random_state' not in state0:
        state0['random_state'] = random.getstate()
        state0['np_random_state'] = np.random.get_state()
    print('Simulazione in corso...')
    state = copy.deepcopy(state0)
    state['next_iteration'] = time.time()
    epic_battle = False
    def do_nothing(*args):
        pass
    def test_epic_battle(state, description):
        global epic_battle
        if not epic_battle:
            leaders = {r['owner'] : 0 for r in state['rooms'].values() if r['owner']}
            for r in state['rooms'].values():
                if r['owner']:
                    leaders[r['owner']] += 1
            if sum(1 for c in leaders.values() if 50 <= c <= 80) >= 2:
                epic_battle = True
    game_engine.main_loop(state, 0, do_nothing, do_nothing, do_nothing, do_nothing, test_epic_battle)
    if state['iterations'] <= max_iterations and epic_battle:
        print('La Grande Guerra del Faedo durerà %d turni' % state['iterations'])
        break
    print('La simulazione è durata %d turni, %s battaglie epiche' % (state['iterations'], 'con' if epic_battle else 'senza'))
    del state0['random_state']
    del state0['np_random_state']

game_engine.main_loop(state0, 0, begin_func, end_func, save_func, prep_func, main_func)