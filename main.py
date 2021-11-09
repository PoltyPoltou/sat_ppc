import multiprocessing
from time import sleep
from solver_python import testing
import sys
import os
testing.test_all()


def benchmark(name, g, s, weeks):
    # runs all sgp problems and copy timings and infos in a file
    if not os.path.exists("./ppc/" + name):
        os.mkdir("./ppc/"+name)
    with open("./ppc/{}/{}-{}.txt".format(name, g, s), "x") as f:
        for w in weeks:
            solve(g, s, w, f, name)
            f.flush()


def bench_core(name, g, s, weeks):
    # start a thread on another CPU core for the given weeks
    th = multiprocessing.Process(
        target=lambda: benchmark(name, g, s, weeks))
    th.start()
    return th


if __name__ == "__main__":
    from solver_python.solver_ppc import solve_ppc
    from solver_set_sat import solve_sgp_adv, solve_sgp_basic
    from solver_ppc_sat import solve_csp_set_sat_mix, solve_csp_pure_sat_mix
    from sgp import solve_pure_sat
    solve = solve_csp_set_sat_mix()
    if not os.path.isdir("./ppc"):
        os.mkdir("./ppc")
    if len(sys.argv) == 4:
        # usage : python main.py 5 3 3
        # will add the pdf tree in ./ppc/pog/5-3-3.pdf
        if not os.path.exists("./ppc/pog"):
            os.mkdir("./ppc/pog")
        solve(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), name="pog")
    if len(sys.argv) == 3 and sys.argv[1] == "bench":
        # usage : python main.py bench foo3
        # will run 5-3 5-4 and 8-4 tests for 1h in *parrallel*
        # all results in ./ppc/foo3/
        name = sys.argv[2]
        os.mkdir("./ppc/{}".format(name))
        th = bench_core(name, 5, 3, range(1, 12))
        th1 = bench_core(name, 5, 4, range(1, 10))
        th2 = bench_core(name, 8, 4, range(1, 10))
        sleep(3600)
        th.terminate()
        th1.terminate()
        th2.terminate()
