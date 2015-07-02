from copy import deepcopy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_attack import GenericAttack

class Eviscerate(GenericAttack):
    _name = 'Eviscerate'
    _cost = 35
    
    def calculate_damage(self, cp):
        # non-normalized weapon strike => (mh_weapon_damage + ap / 3.5 * weapon_speed) * weapon_damage_percentage
        return .3 * cp * self.state_values['effective_ap']
    
    def child_populate(self):
        #this is a basic child populator method. crits, nor multistrikes, matter with this method.
        #b0 = deepcopy(self.breakdown) #miss
        next_event = self.timeline.pop(0)
        
        cp = self.state_values['current_second_power']
        self.state_values['current_second_power'] = self.state_values['anticipation']
        self.state_values['anticipation'] = 0
        
        #basic functionality
        self.update_power_regen()
        self.queue_up_procs()
        
        #rating=self.stat_values['current_stats']['crit'] is_day=self.engine.settings.is_day
        crit_rate = .15 + self.engine.stats.get_crit_from_rating(rating=self.state_values['current_stats']['crit'])
        crit_rate += self.engine.buffs.buff_all_crit() + self.engine.race.get_racial_crit()
        crit_rate -= self.engine.crit_reduction
        
        multistrike_rate = self.engine.stats.get_multistrike_chance_from_rating(rating=self.state_values['current_stats']['multistrike'])
        multistrike_rate += self.engine.buffs.multistrike_bonus()
        
        d1 = self.calculate_damage(cp)
        d1 = (d1 * (1-crit_rate)) + (2.0 * d1 * crit_rate)
        d1 *= 1 + 2 * multistrike_rate * .3
        b1 = self.add_damage_to_breakdown(d1, deepcopy(self.breakdown))
        t1 = self.total_damage + d1
        o1 = self.engine.get_next_attack(next_event[1])(self.engine, b1, next_event[0], self.timeline, t1, deepcopy(self.state_values), self, next_event[2])
        
        self.children = [o1]
        self.probabilities = [.2*cp] #the likelihood of the corrosponding child occuring
        
        if cp != 5:
            states = deepcopy(self.state_values['auras'])
            o2 = self.engine.get_next_attack(next_event[1])(self.engine, self.breakdown, next_event[0], self.timeline, self.total_damage, self.state_values, self, next_event[2])
            
            self.children.append(o0)
            self.probabilities.append(.2*(1-cp))
    