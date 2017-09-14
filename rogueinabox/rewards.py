#Copyright (C) 2017 Andrea Asperti, Carlo De Pieri, Gianmaria Pedrini
#
#This file is part of Rogueinabox.
#
#Rogueinabox is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Rogueinabox is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import itertools
from abc import ABC, abstractmethod

#class naming:

# what is considered in the reward computation
# A = All the infos from get_infos are considered
# E = Exploring a new part of the map
# D = Descending the stairs
# Ps = Player standing Still
# Pp = Past player Positions

# other stuff
# W/nW = Weighted/not Weighted
# C = Clipped
# R = a Reset condition is present

# ABSTRACT CLASS

class RewardGenerator(ABC):
    def __init__(self, rogue_box):
        self.rb = rogue_box
        self.objective_achieved = False

    @abstractmethod
    def compute_reward(self, old_screen, new_screen):
        pass

    def get_infos(self, old_screen, new_screen):
        # parse the screen for infos
        # infos is in the format {"info_name": {"old": old_value, "new": new_value}}
        infos = {"screen": {"old": old_screen, "new": new_screen}}

        for state in ["old", "new"]:
            # parse status bar
            # status bar is the last line
            statusbar = infos["screen"][state][-1]
            parsed_statusbar = self.rb.parse_statusbar_re.match(statusbar)
            statusbar_infos = parsed_statusbar.groupdict()
            for info in statusbar_infos:
                if not infos.get(info):
                    infos[info] = {}
                infos[info][state] = int(statusbar_infos[info])
            
        # count visible map pixels
        # do this only if we are on the same floor
        if infos["dungeon_level"]["new"] == infos["dungeon_level"]["old"]:
            for state in ["old", "new"]:
                count = 0
                # do not include message and status bars
                for line in infos["screen"][state][1:-1]:
                    for pixel in line:
                        if pixel != ' ':
                            count += 1
                if not infos.get("explored_tiles"):
                    infos["explored_tiles"] = {}
                infos["explored_tiles"][state] = count

        # we dont need the screen anymore now
        infos.pop("screen", None)
        return infos

    def get_player_pos(self, screen):
      for i, j in itertools.product(range(1, 23), range(80)):
        pixel = screen[i][j]
        if pixel == "@":
          return (i, j)

    def manhattan_distance(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def clip_reward(self, reward):
        # clip reward to 1 or -1
        if reward > 0:
            reward = 1
        else:
            reward = -1
        return reward

    def player_standing_still(self, old_screen, new_screen):
        infos = self.get_infos(old_screen, new_screen)
        if self.get_player_pos(old_screen) == self.get_player_pos(new_screen):
            if infos["dungeon_level"]["new"] == infos["dungeon_level"]["old"]:
                return True
        return False

class SparseRewardGenerator(RewardGenerator):
    def compute_reward(self, old_screen, new_screen):
        """return the reward (0 or 1) for the last action
        rewards only descending and gathering gold
        """
        if not self.rb.game_over() and self.rb.is_map_view(old_screen) and self.rb.is_map_view(new_screen):
            # parse the screen for infos
            # infos is in the format {"info_name": {"old": old_value, "new": new_value}}
            infos = self.get_infos(old_screen, new_screen)

            if infos["dungeon_level"]["new"] > infos["dungeon_level"]["old"] or infos["gold"]["new"] > infos["gold"]["old"]:
                reward = 1
            else:
                reward = 0

        elif self.rb.game_over():
            reward = 0
        else:
            # we are in some other view, probably a submenu like
            # inventory or options
            # return a dummy reward to avoid crashes
            reward = 0
        return reward

class A_nW_RewardGenerator(RewardGenerator):
    def compute_reward(self, old_screen, new_screen):
        """return the reward for the last action
        consider each increase in the gathered infos positive (+1)
        and each decrease negative (-1)
        """
        if not self.rb.game_over() and self.rb.is_map_view(old_screen) and self.rb.is_map_view(new_screen):
            # parse the screen for infos
            infos = self.get_infos(old_screen, new_screen)
            # compute reward
            # for now higher is better for all infos gathered
            # so we can keep it simple
            reward = 0
            for info in infos:
                if infos[info]["new"] > infos[info]["old"]:
                    reward += 1
                elif infos[info]["new"] < infos[info]["old"]:
                    reward -= 1

        elif self.rb.game_over():
            reward = -1
        else:
            reward = -1
        return reward


class A_nW_C_RewardGenerator(A_nW_RewardGenerator):
    def compute_reward(self, old_screen, new_screen):
        """return the reward for the last action
        clip the reward of A_nW_RewardGenerator to +1, 0, -1
        """
        reward = super().compute_reward(old_screen, new_screen)
        return self.clip_reward(reward)

class A_W_RewardGenerator(RewardGenerator):
    def compute_reward(self, old_screen, new_screen):
        """return the reward for the last action
        consider each variation in the gathered infos
        using the delta as weight
        """
        if not self.rb.game_over() and self.rb.is_map_view(old_screen) and self.rb.is_map_view(new_screen):
            # parse the screen for infos
            infos = self.get_infos(old_screen, new_screen)
            # compute reward
            # various infos are "weighted" differently
            # because we directly use the in game value
            # which might have a different scale for one info in respect to another
            # those probably aren't the best "weights" but are those naturally
            # used in the game
            reward = 0
            for info in infos:
                reward += infos[info]["new"] - infos[info]["old"]
            #living reward
            reward -= 0.1
        elif self.rb.game_over():
            reward = -0.1
        else:
            reward = -1
        return reward

class E_D_W_RewardGenerator(RewardGenerator):
    def compute_reward(self, old_screen, new_screen):
        """return the reward for the last action
        +100 for descending the stairs
        +5 for exploring the map
        -0.1 living reward
        """
        if not self.rb.game_over() and self.rb.is_map_view(old_screen) and self.rb.is_map_view(new_screen):
            # parse the screen for infos
            infos = self.get_infos(old_screen, new_screen)
            # compute reward
            reward = 0
            if infos["dungeon_level"]["new"] > infos["dungeon_level"]["old"]:
              reward = 100
            elif infos["explored_tiles"]["new"] > infos["explored_tiles"]["old"]:
              reward = 5
            else:
              #living reward
              reward = -0.1
        elif self.rb.game_over():
            reward = -1
        else:
            reward = -1
        return reward


class E_D_Ps_W_RewardGenerator(E_D_W_RewardGenerator):
    def compute_reward(self, old_screen, new_screen):
        """return the reward the last action
        +100 for descending the stairs
        +5 for exploring the map
        -1 for standing still
        -0.1 living reward
        """
        reward = super().compute_reward(old_screen, new_screen)
        if not self.rb.game_over() and self.rb.is_map_view(old_screen) and self.rb.is_map_view(new_screen):
            if self.player_standing_still(old_screen, new_screen):
              reward = -1
        return reward

class E_D_Ps_W_R_RewardGenerator(E_D_Ps_W_RewardGenerator):
    def compute_reward(self, old_screen, new_screen):
        """return the reward the last action
        +100 for descending the stairs
        +5 for exploring the map
        -1 for standing still
        -0.1 living reward
        Reset if the agent exits the first room
        """
        reward = super().compute_reward(old_screen, new_screen)
        #reset if we got a positive reward (i.e. we reached the exit of the first room)
        if reward > 0:
            self.objective_achieved = True
        return reward

class E_D_Ps_Pp_W_RewardGenerator(E_D_Ps_W_RewardGenerator):
    def compute_reward(self, old_screen, new_screen):
        """return the reward the last action
        +100 for descending the stairs
        +5 for exploring the map
        from +0.1 to +1 (depending on the distance of the current agent position from
        the agent position 10 time steps ago)
        -1 for standing still
        -0.1 living reward
        """
        reward = super().compute_reward(old_screen, new_screen)
        if not self.rb.game_over() and self.rb.is_map_view(old_screen) and self.rb.is_map_view(new_screen):
            #add movement bonus based on past positions
            a = self.rb.past_positions[0]
            b = self.rb.past_positions[-1]
            reward += self.manhattan_distance(a, b) * 0.1
        return reward
