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

import matplotlib.pyplot as plt
import scipy
import re
loss_pattern = re.compile(r'Loss[a-z ]+:\s(\d+\.\d*)')
qvalue_pattern = re.compile(r'\[\[\s*(\d+\.\d*)\s*(\d+\.\d*)\s*(\d+\.\d*)\s*(\d+\.\d*)\s*(\d+\.\d*)\]\]')

losses = []
qvalues = []
with open('logfile.log', 'r') as log:
    for line in log:
        loss_match = re.search(loss_pattern, line)
        qvalue_match = re.search(qvalue_pattern, line)
        if loss_match:
            losses.append(loss_match.group(1))
        if qvalue_match:
            qvalues.append(sum(map(float, qvalue_match.groups()))/len(qvalue_match.groups()))

losses = list(map(float, losses))
print(len(qvalues))

y = qvalues
x = range(len(y))
import numpy as np
from scipy import interpolate
#p = np.polyfit(x, y, 1)
#f = np.poly1d(p)
p = interpolate.splrep(x, y, s=0)
x_new = np.linspace(x[0], x[-1], 1000)
y_new = interpolate.splev(x_new, p, der=0)
#y_new = f(x_new)

#plt.plot(x, y)
plt.plot(x_new, y_new)
fig = plt.gcf()
fig.autofmt_xdate()
plt.show()
