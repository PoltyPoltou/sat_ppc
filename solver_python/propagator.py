from model import Model
from memento import Memento


class Propagator:
    def __init__(self, model) -> None:
        self.model: Model = model  #  model to propagate stuff on
        self.modifications: list[list[Memento]] = [[]]
        self.loops_backtrack = 3
        self.propagate_loops = 10000

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
        # checking first for false model
        if not self.model.feasable():
            return False
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
                # upgrade 1 : checking effectivity of modification (ie. the var will be affected)
                if m.effective():
                    for new_constraint in self.model.var_to_constraints[m.var]:
                        if new_constraint != constraint:
                            woken_constraints.add(new_constraint)
        # checking feasability
            if i % self.loops_backtrack == 0:
                if not self.model.feasable():
                    return False
            # applying modifications
            for var in self.model.variables:
                if not self.append_modification(var.filter_on_card()):
                    return False  #  modifications made one var impossible thus we return False
        return True

    def backtrack(self):
        modif_to_revert: list[Memento] = self.modifications.pop()
        for memento in modif_to_revert:
            memento.revert()
