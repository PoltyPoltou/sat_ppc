from .model import Model
from .memento import Memento


class Propagator:
    def __init__(self, model, propagate_loops=10000) -> None:
        self.model: Model = model  #  model to propagate stuff on
        self.modifications: list[list[Memento]] = [[]]
        self.loops_backtrack = 3
        self.propagate_loops = propagate_loops

    def add_level_of_modification(self, new_modifs):
        self.modifications.append(new_modifs)

    def append_modification(self, new_modifs):
        """
        add new modifications to the actual level and apply every memento\n
        return the feasability of the variables after applying
        these mementos and the memento object assiociated
        """
        feasible = True
        faulty_memento = None
        for m in new_modifs:
            m.apply()
            if feasible and not m.valid:
                faulty_memento = m
                feasible = False
        self.modifications[-1].extend(new_modifs)
        return feasible, faulty_memento

    def propagate(self, nb_iter=-1):
        # nb_iter defines the number of loops to do, by default it is self.propagate_loops
        if nb_iter < 0:
            nb_iter = self.propagate_loops
        # We put every constraint at initialization
        woken_constraints = set(self.model.constraints)
        i = -1
        while len(woken_constraints) != 0 and i < nb_iter:
            i += 1
            # upgrade 2 : checking first for false model at a fixed frequency
            if i % self.loops_backtrack == 0:
                feasible_status = self.model.feasible()
                if not feasible_status[0]:
                    return feasible_status
            constraint = woken_constraints.pop()
            mementos = constraint.filter()
            modif_infos = self.append_modification(mementos)
            if not modif_infos[0]:
                #  modifications made one var impossible thus we return False
                return False, "Var unsat" + str(modif_infos[1])

            # waking up constraints
            for m in mementos:
                # upgrade 1 : checking effectivity of modification (ie. if the var is affected)
                if m.effective():
                    for new_constraint in self.model.var_to_constraints[m.var]:
                        if new_constraint != constraint:
                            woken_constraints.add(new_constraint)
            # applying card filtering
            for var in self.model.variables:
                if not self.append_modification(var.filter_on_card()):
                    #  modifications made one var impossible thus we return False
                    return False, "Var unsat card"
        return True, ""

    def backtrack(self):
        modif_to_revert: list[Memento] = self.modifications.pop()
        for i in range(len(modif_to_revert)):
            modif_to_revert[-i].revert()
