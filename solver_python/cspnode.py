from ete3 import TreeNode

from .memento import Memento


class CSPNode(TreeNode):
    def __init__(self, memento_modif=None, newick=None, format=0, dist=None, support=None, name=None, quoted_node_names=False):
        super().__init__(newick=newick, format=format, dist=dist,
                         support=support, name=name, quoted_node_names=quoted_node_names)
        self.memento_modif: Memento = memento_modif
        self.name = str(memento_modif)

    def apply_memento(self):
        if self.memento_modif != None:
            self.memento_modif.apply()

    def revert_memento(self):
        if self.memento_modif != None:
            self.memento_modif.revert()
