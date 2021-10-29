from ete3.coretype.tree import Tree, TreeNode
from memento import LB_memento, UB_memento
from model import Model
from propagator import Propagator


def iterate_var_val(model: Model):
    # upgrade 4 having prioritized variables
    priority_var = model.var_priority_dict[max(model.var_priority_dict.keys())]
    for var in priority_var:
        if var.feasable() and not var.defined():
            value = next(iter(var.ub-var.lb))
            return [LB_memento(var, {value}), UB_memento(var, {value})]
    for var in model.variables:
        if var.feasable() and not var.defined():
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
            week = ""
            if sgp:
                week = sgp.get_week_str(1)
            propagator.add_level_of_modification([])
            if solve(model, propagator, sgp, tree.add_child(name=week + str(memento))):
                return True
            propagator.backtrack()
            memento.revert()
    else:
        tree.add_child(name=propagate_infos[1])

    return False
