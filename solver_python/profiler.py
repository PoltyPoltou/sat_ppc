import pstats
import cProfile
from main import solve
#cProfile.run(statement='solve(None,5,3,3)', filename="stats.txt")
f = open("output.txt", mode="w")
a: pstats.Stats = pstats.Stats("stats.txt", stream=f)
a.sort_stats(pstats.SortKey.CUMULATIVE)
a.reverse_order()
a.print_stats()
a.print_callees()
f.close()
