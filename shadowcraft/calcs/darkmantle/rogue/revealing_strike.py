from copy import deepcopy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_attack import GenericAttack

class RevealingStrike(GenericAttack):
    _name = 'Revealing Strike'
    _cost = 40
    
    def calculate_damage(self):
        # non-normalized weapon strike => (mh_weapon_damage + ap / 3.5 * weapon_speed) * weapon_damage_percentage
        return 1.0 * .85 * self.engine.stats.mh.speed * (self.engine.stats.mh.weapon_dps + self.state_values['effective_ap'] / 3.5)
    
    def secondary_effects(self):
        self.state_values['current_second_power'] = min(self.state_values['current_second_power']+1, self.state_values['max_second_power'])
        if 'revealing_strike' not in self.state_values['auras']:
            #if it's not there, add it
            self.state_values['auras'].append('revealing_strike')
        
        t = self.remove_first_aura_occurance('revealing_strike')
        
        if t == None:
            t = 24
        else:
            t = min(t+24, 1.3*24)
        self.insert_event_into_timeline((self.time + t, 'remove_aura', 'revealing_strike'))