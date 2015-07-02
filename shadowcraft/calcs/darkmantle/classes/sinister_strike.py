from copy import deepcopy
import gettext
import __builtin__
import math

__builtin__._ = gettext.gettext

from shadowcraft.calcs.darkmantle.generic_attack import GenericAttack

class SinisterStrike(GenericAttack):
    _name = 'Sinister Strike'
    _cost = 50
    
    def calculate_damage(self):
        # non-normalized weapon strike => (mh_weapon_damage + ap / 3.5 * weapon_speed) * weapon_damage_percentage
        return 1.2 * .85 * self.engine.stats.mh.speed * (self.engine.stats.mh.weapon_dps + self.state_values['effective_ap'] / 3.5)
    
    def child_populate(self):
        #this is a basic child populator method. crits, nor multistrikes, matter with this method.
        #b0 = deepcopy(self.breakdown) #miss
        self.engine.insert_event_into_timeline(self, (self.time, 'swift_poison', False))
        next_event = self.timeline.pop(0)
        
        #basic functionality
        self.update_power_regen()
        self.secondary_effects()
        self.queue_up_procs()
        
        #rating=self.stat_values['current_stats']['crit'] is_day=self.engine.settings.is_day
        crit_rate = .15 + self.engine.stats.get_crit_from_rating(rating=self.state_values['current_stats']['crit'])
        crit_rate += self.engine.buffs.buff_all_crit() + self.engine.race.get_racial_crit()
        crit_rate -= self.engine.crit_reduction
        
        multistrike_rate = self.engine.stats.get_multistrike_chance_from_rating(rating=self.state_values['current_stats']['multistrike'])
        multistrike_rate += self.engine.buffs.multistrike_bonus()
        
        self.state_values['current_second_power'] = min(self.state_values['current_second_power']+1, self.state_values['max_second_power'])
        
        d1 = self.calculate_damage()
        d1 = (d1 * (1-crit_rate)) + (2.0 * d1 * crit_rate)
        d1 *= 1 + 2 * multistrike_rate * .3
        b1 = self.add_damage_to_breakdown(d1, deepcopy(self.breakdown))
        t1 = self.total_damage + d1
        o1 = self.engine.get_next_attack(next_event[1])(self.engine, b1, next_event[0], self.timeline, t1, deepcopy(self.state_values), self, next_event[2])
        
        self.children = [o1]
        self.probabilities = [1.0] #the likelihood of the corrosponding child occuring
        
        if 'revealing_strike' in self.state_values['auras']:
            #Bonus CP chance from RvS
            c = .25
            if self.engine.stats.gear_buffs.rogue_t17_2pc:
                c += .2
            
            #can get away with cp reusage because it was cloned earlier
            self.state_values['current_second_power'] = min(self.state_values['current_second_power']+1, self.state_values['max_second_power'])
            o2 = self.engine.get_next_attack(next_event[1])(self.engine, b1, next_event[0], self.timeline, t1, deepcopy(self.state_values), self, next_event[2])
            self.children.append(o2)
            self.probabilities = [1-c, c]
            
            