import sys
from time import time
from set_sat import Set_Sat


def sgp_set_to_sat(groups,
                   size,
                   weeks,
                   out=sys.stdout):

    model_start = time()
    n_golfers = size * groups
    sgp = Set_Sat()
    schedule = [[0]*groups for i in range(weeks)]

    for w in range(weeks):
        for g in range(groups):
            if w == 0:
                schedule[w][g] = sgp.add_set_var(
                    range(g*size, (g+1)*size), range(g*size, (g+1)*size))
            else:
                schedule[w][g] = sgp.add_set_var([], range(n_golfers))

    for w in range(weeks):
        for g in range(groups):
            sgp.cardinal(schedule[w][g], size)

    for w in range(weeks):
        for g1 in range(groups):
            for g2 in range(g1):
                sgp.intersection_empty(schedule[w][g1], schedule[w][g2])

    for w1 in range(weeks):
        for w2 in range(w1):
            for g1 in range(groups):
                for g2 in range(groups):
                    k = sgp.add_set_var([], range(n_golfers))
                    sgp.intersection(
                        schedule[w1][g1], schedule[w2][g2], k, True, True)
                    sgp.cardinal_ub(k, 1)
    model_end = time()

    mdl = sgp.solve()
    solve_end = time()
    print("\n{}-{}-{}\nvariables : {} clauses : {}".format(groups, size,
          weeks, sgp.idx_next_var-1, len(sgp.cnf.clauses)), file=out)
    print("model : {:.2f}s solver : {:.2f}s".format(
        model_end - model_start, solve_end - model_end), file=out)

    sol = sgp.model_to_set_solution(mdl)
    if sol != []:
        for i in range(groups*weeks):
            if i % groups == 0:
                print("\n|", end="", file=out)
            for elmt in sol[i]:
                print("{:<2}".format(elmt), end=" ", file=out)
            print("| ", end="", file=out)
        print("", file=out)
    else:
        print("UNSAT", file=out)
    return sol


def benchmark(name, g, s, weeks):
    f = open("./set_sat/{}_{}-{}.txt".format(name, g, s), "x")
    for w in weeks:
        sgp_set_to_sat(g, s, w, f)
        f.flush()
    f.close()


if __name__ == "__main__":

    if sys.argv[-1] == "test":

        b = Set_Sat()
        b.add_set_var([1], [1, 2, 3])
        b.add_set_var([1], [1, 2, 3])
        b.add_set_var([2], [1, 2, 3])
        b.intersection(0, 1, 2)
        print(b.model_to_set_solution(b.solve()))
        sgp_set_to_sat(5, 3, 6)

    elif len(sys.argv) == 4:
        sgp_set_to_sat(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[-1] == "bench":
        name = "seteq"
        benchmark(name, 5, 3, range(1, 8))
        benchmark(name, 5, 4, range(1, 6))
        benchmark(name, 8, 4, range(1, 8))
