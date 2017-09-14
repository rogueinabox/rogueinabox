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

import re
import itertools
from rogueinabox import RogueBox


class StalkOMatic(RogueBox):
    def __init__(self, configs):
        super().__init__(configs)
        self.parse_command_re = self._compile_command_re()

    @staticmethod
    def _compile_command_re():
        parse_command_re = re.compile(r"""
                Level:\s*(?P<dungeon_level>\d*)\s*
                Gold:\s*(?P<gold>\d*)\s*
                Hp:\s*(?P<current_hp>\d*)\((?P<max_hp>\d*)\)\s*
                Str:\s*(?P<current_strength>\d*)\((?P<max_strength>\d*)\)\s*
                Arm:\s*(?P<armor>\d*)\s*
                Exp:\s*(?P<exp_level>\d*)/(?P<tot_exp>\d*)\s*
                (?P<command>\w*)""", re.VERBOSE)
        return parse_command_re

    def _update_player_pos(self):
        found = False
        for i, j in itertools.product(range(1, 23), range(80)):
            pixel = self.screen[i][j]
            if pixel == "@":
                found = True
                self.player_pos = (i, j)
        if not found:
            #sometimes rogomatic doesnt show the player
            #dont know why
            pass
