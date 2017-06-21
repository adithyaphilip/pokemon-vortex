import requests
import re
import time
import sys
import random

import util

random.seed(100)

BASE_GAME_URL = 'http://zeta.pokemon-vortex.com/'


def login(username, password, session):
    login_page = "http://www.pokemon-vortex.com/login.php"
    login_request_url = BASE_GAME_URL + "checklogin.php"
    data = {"myusername": username, "mypassword": password}

    session.get(login_page)
    response = session.post(login_request_url, data)
    # if login success, you get the below url
    return 'dashboard.php' in response.url


def search_pokemon(map_val: int, move_val: int, main_val, session):
    url = BASE_GAME_URL + 'xml/toolbox.php?map=%d&move=%d&main=%d' % (map_val, move_val, main_val)
    response = session.get(url)
    if 'form name=' in response.content.decode('utf-8'):
        # pokemon found
        pokemon = re.search(r'pokemon/(.+?)\.gif', response.content.decode('utf-8')).group(1)
        level = int(re.search(r'Level: (\d+?) &lt', response.content.decode('utf-8')).group(1))
        return pokemon, level, 'http://static.pokemon-vortex.com/images/misc/pb.gif' in response.content.decode('utf-8')
    else:
        return None


def start_battle(session: requests.session):
    url = BASE_GAME_URL + "wildbattle.php"
    data = {"wildpoke": "Battle", "39741": "Battle!"}
    response = session.post(url, data)
    return response


def choose_pokemon(session: requests.session, pokemon_id: str):
    url = BASE_GAME_URL + "wildbattle.php?&ajax=1"
    data = {"bat": "1", "action": "1", "active_pokemon": pokemon_id}
    return session.post(url, data)


def do_attack(session: requests.session, chosen_attack_num: int):
    """
    active_pokemon	15677440 (pichu) 15677568 (unknown m)
    :param session:
    :param chosen_attack_num:
    :return: true if enemy has fainted, false otherwise
    """
    url = BASE_GAME_URL + "wildbattle.php?&ajax=1"
    data = {
        "action": [
            "1",
            "attack"
        ],
        "bat": "1",
        "actionattack": "1",
        "attack": "%d" % chosen_attack_num,
        "1": "Thunder Shock",
        "2": "Disarming Voice",
        "3": "Reversal",
        "4": "Thunder Wave",
        "o1": "Razor Wind",
        "o2": "Parabolic Charge",
        "o3": "Mud-slap",
        "o4": "U-turn"
    }
    # below unchecked Non before group() also helps crash the loop in case of our own pokemon dying
    hp = int(
        re.search(r'/\> (\d+?)\</strong\>\</td\>\n\</tr\>', session.post(url, data).content.decode('utf-8')).group(1))
    return hp


def acknowledge_win(session: requests.session):
    url = BASE_GAME_URL + "wildbattle.php?&ajax=1"
    data = {"action": "1", "bat": "1"}
    return session.post(url, data)


def return_map_after_battle(session: requests.session):
    url = BASE_GAME_URL + "map.php?map=11"
    return session.get(url)


def throw_master_ball(session: requests.session):
    return catch_pokemon(session=session, ball_name="Master Ball")


def catch_pokemon(session: requests.session, ball_name="Ultra Ball"):
    data = {
        "o1": "Clamp",
        "o2": "Scratch",
        "o3": "Mud-slap",
        "o4": "Ancient Power",
        "actionattack": [
            "1",
            "1"
        ],
        "action": [
            "1",
            "use_item"
        ],
        "bat": "1",
        "item": ball_name,
        "active_pokemon": "1"
    }
    url = BASE_GAME_URL + "wildbattle.php?&ajax=1"
    return "mon has been caught" in session.post(url, data).content.decode('utf-8')


def main():
    special_types = ["Mystic"]
    fights = 0
    caught = 0
    balls_used = 0
    avg_not_catch_hp = 0
    avg_catch_hp = 0
    pokemon_list = ["15723150", "15723210"]
    legend_seen_ctr = 0
    legends_caught_ctr = 0
    legends_list = util.get_legends()
    fight_counted = False
    while True:
        try:
            session = requests.session()
            print(login("gameburger", "Happiness123_", session))
            while True:
                fight_counted = False
                print("Fights:", fights, "Caught:", caught, "Balls used:", balls_used, "Avg. HP:", avg_catch_hp,
                      "Avg. Not Catch HP:", avg_not_catch_hp, "Legends Seen:", legend_seen_ctr,
                      "Caught:", legends_caught_ctr)
                result = search_pokemon(6, 2, 2, session)
                if result is None:
                    continue
                pokemon, level, is_caught = result
                # if int(level) > 10 and fights < 50:
                #     continue
                fights += 1
                fight_counted = True
                print("Fighting %s Level %s!" % (pokemon, level), "Caught:", is_caught)
                start_battle(session)
                choose_pokemon(session, random.choice(pokemon_list))
                attack_num = 1
                hp = 1  # default value, never really used
                prev_hp = -1
                while hp != 0:
                    print("Attacking with reversal")
                    hp = do_attack(session, attack_num)
                    if prev_hp == hp:
                        attack_num = 5
                    prev_hp = hp
                    is_legendary = any(legend in pokemon for legend in legends_list)
                    if not is_caught and is_legendary:
                        legend_seen_ctr += 1
                        if throw_master_ball(session):
                            legends_caught_ctr += 1
                            break
                        else:
                            catch_pokemon(session)
                    elif pokemon == "Mystic Eevee" or (
                                    not is_caught and 0 < hp <= 40 and any(
                                    special in pokemon for special in special_types)):
                        print("Attempting to catch!")
                        balls_used += 1
                        if catch_pokemon(session):
                            print("Caught pokemon!")
                            avg_catch_hp = caught / (caught + 1) * avg_catch_hp + hp / (caught + 1)
                            caught += 1
                            break
                        else:
                            avg_not_catch_hp = (balls_used - caught - 1) / (
                                balls_used - caught) * avg_not_catch_hp + hp / (balls_used - caught)
                print("Acknowledging win!")
                acknowledge_win(session)
                print("Returning to map!")
                return_map_after_battle(session)
        except Exception as e:
            if fight_counted:
                fights -= 1
            print("ERROR:", e, file=sys.stderr)


if __name__ == '__main__':
    main()
