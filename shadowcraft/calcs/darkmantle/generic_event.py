from copy import deepcopy
import gettext
import __builtin__
import math
from __builtin__ import False

__builtin__._ = gettext.gettext

from shadowcraft.core import exceptions
from shadowcraft.objects import procs
from shadowcraft.objects import proc_data

class GenericEvent(object):
    _can_crit = False
    _cost = 0
    _can_multistrike = False
    _multistrike_delay = .3
    _cost = 0
    _gcd_size = 1.0
    _stance = None #the stance(s) required
    _cost_secondary = 0
    _cast_time = 0.0
    _required_stances = None
    
    def __init__(self, engine, name, breakdown, time, timeline, total_damage, state_values, parent, extra, print_message=False):
        self.name = name
        self.engine = engine
        self.breakdown = deepcopy(breakdown)
        self.time = time #gets passed by value not reference, no need to clone
        self.timeline = deepcopy(timeline) #array/list of future events
        self.total_damage = total_damage #gets passed by value not reference, no need to clone
        self.state_values = state_values #general data about the circumstances of the event
        self.parent = parent #the parent node
        self.extra = extra #extra data is created for each event, don't need to clone
        self.print_message = print_message #Used for creating sample logs

        self.children = None
        self.probabilities = None
        self.final_breakdown = {}
        self.current_child = 0 #used for tracking which child we're on faster, must be a number
    
    