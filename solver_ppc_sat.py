import multiprocessing
import os
from time import time

from ete3.coretype.tree import Tree, TreeNode
from ete3.treeview.faces import TextFace
from set_sat import Set_Sat
from set_sat_advanced import Set_Sat_Adv
from sgp import SGP_pure_sat, init_constraint_pure_sat
from solver_python import model, propagator, solver
import numpy as np
import solver_set_sat

lock = multiprocessing.Lock()


def solve_ppc(g, s, w, f=None, name=None):
    # create a sgp in CSP
    set_sgp = model.Sgp(g, s, w)

    # time and create an instance of this sgp
    start = time()
    set_model = set_sgp.all_week_model()
    model_ppc_time = time() - start

    # time and propagate at the beggining
    set_propagator = propagator.Propagator(set_model)
    start = time()
    set_propagator.propagate()
    propagation_time = time() - start
    # to finish idk if it will be useful


def init_sat_set_sgp_variables_from_csp(sgp_csp: model.Sgp, sgp_sat: Set_Sat):
    """
    takes a CSP sgp and add every schedule variable and add it to the SAT sgp problem\n
    return the array schedule with the indexes of the variables
    """
    weeks = sgp_csp.weeks
    groups = sgp_csp.groups
    schedule = [[0] * groups for i in range(weeks)]
    for w in range(weeks):
        for g in range(groups):
            schedule[w][g] = sgp_sat.add_set_var(
                sgp_csp.schedule[w][g].lb, sgp_csp.schedule[w][g].ub
            )
    return schedule


def transform_csp_to_sat_sgp_adv(sgp_csp: model.Sgp):
    """
    take a existing CSP sgp and returns a SAT (Set_Sat_Adv) modelisation with the actual lb-ub found by the CSP\n
    and the schedule array indexes
    """
    sgp_sat = Set_Sat_Adv()
    schedule = init_sat_set_sgp_variables_from_csp(sgp_csp, sgp_sat)
    solver_set_sat.init_constraints(
        sgp_csp.groups, sgp_csp.size, sgp_csp.weeks, sgp_sat, sgp_csp.n, schedule
    )
    return sgp_sat, schedule


def solve_pure_sat_from_csp(sgp_csp: model.Sgp, pure_sat_model: SGP_pure_sat):
    """
    take a existing CSP sgp and returns a SAT (pure) modelisation with the actual lb-ub found by the CSP
    """
    assumptions = []
    for w in range(sgp_csp.weeks):
        for g in range(sgp_csp.groups):
            for golfer in range(sgp_csp.n):
                if golfer in sgp_csp.schedule[w][g].lb:
                    assumptions.append(pure_sat_model.var_encoding[w][g][golfer])
                if golfer not in sgp_csp.schedule[w][g].ub:
                    assumptions.append(-pure_sat_model.var_encoding[w][g][golfer])
    pure_sat_model.solve(assumptions)
    return pure_sat_model.get_set_solution()


def solve_sgp_ppc_pure_sat(
    model: model.Model,
    propag=None,
    sgp_csp: model.Sgp = None,
    tree: TreeNode = Tree(),
    depth=0,
    pure_sat_model=None,
):
    if pure_sat_model == None:
        pure_sat_model = SGP_pure_sat(sgp_csp.groups, sgp_csp.size, sgp_csp.weeks)
        init_constraint_pure_sat(pure_sat_model)
    if depth == 5:
        # we switch to sat modeling and solve it
        start = time()
        solution_set = solve_pure_sat_from_csp(sgp_csp, pure_sat_model)
        sat_solve = time() - start
        if len(solution_set) == 0:
            tree.add_child(name="SAT->UNSAT {:.2f}".format(sat_solve))
            return False
        else:
            # we found a solution in SAT, we must set variables of the csp
            # to the value found in the SAT problem
            for w in range(sgp_csp.weeks):
                for g in range(sgp_csp.groups):
                    sgp_csp.schedule[w, g].lb = set(solution_set[w][g])
                    sgp_csp.schedule[w, g].ub = set(solution_set[w][g])
            tree.add_child(name="SAT->EOF {:.2f}".format(sat_solve))
            return True
    else:
        if propag == None:
            # init of solving
            propag = propagator.Propagator(model, 500)
        propagate_infos = propag.propagate()
        if propagate_infos[0]:
            modifs = solver.iterate_var_val(model)
            if len(modifs) == 0:
                valid = model.model_truth()
                tree.add_child(name="EOF" + str(valid))
                return valid
            for memento in modifs:
                memento.apply()
                propag.add_level_of_modification([])
                if solve_sgp_ppc_pure_sat(
                    model,
                    propag,
                    sgp_csp,
                    tree.add_child(name=str(memento)),
                    depth=depth + 1,
                    pure_sat_model=pure_sat_model,
                ):
                    return True
                propag.backtrack()
                memento.revert()
        else:
            tree.add_child(name=propagate_infos[1])
        return False


