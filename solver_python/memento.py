

class Memento:
    def __init__(self) -> None:
        raise NotImplementedError()

    def apply(self) -> None:
        raise NotImplementedError()

    def revert(self) -> None:
        raise NotImplementedError()

    def effective(self) -> bool:
        raise NotImplementedError()


class LB_memento(Memento):
    def __init__(self, var, to_add: set[int], causality_var=None) -> None:
        self.var = var
        self.causality_var = causality_var
        self.to_add = to_add
        self.applied = False
        self.valid = True

    def apply(self) -> None:
        if not self.applied:
            self.var.add_causality(self.causality_var)
            for elmt in self.to_add:
                self.valid = self.valid & self.var.add_to_lb(elmt)
            self.applied = True

    def revert(self) -> None:
        if self.applied:
            self.var.remove_causality(self.causality_var)
            for elmt in self.to_add:
                self.var.remove_from_lb(elmt)
            self.applied = False

    def effective(self) -> bool:
        return len(self.to_add) > 0

    def __str__(self) -> str:
        if self.var.name != "":
            return str(self.to_add) + " \u2208 " + self.var.name
        else:
            return str(self.to_add) + " \u2208 " + str(self.var)


class UB_memento(Memento):
    def __init__(self, var, to_remove: set[int], causality_var=None) -> None:
        self.var = var
        self.causality_var = causality_var
        self.to_remove = to_remove
        self.applied = False
        self.valid = True

    def apply(self) -> None:
        if not self.applied:
            self.var.add_causality(self.causality_var)
            for elmt in self.to_remove:
                self.valid = self.valid & self.var.remove_from_ub(elmt)
            self.applied = True

    def revert(self) -> None:
        if self.applied:
            self.var.remove_causality(self.causality_var)
            for elmt in self.to_remove:
                self.var.add_to_ub(elmt)
            self.applied = False

    def effective(self) -> bool:
        return len(self.to_remove) > 0

    def __str__(self) -> str:
        if self.var.name != "":
            return str(self.to_remove) + " \u2209 " + self.var.name
        else:
            return str(self.to_remove) + " \u2209 " + str(self.var)


class Card_memento(Memento):
    def __init__(self, var, new_card: tuple[int, int], causality_var=None) -> None:
        self.var = var
        self.causality_var = causality_var
        self.new_card = new_card
        self.old_card = None
        self.applied_card = None
        self.applied = False
        self.valid = True

    def apply(self) -> None:
        if not self.applied:
            self.var.add_causality(self.causality_var)
            self.old_card = self.var.card_bounds
            self.valid = self.valid & self.var.change_card_tuple(self.new_card)
            self.applied_card = self.var.card_bounds
            self.applied = True

    def revert(self) -> None:
        if self.applied and self.old_card != None:
            self.var.remove_causality(self.causality_var)
            self.var.set_card(self.old_card)
            self.old_card = None
            self.applied = False

    def effective(self) -> bool:
        return self.new_card[0] > self.var.card_bounds[0] or self.new_card[1] < self.var.card_bounds[1]

    def __str__(self) -> str:
        if self.var.name != "":
            return str(self.old_card) + "->" + str(self.applied_card) + self.var.name
        else:
            return str(self.old_card) + "->" + str(self.applied_card) + str(self.var)
