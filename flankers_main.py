import csv
import numpy.random
import yaml
import random
import atexit
import codecs

from typing import List, Dict
from os.path import join
from psychopy import visual, event, logging, gui, core

@atexit.register
def save_beh_results() -> None:
    """
    Save results of experiment. Decorated with @atexit in order to make sure, that intermediate
    results will be saved even if interpreter will break.

    Returns:
        Nothing.
    """
    file_name = PART_ID + '_' + str(random.choice(range(100, 1000))) + '_beh.csv'
    if open(join('results', file_name), 'w', encoding='utf-8') == -1:
        open(join('results', file_name), 'x', encoding='utf-8')

    with open(join('results', file_name), 'w', encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()

def read_text_from_file(file_name: str, insert: str = '') -> str:
    """
    Method that read message from text file, and optionally add some
    dynamically generated info.
    Args:
        file_name: Name of file to read
        insert:

    Returns:
        String to display.
    """
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)

def check_exit(conf, key: str = '') -> None:
    """
    Check if exit button pressed.

    Returns:
        Nothing.
    """
    key = conf['EXIT_KEY']
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error('Experiment finished by user! {} pressed.'.format(key))

def show_info(conf, win: visual.Window, file_name: str, insert: str = '', resol_width: int = 0, height = 0) -> None:
    """
    Clear way to show info message into screen.
    Args:
        win:
        file_name:
        insert:

    Returns:
        Nothing.
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color=conf['STIM_COLOR'], text=msg, height=height, wrapWidth=resol_width)
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=conf['WAIT_KEYS'])
    if key[0] == conf['EXIT_KEY']:
        abort_with_error('Experiment finished by user on info screen! {} pressed.'.format(key))
    win.flip()

def abort_with_error(err: str) -> None:
    """
    Call if an error occurred.

    Returns:
        Nothing.
    """
    logging.critical(err)
    raise Exception(err)

def gen_stim(conf) -> List[str]:
    gen_lista: List[str] = []
    stim_str: str = ''

    # losowanie warunku zgodności bodźca zgodnie z częstością ich wystąpienia:
    # warunek tożsamy – 10%, warunek zgodny – 40%, warunek niezgodny – 40%, warunek neutralny – 10%

    target_list: List[str] = conf['TARGET_LETTERS']
    flankers_list: List[str] = conf['FLANKERS']
    warunek_no: int = random.choice(range(1, 11))
    warunek: str = ''
    if warunek_no == 1:                         warunek = 'T'
    elif warunek_no == 2:                       warunek = 'N'
    elif warunek_no > 2 and warunek_no < 7:     warunek = 'Z'
    else :                                      warunek = 'NZ'

    # ---- generowanie ciągu liter ----
    target_no: int = random.choice(range(0, 4))
    flanker_no: int = random.choice(range(0, 2))
    group_no: int = random.choice(range(0, 2))

    # warunek tożsamy
    if warunek == 'T':
        stim_str = (target_list[target_no] + ' ') * 6 + target_list[target_no]

    # warunek neutralny
    elif warunek == 'N':
        stim_str = (flankers_list[4] + ' ') * 3 + target_list[target_no] + (' ' + flankers_list[4]) * 3

    # warunek zgodny:
    elif warunek_no > 2 and warunek_no < 7:
        letter_list: List[str] = conf['TARGET_GROUPS'][group_no]
        stim_str = (letter_list[flanker_no] + ' ') * 3 + letter_list[(flanker_no+1)%2] + (' ' + letter_list[flanker_no]) * 3

    # warunek niezgodny:
    else :
        letter_list_1: List[str] = conf['TARGET_GROUPS'][group_no]
        letter_list_2: List[str] = conf['TARGET_GROUPS'][(group_no+1)%2]
        flanker_no_2: int = random.choice(range(0, 2))
        stim_str = (letter_list_1[flanker_no] + ' ') * 3 + letter_list_2[flanker_no_2] + (' ' + letter_list_1[flanker_no]) * 3

    gen_lista.append(warunek)
    gen_lista.append(stim_str)
    if stim_str[6] == conf['TARGET_GROUPS'][0][0] or stim_str[6] == conf['TARGET_GROUPS'][0][1]:
        gen_lista.append(conf['REACTION_KEYS'][0])
    else:
        gen_lista.append(conf['REACTION_KEYS'][1])

    return gen_lista

# GLOBALS
RESULTS = list()  # list in which data will be colected
RESULTS.append(['Part_ID', 'Session', 'Trial_no', 'Reaction_time', 'Pressed_key', 'Correctness', 'Congruence', 'Stimulus'])  # ... Results header

def main():
    global PART_ID

    info: Dict = {'ID': '', 'Sex': ['M', "F"], 'Age': ''}
    dict_dlg = gui.DlgFromDict(dictionary=info, title='Flanker Experiment')
    if not dict_dlg.OK:
        abort_with_error('Info dialog terminated.')
    PART_ID = info['ID'] + '_' + info['Sex'] + '_' + info['Age']

    conf: Dict = yaml.load(open('config.yaml', encoding='utf-8'), Loader=yaml.SafeLoader)
    frame_rate: int = conf['FRAME_RATE']
    screen_res: List[int] = conf['SCREEN_RES']

    win = visual.Window(screen_res, fullscr=True, monitor='testMonitor', units='pix', color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)

    logging.LogFile(join('results', f'{PART_ID}.log'), level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(frame_rate))
    logging.info('SCREEN RES: {}'.format(screen_res))

    fix_cross = visual.TextStim(win, text='+', height=conf['FIX_CROSS_SIZE'], color=conf['FIX_CROSS_COLOR'])

    # ----- TRAINING -----

    # 2., 4., 6. i 8. trials zdefiniowane, aby upewnić się, że w treningu pojawi się każdy typ warunku

    stim_str_list: List[str] =[]
    warunek_list: List[str] =[]
    press_list: List[str] =[]
    cur_stim: List[str] =[]

    for i in range(conf['NO_TRAINING_TRIALS']):
        cur_stim = gen_stim(conf)
        stim_str_list.append(cur_stim[1])
        warunek_list.append(cur_stim[0])
        press_list.append(cur_stim[2])

    # 2. trial - warunek tożsamy
    target_letter: str = random.choice(conf['TARGET_LETTERS'])
    flanker_letter: str = ''
    warunek_list[1] = 'T'
    stim_str_list[1] = (target_letter + ' ') * 6 + target_letter
    if target_letter == conf['TARGET_GROUPS'][0][0] or target_letter == conf['TARGET_GROUPS'][0][1]:
        press_list[1] = conf['REACTION_KEYS'][0]
    else:
        press_list[1] = conf['REACTION_KEYS'][1]

    # 4. trial - warunek niezgodny
    target_letter = random.choice([conf['TARGET_GROUPS'][0][1], conf['TARGET_GROUPS'][1][0]])
    warunek_list[4] = 'NZ'
    if target_letter == conf['TARGET_GROUPS'][0][1]:
        flanker_letter = conf['TARGET_GROUPS'][1][1]
    else:
        flanker_letter = conf['TARGET_GROUPS'][0][0]
    stim_str_list[4] = (flanker_letter + ' ') * 3 + target_letter + (' ' + flanker_letter) * 3
    if target_letter == conf['TARGET_GROUPS'][0][0] or target_letter == conf['TARGET_GROUPS'][0][1]:
        press_list[4] = conf['REACTION_KEYS'][0]
    else:
        press_list[4] = conf['REACTION_KEYS'][1]

    # 6. trial - warunek zgodny
    target_letter = random.choice([conf['TARGET_GROUPS'][0][0], conf['TARGET_GROUPS'][1][0]])
    warunek_list[6] = 'Z'
    if target_letter == conf['TARGET_GROUPS'][0][0]:
        flanker_letter = conf['TARGET_GROUPS'][0][1]
    else:
        flanker_letter = conf['TARGET_GROUPS'][1][1]
    stim_str_list[6] = (flanker_letter + ' ') * 3 + target_letter + (' ' + flanker_letter) * 3
    if target_letter == conf['TARGET_GROUPS'][0][0] or target_letter == conf['TARGET_GROUPS'][0][1]:
        press_list[6] = conf['REACTION_KEYS'][0]
    else:
        press_list[6] = conf['REACTION_KEYS'][1]

    # 8. trial - warunek neutralny
    target_letter = random.choice(conf['TARGET_LETTERS'])
    warunek_list[8] = 'N'
    stim_str_list[8] = (conf['FLANKERS'][4] + ' ') * 3 + target_letter + (' ' + conf['FLANKERS'][4]) * 3
    if target_letter == conf['TARGET_GROUPS'][0][0] or target_letter == conf['TARGET_GROUPS'][0][1]:
        press_list[8] = conf['REACTION_KEYS'][0]
    else:
        press_list[8] = conf['REACTION_KEYS'][1]

    # Instruction before training
    show_info(conf, win, "instrukcja_trening.txt", "", screen_res[0], conf['INSTRUCTION_SIZE'])

    # Break before training
    show_info(conf, win, "przerwa_trening.txt", "", screen_res[0], conf['BREAK_INFO_SIZE'])

    clock = core.Clock()

    # Training trials + feedback
    for i in range(conf['NO_TRAINING_TRIALS']):
        reaction_time, response, acc, warunek, stim_str = run_training(win, conf, clock, fix_cross, stim_str_list[i], warunek_list[i], press_list[i])
        RESULTS.append([PART_ID,'training', i+1, reaction_time * 1000, response, acc, warunek, stim_str])
        if acc == 1:
            feedb = "Poprawna odpowiedź"
        elif acc == -1:
            feedb = "Niepoprawna odpowiedź"
        else:
            feedb = "Nie udzielono odpowiedzi"

        feedb = visual.TextStim(win, text=feedb, height=conf['FEEDBACK_SIZE'], color=conf['STIM_COLOR'], wrapWidth= conf['SCREEN_RES'][0])
        feedb.draw()
        win.flip()
        core.wait(2)
        win.flip()

    # ----- EXPERIMENT -----

    # Instruction
    show_info(conf, win, "instrukcja_eksp.txt", "", screen_res[0], conf['INSTRUCTION_SIZE'])

    # Blocks
    for i in range(conf['NO_EXPERIMENT_BLOCKS']):
        if i > 0:
            show_info(conf, win, "przerwa.txt", "", screen_res[0], conf['BREAK_INFO_SIZE'])
        else:
            show_info(conf, win, "przerwa_eksp.txt", "", screen_res[0], conf['BREAK_INFO_SIZE'])

    # Experimental trials
        for j in range(conf['NO_EXPERIMENT_TRIALS']):
            reaction_time, response, acc, warunek, stim_str = run_experiment(win, conf, clock, fix_cross)
            RESULTS.append([PART_ID, 'experiment{}'.format(i+1), j+1, reaction_time * 1000 , response, acc, warunek, stim_str])

    # Ending info
    show_info(conf, win, "zakonczenie.txt", "", screen_res[0], conf['BREAK_INFO_SIZE'])
    win.close()
    core.quit()

def run_training(win, conf, clock, fix_cross, stim_str, warunek, key_press):
    reaction_time: float = 0
    acc: int = 0
    response: str = 'None'
    stim = visual.TextStim(win, text=stim_str, height=conf['STIM_SIZE'], color=conf['STIM_COLOR'], wrapWidth= conf['STIM_SIZE'] * 15)

    # ----- Start training -----
    # This part is time-crucial. All stims must be already prepared.
    # Only .draw() .flip() and reaction related stuff goes there.
    event.clearEvents()

    # ----- Training trial -----
    fix_cross.draw()
    win.flip()
    core.wait(conf['FIX_CROSS_TIME'])

    win.flip()
    core.wait(conf['STIM_DELAY'])
    stim.draw()
    win.callOnFlip(clock.reset)
    win.callOnFlip(event.clearEvents)
    win.flip()
    core.wait(conf['STIM_TIME'])
    win.flip()
    for _ in range(conf['REACTION_TIME']):
        reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']), timeStamped=clock)
        reaction_time = clock.getTime()
        core.wait(numpy.random.random() / conf['FRAME_RATE'])
        check_exit(conf)
        if reaction:
            response = reaction[0][0]
            if reaction[0][0] == key_press:
                acc = 1
            else:
                acc = -1
            break
        if not reaction:
            reaction_time = 0
        core.wait(numpy.random.random() / conf['FRAME_RATE'])

    return reaction_time, response, acc, warunek, stim_str

def run_experiment(win, conf, clock, fix_cross):
    """
    Prepare and present single trial of experiment.
    Input (params) should consist all data need for presenting stimuli.
    Returns:
        All behavioral data (reaction time, answer, etc. should be returned from this function).
    """
    reaction_time: float = 0
    acc: int = 0
    response: str = 'None'

    # ----- Trial-related stimulus -----
    lista: List[str] = gen_stim(conf)
    stim = visual.TextStim(win, text=lista[1], height=conf['STIM_SIZE'], color=conf['STIM_COLOR'], wrapWidth=conf['STIM_SIZE'] * 15)

    # ----- Start trial -----
    # This part is time-crucial. All stims must be already prepared.
    # Only .draw() .flip() and reaction related stuff goes there.
    event.clearEvents()

    core.wait(conf['FIX_CROSS_TIME'])
    fix_cross.draw()
    win.flip()
    core.wait(conf['FIX_CROSS_TIME'])
    win.flip()
    core.wait(conf['STIM_DELAY'])
    stim.draw()
    win.callOnFlip(clock.reset)
    win.callOnFlip(event.clearEvents)
    win.flip()
    core.wait(conf['STIM_TIME'])
    win.flip()
    for _ in range(conf['REACTION_TIME']):
        reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']), timeStamped=clock)
        reaction_time = clock.getTime()
        core.wait(numpy.random.random() / conf['FRAME_RATE'])
        check_exit(conf)
        if reaction:
            response = reaction[0][0]
            if reaction[0][0] == lista[2]:
                acc = 1
            else:
                acc = -1
            break
        if not reaction:
            reaction_time = 0
        core.wait(numpy.random.random() / conf['FRAME_RATE'])

    return reaction_time, response, acc, lista[0], lista[1]

if __name__ == '__main__':
    PART_ID = ''
    main()
