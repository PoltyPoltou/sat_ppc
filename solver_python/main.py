import model
import solver
import testing
testing.test_all()

a = model.Sgp(4, 3, 3)
mdl = a.first_week_model()

solver.solve(mdl, sgp=a)

a.print_sol()
