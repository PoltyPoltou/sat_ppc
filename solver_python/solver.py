from ete3.coretype.tree import Tree, TreeNode
from memento import LB_memento, UB_memento
from model import Model
from propagator import Propagator


def iterate_var_val(model: Model):
    for var in model.variables:
        if var.feasable() and not var.defined():
            value = next(iter(var.ub-var.lb))
            return [LB_memento(var, {value}), UB_memento(var, {value})]
    return []


def solve(model: Model, propagator=None, sgp=None, tree: TreeNode = Tree()):
    if propagator == None:
        # init of solving
        propagator = Propagator(model)
    if propagator.propagate():
        modifs = iterate_var_val(model)
        if len(modifs) == 0:
            return model.model_truth()
        for memento in modifs:
            memento.apply()
            propagator.add_level_of_modification([])
            if solve(model, propagator, sgp, tree.add_child(name=str(memento))):
                return True
            propagator.backtrack()
            memento.revert()
    return False
