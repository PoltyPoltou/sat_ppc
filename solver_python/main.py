import multiprocessing
from time import sleep
import testing
import sys
import os
from .solver_ppc import solve
testing.test_all()


def benchmark(name, g, s, weeks):
    # runs all sgp problems and copy timings and infos in a file
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
    lock = multiprocessing.Lock()
    if len(sys.argv) == 4:
        # usage : python main.py 5 3 3
        # will add the pdf tree in ./ppc/pog/5-3-3.pdf
        solve(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), name="pog")
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
