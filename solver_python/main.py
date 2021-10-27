import model
import solver
import testing
testing.test_all()

a = model.Sgp(2, 2, 3)
mdl = a.get_basic_model()

solver.solve(mdl, sgp=a)

a.print_sol()
