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
import numpy as np

# load data
base = "/assetspath/"
sfile = "{}{}".format(base, "scores.log")
mfile = "{}{}".format(base, "means.log")
simg = "{}{}".format(base, "scores.png")
mimg = "{}{}".format(base, "means.png")
scores = []
with open(sfile) as scoresfile:
    for score in scoresfile:
        scores.append(int(score))
means = []
with open(mfile) as meansfile:
    for mean in meansfile:
        means.append(float(mean))

# 'cause why not
def add_regression(x, y, plotter, order=1, style='-b', label=None):
    if label is None:
        label = "regression order {}".format(order)
    fit = np.polyfit(x,y,order)
    fit_fn = np.poly1d(fit) 
    plotter.plot(x,fit_fn(x), style, label=label)

# plot scores
plt.plot(range(len(scores)), scores, 'y|', label="score")
add_regression(range(len(scores)), scores, plt, order=3, label='3rd order regression')
add_regression(range(len(scores)), scores, plt, order=4, style='r-', label='4th order regression')
plt.legend()
plt.xlabel('Games')
plt.ylabel('Score')
fig_scores = plt.gcf()
plt.show()

# plot means
plt.plot(range(len(means)), means, 'y-', label="mean")
add_regression(range(len(means)), means, plt, order=3, label='3rd order regression')
add_regression(range(len(means)), means, plt, order=4, style='r-', label='4th order regression')
plt.legend(loc=4)
plt.xlabel('Games')
plt.ylabel('Average score')
fig_means = plt.gcf()
plt.show()

print("max mean: {} last mean: {} number of scores: {}".format(max(means), means[-1], len(scores))

# save plots
# fig_scores.savefig(simg)
# fig_means.savefig(mimg)
