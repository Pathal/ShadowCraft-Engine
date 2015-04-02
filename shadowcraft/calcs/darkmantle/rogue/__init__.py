from copy import deepcopy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

import shadowcraft
from shadowcraft.calcs.darkmantle import DarkmantleCalculator
from shadowcraft.calcs.darkmantle.rogue import mh_attack
from shadowcraft.calcs.darkmantle.rogue import oh_attack
from shadowcraft.calcs.darkmantle.rogue import instant_poison
from shadowcraft.core import exceptions
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data


class InputNotModeledException(exceptions.InvalidInputException):
    # I'll return these when inputs don't make sense to the model.
    pass

class RogueDarkmantleCalculator(DarkmantleCalculator):
    abilities_list = {
        'mh_autoattack': mh_attack,
        'oh_autoattack': oh_attack,
        'instant_poison': instant_poison,
    }    
    ability_constructors = {
        'mh_autoattack': mh_attack.MHAttack,
        'oh_autoattack': oh_attack.OHAttack,
        'instant_poison': instant_poison.InstantPoison,
    }
    
    def get_next_attack(self, name):
        #pulls the constructor, not the module
        if name not in self.ability_constructors:
            raise InputNotModeledException(_('Can\'t locate action: {action}').format(action=str(name)))
        return self.ability_constructors[name]
    
    def can_cast_ability(self, name):
        if abilities_list._cost < self.state_values['current_power'] and self.state_values['cooldown'][name] < self.time:
            return True
        return False
    
    def _get_values_for_class(self):
        #override global states if necessary
        if self.settings.is_combat_rogue():
            self.base_dw_miss_rate = 0
        
        #initialize variables into a table that won't disappear throughout the calculations
        #additionally, set up data structures (like combo points)
        class_table = {}
        class_table['current_second_power'] = 0 #combo points
        class_table['max_second_power'] = 5 #can only get to 5 CP (for now?)
        
        class_table['max_power'] = 100 #energy
        if self.settings.is_assassination_rogue():
            class_table['max_power'] += 20
        if self.glyphs.energy:
            class_table['max_power'] += 20
        if self.talents.lemon_zest:
            class_table['max_power'] += 15
        if self.stats.gear_buffs.rogue_pvp_4pc_extra_energy():
            class_table['max_power'] += 30
        class_table['current_power'] = class_table['max_power']
        class_table['base_power_regen'] = 10
        if self.settings.is_combat_rogue():
            class_table['base_power_regen'] *= 1.2
        
        if self.talents.anticipation:
            class_table['anticipation'] = 0
            class_table['anticipation_max'] = 5
        if self.settings.is_combat_rogue():
            class_table['bg_counter'] = 0
        
        return class_table
    
    def _class_bonus_crit(self):
        return .05 #rogues get a "free" 5% extra crit
    
    def get_dps(self):
        if self.settings.is_assassination_rogue():
            return self.assassination_dps_estimate()
        elif self.settings.is_combat_rogue():
            return self.combat_dps_estimate()
        elif self.settings.is_subtlety_rogue():
            return self.subtlety_dps_estimate()
        else:
            raise InputNotModeledException(_('You must specify a spec.'))

    def get_dps_breakdown(self):
        if self.settings.is_assassination_rogue():
            return self.assassination_dps_breakdown()
        elif self.settings.is_combat_rogue():
            return self.combat_dps_breakdown()
        elif self.settings.is_subtlety_rogue():
            return self.subtlety_dps_breakdown()
        else:
            raise InputNotModeledException(_('You must specify a spec.'))
    
    def assassination_dps_estimate(self):
        return sum(self.assassination_dps_breakdown().values())
    def assassination_dps_breakdown(self):
        #determine pre-fight sequence, establish baseline event_queue and auras
        #read priority list, determine first action
        #load event_state object with event_queue
        return {'none':1.}
    
    def combat_dps_estimate(self):
        return sum(self.combat_dps_breakdown().values())
    def combat_dps_breakdown(self):
        print 'Calculating Combat Breakdown...'
        breakdown = {}
        total_damage = 0
        event_queue = []
        time = 0
        #determine pre-fight sequence, establish baseline event_queue and auras
        #read priority list, determine first action
        #load event_state object with event_queue
        #              (time, name, multistrike)
        event_queue = [(0.0, 'mh_autoattack', False), (0.01, 'oh_autoattack', False)] #temporary for development purposes
        #self.combat_priority_list() #should determine opener, as well as handle normal rotational decisions
        first_event = event_queue.pop(0)
        current_node = self.get_next_attack(first_event[1])(self, deepcopy(breakdown), deepcopy(time), deepcopy(event_queue),
                                                            deepcopy(total_damage), deepcopy(self.state_values), None)
        
        l=0
        while True:
            print l
            l += 1
            current_node.try_to_populate()
            
            if current_node.has_next_child():
                print "children: "
                for e in current_node.children:
                    print " ", e._name 
                print "going from ", current_node._name
                current_node = current_node.get_next_child()
                print "        to ", current_node._name, current_node.current_child
            else:
                print "Reached bottom!"
                #else return breakdown average to parent
                if current_node.parent == None:
                    #this means we're at the root node, lets split this joint!
                    print "And we're done!"
                    return current_node.final_breakdown
                current_node.send_data_to_parent()

                p = current_node.parent
                current_node = None #kill the data to clean up memory
                current_node = p

        return breakdown
    
    def combat_priority_list(self):
        action = 'wait'
        if self.state_values['current_energy'] > 50 and self.state_values['combo_points'] < self.state_values['max_second_power']:
            action = 'sinister_strike'
        if self.state_values['current_energy'] > 35 and self.state_values['combo_points'] == self.state_values['max_second_power']:
            action = 'eviscerate'
        if self.state_values:
            return
        return action
    
    def get_breakdown(self, queue):
        breakdown = {}
        return
    
    def subtlety_dps_estimate(self):
        return sum(self.subtlety_dps_breakdown().values())
    def subtlety_dps_breakdown(self):
        #determine pre-fight sequence, establish baseline event_queue and auras
        #read priority list, determine first action
        #load event_state object with event_queue
        return {'none':1.}
    