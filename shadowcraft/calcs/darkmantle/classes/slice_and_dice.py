from copy import deepcopy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_attack import GenericAttack

class SliceAndDice(GenericAttack):
    _name = 'slice_and_dice'
    _cost = 25
    
    def child_populate(self):
        cp = self.state_values['current_second_power']
        d = 6*(1+cp)
        self.state_values['current_second_power'] = 0
        #doesn't consume anticipation stacks
                        
        self.update_power_regen()

        if 'slice_and_dice' not in self.state_values['auras']:
            #if it's not there, add it
            self.state_values['auras'].append('slice_and_dice')
        
        t = self.engine.remove_first_aura_occurance(self, 'slice_and_dice') #removes the aura removal event
        
        if t == None:
            t = d
        else:
            t = min(t+d, 1.3*d)
        self.engine.insert_event_into_timeline(self, (self.time + t, 'remove_aura', 'slice_and_dice'))
        
        next_event = self.timeline.pop(0)
        states = deepcopy(self.state_values['auras'])
        states['current_power'] += 25
        o1 = self.engine.get_next_attack(next_event[1])(self.engine, self.breakdown, next_event[0], self.timeline, self.total_damage, self.state_values, self, next_event[2])
        
        self.children = [o1]
        self.probabilities = [.2*cp]
        
        if cp != 5:
            states = deepcopy(self.state_values['auras'])
            states['current_power'] -= 25
            o2 = self.engine.get_next_attack(next_event[1])(self.engine, self.breakdown, next_event[0], self.timeline, self.total_damage, self.state_values, self, next_event[2])
            
            self.children.append(o0)
            self.probabilities.append(.2*(1-cp))
            