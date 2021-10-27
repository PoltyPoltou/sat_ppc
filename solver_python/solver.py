import set_var
import constraint
from memento import LB_memento, Memento, UB_memento


class Model:
    def __init__(self) -> None:
        self.constraints: set(constraint.Constraint) = set()
        self.variables: set(set_var.Set_var) = set()
        self.var_to_constraints = {}

    def add_constraint(self, cons: constraint.Constraint):
        self.constraints.add(cons)
        for var in cons.get_vars():
            self.variables.add(var)
            if var not in self.var_to_constraints.keys():
                self.var_to_constraints[var] = []
        for var in cons.get_vars():
            self.var_to_constraints[var].append(cons)


class Propagator:
    def __init__(self, model) -> None:
        self.model: Model = model  #  model to propagate stuff on
        self.modifications: list[list[Memento]] = [[]]
        self.loops_backtrack = 3
        self.propagate_loops = 10

    def add_level_of_modification(self, new_modifs):
        self.modifications.append(new_modifs)

    def append_modification(self, new_modifs):
        feasable = True
        for m in new_modifs:
            m.apply()
            feasable = feasable and m.valid
        self.modifications[-1].extend(new_modifs)
        return feasable

    def propagate(self):
        woken_constraints = set(self.model.constraints)
        i = 0
        while len(woken_constraints) != 0 and i < self.propagate_loops:
            i += 1
            constraint = woken_constraints.pop()
            mementos = constraint.filter()

            if not self.append_modification(mementos):
                return False  #  modifications made one var impossible thus we return False

            # waking up constraints
            for m in mementos:
                for new_constraint in self.model.var_to_constraints[m.var]:
                    if new_constraint != constraint:
                        woken_constraints.add(new_constraint)
            # applying modifications
            for var in self.model.variables:
                if not self.append_modification(var.filter_on_card()):
                    return False  #  modifications made one var impossible thus we return False
            # checking feasability
            if i % self.loops_backtrack == 0:
                for var in self.model.variables:
                    if not var.feasable():
                        return False
        return True

    def backtrack(self):
        modif_to_revert: list[Memento] = self.modifications.pop()
        for memento in modif_to_revert:
            memento.revert()


def iterate_var_val(model: Model):
    for var in model.variables:
        if var.feasable() and not var.defined():
            value = next(iter(var.ub-var.lb))
            return [LB_memento(var, {value}), UB_memento(var, {value})]
    return []


def model_truth(model: Model):
    for c in model.constraints:
        if not c.satisfied():
            return False
    return True


def solve(model: Model, propagator=None, sgp=None):
    if propagator == None:
        # init of solving
        propagator = Propagator(model)
    if propagator.propagate():
        modifs = iterate_var_val(model)
        if len(modifs) == 0:
            if sgp != None:
                sgp.print_sol()
            return model_truth(model)
        for memento in modifs:
            memento.apply()
            propagator.add_level_of_modification([])
            if solve(model, propagator):
                return True
            propagator.backtrack()
            memento.revert()
    return False
