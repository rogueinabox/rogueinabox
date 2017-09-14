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

from tkinter import Tk, StringVar, Label
from ui.UI import UI


class UITk(UI):
    """TODO doc for UITk"""

    def __init__(self, rogue):
        """Constructor for UITk"""
        super().__init__(rogue)
        self.window = Tk()
        self.screen = StringVar()
        self.draw_from_rogue()
        self.label = Label(self.window, textvariable=self.screen, fg="white", bg="black", font=("monospace", 11))
        self.label.focus_set()
        self.label.pack()

    def start_ui(self):
        """TODO docs"""
        self.window.mainloop()

    def on_timer_end(self, timer, callback):
        """TODO docs"""
        return self.window.after(timer, callback)

    def cancel_timer(self, timer):
        """TODO docs"""
        if timer is not None:
            self.window.after_cancel(timer)

    def on_key_press(self, callback):
        """TODO docs"""
        self.label.bind("<Key>", callback)

    def draw(self, string):
        """Draw on the screen the provided string"""
        self.screen.set(string)

    def read_rogue(self):
        """Return the string on the rogue process screen"""
        return self.rb.get_screen_string()

    def draw_from_rogue(self):
        """Draw on the screen whats on rogue"""
        self.draw(self.read_rogue())

    def draw_log(self, string):
        pass
