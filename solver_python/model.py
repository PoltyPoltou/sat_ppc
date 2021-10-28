import numpy as np
from constraint import *

from set_var import Set_var


class Model:
    def __init__(self) -> None:
        self.constraints: set(Constraint) = set()
        self.variables: set(Set_var) = set()
        self.var_to_constraints = {}

    def add_constraint(self, cons: Constraint):
        self.constraints.add(cons)
        for var in cons.get_vars():
            self.variables.add(var)
            if var not in self.var_to_constraints.keys():
                self.var_to_constraints[var] = []
        for var in cons.get_vars():
            self.var_to_constraints[var].append(cons)

    def feasable(self) -> tuple[bool, str]:
        for var in self.variables:
            if not var.feasable():
                return False, "Var unsat"
        # upgrade 3 : checking failure of constraints too
        for c in self.constraints:
            if c.failure():
                return False, "Constraint Fail"
        return True, ""

    def model_truth(self):
        for c in self.constraints:
            if not c.satisfied():
                return False
        return True


class Sgp:
    def __init__(self, g, s, w) -> None:
        self.groups = g
        self.size = s
        self.weeks = w
        self.n = self.groups * self.size
        self.schedule = []

    def init_schedule(self):
        self.schedule = np.empty((self.weeks, self.groups), Set_var)
        for w in range(len(self.schedule)):
            for g in range(len(self.schedule[w])):
                self.schedule[w, g] = Set_var(
                    [], list(range(self.n)), (self.size, self.size), "s[{},{}]".format(w, g))

    def init_schedule_first_week(self):
        self.schedule = np.empty((self.weeks, self.groups), Set_var)
        for w in range(len(self.schedule)):
            for g in range(len(self.schedule[w])):
                if w == 0:
                    self.schedule[w, g] = Set_var(
                        range(g*self.size, (g+1)*self.size), range(g*self.size, (g+1)*self.size), (self.size, self.size))
                else:
                    self.schedule[w, g] = Set_var(
                        [], list(range(self.n)), (self.size, self.size), "s[{},{}]".format(w, g))

    def model_sgp(self):
        model = Model()
        for w in range(self.weeks):
            for g1 in range(self.groups):
                for g2 in range(g1):
                    model.add_constraint(EmptyIntersection(
                        self.schedule[w, g1], self.schedule[w, g2]))

        for w1 in range(self.weeks):
            for w2 in range(w1):
                for g1 in range(self.groups):
                    for g2 in range(self.groups):
                        H = Set_var([], list(range(self.n)), (0, 1),
                                    "[{},{}]\u2229[{},{}]".format(w1, g1, w2, g2))
                        model.add_constraint(Intersection(
                            self.schedule[w1, g1], self.schedule[w2, g2], H))
        return model

    def get_basic_model(self):
        self.init_schedule()
        return self.model_sgp()

    def first_week_model(self):
        self.init_schedule_first_week()
        return self.model_sgp()

    def print_sol(self):
        for w in range(len(self.schedule)):
            print("", end="| ")
            for g in range(len(self.schedule[w])):
                for golfer in self.schedule[w, g].lb:
                    print("{:<2}".format(golfer), end=" ")
                print("", end="| ")
            print("")
