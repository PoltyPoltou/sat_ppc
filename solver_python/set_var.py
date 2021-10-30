from memento import Card_memento, LB_memento, Memento, UB_memento


class Set_var:
    '''
    Set Variable for the ppc solver \n
    lower bound, upper bound for the set (lb,ub) and for the cardinality card_bounds \n
    name : name of the variable \n
    priority : solver will enumerate on higher priority variables first
    '''

    def __init__(self, lb: list[int], ub: list[int], card_bounds: tuple[int, int], name="", priority=0) -> None:
        self.lb: set[int] = set(lb)
        self.ub: set[int] = set(ub)
        self.card_bounds = card_bounds
        self.name = name
        self.priority = priority

    def check_bounds(self):
        '''
        checks the cardinality bounds coherance with lb and ub
        '''
        return self.card_bounds[0] <= self.card_bounds[1] and len(self.ub) >= self.card_bounds[0] and len(self.lb) <= self.card_bounds[1]

    def check_sets(self):
        '''
        checks lb \u2282 ub
        '''
        return self.lb.issubset(self.ub)

    def add_to_lb(self, elmt: int) -> bool:
        '''
        add elmt to lb \n
        returns true iff var is still feasible
        '''
        self.lb.add(elmt)
        return elmt in self.ub and self.check_bounds()

    def remove_from_ub(self, elmt: int) -> bool:
        '''
        remove elmt to ub \n
        returns true iff var is still feasible
        '''
        if elmt in self.ub:
            self.ub.remove(elmt)
        return elmt not in self.lb and self.check_bounds()

    def remove_from_lb(self, elmt: int):
        '''
        remove elmt to lb \n
        nothing is checked ! (used to revert changes on this var)
        '''
        if elmt in self.lb:
            self.lb.remove(elmt)

    def add_to_ub(self, elmt: int):
        '''
        add elmt to ub \n
        nothing is checked ! (used to revert changes on this var)
        '''
        self.ub.add(elmt)

    def change_card_tuple(self, new_card: tuple[int, int]) -> bool:
        '''
        gives new bounds for the cardinality\n
        the var will keep the better bounds out of card_bounds and new_card\n
        return True iff the var is still feasible
        '''
        self.card_bounds = (
            max(new_card[0], self.card_bounds[0]),
            min(new_card[1], self.card_bounds[1]))
        return self.check_bounds()

    def change_card(self, lower=None, upper=None) -> bool:
        '''
        gives new bounds for the cardinality\n
        the var will keep the better bounds out of card_bounds and new_card\n
        return True iff the var is still feasible
        '''
        self.card_bounds = (
            max(lower, self.card_bounds[0]
                ) if lower != None else self.card_bounds[0],
            min(upper, self.card_bounds[1]
                ) if upper != None else self.card_bounds[1])
        return self.check_bounds()

    def set_card(self, new_card):
        '''
        Change card_bounds without any restriction
        '''
        self.card_bounds = new_card

    def filter_on_card(self) -> list[Memento]:
        '''
        filter over the variable alone\n
        three cases are covered :\n
            -lb is the solution\n
            -ub is the solution\n
            -we can have better cardinality bounds\n
        return the Memento list of modifications to do
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
        '''
        return True iff the variable is fully set
        '''
        return len(self.lb) == len(self.ub) and self.feasible()

    def feasible(self):
        '''
        return True iff the variable is valid
        '''
        return self.check_sets() and self.check_bounds()
