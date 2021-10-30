import multiprocessing
from time import sleep, time
from ete3.treeview.faces import TextFace
import model
import solver
import testing
import sys
from ete3 import Tree
import os.path

testing.test_all()


def print_tree(t, name):
    for node in t.traverse():
        if not node.is_leaf():
            node.add_face(TextFace(node.name), 0)
    t.render("./ppc/" + name + ".svg")


def solve(name, g, s, w, f):
    a = model.Sgp(g, s, w)
    model_0 = time()
    mdl = a.all_week_model()
    model_1 = time()
    t = Tree()
    solve_0 = time()
    feseable = solver.solve(mdl, sgp=a, tree=t)
    solve_1 = time()

    for node in t.traverse():
        if not node.is_leaf():
            node.add_face(TextFace(node.name), 0)
    global lock
    pdf_name = "./ppc/{}_{}-{}-{}.pdf".format(name, g, s, w)
    if not os.path.isfile(pdf_name):
        with lock:
            t.render(pdf_name)
    f.write("{}-{}-{} feasable : {}, model : {:.2f}s, solve : {:.2f}s\n".format(
        g, s, w, feseable, model_1-model_0, solve_1-solve_0))


def benchmark(name, g, s, weeks):
    with open("./ppc/{}_{}-{}.txt".format(name, g, s), "x") as f:
        for w in weeks:
            solve(name, g, s, w, f)
            f.flush()


def bench_core(name, g, s, weeks):
    th = multiprocessing.Process(
        target=lambda: benchmark(name, g, s, weeks))
    th.start()
    return th


if __name__ == "__main__":
    lock = multiprocessing.Lock()
    if len(sys.argv) == 3 and sys.argv[1] == "bench":
        name = sys.argv[2]
        th = bench_core(name, 5, 3, range(1, 12))
        th1 = bench_core(name, 5, 4, range(1, 10))
        th2 = bench_core(name, 8, 4, range(1, 10))
        sleep(3600)
        th.terminate()
        th1.terminate()
        th2.terminate()
