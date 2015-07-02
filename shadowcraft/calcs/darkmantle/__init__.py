import copy
import gettext
import __builtin__
import math
import sys
import traceback
from __builtin__ import None
from pickle import NONE

__builtin__._ = gettext.gettext

from shadowcraft.core import exceptions
from shadowcraft.calcs import armor_mitigation
from shadowcraft.objects import class_data
from shadowcraft.objects.procs import InvalidProcException

from shadowcraft.calcs.darkmantle import generic_event


class InputNotModeledException(exceptions.InvalidInputException):
    pass

class DarkmantleCalculator(object):

    def __init__(self, stats, talents, glyphs, buffs, race, settings=None, level=100, target_level=103, char_class='rogue'):
        #load stats, class, procs, etc to main content
        self.tools = class_data.Util()
        self.stats = stats
        self.talents = talents
        self.glyphs = glyphs
        self.buffs = buffs
        self.race = race
        self.char_class = char_class
        self.settings = settings
        self.target_level = target_level
        self.level = level
        
        self.buffs.level = self.level
        self.stats.level = self.level
        self.race.level = self.level
        self.stats.gear_buffs.level = self.level
        # calculate and cache the level-dependent armor mitigation parameter
        self.armor_mitigation_parameter = armor_mitigation.parameter(self.level)
        
        #setup global variables, these get deep-copy and passed to new objects
        self.state_values = {}
        self.state_values['last_event'] = 0
        self.state_values['damage_multiplier'] = 1.0
        self.state_values['gcd_size'] = 1.0
        self.state_values['range'] = 4.0
        self.state_values['stance'] = 0
        self.state_values['player_state'] = 'normal' #normal, casting, 
        self.state_values['cooldown'] = {}
        self.state_values['stat_multipliers'] = {
            'primary':self.stats.gear_buffs.gear_specialization_multiplier(), #armor specialization
            'ap':self.buffs.attack_power_multiplier(),
            'haste':1.0,
            'crit':1.0,
            'mastery':1.0,
            'versatility':1.0,
            'readiness':1.0,
            'multistrike':1.0,
        }
        self.state_values['current_stats'] = {
            'str': (self.stats.str), #useless for rogues now
            'agi': (self.stats.agi + self.race.racial_agi), #+ self.buffs.buff_agi()
            'int': (self.stats.int), #useless for rogues now
            'ap': (self.stats.ap),
            'crit': (self.stats.crit),
            'haste': (self.stats.haste),
            'mastery': (self.stats.mastery), # + self.buffs.buff_mast()
            'readiness': (self.stats.readiness),
            'multistrike': (self.stats.multistrike),
            'versatility': (self.stats.versatility),
        }
        self.state_values['attack_speed'] = 1.0 #decimal value
        self.state_values['haste'] = 1.0 #decimal value
        self.calculate_effective_ap()

        self.state_values['auras'] = [] #handles permanent and temporary
        for e in self.buffs.buffs_debuffs:
            self.state_values['auras'].append(e)
            
        #change stats to match buffs
        
        #combat tables
        self.base_one_hand_miss_rate = 0
        self.base_parry_chance = .03
        self.base_dodge_chance = 0
        self.base_spell_miss_rate = 0
        self.base_dw_miss_rate = .17
        self.base_block_chance = .075
        self.crit_reduction = .01 * (self.target_level - self.level)
        
        #load class module data
        class_variables = self._get_values_for_class()
        for key in class_variables:
            self.state_values[key] = class_variables[key]
            
        #trash objects, for reusing memory
        self.trash_queue = None
    
    def tree_walk_algorithm(self, event_queue):
        #base data
        breakdown = {}
        total_damage = 0
        #event_queue = []
        time = 0
        
        first_event = event_queue.pop(0)
        current_node = generic_event.GenericEvent(self, first_event[1], breakdown, time, event_queue, total_damage, self.state_values, None, first_event[2])
        
        l=0
        d=0
        while True:
            l += 1
            #print l, current_node.time
            if l % 1000 == 0:
                print "iteration ", l
            #print ''
            #print current_node._name, current_node.time, current_node.timeline
            #print current_node.final_breakdown
            self.try_to_populate(current_node)
                           
            if self.node_has_next_child(current_node):
                d+=1
                current_node = self.node_get_next_child(current_node)
            else:
                d-=1
                #else return breakdown average to parent
                if current_node.parent == None:
                    #this means we're at the root node, lets split this joint!
                    print "And we're done!"
                    print "total iterations:", l 
                    print " "
                    return current_node.final_breakdown
                self.send_data_to_parent(current_node)

                p = current_node.parent
                current_node = p
                self.kill_last_child(current_node)
    
    def node_has_next_child(self, node):
        #if node.current_child == len(node.children)-1
        if node.children == None:
            return False
        for e in node.children:
            if e != None:
                return True
        return False
    
    def node_get_next_child(self, node):
        if node.children is not None:
            for i in xrange(0, len(node.children)):
                if node.children[i] is not None:
                    node.current_child = i
                    return node.children[i]
        return None
    
    def calculate_effective_ap(self):
        self.state_values['effective_ap'] = (self.state_values['current_stats']['agi'] * self.state_values['stat_multipliers']['primary'] + self.stats.ap)
        self.state_values['effective_ap'] *= self.state_values['stat_multipliers']['ap']
        
    def end_calc_branch(self, current_time, total_damage_done):
        if self.settings.style == 'time' and current_time >= self.settings.limit:
            #print 'Fork ends at: ', current_time, ' seconds', total_damage_done
            #print '--------'
            return True
        if self.settings.style == 'health' and total_damage_done >= self.settings.limit:
            #print 'Fork ends at: ', total_damage_done, ' damage', current_time
            #print '--------'
            return True
        return False
    
    def send_data_to_parent(self, node):
        prob = node.parent.probabilities[node.parent.current_child]
        for k in node.final_breakdown:
            if k in node.parent.final_breakdown:
                node.parent.final_breakdown[k] += node.final_breakdown[k] * prob
            else:
                node.parent.final_breakdown[k] = node.final_breakdown[k] * prob
    
    def add_damage_to_breakdown(self, name, damage, breakdown):
        if name in breakdown:
            breakdown[name] += damage
        else:
            breakdown[name] = damage
        return breakdown
    
    def insert_event_into_timeline(self, node, event):
        #event is a tuple of (time, name, extra)
        if len(node.timeline) == 0:
            node.timeline.append(event)
        elif event[0] < node.timeline[0][0]:
            node.timeline.insert(0, event)
        elif event[0] > node.timeline[len(node.timeline)-1][0]:
            node.timeline.append(event)
        else:
            for i in xrange(len(node.timeline)): #from 0 to len()-1
                if node.timeline[i-1][0] < event[0] and event[0] <= node.timeline[i][0]:
                    node.timeline.insert(i, event)
                    
    def timeline_contains(self, node, name):
        for e in node.timeline:
            if e[1] == name:
                return True
        return False
    
    def recycle_object(self, node):
        #just inserts an object on the top of the recycling stack
        #NOTE: REMOVE OBJECT REFERENCE BEFORE PASSING TO THIS METHOD
        node.children = self.trash_queue
        self.trash_queue = node
    
    def pull_from_recycling(self):
        if self.trash_queue == None:
            return None
        
        obj = self.trash_queue
        self.trash_queue = obj.children
        return obj
    
    def remove_first_occurance(self, node, name):
        for i in xrange(0, len(node.timeline)):
            if node.timeline[i][1] == name:
                e = node.timeline.pop(i) #discard the return
                return e[0] - node.time
    
    def remove_first_aura_occurance(self, node, name):
        for i in xrange(0, len(node.timeline)):
            if node.timeline[i][2] == name:
                e = node.timeline.pop(i) #discard the return
                return e[0] - node.time
    
    def _class_bonus_crit(self):
        return 0 #should be overwritten by individual class modules if the crit rate needs to be shifted
    
    def calculate_crit_rate(self):
        crit = self.stats.get_crit_from_rating(rating=self.state_values['current_stats']['crit'])
        crit += self._class_bonus_crit() + self.buffs.buff_all_crit()
        return crit
    
    def kill_last_child(self, node):
        if node.children is not None:
            #check current child, if that fails then just iterate to find the right one
            if node.children[node.current_child] is not None:
                #save object reference for later, then delete the previous reference
                    self.recycle_object(node.children[node.current_child])
                    node.children[node.current_child] = None
                    return
                
            for i in xrange(0, len(node.children)):
                if node.children[i] is not None:
                    #save object reference for later, then delete the previous reference
                    self.recycle_object(node.children[i])
                    node.children[i] = None
                    return
        