from copy import deepcopy
import gettext
import __builtin__
import math
from __builtin__ import False
from Carbon.Aliases import false

__builtin__._ = gettext.gettext

import shadowcraft
from shadowcraft.calcs.darkmantle import DarkmantleCalculator
from shadowcraft.calcs.darkmantle import generic_event
from shadowcraft.calcs.darkmantle import remove_aura

from shadowcraft.core import exceptions
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data


class InputNotModeledException(exceptions.InvalidInputException):
    # I'll return these when inputs don't make sense to the model.
    pass

class RogueDarkmantleCalculator(DarkmantleCalculator):
    spec_apl = None
    abilities_list = { }
    
    def try_to_populate(self, node):
        if self.end_calc_branch(node.time, node.total_damage):
            node.final_breakdown = node.breakdown
            return
        if node.children != None:
            return
        #run event method
        self.abilities_list[node.name](node)
    
    def get_next_attack(self, name, node):
        if name[1] not in self.abilities_list:
            raise InputNotModeledException(_('Can\'t locate action: {action}').format(action=str(name)))
        return self.abilities_list[name[1]]
    
    def can_cast_ability(self, name, state):
        action = self.abilities_list[name] #converts a string to an object with stats
        if action._cost > state['current_power']:
            return False
        if action._cost_secondary > state['current_second_power']:
            return False
        if action._required_stances is not None:
            if state['stance'] in action._required_stances:
                return False
        return True
    
    def _get_values_for_class(self):
        #override global states if necessary
        if self.settings.is_combat_rogue():
            self.base_dw_miss_rate = 0
            
        self.abilities_list = {
            'apl': self.apl,
            'remove_aura': self.remove_aura,
        
            'mh_autoattack': self.mh_attack,
            'oh_autoattack': self.oh_attack,
            'swift_poison': self.swift_poison,
            'slice_and_dice': self.slice_and_dice,
            'eviscerate': self.eviscerate,
        
            #combat
            'sinister_strike': self.sinister_strike,
            'revealing_strike': self.revealing_strike,
        }
        
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
        
        class_table['anticipation'] = 0
        class_table['anticipation_max'] = 5
        if self.settings.is_combat_rogue():
            class_table['bg_counter'] = 0
        
        return class_table
    
    def queue_up_procs(self):
        pass
    
    def update_power_regen(self, node):
        regen = node.state_values['base_power_regen'] * self.stats.get_haste_multiplier_from_rating(rating=node.state_values['current_stats']['haste'])
        regen *= (node.time - node.state_values['last_event'])
        node.state_values['current_power'] += regen
        node.state_values['current_power'] = min(node.state_values['current_power'], node.state_values['max_power'])
        node.state_values['last_event'] = node.time
    
    def _class_bonus_crit(self):
        return .05 #rogues get a "free" 5% extra crit
    
    def get_dps(self):
        if self.settings.is_assassination_rogue():
            self.spec_apl=assassination_apl
            return self.assassination_dps_estimate()
        elif self.settings.is_combat_rogue():
            self.spec_apl=combat_apl
            return self.combat_dps_estimate()
        elif self.settings.is_subtlety_rogue():
            self.spec_apl=subtlety_apl
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
        self.spec_apl=assassination_apl
        return {'none':1.}
    
    def combat_dps_estimate(self):
        return sum(self.combat_dps_breakdown().values())
    def combat_dps_breakdown(self):
        print 'Calculating Combat Breakdown...'
        print ""
        self.spec_apl=self.combat_apl
        #determine pre-fight sequence, establish baseline event_queue and auras
        #read priority list, determine first action
        #load event_state object with event_queue
        #              (time, name, extra)
        event_queue = [(0.0, 'mh_autoattack', False), (0.0, 'apl', False), (0.01, 'oh_autoattack', False)] # temporary for development purposes
        #self.combat_priority_list() #should determine opener, as well as handle normal rotational decisions
        return self.tree_walk_algorithm(event_queue)
    def combat_apl(self, node):
        if node.state_values['current_power'] > 40 and node.state_values['current_second_power'] < node.state_values['max_second_power']:
            if 'revealing_strike' not in node.state_values['auras']:
                return 'revealing_strike'
        if node.state_values['current_power'] > 50 and node.state_values['current_second_power'] < node.state_values['max_second_power']:
            return 'sinister_strike'
        if node.state_values['current_power'] > 35 and node.state_values['current_second_power'] == node.state_values['max_second_power']:
            return 'eviscerate'
        return 'wait'
        #ignore below
        if self.can_cast_ability('revealing_strike', node.state_values):
            if node.state_values['current_second_power'] < node.state_values['max_second_power']:
                if 'revealing_strike' not in node.state_values['auras']:
                    return 'revealing_strike'
        if self.can_cast_ability('sinister_strike', node.state_values):
            if node.state_values['current_second_power'] < node.state_values['max_second_power']:
                return 'sinister_strike'
        if self.can_cast_ability('eviscerate', node.state_values):
            if node.state_values['current_second_power'] == node.state_values['max_second_power']:
                return 'eviscerate'
        return 'wait'
    
    def subtlety_dps_estimate(self):
        return sum(self.subtlety_dps_breakdown().values())
    def subtlety_dps_breakdown(self):
        self.spec_apl=subtlety_apl
        return {'none':1.}
    
    
    
    ######################
    # Abilities and Events
    ######################
    
    def apl(self, node):
        self.update_power_regen(node)
        
        a = self.spec_apl(node)
        if a == 'wait':
            a = 'apl'
            t = node.time + self.settings.apl_cd #apl_cd is just the interval of how often to check when there's nothing to do
        else:
            t = node.time + self.settings.latency
            #add another apl to queue down the line if we have something to cast
            self.insert_event_into_timeline(node, (node.time + node._gcd_size, 'apl', None))
            
        n = (t, a, False)
        self.insert_event_into_timeline(node, n)
        
        next_event = node.timeline.pop(0)
        
        o1 = generic_event.GenericEvent(self, next_event[1], node.breakdown, next_event[0],
                           node.timeline, node.total_damage, node.state_values, node, next_event[2])
        
        node.children = [o1]
        node.probabilities = [1.0]
    
    def remove_aura(self, node):
        #this is a basic child populator method. crits, nor multistrikes, matter with this method.
        #b0 = deepcopy(self.breakdown) #miss
        next_event = node.timeline.pop(0)
        
        #basic functionality
        self.update_power_regen(node)
        
        self.remove_first_aura_occurance(node, node.extra)
        
        o1 = generic_event.GenericEvent(self, next_event[1], node.breakdown, next_event[0],
                                        node.timeline, node.total_damage, node.state_values, node, next_event[2])
        
        node.children = [o1]
        node.probabilities = [1.0] #the likelihood of the corrosponding child occuring
    
    def mh_attack(self, node):
        #basic functionality
        self.update_power_regen(node)
        swing_timer = self.stats.mh.speed / self.stats.get_haste_multiplier_from_rating(rating=node.state_values['current_stats']['haste'])
        self.insert_event_into_timeline(node, (node.time + swing_timer, node.name, False))
        self.queue_up_procs()
        
        next_event = node.timeline.pop(0)
        
        #rating=self.stat_values['current_stats']['crit'] is_day=self.engine.settings.is_day
        crit_rate = .15 + self.stats.get_crit_from_rating(rating=node.state_values['current_stats']['crit'])
        crit_rate += self.buffs.buff_all_crit() + self.race.get_racial_crit()
        crit_rate -= self.crit_reduction
        
        multistrike_rate = self.stats.get_multistrike_chance_from_rating(rating=node.state_values['current_stats']['multistrike'])
        multistrike_rate += self.buffs.multistrike_bonus()
        
        d1 = self.stats.mh.speed * (self.stats.mh.weapon_dps + node.state_values['effective_ap'] / 3.5)
        d1 = (d1 * (1-crit_rate)) + (2.0 * d1 * crit_rate)
        d1 *= 1 + 2 * multistrike_rate * .3
        b1 = self.add_damage_to_breakdown('mh_attack', d1, deepcopy(node.breakdown))
        t1 = node.total_damage + d1
        o1 = generic_event.GenericEvent(self, next_event[1], b1, next_event[0], node.timeline, t1, deepcopy(node.state_values), node, next_event[2])
        
        node.children = [o1]
        node.probabilities = [1.0] #the likelihood of the corrosponding child occuring
        
    def oh_attack(self, node):
        #basic functionality
        self.update_power_regen(node)
        swing_timer = self.stats.oh.speed / self.stats.get_haste_multiplier_from_rating(rating=node.state_values['current_stats']['haste'])
        self.insert_event_into_timeline(node, (node.time + swing_timer, node.name, False))
        self.queue_up_procs()
        
        next_event = node.timeline.pop(0)
        
        #rating=self.stat_values['current_stats']['crit'] is_day=self.engine.settings.is_day
        crit_rate = .15 + self.stats.get_crit_from_rating(rating=node.state_values['current_stats']['crit'])
        crit_rate += self.buffs.buff_all_crit() + self.race.get_racial_crit()
        crit_rate -= self.crit_reduction
        
        multistrike_rate = self.stats.get_multistrike_chance_from_rating(rating=node.state_values['current_stats']['multistrike'])
        multistrike_rate += self.buffs.multistrike_bonus()
        
        d1 = self.stats.oh.speed * (self.stats.oh.weapon_dps + node.state_values['effective_ap'] / 3.5) * 0.5
        d1 = (d1 * (1-crit_rate)) + (2.0 * d1 * crit_rate)
        d1 *= 1 + 2 * multistrike_rate * .3
        b1 = self.add_damage_to_breakdown('oh_attack', d1, deepcopy(node.breakdown))
        t1 = node.total_damage + d1
        o1 = generic_event.GenericEvent(self, next_event[1], b1, next_event[0], node.timeline, t1, deepcopy(node.state_values), node, next_event[2])
        
        node.children = [o1]
        node.probabilities = [1.0] #the likelihood of the corrosponding child occuring
    
    def sinister_strike(self, node):
        #this is a basic child populator method. crits, nor multistrikes, matter with this method.
        #b0 = deepcopy(self.breakdown) #miss
        self.insert_event_into_timeline(node, (node.time, 'swift_poison', False))
        
        #basic functionality
        self.update_power_regen(node)
        node.state_values['current_power'] -= 50
        self.queue_up_procs()
        
        next_event = node.timeline.pop(0)
        
        #rating=self.stat_values['current_stats']['crit'] is_day=self.engine.settings.is_day
        crit_rate = .15 + self.stats.get_crit_from_rating(rating=node.state_values['current_stats']['crit'])
        crit_rate += self.buffs.buff_all_crit() + self.race.get_racial_crit()
        crit_rate -= self.crit_reduction
        
        multistrike_rate = self.stats.get_multistrike_chance_from_rating(rating=node.state_values['current_stats']['multistrike'])
        multistrike_rate += self.buffs.multistrike_bonus()
        
        node.state_values['current_second_power'] = min(node.state_values['current_second_power']+1, node.state_values['max_second_power'])
        
        d1 = 1.2 * .85 * self.stats.mh.speed * (self.stats.mh.weapon_dps + node.state_values['effective_ap'] / 3.5)
        d1 = (d1 * (1-crit_rate)) + (2.0 * d1 * crit_rate)
        d1 *= 1 + 2 * multistrike_rate * .3
        b1 = self.add_damage_to_breakdown('sinister_strike', d1, deepcopy(node.breakdown))
        t1 = node.total_damage + d1
        o1 = generic_event.GenericEvent(self, next_event[1], b1, next_event[0], node.timeline, t1, deepcopy(node.state_values), node, next_event[2])
        
        node.children = [o1]
        node.probabilities = [1.0] #the likelihood of the corrosponding child occuring
        
        if 'revealing_strike' in node.state_values['auras']:
            #Bonus CP chance from RvS
            c = .25
            if self.stats.gear_buffs.rogue_t17_2pc:
                c += .2
            
            #can get away with cp reusage because it was cloned earlier
            node.state_values['current_second_power'] = min(node.state_values['current_second_power']+1, node.state_values['max_second_power'])
            o2 = generic_event.GenericEvent(self, next_event[1], b1, next_event[0], node.timeline, t1, deepcopy(node.state_values), node, next_event[2])
            node.children.append(o2)
            node.probabilities = [1-c, c]
            
    def eviscerate(self, node):
        next_event = node.timeline.pop(0)
        
        cp = node.state_values['current_second_power']
        node.state_values['current_second_power'] = node.state_values['anticipation']
        node.state_values['anticipation'] = 0
        
        #basic functionality
        self.update_power_regen(node)
        node.state_values['current_power'] -= 35
        self.queue_up_procs()
        
        #rating=self.stat_values['current_stats']['crit'] is_day=self.engine.settings.is_day
        crit_rate = .15 + self.stats.get_crit_from_rating(rating=node.state_values['current_stats']['crit'])
        crit_rate += self.buffs.buff_all_crit() + self.race.get_racial_crit()
        crit_rate -= self.crit_reduction
        
        multistrike_rate = self.stats.get_multistrike_chance_from_rating(rating=node.state_values['current_stats']['multistrike'])
        multistrike_rate += self.buffs.multistrike_bonus()
        
        d1 = .3 * cp * node.state_values['effective_ap']
        d1 = (d1 * (1-crit_rate)) + (2.0 * d1 * crit_rate)
        d1 *= 1 + 2 * multistrike_rate * .3
        b1 = self.add_damage_to_breakdown('eviscerate', d1, deepcopy(node.breakdown))
        t1 = node.total_damage + d1
        o1 = generic_event.GenericEvent(self, next_event[1], b1, next_event[0], node.timeline, t1, deepcopy(node.state_values), node, next_event[2])
        
        node.children = [o1]
        node.probabilities = [.2*cp] #the likelihood of the corrosponding child occuring
        
        if cp != 5:
            states = deepcopy(node.state_values['auras'])
            o2 = generic_event.GenericEvent(self, next_event[1], node.breakdown, next_event[0], node.timeline, node.total_damage, node.state_values, node, next_event[2])
            
            node.children.append(o0)
            node.probabilities.append(.2*(1-cp))
    
    def slice_and_dice(self, node):
        cp = node.state_values['current_second_power']
        d = 6*(1+cp)
        node.state_values['current_second_power'] = 0
        #doesn't consume anticipation stacks
                        
        node.update_power_regen(node)
        node.state_values['current_power'] -= 25

        if 'slice_and_dice' not in node.state_values['auras']:
            #if it's not there, add it
            node.state_values['auras'].append('slice_and_dice')
        
        t = self.remove_first_aura_occurance(node, 'slice_and_dice') #removes the aura removal event
        
        if t == None:
            t = d + node.time
        else:
            t = min(t+d-node.time, 1.3*d)
        self.insert_event_into_timeline(node, (node.time + t, 'remove_aura', 'slice_and_dice'))
        
        next_event = node.timeline.pop(0)
        states = deepcopy(node.state_values['auras'])
        states['current_power'] += 25
        o1 = generic_event.GenericEvent(self, next_event[1], node.breakdown, next_event[0], node.timeline, node.total_damage, states, node, next_event[2])
        
        node.children = [o1]
        node.probabilities = [.2*cp]
        
        if cp != 5:
            states = deepcopy(node.state_values['auras'])
            states['current_power'] -= 25
            o2 = generic_event.GenericEvent(self, next_event[1], node.breakdown, next_event[0], node.timeline, node.total_damage, states, node, next_event[2])
            
            node.children.append(o0)
            node.probabilities.append(.2*(1-cp))
    
    def swift_poison(self, node):
        next_event = node.timeline.pop(0)
                
        #rating=self.stat_values['current_stats']['crit'] is_day=self.engine.settings.is_day
        crit_rate = .15 + self.stats.get_crit_from_rating(rating=node.state_values['current_stats']['crit'])
        crit_rate += self.buffs.buff_all_crit() + self.race.get_racial_crit()
        crit_rate -= self.crit_reduction
        
        multistrike_rate = self.stats.get_multistrike_chance_from_rating(rating=node.state_values['current_stats']['multistrike'])
        multistrike_rate += self.buffs.multistrike_bonus()
                
        d1 = node.state_values['effective_ap'] * .20 * .3 #just average the proc rate into the damage
        d1 = (d1 * (1-crit_rate)) + (2.0 * d1 * crit_rate)
        d1 *= 1 + 2 * multistrike_rate * .3
        b1 = self.add_damage_to_breakdown('swift_poison', d1, deepcopy(node.breakdown))
        t1 = node.total_damage + d1
        o1 = generic_event.GenericEvent(self, next_event[1], b1, next_event[0], node.timeline, t1, deepcopy(node.state_values), node, next_event[2])        
        
        node.children = [o1]
        node.probabilities = [1.0]
    
    def revealing_strike(self, node):
        #basic functionality
        self.update_power_regen(node)
        node.state_values['current_power'] -= 40
        
        node.state_values['current_second_power'] = min(node.state_values['current_second_power']+1, node.state_values['max_second_power'])
                
        if 'revealing_strike' not in self.state_values['auras']:
            #if it's not there, add it
            node.state_values['auras'].append('revealing_strike')
        
        d = 24
        t = self.remove_first_aura_occurance(node, 'revealing_strike') #removes the aura removal event
        if t == None:
            t = d + node.time
        else:
            t = min(t+d-node.time, 1.3*d)
        self.insert_event_into_timeline(node, (node.time + t, 'remove_aura', 'revealing_strike'))
        
        self.queue_up_procs()
        
        next_event = node.timeline.pop(0)

        #rating=self.stat_values['current_stats']['crit'] is_day=self.engine.settings.is_day
        crit_rate = .15 + self.stats.get_crit_from_rating(rating=node.state_values['current_stats']['crit'])
        crit_rate += self.buffs.buff_all_crit() + self.race.get_racial_crit()
        crit_rate -= self.crit_reduction
        
        multistrike_rate = self.stats.get_multistrike_chance_from_rating(rating=node.state_values['current_stats']['multistrike'])
        multistrike_rate += self.buffs.multistrike_bonus()
        
        d1 = 1.0 * .85 * self.stats.mh.speed * (self.stats.mh.weapon_dps + node.state_values['effective_ap'] / 3.5)
        d1 = (d1 * (1-crit_rate)) + (2.0 * d1 * crit_rate)
        d1 *= 1 + 2 * multistrike_rate * .3
        b1 = self.add_damage_to_breakdown('revealing_strike', d1, deepcopy(node.breakdown))
        t1 = node.total_damage + d1
        o1 = generic_event.GenericEvent(self, next_event[1], b1, next_event[0], node.timeline, t1, deepcopy(node.state_values), node, next_event[2])
        
        node.children = [o1]
        node.probabilities = [1.0] #the likelihood of the corrosponding child occuring
    
    