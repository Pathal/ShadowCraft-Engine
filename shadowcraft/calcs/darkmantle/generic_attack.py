from copy import deepcopy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.rogue import RogueDamageCalculator
from shadowcraft.calcs.darkmantle.generic_event import GenericEvent
from shadowcraft.core import exceptions
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data

class GenericAttack(GenericEvent):
    _name = 'generic_attack'
    _hand = 'mh'
    _can_crit = True
    _can_multistrike = True
    _multistrike_delay = .3
    _cost = 0
    _gcd_size = 1.0
    _stance = None #the stance(s) required
    _cost_secondary = 0
    _cast_time = 0.0
    _required_stances = None #otherwise, use an array
    
    
    #def __init__(self, engine, breakdown, time, timeline, total_damage, state_values, parent):
    #    super(GenericEvent, self).__init__(engine, breakdown, time, timeline, total_damage, state_values, parent)
    
    def calculate_damage(self):
        return 1 #to be overwritten by actual actions
    
    def secondary_effects(self):
        return #to be overwritten
    
    def add_damage_to_breakdown(self, damage, breakdown):
        if self._name in breakdown:
            breakdown[self._name] += damage
        else:
            breakdown[self._name] = damage
        return breakdown
    
    def add_procs_for_hand(self):
        if self._hand == 'mh':
            'add mh and both hand procs'
        elif self._hand == 'oh':
            'add oh and both hand procs'
    
    def try_to_populate(self):
        #forks into a separate method to reduce having to rewrite core logic
        if self.engine.end_calc_branch(self.time, self.total_damage):
            self.final_breakdown = self.breakdown
            return
        if self.children != None:
            return
        self.child_populate()
        
    def child_populate(self):
        #this is a basic child populator method. crits, nor multistrikes, matter with this method.
        #b0 = deepcopy(self.breakdown) #miss
        next_event = self.timeline.pop()
        
        #basic functionality
        self.update_power_regen()
        self.secondary_effects()
        
        #rating=self.stat_values['current_stats']['crit'] is_day=self.engine.settings.is_day
        crit_rate = .15 + self.engine.stats.get_crit_from_rating(rating=self.state_values['current_stats']['crit'])
        crit_rate += self.engine.buffs.buff_all_crit() + self.engine.race.get_racial_crit()
        crit_rate -= self.engine.crit_reduction
        
        multistrike_rate = self.engine.stats.get_multistrike_chance_from_rating(rating=self.state_values['current_stats']['multistrike'])
        multistrike_rate += self.engine.buffs.multistrike_bonus()
        
        d1 = self.calculate_damage()
        d1 = (d1 * (1-crit_rate)) + (2.0 * d1 * crit_rate) #dummy 80% chance normal, 20% chance crit for now
        d1 *= 1 + 2 * multistrike_rate * .3 #multistrike
        b1 = self.add_damage_to_breakdown(d1, deepcopy(self.breakdown)) #normal
        t1 = self.total_damage + d1
        o1 = self.engine.get_next_attack(next_event[1])(self.engine, b1, next_event[0], self.timeline, t1, self.state_values, self)
        
        self.children = [o1]
        self.probabilities = [1.0] #the likelihood of the corrosponding child occuring
        
    
    def bonus_crit_rate(self):
        return 0
    
    def bonus_crit_damage(self):
        return 0
    
