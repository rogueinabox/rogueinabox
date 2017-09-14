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

class UI(object):
    def __init__(self, rogue_box):
        """Prepare everything needed by the other methods"""
        self.rb = rogue_box

    def on_key_press(self, callback):
        """Catch a key event and call the callback function"""
        pass

    def on_timer_end(self, timer, callback):
        """After the given time in ms is passed, call the callback function, return the timer"""
        pass

    def cancel_timer(self, timer):
        """Cancel a previously set timer"""
        pass

    def start_ui(self):
        """Last command to be launched, really start the gui"""
        pass

    def draw(self, string):
        """Draw on screen something"""
        pass

    def read_rogue(self):
        """Return the string on the rogue process screen"""
        pass

