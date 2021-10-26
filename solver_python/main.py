import model
import solver
import testing
testing.test_all()

a = model.Sgp(5, 3, 2)
mdl = a.get_basic_model()

solver.solve(mdl)

a.print_sol()
