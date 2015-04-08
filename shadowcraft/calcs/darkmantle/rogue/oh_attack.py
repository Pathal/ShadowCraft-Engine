import copy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_attack import GenericAttack

class OHAttack(GenericAttack):
    _name = 'oh_autoattack'
    _multistrike_delay = 0.0
    
    def calculate_damage(self):
        # non-normalized weapon strike => (oh_weapon_damage + ap / 3.5 * weapon_speed) * weapon_damage_percentage
        return self.engine.stats.oh.speed * (self.engine.stats.oh.weapon_dps + self.state_values['effective_ap'] / 3.5) * .5
    
    def secondary_effects(self):
        #queue up another attack
        swing_timer = self.engine.stats.oh.speed / self.engine.stats.get_haste_multiplier_from_rating(rating=self.state_values['current_stats']['haste'])
        self.insert_event_into_timeline((self.time + swing_timer, self._name, False))