def solve_sgp_ppc_sat(
    model: model.Model,
    propag=None,
    sgp_csp: model.Sgp = None,
    tree: TreeNode = Tree(),
    depth=0,
):
    if depth == 5:
        # we switch to sat modeling and solve it
        sat_sgp, schedule = transform_csp_to_sat_sgp_adv(sgp_csp)
        start = time()
        solution_sat = sat_sgp.solve()
        sat_solve = time() - start
        if len(solution_sat) == 0:
            tree.add_child(name="SAT->UNSAT {:.2f}".format(sat_solve))
            return False
        else:
            # we found a solution in SAT, we must set variables of the csp
            # to the value found in the SAT problem
            solution_set = sat_sgp.model_to_set_solution(solution_sat)
            for w in range(sgp_csp.weeks):
                for g in range(sgp_csp.groups):
                    sgp_csp.schedule[w, g].lb = set(solution_set[schedule[w][g]])
                    sgp_csp.schedule[w, g].ub = set(solution_set[schedule[w][g]])
            tree.add_child(name="SAT->FOUND EOF {:.2f}".format(sat_solve))
            return True
    else:
        if propag == None:
            # init of solving
            propag = propagator.Propagator(model, 1000)
        propagate_infos = propag.propagate()
        if propagate_infos[0]:
            modifs = solver.iterate_var_val(model)
            if len(modifs) == 0:
                valid = model.model_truth()
                tree.add_child(name="EOF" + str(valid))
                return valid
            for memento in modifs:
                memento.apply()
                propag.add_level_of_modification([])
                if solve_sgp_ppc_sat(
                    model,
                    propag,
                    sgp_csp,
                    tree.add_child(name=str(memento)),
                    depth=depth + 1,
                ):
                    return True
                propag.backtrack()
                memento.revert()
        else:
            tree.add_child(name=propagate_infos[1])
        return False


def solve_csp_sat(g, s, w, f=None, name=None, solve_method=None):
    # Solve and timings and writing
    sgp_ppc_model = model.Sgp(g, s, w)
    model_0 = time()
    mdl = sgp_ppc_model.all_week_model()
    model_1 = time()
    t = Tree()
    solve_0 = time()
    feseable = solve_method(mdl, sgp_csp=sgp_ppc_model, tree=t)
    solve_1 = time()

    for node in t.traverse():
        if not node.is_leaf():
            node.add_face(TextFace(node.name), 0)
    if name != None:
        pdf_name = "./ppc/{}/{}-{}-{}.pdf".format(name, g, s, w)
        if not os.path.isfile(pdf_name):
            with lock:
                t.render(pdf_name)
    if f != None:
        f.write(
            "{}-{}-{} feasible : {}, model : {:.2f}s, solve : {:.2f}s\n".format(
                g, s, w, feseable, model_1 - model_0, solve_1 - solve_0
            )
        )
    else:
        print(
            "{}-{}-{} feasible : {}, model : {:.2f}s, solve : {:.2f}s".format(
                g, s, w, feseable, model_1 - model_0, solve_1 - solve_0
            )
        )


def solve_csp_set_sat_mix():
    return lambda g, s, w, f=None, name=None: solve_csp_sat(
        g, s, w, f, name, solve_method=solve_sgp_ppc_sat
    )


def solve_csp_pure_sat_mix():
    return lambda g, s, w, f=None, name=None: solve_csp_sat(
        g, s, w, f, name, solve_method=solve_sgp_ppc_pure_sat
    )
