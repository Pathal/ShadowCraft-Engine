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
    _stance = None #the stance(s) required
    _cost_secondary = 0
    _cast_time = 0.0
    
    #def __init__(self, engine, breakdown, time, timeline, total_damage, state_values, parent):
    #    super(GenericEvent, self).__init__(engine, breakdown, time, timeline, total_damage, state_values, parent)
    
    def calculate_damage(self):
        return 1 #to be overwritten by actual actions
    
    def secondary_effects(self):
        return
    
    def add_damage_to_breakdown(self, damage, breakdown):
        if self._name in breakdown:
            breakdown[self._name] += damage
        else:
            breakdown[self._name] = damage
        return breakdown
    
    def try_to_populate(self):
        if self.engine.end_calc_branch(self.time, self.total_damage):
            print self.breakdown
            return
        #b0 = deepcopy(self.breakdown) #miss
        next_event = self.timeline[0]
        self.timeline = self.timeline[1:]
        self.timeline.append((self.time + self.engine.stats.mh.speed, self._name, False))
        
        d1 = self.calculate_damage()
        b1 = self.add_damage_to_breakdown(d1, deepcopy(self.breakdown)) #normal
        t1 = self.total_damage + d1
        o1 = self.engine.get_next_attack(next_event[1])(self.engine, b1, next_event[0], self.timeline, t1, self.state_values, self)
        print "child1", self._name, d1
        
        d2 = self.calculate_damage() * 2 #TODO
        b2 = self.add_damage_to_breakdown(d2, deepcopy(self.breakdown)) #crit
        t2 = self.total_damage + d2
        o2 = self.engine.get_next_attack(next_event[1])(self.engine, b2, next_event[0], self.timeline, t2, self.state_values, self)
        print "child2", self._name, d2
        
        self.children = [o1, o2]
        self.probabilities = [.8, .2]
        
    
    def bonus_crit_rate(self):
        return 0
    
    def bonus_crit_damage(self):
        return 0
    
    def can_cast(self, state):
        if state['current_power'] < _cost:
            return False
        if state['stance'] not in _stance or _stance is None:
            return False
        return True
    
