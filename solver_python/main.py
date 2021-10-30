import multiprocessing
from time import sleep, time
from ete3.treeview.faces import TextFace
import model
import solver
import testing
import sys
from ete3 import Tree
import os

testing.test_all()


def solve(g, s, w, name=None, f=None):
    # Solve and timings and writing
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
    if name != None:
        global lock
        pdf_name = "./ppc/{}/{}-{}-{}.pdf".format(name, g, s, w)
        if not os.path.isfile(pdf_name):
            with lock:
                t.render(pdf_name)
    if f != None:
        f.write("{}-{}-{} feasible : {}, model : {:.2f}s, solve : {:.2f}s\n".format(
            g, s, w, feseable, model_1-model_0, solve_1-solve_0))


def benchmark(name, g, s, weeks):
    # runs all sgp problems and copy timings and infos in a file
    with open("./ppc/{}/{}-{}.txt".format(name, g, s), "x") as f:
        for w in weeks:
            solve(g, s, w, name, f)
            f.flush()


def bench_core(name, g, s, weeks):
    # start a thread on another CPU core for the given weeks
    th = multiprocessing.Process(
        target=lambda: benchmark(name, g, s, weeks))
    th.start()
    return th


if __name__ == "__main__":
    lock = multiprocessing.Lock()
    if len(sys.argv) == 4:
        # usage : python main.py 5 3 3
        # will add the pdf tree in ./ppc/pog/5-3-3.pdf
        solve(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), "pog")
    if len(sys.argv) == 3 and sys.argv[1] == "bench":
        # usage : python main.py bench foo3
        # will run 5-3 5-4 and 8-4 tests for 1h in *parrallel*
        # all results in ./ppc/foo3/
        name = sys.argv[2]
        if not os.path.isdir("./ppc"):
            os.mkdir("./ppc")
        os.mkdir("./ppc/{}".format(name))
        th = bench_core(name, 5, 3, range(1, 12))
        th1 = bench_core(name, 5, 4, range(1, 10))
        th2 = bench_core(name, 8, 4, range(1, 10))
        sleep(3600)
        th.terminate()
        th1.terminate()
        th2.terminate()
