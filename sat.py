from time import time
import pysat.solvers
import pysat.formula
import itertools
weeks = 7
groups = 5
size = 3
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

solverg = pysat.solvers.Glucose4()
cnf_file = pysat.formula.CNF()

# force first week of schedule
for g in range(groups):
    for i in range(size*g, size*(g+1)):
        clause = [indices[0][g][i]]
        solverg.add_clause(clause)
        cnf_file.append(clause)


for i in range(golfers):
    for w in range(weeks):
        # at least 1
        clause = []
        for g in range(groups):
            clause.append(indices[w][g][i])
        solverg.add_clause(clause)
        cnf_file.append(clause)

        # at most 1
        for g1 in range(groups):
            for g2 in range(g1 + 1, groups):
                clause = [-indices[w][g1][i], -indices[w][g2][i]]
                solverg.add_clause(clause)
                cnf_file.append(clause)
# no pair of golfers can play together more than once
for w1 in range(weeks):
    for w2 in range(weeks):
        if(w1 != w2):
            for i1 in range(golfers):
                for i2 in range(golfers):
                    if(i1 != i2):
                        for g1 in range(groups):
                            for g2 in range(groups):
                                clause = [-indices[w1][g1][i1], -indices[w2][g2]
                                          [i1], -indices[w1][g1][i2], -indices[w2][g2][i2]]
                                solverg.add_clause(clause)
                                cnf_file.append(clause)

# group size is defined
all_combin = list(itertools.combinations(range(golfers), size+1))
for w in range(weeks):
    for g in range(groups):
        for subset in all_combin:
            clause = []
            for i in subset:
                clause.append(-indices[w][g][i])
            solverg.add_clause(clause)
            cnf_file.append(clause)

cnf_file.to_file("sat.sat")
print("start solving")
start = time()
solverg.solve()
end = time()
print("done solving", end-start, "s")
# good output
schedule = []
for w in range(weeks):
    schedule.append([])
    for g in range(groups):
        schedule[w].append([])

for var in solverg.get_model():
    idx = abs(var)
    sign = (idx / var) == 1
    idx -= 1
    golfeur = idx % golfers
    g = ((idx - golfeur) // golfers) % groups
    w = (idx - golfeur - g * golfers) // (golfers * groups)
    if(sign):
        schedule[w][g].append(golfeur)
for w in schedule:
    for g in w:
        for i in g:
            print("{0:2}".format(i), end="")
            print(" ", end="")
        print("| ", end="")
    print("")
