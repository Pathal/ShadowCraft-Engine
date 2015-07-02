# Simple test program to debug + play with assassination models.
from os import path
import sys
sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))

from shadowcraft.calcs.darkmantle import DarkmantleCalculator
from shadowcraft.calcs.darkmantle.classes.rogue import RogueDarkmantleCalculator
from shadowcraft.calcs.darkmantle import settings

from shadowcraft.objects import buffs
from shadowcraft.objects import race
from shadowcraft.objects import stats
from shadowcraft.objects import procs
from shadowcraft.objects import talents
from shadowcraft.objects import glyphs
from shadowcraft.objects import priority_list

from shadowcraft.core import i18n

import time

# Set up language. Use 'en_US', 'es_ES', 'fr' for specific languages.
test_language = 'local'
i18n.set_language(test_language)

start = time.time()

# Set up level/class/race
test_level = 100
test_race = race.Race('blood_elf')
test_class = 'rogue'

# Set up buffs.
test_buffs = buffs.Buffs(
        'short_term_haste_buff',
        'stat_multiplier_buff',
        'crit_chance_buff',
        'mastery_buff',
        'haste_buff',
        'multistrike_buff',
        'versatility_buff',
        'attack_power_buff',
        'physical_vulnerability_debuff',
        'spell_damage_debuff',
        'flask_wod_agi',
        'food_mop_agi'
    )

# Set up weapons.
test_mh = stats.Weapon(410., 2.6, 'sword', 'dancing_steel')
#test_mh = stats.Weapon(420.5, 1.8, 'dagger', 'mark_of_the_shattered_hand')
test_oh = stats.Weapon(410., 2.6, 'sword', 'dancing_steel')

# Set up procs.
test_procs = procs.ProcsList(('assurance_of_consequence', 588), ('draenic_philosophers_stone', 620), 'virmens_bite', 'virmens_bite_prepot', 'archmages_incandescence') #trinkets, other things (legendary procs)

# Set up gear buffs.
test_gear_buffs = stats.GearBuffs('gear_specialization', 'rogue_t17_2pc', 'rogue_t17_4pc') #tier buffs located here

# Set up a calcs object..
test_stats = stats.Stats(test_mh, test_oh, test_procs, test_gear_buffs,
                         agi=3650,
                         stam=2426,
                         crit=1039,
                         haste=1100,
                         mastery=1015,
                         readiness=0,
                         versatility=122,
                         multistrike=1034,)

# Initialize talents..
test_talents = talents.Talents('3111121', test_class, test_level)

# Initialize talents..
test_talents = talents.Talents('332213', test_class, test_level)

# Just a priority list to define the course of actions
#priority_list = PriorityList()#'prepot = prefight,!buff.stealth',
                             #'stealth = prefight,!buff.stealth',
                             #'ambush = buff.stealth')

# Set up glyphs.
glyph_list = ['recuperate']
test_glyphs = glyphs.Glyphs(test_class, *glyph_list)

# Set up settings.
test_cycle = settings.CombatCycle()
test_settings = settings.Settings(test_cycle, response_time=.5, latency=.03, merge_damage=True, style='time', limit=30)

# Build a DPS object.
calculator = RogueDarkmantleCalculator(test_stats, test_talents, test_glyphs, test_buffs, test_race, test_settings, test_level)

# Compute DPS Breakdown.
dps_breakdown = calculator.get_dps_breakdown()
total_dps = sum(entry[1] for entry in dps_breakdown.items())

def max_length(dict_list):
    max_len = 0
    for i in dict_list:
        dict_values = i.items()
        if max_len < max(len(entry[0]) for entry in dict_values):
            max_len = max(len(entry[0]) for entry in dict_values)

    return max_len

def pretty_print(dict_list, total_sum = 1., show_percent=False):
    max_len = max_length(dict_list)

    for i in dict_list:
        dict_values = i.items()
        dict_values.sort(key=lambda entry: entry[1], reverse=True)
        for value in dict_values:
            #print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1])
            if show_percent and ("{0:.2f}".format(float(value[1])/total_dps)) != '0.00':
                print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1]) + ' ('+str( "{0:.2f}".format(100*float(value[1])/total_sum) )+'%)'
            else:
                print value[0] + ':' + ' ' * (max_len - len(value[0])), str(value[1])
        print '-' * (max_len + 15)

pretty_print([dps_breakdown], total_sum=total_dps, show_percent=True)
print ' ' * (max_length([dps_breakdown]) + 1), total_dps, _("Average Total Damage")
print "Request time: %s sec" % (time.time() - start)