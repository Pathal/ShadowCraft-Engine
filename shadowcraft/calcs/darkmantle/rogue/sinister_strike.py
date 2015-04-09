import copy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_attack import GenericAttack

class SinisterStrike(GenericAttack):
    _name = 'Sinister Strike'
    _cost = 50
    
    def calculate_damage(self):
        # non-normalized weapon strike => (mh_weapon_damage + ap / 3.5 * weapon_speed) * weapon_damage_percentage
        return 1.2 * .85 * self.engine.stats.mh.speed * (self.engine.stats.mh.weapon_dps + self.state_values['effective_ap'] / 3.5)
    
    def secondary_effects(self):
        #Added CP, RvS procs can be done as a separate event
        self.state_values['current_second_power'] = min(self.state_values['current_second_power']+1, self.state_values['max_second_power'])
