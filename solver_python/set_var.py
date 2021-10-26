from memento import Card_memento, LB_memento, Memento, UB_memento


class Set_var:

    def __init__(self, lb: list[int], ub: list[int], card_bounds: tuple[int, int], name="") -> None:
        self.lb: set[int] = set(lb)
        self.ub: set[int] = set(ub)
        self.card_bounds = card_bounds
        self.name = name

    def check_bounds(self):
        return self.card_bounds[0] <= self.card_bounds[1] and len(self.ub) >= self.card_bounds[0] and len(self.lb) <= self.card_bounds[1]

    def check_sets(self):
        return self.lb.issubset(self.ub)

    def add_to_lb(self, elmt: int) -> bool:
        self.lb.add(elmt)
        return elmt in self.ub and self.check_bounds()

    def remove_from_ub(self, elmt: int) -> bool:
        if elmt in self.ub:
            self.ub.remove(elmt)
        return elmt not in self.lb and self.check_bounds()

    def remove_from_lb(self, elmt: int):
        if elmt in self.lb:
            self.lb.remove(elmt)

    def add_to_ub(self, elmt: int):
        self.ub.add(elmt)

    def change_card_tuple(self, new_card: tuple[int, int]) -> bool:
        return self.change_card(new_card[0], new_card[1])

    def change_card(self, lower=None, upper=None) -> bool:
        self.card_bounds = (
            max(lower, self.card_bounds[0]
                ) if lower != None else self.card_bounds[0],
            min(upper, self.card_bounds[1]
                ) if upper != None else self.card_bounds[1])
        return self.check_bounds()

    def set_card(self, new_card):
        self.card_bounds = new_card

    def filter_on_card(self) -> list[Memento]:
        '''
            list of modifications to do
        '''
        if self.card_bounds[0] == len(self.ub):
            modifs = [Card_memento(
                self, (self.card_bounds[0], self.card_bounds[0]))]
            if len(self.lb) != len(self.ub):
                modifs.append(LB_memento(self, self.ub - self.lb))
            return modifs
        if self.card_bounds[1] == len(self.lb):
            modifs = [Card_memento(
                self, (self.card_bounds[1], self.card_bounds[1]))]
            if len(self.lb) != len(self.ub):
                modifs.append(UB_memento(self, self.ub - self.lb))
            return modifs
        if self.card_bounds[1] > len(self.ub) or self.card_bounds[0] < len(self.lb):
            return [Card_memento(self, (max(self.card_bounds[0], len(self.lb)), min(self.card_bounds[1], len(self.ub))))]
        return []

    def defined(self):
        return len(self.lb) == len(self.ub) and self.feasable()

    def feasable(self):
        return self.check_sets() and self.check_bounds()
