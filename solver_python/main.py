from ete3.treeview.faces import TextFace
import model
import solver
import testing
from ete3 import Tree
testing.test_all()

a = model.Sgp(4, 3, 3)
mdl = a.first_week_model()
t = Tree()
solver.solve(mdl, sgp=a, tree=t)

for node in t.traverse():
    if not node.is_leaf():
        node.add_face(TextFace(node.name), 0)
t.render("test.png")
a.print_sol()
