

class Memento:
    def __init__(self) -> None:
        raise NotImplementedError()

    def apply(self) -> None:
        raise NotImplementedError()

    def revert(self) -> None:
        raise NotImplementedError()


class LB_memento(Memento):
    def __init__(self, var, to_add: set[int]) -> None:
        self.var = var
        self.to_add = to_add
        self.applied = False

    def apply(self) -> None:
        if not self.applied:
            for elmt in self.to_add:
                self.var.add_to_lb(elmt)
            self.applied = True

    def revert(self) -> None:
        if self.applied:
            for elmt in self.to_add:
                self.var.remove_from_lb(elmt)
            self.applied = False


class UB_memento(Memento):
    def __init__(self, var, to_remove: set[int]) -> None:
        self.var = var
        self.to_remove = to_remove
        self.applied = False

    def apply(self) -> None:
        if not self.applied:
            for elmt in self.to_remove:
                self.var.remove_from_ub(elmt)
            self.applied = True

    def revert(self) -> None:
        if self.applied:
            for elmt in self.to_remove:
                self.var.add_to_ub(elmt)
            self.applied = False


class Card_memento(Memento):
    def __init__(self, var, new_card: tuple[int, int]) -> None:
        self.var = var
        self.new_card = new_card
        self.old_card = None
        self.applied = False

    def apply(self) -> None:
        if not self.applied:
            self.old_card = self.var.card_bounds
            self.var.change_card_tuple(self.new_card)
            self.applied = True

    def revert(self) -> None:
        if self.applied and self.old_card != None:
            self.var.set_card(self.old_card)
            self.old_card = None
            self.applied = False
