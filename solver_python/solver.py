from ete3.coretype.tree import Tree, TreeNode
import random

from .cspnode import CSPNode
from .memento import LB_memento, UB_memento
from .model import Model
from .propagator import Propagator
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


def go_to_next_node(exec_node: CSPNode, propagator: Propagator, backtrack=False, backjump=None):
    if backjump != None:
        pass
    elif backtrack:
        if exec_node.up == None:
            raise Exception("backtrack on root node")
        else:
            while exec_node.up != None and exec_node.up.children.index(exec_node) == len(exec_node.up.children)-1:
                propagator.backtrack()
                exec_node.revert_memento()
                exec_node = exec_node.up
            if exec_node.up == None:
                # we have no node left to explore
                return None
        propagator.backtrack()
        exec_node.revert_memento()
        child_idx = exec_node.up.children.index(exec_node)
        exec_node = exec_node.up.children[child_idx+1]
        exec_node.apply_memento()
        propagator.add_level_of_modification([])
        return exec_node
    else:
        if len(exec_node.children) == 0:
            raise Exception(
                "go_to_next_node without backtrack used with no children available")
        else:
            exec_node.children[0].apply_memento()
            propagator.add_level_of_modification([])
            return exec_node.children[0]


def solve_iterative(model: Model, sgp=None):
    propagator = Propagator(model)
    exec_tree = CSPNode()
    exec_node = exec_tree
    while exec_node != None:
        propagate_infos = propagator.propagate()
        new_modifs = iterate_var_val(model)
        if len(new_modifs) == 0 and model.model_truth():
            exec_node.add_child(name="Found")
            return True, exec_tree
        elif len(new_modifs) == 0 or not propagate_infos[0]:
            exec_node.add_child(name="backtrack")
            if exec_node == exec_tree:
                # special case of backtrack on root node
                return False, exec_tree
            exec_node = go_to_next_node(
                exec_node, propagator, backtrack=True)
        else:
            for modif in new_modifs:
                exec_node.add_child(CSPNode(modif))
            exec_node = go_to_next_node(exec_node, propagator)

    return False, exec_tree
