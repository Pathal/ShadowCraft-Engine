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
            self.insert_event_into_timeline(n)
            
            self.insert_event_into_timeline((self.time + self.engine.settings.latency + self._gcd_size, 'apl', None))
        else:
            a = 'apl'
            t = self.time + self.engine.settings.apl_cd #apl_cd is just the interval of how often to check when there's nothing to do
            
            n = (t, a, False)
            self.insert_event_into_timeline(n)

        
        
        next_event = self.timeline.pop()
        
        o1 = self.engine.get_next_attack(next_event[1])(self.engine, self.breakdown, next_event[0],
                                                        self.timeline, self.total_damage, self.state_values, self)
        
        self.children = [o1]
        self.probabilities = [1.0]
    
    def spec_apl(self):
        return 'wait'
        if self.engine.can_cast_ability('sinister_strike'):
            if self.state_values['current_energy'] > 50 and self.state_values['combo_points'] < self.state_values['max_second_power']:
                return 'sinister_strike'
        if self.engine.can_cast_ability('eviscerate'):
            if self.state_values['current_energy'] > 35 and self.state_values['combo_points'] == self.state_values['max_second_power']:
                return 'eviscerate'
        return 'wait'