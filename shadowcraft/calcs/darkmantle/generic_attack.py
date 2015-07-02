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
        #to be overwritten
        #used for setting up data, and reusing inherited child generators.
        return
    
    def add_damage_to_breakdown(self, damage, breakdown):
        if self._name in breakdown:
            breakdown[self._name] += damage
        else:
            breakdown[self._name] = damage
        return breakdown
        
    def child_populate(self):
        #this is a basic child populator method. crits, nor multistrikes, matter with this method.
        #b0 = deepcopy(self.breakdown) #miss
        next_event = self.timeline.pop(0)
        
        #basic functionality
        self.update_power_regen()
        self.secondary_effects()
        self.queue_up_procs()
        
        #rating=self.stat_values['current_stats']['crit'] is_day=self.engine.settings.is_day
        crit_rate = .15 + self.engine.stats.get_crit_from_rating(rating=self.state_values['current_stats']['crit'])
        crit_rate += self.engine.buffs.buff_all_crit() + self.engine.race.get_racial_crit()
        crit_rate -= self.engine.crit_reduction
        
        multistrike_rate = self.engine.stats.get_multistrike_chance_from_rating(rating=self.state_values['current_stats']['multistrike'])
        multistrike_rate += self.engine.buffs.multistrike_bonus()
        
        d1 = self.calculate_damage()
        d1 = (d1 * (1-crit_rate)) + (2.0 * d1 * crit_rate)
        d1 *= 1 + 2 * multistrike_rate * .3
        b1 = self.add_damage_to_breakdown(d1, deepcopy(self.breakdown))
        t1 = self.total_damage + d1
        o1 = self.engine.get_next_attack(next_event[1])(self.engine, b1, next_event[0], self.timeline, t1, deepcopy(self.state_values), self, next_event[2])
        
        self.children = [o1]
        self.probabilities = [1.0] #the likelihood of the corrosponding child occuring
    
    
