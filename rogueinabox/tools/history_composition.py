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
import random
import pickle
h = pickle.load(open("history.pkl", 'rb'))

def hist_stats(hist):
    pos = 0
    neg = 0
    zer = 0
    term = 0
    descend = 0
    posl = [0,0,0,0]
    negl = [0,0,0,0]
    zerl = [0,0,0,0]
    for s1, a, r, s2, t in hist:
        if r > 0:
            pos += 1
            posl[a] += 1
        elif r == -1:
            neg += 1
            negl[a] += 1
        elif r < 0:
            zer += 1
            zerl[a] += 1
        if t:
            term += 1
        if a == 4 and r>0:
            descend += 1
    print('pos: {}, neg: {}, zer: {}, term: {}, descend: {}'.format(pos, neg, zer, term, descend))
    print('positive distribution between actions: {}'.format(posl))
    print('negative distribution between actions: {}'.format(negl))
    print('zeros distribution between actions: {}'.format(zerl))

hist_stats(h)

for i in range(10):
    rnd = random.randrange(len(h))
    plt.imshow(h[rnd][0][0][0])
    plt.show()
