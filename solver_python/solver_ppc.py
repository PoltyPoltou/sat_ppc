import multiprocessing
import os
from ete3.treeview.faces import TextFace
from time import time
from ete3 import Tree
from . import model
from . import solver
lock = multiprocessing.Lock()


def solve_ppc_recur(g, s, w, f=None, name=None):
    # Solve and timings and writing
    sgp_ppc_model = model.Sgp(g, s, w)
    model_0 = time()
    mdl = sgp_ppc_model.all_week_model()
    model_1 = time()
    t = Tree()
    solve_0 = time()
    feseable = solver.solve(mdl, sgp=sgp_ppc_model, tree=t)
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
        f.write("{}-{}-{} feasible : {}, model : {:.2f}s, solve : {:.2f}s\n".format(
            g, s, w, feseable, model_1-model_0, solve_1-solve_0))
    else:
        print("{}-{}-{} feasible : {}, model : {:.2f}s, solve : {:.2f}s".format(
            g, s, w, feseable, model_1-model_0, solve_1-solve_0))


def solve_ppc_iter(g, s, w, f=None, name=None):
    # Solve and timings and writing
    sgp_ppc_model = model.Sgp(g, s, w)
    model_0 = time()
    mdl = sgp_ppc_model.all_week_model()
    model_1 = time()
    solve_0 = time()
    feseable, t = solver.solve_iterative(mdl)
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
        f.write("{}-{}-{} feasible : {}, model : {:.2f}s, solve : {:.2f}s\n".format(
            g, s, w, feseable, model_1-model_0, solve_1-solve_0))
    else:
        print("{}-{}-{} feasible : {}, model : {:.2f}s, solve : {:.2f}s".format(
            g, s, w, feseable, model_1-model_0, solve_1-solve_0))
