import sys
from time import time
from set_sat import Set_Sat
from set_sat_advanced import Set_Sat_Adv


def init_set_variables(groups, size, weeks, sgp, n_golfers, schedule):
    for w in range(weeks):
        for g in range(groups):
            if w == 0:
                schedule[w][g] = sgp.add_set_var(
                    range(g*size, (g+1)*size), range(g*size, (g+1)*size))
            else:
                schedule[w][g] = sgp.add_set_var(
                    [i for i in range(size) if i % groups == g], range(n_golfers))


def init_constraints(groups, size, weeks, sgp, n_golfers, schedule):
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
    for w in range(weeks):
        sgp.order_by_min(schedule[w])
    # sgp.order_by_max([schedule[w][0] for w in range(weeks)])


def sgp_set_to_sat(groups,
                   size,
                   weeks,
                   out=sys.stdout,
                   sgp=Set_Sat()):

    model_start = time()
    n_golfers = size * groups
    schedule = [[0]*groups for i in range(weeks)]

    init_set_variables(groups, size, weeks, sgp, n_golfers, schedule)

    init_constraints(groups, size, weeks, sgp, n_golfers, schedule)
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


def solve_sgp_adv(g, s, w, f=None, name=None):
    sgp_set_to_sat(g, s, w, f, sgp=Set_Sat_Adv())


def solve_sgp_basic(g, s, w, f=None, name=None):
    sgp_set_to_sat(g, s, w, f, sgp=Set_Sat())
