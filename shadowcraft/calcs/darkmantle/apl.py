from copy import deepcopy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_event import GenericEvent
from shadowcraft.core import exceptions
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data

class APL(GenericEvent):
    _name = 'apl'
    
    def try_to_populate(self):
        #forks into a separate method to reduce having to rewrite core logic
        if self.engine.end_calc_branch(self.time, self.total_damage):
            self.final_breakdown = self.breakdown
            return
        if self.children != None:
            return
        self.child_populate()
        
    def child_populate(self):
        #basic functionality
        self.update_power_regen()
        
        #
        a = self.spec_apl()
        if a != 'wait':
            t = self.time + self.engine.settings.latency
            
            n = (t, a, False)
            self.engine.insert_event_into_timeline(self, n)
            
            self.engine.insert_event_into_timeline(self, (self.time + self._gcd_size, 'apl', None))
        else:
            a = 'apl'
            t = self.time + self.engine.settings.apl_cd #apl_cd is just the interval of how often to check when there's nothing to do
            
            n = (t, a, False)
            self.engine.insert_event_into_timeline(self, n)
        
        
        next_event = self.timeline.pop(0)
        
        o1 = self.engine.get_next_attack(next_event[1])(self.engine, self.breakdown, next_event[0],
                                                        self.timeline, self.total_damage, self.state_values, self, next_event[2])
        
        self.children = [o1]
        self.probabilities = [1.0]
    
    def spec_apl(self):
        if self.engine.can_cast_ability('revealing_strike', self.state_values):
            if self.state_values['current_second_power'] < self.state_values['max_second_power']:
                if 'revealing_strike' not in self.state_values['auras']:
                    return 'revealing_strike'
        if self.engine.can_cast_ability('sinister_strike', self.state_values):
            if self.state_values['current_second_power'] < self.state_values['max_second_power']:
                return 'sinister_strike'
        if self.engine.can_cast_ability('eviscerate', self.state_values):
            if self.state_values['current_second_power'] == self.state_values['max_second_power']:
                return 'eviscerate'
        return 'wait'