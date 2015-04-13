from copy import deepcopy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_attack import GenericAttack

class SwiftPoison(GenericAttack):
    _name = 'swift_poison'
    _cost = 0
    _cast_time = 0.0
    
    def calculate_damage(self):
        # non-normalized weapon strike => (mh_weapon_damage + ap / 3.5 * weapon_speed) * weapon_damage_percentage
        return self.state_values['effective_ap'] * .20 #???
    
    def child_populate(self):
        #this is a basic child populator method. crits, nor multistrikes, matter with this method.
        #b0 = deepcopy(self.breakdown) #miss
        next_event = self.timeline.pop(0)
                
        #rating=self.stat_values['current_stats']['crit'] is_day=self.engine.settings.is_day
        crit_rate = .15 + self.engine.stats.get_crit_from_rating(rating=self.state_values['current_stats']['crit'])
        crit_rate += self.engine.buffs.buff_all_crit() + self.engine.race.get_racial_crit()
        crit_rate -= self.engine.crit_reduction
        
        multistrike_rate = self.engine.stats.get_multistrike_chance_from_rating(rating=self.state_values['current_stats']['multistrike'])
        multistrike_rate += self.engine.buffs.multistrike_bonus()
        
        #o0 = self.engine.get_next_attack(next_event[1])(self.engine, self.breakdown, next_event[0], self.timeline, self.total_damage, self.state_values, self)
        
        d1 = self.calculate_damage() * .3 #just average the proc rate into the damage
        d1 = (d1 * (1-crit_rate)) + (2.0 * d1 * crit_rate)
        d1 *= 1 + 2 * multistrike_rate * .3
        b1 = self.add_damage_to_breakdown(d1, deepcopy(self.breakdown))
        t1 = self.total_damage + d1
        o1 = self.engine.get_next_attack(next_event[1])(self.engine, b1, next_event[0], self.timeline, t1, self.state_values, self)        
        
        self.children = [o1]
        self.probabilities = [1.0]