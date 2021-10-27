import numpy as np
from constraint import *

from set_var import Set_var
from solver import Model


class Sgp:
    def __init__(self, g, s, w) -> None:
        self.groups = g
        self.size = s
        self.weeks = w
        self.n = self.groups * self.size
        self.schedule = []

    def get_basic_model(self):
        self.schedule = np.empty((self.weeks, self.groups), Set_var)
        model = Model()
        for w in range(len(self.schedule)):
            for g in range(len(self.schedule[w])):
                self.schedule[w, g] = Set_var(
                    [], list(range(self.n)), (self.size, self.size), "s[{},{}]".format(w, g))
        for w in range(self.weeks):
            for g1 in range(self.groups):
                for g2 in range(g1):
                    model.add_constraint(EmptyIntersection(
                        self.schedule[w, g1], self.schedule[w, g2]))

        for w1 in range(self.weeks):
            for w2 in range(w1):
                for g1 in range(self.groups):
                    for g2 in range(self.groups):
                        H = Set_var([], list(range(self.n)), (0, 1))
                        model.add_constraint(Intersection(
                            self.schedule[w1, g1], self.schedule[w2, g2], H))
        return model

    def print_sol(self):
        for w in range(len(self.schedule)):
            for g in range(len(self.schedule[w])):
                print(self.schedule[w, g].lb, end=" | ")
            print("")
