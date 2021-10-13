import multiprocessing
from contextlib import redirect_stdout
import sys
import itertools
from time import sleep, time
import pysat.solvers
import pysat.formula


class SGP:
    def __init__(self, groups, size, weeks):
        self.groups = groups
        self.size = size
        self.weeks = weeks
        self.n_golfers = size * groups
        self.solver = pysat.solvers.Glucose4()
        self.cnf = pysat.formula.CNF()
        self.idx_next_var = 1
        self.idx_last_encoding_var = 0

        self.var_encoding = []
        for w in range(weeks):
            self.var_encoding.append([])
            for g in range(groups):
                self.var_encoding[w].append([])
                for i in range(self.n_golfers):
                    self.var_encoding[w][g].append(self.idx_next_var)
                    self.idx_next_var += 1
        self.idx_last_encoding_var = self.idx_next_var

    def add_clause(self, clause):
        self.solver.add_clause(clause)
        self.cnf.append(clause)

    def print_solution(self, f=sys.stdout):
        if self.solver.status:
            schedule = []
            for w in range(self.weeks):
                schedule.append([])
                for g in range(self.groups):
                    schedule[w].append([])

            for var in self.solver.get_model():
                idx = abs(var)
                if(idx == self.idx_last_encoding_var):
                    break
                sign = (idx / var) == 1
                idx -= 1
                golfeur = idx % self.n_golfers
                g = ((idx - golfeur) // self.n_golfers) % self.groups
                w = (idx - golfeur - g *
                     self.n_golfers) // (self.n_golfers * self.groups)
                if(sign):
                    schedule[w][g].append(golfeur)
            for w in schedule:
                for g in w:
                    for i in g:
                        print("{0:2}".format(i), end="", file=f)
                        print(" ", end="", file=f)
                    print("| ", end="", file=f)
                print("", file=f)
        else:
            print("UNSAT", file=f)

    def solve(self):
        self.solver.solve()


def golfer_one_group_per_week(sgp_pb: SGP):
    for i in range(sgp_pb.n_golfers):
        for w in range(sgp_pb.weeks):
            # at least 1
            clause = []
            for g in range(sgp_pb.groups):
                clause.append(sgp_pb.var_encoding[w][g][i])
            sgp_pb.add_clause(clause)

            # at most 1
            for g1 in range(sgp_pb.groups):
                for g2 in range(g1 + 1, sgp_pb.groups):
                    clause = [-sgp_pb.var_encoding[w][g1]
                              [i], -sgp_pb.var_encoding[w][g2][i]]
                    sgp_pb.add_clause(clause)


def golfers_arent_social(sgp_pb: SGP):
    for w1 in range(sgp_pb.weeks):
        for w2 in range(sgp_pb.weeks):
            if(w1 != w2):
                for i1 in range(sgp_pb.n_golfers):
                    for i2 in range(sgp_pb.n_golfers):
                        if(i1 != i2):
                            for g1 in range(sgp_pb.groups):
                                for g2 in range(sgp_pb.groups):
                                    clause = [-sgp_pb.var_encoding[w1][g1][i1], -sgp_pb.var_encoding[w2][g2]
                                              [i1], -sgp_pb.var_encoding[w1][g1][i2], -sgp_pb.var_encoding[w2][g2][i2]]
                                    sgp_pb.add_clause(clause)


def golfers_arent_social_1(sgp_pb: SGP):
    encounter = [None] * sgp_pb.weeks
    for w in range(sgp_pb.weeks):
        encounter[w] = [None] * sgp_pb.groups
        for g in range(sgp_pb.groups):
            encounter[w][g] = [None] * sgp_pb.n_golfers
            for i1 in range(sgp_pb.n_golfers):
                encounter[w][g][i1] = [None] * sgp_pb.n_golfers
                for i2 in range(sgp_pb.n_golfers):
                    if i1 != i2:
                        encounter[w][g][i1][i2] = sgp_pb.idx_next_var
                        sgp_pb.idx_next_var += 1

    for w in range(sgp_pb.weeks):
        for g in range(sgp_pb.groups):
            for i1 in range(sgp_pb.n_golfers):
                for i2 in range(sgp_pb.n_golfers):
                    if i1 != i2:
                        sgp_pb.add_clause([-sgp_pb.var_encoding[w][g][i1],
                                           -sgp_pb.var_encoding[w][g][i2],
                                           encounter[w][g][i1][i2]])
                        sgp_pb.add_clause([sgp_pb.var_encoding[w][g][i1],
                                           -encounter[w][g][i1][i2]])
                        sgp_pb.add_clause([sgp_pb.var_encoding[w][g][i2],
                                           -encounter[w][g][i1][i2]])

    for w1 in range(sgp_pb.weeks):
        for w2 in range(sgp_pb.weeks):
            if(w1 != w2):
                for i1 in range(sgp_pb.n_golfers):
                    for i2 in range(sgp_pb.n_golfers):
                        if(i1 != i2):
                            for g1 in range(sgp_pb.groups):
                                for g2 in range(sgp_pb.groups):
                                    sgp_pb.add_clause([-encounter[w1][g1][i1][i2],
                                                       -encounter[w2][g2][i1][i2]])


def group_size_fixed_binomial_encoding(sgp_pb: SGP):
    # group size is defined
    all_combin = list(itertools.combinations(
        range(sgp_pb.n_golfers), sgp_pb.size+1))
    for w in range(sgp_pb.weeks):
        for g in range(sgp_pb.groups):
            for subset in all_combin:
                clause = []
                for i in subset:
                    clause.append(-sgp_pb.var_encoding[w][g][i])
                sgp_pb.add_clause(clause)


def at_most_k(sgp_pb: SGP, k, x):
    # http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.83.9527&rep=rep1&type=pdf
    n = len(x)
    s = []
    for i in range(n-1):
        s.append([])
        for j in range(k):
            s[i].append(sgp_pb.idx_next_var)
            sgp_pb.idx_next_var += 1

    clauses = [[-x[0], s[0][0]]]
    for j in range(1, k):
        clauses.append([-s[0][j]])
    for i in range(1, n-1):
        clauses.append([-x[i], s[i][0]])
        clauses.append([-s[i-1][0], s[i][0]])
        for j in range(1, k):
            clauses.append([-x[i], -s[i-1][j-1], s[i][j]])
            clauses.append([-s[i-1][j], s[i][j]])
        clauses.append([-x[i], -s[i-1][k-1]])
    clauses.append([-x[-1], -s[-1][k-1]])
    return clauses


def group_size_fixed_sequential_encoding(sgp_pb: SGP):
    # group size is defined
    for w in range(sgp_pb.weeks):
        for g in range(sgp_pb.groups):
            for c in at_most_k(sgp_pb, sgp_pb.size, sgp_pb.var_encoding[w][g]):
                sgp_pb.add_clause(c)


def first_week(sgp_pb: SGP):
    for g in range(sgp_pb.groups):
        for i in range(sgp_pb.size*g, sgp_pb.size*(g+1)):
            clause = [sgp_pb.var_encoding[0][g][i]]
            sgp_pb.add_clause(clause)


def second_week(sgp_pb: SGP):
    for w in range(1, sgp_pb.weeks):
        for i in range(sgp_pb.size):
            sgp_pb.add_clause([sgp_pb.var_encoding[w][i % sgp_pb.groups][i]])


def order_groups(sgp_pb: SGP):
    group_minimums = []
    # min variables declarations
    for w in range(sgp_pb.weeks):
        group_minimums.append([])
        for g in range(sgp_pb.groups):
            group_minimums[w].append([])
            for i in range(sgp_pb.n_golfers):
                group_minimums[w][g].append(sgp_pb.idx_next_var)
                sgp_pb.idx_next_var += 1

    # min[w,g,i] => x[w,g,i]
    for w in range(sgp_pb.weeks):
        for g in range(sgp_pb.groups):
            for i in range(sgp_pb.n_golfers):
                sgp_pb.add_clause(
                    [-group_minimums[w][g][i], sgp_pb.var_encoding[w][g][i]])
    # at least 1 and at most 1
    for w in range(sgp_pb.weeks):
        for g in range(sgp_pb.groups):
            sgp_pb.add_clause(group_minimums[w][g])
            for i1 in range(sgp_pb.n_golfers):
                for i2 in range(i1+1, sgp_pb.n_golfers):
                    sgp_pb.add_clause(
                        [-group_minimums[w][g][i1], -group_minimums[w][g][i2]])

    # min[w,g,i] => !x[w,g,i'] for all i' < i
    for w in range(sgp_pb.weeks):
        for g in range(sgp_pb.groups):
            for i1 in range(sgp_pb.n_golfers):
                for i2 in range(i1):
                    sgp_pb.add_clause(
                        [-group_minimums[w][g][i1], -sgp_pb.var_encoding[w][g][i2]])

    # min[w,g1,i1] => !min[w,g2,i2] for all i1 < i2 for all g2 < g1
    for w in range(sgp_pb.weeks):
        for g1 in range(sgp_pb.groups):
            for g2 in range(g1):
                for i1 in range(sgp_pb.n_golfers):
                    for i2 in range(i1+1, sgp_pb.n_golfers):
                        sgp_pb.add_clause(
                            [-group_minimums[w][g1][i1], -group_minimums[w][g2][i2]])


def order_weeks(sgp_pb: SGP):
    week_max = []
    # miax variables declarations
    for w in range(sgp_pb.weeks):
        week_max.append([])
        for i in range(sgp_pb.n_golfers):
            week_max[w].append(sgp_pb.idx_next_var)
            sgp_pb.idx_next_var += 1

    # max[w,i] => x[w,0,i]
    for w in range(sgp_pb.weeks):
        for i in range(sgp_pb.n_golfers):
            sgp_pb.add_clause(
                [-week_max[w][i], sgp_pb.var_encoding[w][0][i]])
    # at least 1 and at most 1
    for w in range(sgp_pb.weeks):
        sgp_pb.add_clause(week_max[w])
        for i1 in range(sgp_pb.n_golfers):
            for i2 in range(i1+1, sgp_pb.n_golfers):
                sgp_pb.add_clause(
                    [-week_max[w][i1], -week_max[w][i2]])

    # max[w,i] => !x[w,0,i'] for all i' > i
    for w in range(sgp_pb.weeks):
        for i1 in range(sgp_pb.n_golfers):
            for i2 in range(i1+1, sgp_pb.n_golfers):
                sgp_pb.add_clause(
                    [-week_max[w][i1], -sgp_pb.var_encoding[w][0][i2]])

    # max[w1,i1] => !max[w2,i2] for all i2 < i1 for all w2 > w1
    for w1 in range(sgp_pb.weeks):
        for w2 in range(w1+1, sgp_pb.weeks):
            for i1 in range(sgp_pb.n_golfers):
                for i2 in range(i1):
                    sgp_pb.add_clause(
                        [-week_max[w1][i1], -week_max[w2][i2]])


def latch(sgp_pb: SGP, array_idx):
    # defining the latch
    latch_lst = []
    n = len(array_idx)
    for i in range(n):
        latch_lst.append(sgp_pb.idx_next_var)
        sgp_pb.idx_next_var += 1
    sgp_pb.add_clause([latch_lst[0], -array_idx[0]])
    sgp_pb.add_clause([-latch_lst[0], array_idx[0]])
    for i in range(1, n):
        sgp_pb.add_clause([latch_lst[i], -latch_lst[i-1]])
        sgp_pb.add_clause([latch_lst[i], -array_idx[i]])
        sgp_pb.add_clause([-latch_lst[i], array_idx[i], latch_lst[i-1]])
    return latch_lst


def min_latch(sgp_pb: SGP, array_idx):
    clauses = []
    n = len(array_idx)

    # defining the latch
    latch = []
    for i in range(n):
        latch.append(sgp_pb.idx_next_var)
        sgp_pb.idx_next_var += 1
    clauses.append([latch[0], -array_idx[0]])
    clauses.append([-latch[0], array_idx[0]])
    for i in range(1, n):
        clauses.append([latch[i], -latch[i-1]])
        clauses.append([latch[i], -array_idx[i]])
        clauses.append([-latch[i], -array_idx[i], -latch[i-1]])

    # defining the minimum
    min_var = []
    for i in range(n):
        min_var.append(sgp_pb.idx_next_var)
        sgp_pb.idx_next_var += 1
    clauses.append([latch[0], -min_var[0]])
    clauses.append([-latch[0], min_var[0]])
    for i in range(1, n):
        clauses.append([min_var[i], -latch[i-1]])
        clauses.append([-min_var[i], latch[i]])
        clauses.append([latch[i-1], -latch[i], min_var[i]])
    return min_var


def order_group_latch(sgp_pb: SGP):
    latch_group_list = []
    for w in range(sgp_pb.weeks):
        latch_group_list.append([])
        for g in range(sgp_pb.groups):
            latch_group_list[w].append(
                latch(sgp_pb, sgp_pb.var_encoding[w][g]))

    for w in range(sgp_pb.weeks):
        for g in range(1, sgp_pb.groups):
            for i in range(len(latch_group_list[w][g])):
                sgp_pb.add_clause(
                    [latch_group_list[w][g-1][i], -latch_group_list[w][g][i]])
    return latch_group_list


def order_week_latch(sgp_pb: SGP):
    latch_week_list = []
    for w in range(sgp_pb.weeks):
        latch_week_list.append(
            latch(sgp_pb, sgp_pb.var_encoding[w][0][::-1]))

    for w in range(1, sgp_pb.weeks):
        for i in range(len(latch_week_list[w])):
            sgp_pb.add_clause(
                [-latch_week_list[w-1][i], latch_week_list[w][i]])
    return latch_week_list


def solver(groups, size, weeks, f=sys.stdout):
    pb = SGP(groups, size, weeks)
    start_model = time()
    # symmetry breaking
    first_week(pb)
    second_week(pb)
    order_group_latch(pb)
    order_week_latch(pb)
    # order_groups(pb)
    # order_weeks(pb)

    # sgp base model
    golfer_one_group_per_week(pb)

    golfers_arent_social(pb)
    # golfers_arent_social_1(pb)
    # golfers_arent_social_2(pb)

    # group_size_fixed_binomial_encoding(pb)
    group_size_fixed_sequential_encoding(pb)

    end_model = time()
    print("\n{}-{}-{}\nvariables : {} clauses : {}".format(groups, size,
          weeks, pb.idx_next_var-1, len(pb.cnf.clauses)), file=f)
    print(
        "model : {:.2f}s".format(end_model-start_model), end=" ", file=f)
    start = time()
    pb.solve()
    end = time()
    print("solve : {:.2f}s".format(end-start), file=f)
    pb.print_solution(f)


def benchmark(name, g, s, weeks):
    with open("./sat/{}_{}-{}.txt".format(name, g, s), "x") as f:
        for w in weeks:
            solver(g, s, w, f)
            f.flush()


def bench_core(name, g, s, weeks):
    th = multiprocessing.Process(
        target=lambda: benchmark(name, g, s, weeks))
    th.start()
    return th


if __name__ == "__main__":

    if len(sys.argv) == 4:
        solver(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    elif len(sys.argv) == 3 and sys.argv[1] == "bench":
        name = sys.argv[2]
        th = bench_core(name, 5, 3, range(1, 12))
        th1 = bench_core(name, 5, 4, range(1, 10))
        th2 = bench_core(name, 8, 4, range(1, 10))
        sleep(3600)
        th.terminate()
        th1.terminate()
        th2.terminate()
