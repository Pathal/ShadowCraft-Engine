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

class RemoveAura(GenericEvent):
    _name = 'remove_aura'
    _hand = 'mh'
    _cost = 0
    _gcd_size = 0
    _stance = None #the stance(s) required
    _cost_secondary = 0
    _cast_time = 0.0
    _required_stances = None #otherwise, use an array
    
    
    def child_populate(self):
        #this is a basic child populator method. crits, nor multistrikes, matter with this method.
        #b0 = deepcopy(self.breakdown) #miss
        next_event = self.timeline.pop(0)
        
        #basic functionality
        self.update_power_regen()
        
        self.remove_first_aura_occurance(next_event[2])
        
        o1 = self.engine.get_next_attack(next_event[1])(self.engine, self.breakdown, next_event[0], self.timeline,
                                                        self.total_damage, self.state_values, self, extra=next_event[2])
        
        self.children = [o1]
        self.probabilities = [1.0] #the likelihood of the corrosponding child occuring
