import numpy as np
from .constraint import *
from .set_var import Set_var


class Model:
    '''
    Class that stores contraints and variables of a model
    a map to link variables to its constraints
    a map to link priority to every variables with that priority
    '''

    def __init__(self) -> None:
        self.constraints: set(Constraint) = set()
        self.variables: set(Set_var) = set()
        self.var_priority_dict = {}
        self.var_to_constraints = {}

    def add_constraint(self, cons: Constraint):
        '''
        add the constraint, every variable not yet in the model and updates var_priority_dict and var_to_constraints
        '''
        self.constraints.add(cons)
        for var in cons.get_vars():
            if var not in self.variables:
                self.variables.add(var)
                if var.priority not in self.var_priority_dict.keys():
                    self.var_priority_dict[var.priority] = []
                self.var_priority_dict[var.priority].append(var)
            if var not in self.var_to_constraints.keys():
                self.var_to_constraints[var] = []
        for var in cons.get_vars():
            self.var_to_constraints[var].append(cons)

    def feasible(self) -> tuple[bool, str]:
        '''
        checks constraints failure and variable feasibility
        return True, "" if the model is still feasible
        return (False, reason) if the model is not feasible
        '''
        for var in self.variables:
            if not var.feasible():
                return False, "Var unsat"
        # upgrade 3 : checking failure of constraints too
        for c in self.constraints:
            if c.failure():
                return False, "Constraint Fail"
        return True, ""

    def model_truth(self):
        '''
        checks that every constraint is satisfied
        '''
        for c in self.constraints:
            if not c.satisfied():
                return False
        return True

    def enum_variables(self):
        '''
        return a list of variables not yet set
        '''
        return [v for v in self.variables if not v.set()]


class Sgp:
    '''
    sgp modelisation
    functions to get a Model with different symmetry breaking
    main use is with :\n
    - get_basic_model\n
    - first_week_model\n
    - all_week_model\n
    - print_sol
    '''

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
                    [], list(range(self.n)), (self.size, self.size), "s[{},{}]".format(w, g), 1)

    def init_schedule_first_week(self):
        self.schedule = np.empty((self.weeks, self.groups), Set_var)
        for w in range(len(self.schedule)):
            for g in range(len(self.schedule[w])):
                if w == 0:
                    self.schedule[w, g] = Set_var(
                        range(g*self.size, (g+1)*self.size), range(g*self.size, (g+1)*self.size), (self.size, self.size), "s[{},{}]".format(w, g))
                else:
                    self.schedule[w, g] = Set_var(
                        [], list(range(self.n)), (self.size, self.size), "s[{},{}]".format(w, g), 1)

    def init_schedule_all_week(self):
        self.schedule = np.empty((self.weeks, self.groups), Set_var)
        for w in range(self.weeks):
            for g in range(self.groups):
                if w == 0:
                    self.schedule[w, g] = Set_var(
                        range(g*self.size, (g+1)*self.size), range(g*self.size, (g+1)*self.size), (self.size, self.size), "s[{},{}]".format(w, g))
                else:
                    self.schedule[w, g] = Set_var(
                        [i for i in range(self.size) if i % self.groups == g], list(range(self.n)), (self.size, self.size), "s[{},{}]".format(w, g), 1)

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
        for w in range(self.weeks):
            for g in range(1, self.groups):
                model.add_constraint(strict_less_than_by_min(
                    self.schedule[w, g-1], self.schedule[w, g]))
        for w in range(1, self.weeks):
            model.add_constraint(strict_less_than_by_max(
                self.schedule[w-1, 0], self.schedule[w, 0]))
        return model

    def get_basic_model(self):
        self.init_schedule()
        return self.model_sgp()

    def first_week_model(self):
        self.init_schedule_first_week()
        return self.model_sgp()

    def all_week_model(self):
        self.init_schedule_all_week()
        return self.model_sgp()

    def get_week_str(self, w):
        string = "|"
        for g in range(len(self.schedule[w])):
            for golfer in self.schedule[w, g].lb:
                string += "{:<2}".format(golfer) + " "
            string += "|"
        return string

    def print_sol(self, lb=True):
        for w in range(len(self.schedule)):
            print("", end="| ")
            for g in range(len(self.schedule[w])):
                for golfer in (self.schedule[w, g].lb if lb else self.schedule[w, g].ub):
                    print("{:<2}".format(golfer), end=" ")
                print("", end="| ")
            print("")
