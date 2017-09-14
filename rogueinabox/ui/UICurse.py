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

import curses
import time
from ui.UI import UI

class Event(object):
    """the event to return to a key press callback"""
    # its ugly i know
    pass


class UICurse(UI):
    """"""
    def __init__(self, rogue):
        """Constructor for UITk"""
        super().__init__(rogue)
        self.timer_callback = None
        self.keypress_callback = None
        self.sleep_time = 0.1
        self.stdscr = None
        self.logpad = None
        self.startlog = 25
        self.loglines = 2

    def start_ui(self):
        curses.wrapper(self._start_ui)

    def _start_ui(self, stdscr):
        """TODO docs"""
        rogue_height = 26
        rogue_width = 84
        # using a pad instead of the default win, it's safer
        self.stdscr = curses.newpad(rogue_height, rogue_width)
        self.stdscr.nodelay(True)
        curses.curs_set(False)
        self.draw_from_rogue()
        minlogsize = 4
        if curses.LINES - 1 >= rogue_height + minlogsize:
            # there's enough space to show the logs
            self.logpad = curses.newpad(curses.LINES - 1, curses.COLS - 1)
        while True:
            if self.timer_callback:
                self.timer_callback()
                time.sleep(self.sleep_time)
            if self.keypress_callback:
                try:
                    key = self.stdscr.getkey()
                    event = Event()
                    event.char = key
                    self.keypress_callback(event)
                except curses.error:
                    pass

    def on_timer_end(self, timer, callback):
        """TODO docs"""
        self.timer_callback = callback
        self.sleep_time = timer/1000
        return True

    def cancel_timer(self, timer):
        """TODO docs"""
        self.timer_callback = None

    def on_key_press(self, callback):
        """TODO docs"""
        self.keypress_callback = callback

    def draw_from_rogue(self):
        """Draw on the screen whats on rogue"""
        screen = self.rb.get_screen()
        for y, line in enumerate(screen, 2):
            self.stdscr.addstr(y, 0, line)
        self.stdscr.refresh(2,0, 0, 0, curses.LINES - 1, curses.COLS - 1)

    def draw_log(self, string):
        """Draw some logs on the screen"""
        if self.logpad is not None and not self.rb.game_over():
            limit = curses.LINES - self.startlog - 3
            self.logpad.addstr(0, 0, "  LOGS")
            self.logpad.hline(1,0, "-", curses.COLS - 1)
            self.logpad.hline(limit + 1,0, "-", curses.COLS - 1)
            if self.loglines > limit:
                self.logpad.move(2, 0)
                self.logpad.deleteln()
                self.logpad.move(self.loglines - 1, 0)
                self.logpad.clrtoeol()
                self.logpad.addstr(self.loglines - 1, 0, string)
                self.logpad.hline(limit + 1,0, "-", curses.COLS - 1)
            else:
                self.logpad.addstr(self.loglines, 0, string)
            if self.loglines <= limit:
                self.loglines += 1
            self.logpad.refresh(0,0, self.startlog, 0, curses.LINES - 1, curses.COLS - 1)
