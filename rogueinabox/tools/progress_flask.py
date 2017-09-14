#!/usr/bin/env python
# coding: utf-8

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

from flask import Flask
from flask import render_template
import subprocess
app = Flask(__name__)

@app.route("/")
def index():
    return render_template('templates/index.html')

@app.route("/update")
def progress():
    out =  ''
    with open('./watch_script', 'r') as f:
        for line in f:
            try:
                out += subprocess.check_output(line, shell=True, universal_newlines=True)
                out += '<br>'
            except:
                pass
    return(str(out))

if __name__ == "__main__":
    app.run(port=8888)
