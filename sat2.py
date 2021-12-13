from time import time
import pysat.solvers
import pysat.formula
import itertools

weeks = 8
groups = 8
size = 4
golfers = groups * size
indices = []
acc = 1
for w in range(weeks):
    indices.append([])
    for g in range(groups):
        indices[w].append([])
        for i in range(golfers):
            indices[w][g].append(acc)
            acc += 1
idx_max = acc
solverg = pysat.solvers.Glucose4()
cnf_file = pysat.formula.CNF()

# force first week of schedule
for g in range(groups):
    for i in range(size * g, size * (g + 1)):
        clause = [indices[0][g][i]]
        solverg.add_clause(clause)
        cnf_file.append(clause)


for i in range(golfers):
    for w in range(weeks):
        # at least 1
        clause = []
        for g in range(groups):
            clause.append(indices[w][g][i])
        solverg.add_clause(clause)
        cnf_file.append(clause)

        # at most 1
        for g1 in range(groups):
            for g2 in range(g1 + 1, groups):
                clause = [-indices[w][g1][i], -indices[w][g2][i]]
                solverg.add_clause(clause)
                cnf_file.append(clause)

# no pair of golfers can play together more than once
for w1 in range(weeks):
    for w2 in range(weeks):
        if w1 != w2:
            for i1 in range(golfers):
                for i2 in range(golfers):
                    if i1 != i2:
                        for g1 in range(groups):
                            for g2 in range(groups):
                                clause = [
                                    -indices[w1][g1][i1],
                                    -indices[w2][g2][i1],
                                    -indices[w1][g1][i2],
                                    -indices[w2][g2][i2],
                                ]
                                solverg.add_clause(clause)
                                cnf_file.append(clause)


def at_most_k(k, x):
    # http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.83.9527&rep=rep1&type=pdf
    global acc
    n = len(x)
    s = []
    for i in range(n - 1):
        s.append([])
        for j in range(k):
            s[i].append(acc)
            acc += 1

    clauses = [[-x[0], s[0][0]]]
    for j in range(1, k):
        clauses.append([-s[0][j]])
    for i in range(1, n - 1):
        clauses.append([-x[i], s[i][0]])
        clauses.append([-s[i - 1][0], s[i][0]])
        for j in range(1, k):
            clauses.append([-x[i], -s[i - 1][j - 1], s[i][j]])
            clauses.append([-s[i - 1][j], s[i][j]])
        clauses.append([-x[i], -s[i - 1][k - 1]])
    clauses.append([-x[-1], -s[-1][k - 1]])
    return clauses


# group size is defined
for w in range(weeks):
    for g in range(groups):
        clauses_to_add = at_most_k(size, indices[w][g])
        for c in clauses_to_add:
            solverg.add_clause(c)
            cnf_file.append(c)

cnf_file.to_file("sat.sat")
print("start solving")
start = time()
solverg.solve()
end = time()
print("done solving", end - start, "s")
# good output
schedule = []
for w in range(weeks):
    schedule.append([])
    for g in range(groups):
        schedule[w].append([])

for var in solverg.get_model():
    idx = abs(var)
    if idx == idx_max:
        break
    sign = (idx / var) == 1
    idx -= 1
    golfeur = idx % golfers
    g = ((idx - golfeur) // golfers) % groups
    w = (idx - golfeur - g * golfers) // (golfers * groups)
    if sign:
        schedule[w][g].append(golfeur)

for w in schedule:
    for g in w:
        for i in g:
            print("{0:2}".format(i), end="")
            print(" ", end="")
        print("| ", end="")
    print("")
