from copy import deepcopy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.core import exceptions
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data

class GenericEvent(object):
    _can_crit = False
    _cost = 0
    _can_multistrike = False
    
    def __init__(self, engine, breakdown, time, timeline, total_damage, state_values, parent):
        self.engine = engine
        self.breakdown = deepcopy(breakdown)
        self.time = deepcopy(time)
        self.timeline = deepcopy(timeline)
        self.total_damage = deepcopy(total_damage)
        self.state_values = deepcopy(state_values)
        self.parent = parent
        self.children = None
        self.probabilities = None
        self.final_breakdown = {}
        self.current_child = 0 #used for tracking which child we're on faster, must be a number
        
    def try_to_populate(self):
        pass
    
    def send_data_to_parent(self):
        prob = self.parent.probabilities[self.parent.current_child]
        for k in self.final_breakdown:
            if k in self.parent.final_breakdown:
                self.parent.final_breakdown[k] += self.final_breakdown[k] * prob
            else:
                self.parent.final_breakdown[k] = self.final_breakdown[k] * prob
    
    def add_breakdown_to_state_final(self):
        pass
        
    def has_next_child(self):
        #if self.current_child == len(self.children)-1
        if self.children == None:
            return False
        for e in self.children:
            if e != None:
                return True
        return False
    
    def can_cast(self, state):
        return True
    
    def insert_event_into_timeline(self, event):
        #event is a tuple of (time, name, extra)
        if len(self.timeline) == 0:
            self.timeline.append(event)
        if event[0] < self.timeline[0][0]:
            self.timeline.insert(0, event)
        if event[0] > self.timeline[len(self.timeline)-1][0]:
            self.timeline.append(event)
        for i in xrange(len(self.timeline)): #from 0 to len()-1
            if self.timeline[i-1][0] < event[0] and event[0] <= self.timeline[i][0]:
                self.timeline.insert(i+1, event)
    
    def is_done(self):
        if self.current_child == len(self.children)-1:
            return True
        return False
    
    def get_next_child(self):
        if self.children is not None:
            for i in xrange(0, len(self.children)):
                if self.children[i] is not None:
                    self.current_child = i
                    return self.children[i]
        return None
    
    def kill_last_child(self):
        if self.children is not None:
            for i in xrange(0, len(self.children)):
                if self.children[i] is not None:
                    self.children[i] = None
                    return
    