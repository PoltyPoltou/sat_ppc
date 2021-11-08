from ete3.coretype.tree import Tree, TreeNode
from memento import LB_memento, UB_memento
from model import Model
from propagator import Propagator
import random
random.seed(0)


def iterate_var_val(model: Model):
    # upgrade 4 having prioritized variables
    priority_var = model.var_priority_dict[max(model.var_priority_dict.keys())]
    for var in [v for v in priority_var if not v.set()]:
        if var.feasible() and not var.defined():
            value = next(iter(var.ub-var.lb))
            return [LB_memento(var, {value}), UB_memento(var, {value})]
    for var in model.enum_variables():
        if var.feasible() and not var.defined():
            value = next(iter(var.ub-var.lb))
            return [LB_memento(var, {value}), UB_memento(var, {value})]
    return []


def iterate_var_val_order_bound(model: Model, ub=True, descending=False):
    # upgrade 5 ?
    ordered_var = sorted(
        model.enum_variables(), key=lambda var: len(var.ub if ub else var.lb), reverse=descending)
    for var in ordered_var:
        if var.feasible() and not var.defined():
            value = next(iter(var.ub-var.lb))
            return [LB_memento(var, {value}), UB_memento(var, {value})]
    return []


def solve(model: Model, propagator=None, sgp=None, tree: TreeNode = Tree()):
    if propagator == None:
        # init of solving
        propagator = Propagator(model)
    propagate_infos = propagator.propagate()
    if propagate_infos[0]:
        modifs = iterate_var_val(model)
        if len(modifs) == 0:
            valid = model.model_truth()
            tree.add_child(name="EOF" + str(valid))
            return valid
        for memento in modifs:
            memento.apply()
            propagator.add_level_of_modification([])
            if solve(model, propagator, sgp, tree.add_child(name=str(memento))):
                return True
            propagator.backtrack()
            memento.revert()
    else:
        tree.add_child(name=propagate_infos[1])

    return False
