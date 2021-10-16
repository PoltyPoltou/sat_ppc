from set_sat import Set_Sat


class Set_Sat_Adv(Set_Sat):
    def __init__(self):
        super().__init__()
        self.treillis = []  #  upper_bound - lower_bound

    def model_to_set_solution(self, model):
        if len(model) == 0:
            return []  #  UNSAT
        #  reindex the model because solvers idexes begin at 0
        idx_list = [0] + model
        solution_set = [list(sorted(self.lbounds[i]))
                        for i in range(len(self.set_sat_idx))]
        for i in range(len(self.set_sat_idx)):
            for key in self.set_sat_idx[i]:
                idx = self.set_sat_idx[i][key]
                if idx < len(idx_list) and idx_list[idx] > 0:
                    # last var might not be in the model and unconstrained
                    solution_set[i].append(key)
        return solution_set

    def add_set_var(self, lb, ub):

        set_idx = len(self.set_sat_idx)
        self.lbounds.append(set(lb))
        self.ubounds.append(set(ub))
        self.treillis.append(self.ubounds[set_idx] - self.lbounds[set_idx])

        set_list_idx = {}

        for elmt in self.treillis[set_idx]:
            set_list_idx[elmt] = self.next_var()
        self.set_sat_idx.append(set_list_idx)

        if not self.lbounds[set_idx].issubset(self.ubounds[set_idx]):
            # ub and lb are not compatible, we add -x /\ x in the formula
            self.unsat_var()
        return set_idx

    def add_clever_clause(self, tuple_set_idx_list):
        '''
            add_clever_clause([(0,2,False),(1,3,True)])
            will add the clause [-self.set_sat_idx[0][2], self.set_sat_idx[1][3]]
            trying to remove trivial clauses or variables
        '''
        if tuple_set_idx_list != []:
            clause = []
            fulfillment = False
            for set_idx, val, sign in tuple_set_idx_list:
                if val in self.lbounds[set_idx]:
                    if sign:
                        fulfillment = True
                elif val in self.treillis[set_idx]:
                    if sign:
                        clause.append(self.set_sat_idx[set_idx][val])
                    else:
                        clause.append(-self.set_sat_idx[set_idx][val])
                elif val not in self.ubounds[set_idx]:
                    if not sign:
                        fulfillment = True
            if not fulfillment and clause == []:
                self.unsat_var()
            elif not fulfillment:
                self.add_clause(clause)

    def intersection(self, i, j, k, left_right=True, right_left=True):
        '''
            a constraint about intersection\n
            left_right => i intersection j ⊆ k \n
            right_left => k ⊆ i intersection j \n
            i,j,k are the indexes of the corresponding sets
        '''
        for elmt in self.ubounds[i] & self.ubounds[j]:
            if left_right:
                self.add_clever_clause([(i, elmt, False),
                                        (j, elmt, False),
                                        (k, elmt, True)])
            if right_left:
                self.add_clever_clause([(i, elmt, True),
                                        (k, elmt, False)])
                self.add_clever_clause([(j, elmt, True),
                                        (k, elmt, False)])
        return
        '''
            a constraint about intersection\n
            left_right => i intersection j ⊆ k \n
            right_left => k ⊆ i intersection j \n
            i,j,k are the indexes of the corresponding sets
        '''
        for elmt in self.lbounds[i]:
            if elmt in self.lbounds[j]:
                pass
            if elmt in self.treillis[j]:
                pass
            if elmt not in self.ubounds[j]:
                self.unsat_var()
        for elmt in self.treillis[i]:
            if elmt in self.lbounds[j]:
                pass
            if elmt in self.treillis[j]:
                if left_right:
                    self.add_clause([-self.set_sat_idx[i][elmt],
                                    -self.set_sat_idx[j][elmt],
                                    self.set_sat_idx[k][elmt]])
                if right_left:
                    self.add_clause([self.set_sat_idx[i][elmt],
                                    -self.set_sat_idx[k][elmt]])
                    self.add_clause([self.set_sat_idx[j][elmt],
                                    -self.set_sat_idx[k][elmt]])
            if elmt not in self.ubounds[j]:
                pass
        for elmt in self.treillis[i]:
            if elmt in self.treillis[j]:
                pass
            if elmt not in self.ubounds[j]:
                pass

    def intersection_empty(self, i, j):
        '''
            constraint for i intersection j = ø
            i,j are the indexes of the corresponding sets
        '''
        if self.lbounds[i] & self.lbounds[j]:
            self.unsat_var()
        for common_elmt in self.ubounds[i] & self.ubounds[j]:
            self.add_clever_clause([(i, common_elmt, False),
                                   (j, common_elmt, False)])

    def cardinal_lb(self, i, lb):
        '''
            constraint for card(i) >= lb
            i is the index of the corresponding set
        '''
        # at_most_k(n-k,-x_n) is equivalent to at_least_k(k,x_n)
        # see at_most_k paper
        negated_lst = list(map(lambda x: -x, self.set_sat_idx[i].values()))
        if lb > len(self.lbounds[i]):
            for c in self.at_most_k(len(self.set_sat_idx[i]) - lb + len(self.lbounds[i]), negated_lst):
                self.add_clause(c)

    def cardinal_ub(self, i, ub):
        '''
            constraint for card(i) <= ub
            i is the index of the corresponding set
        '''
        if ub - len(self.lbounds[i]) >= 0:
            for c in self.at_most_k(ub - len(self.lbounds[i]), list(self.set_sat_idx[i].values())):
                self.add_clause(c)

    def cardinal(self, i, c):
        '''
            constraint for card(i) = c
            i is the index of the corresponding set
        '''
        self.cardinal_lb(i, c)
        self.cardinal_ub(i, c)

    def update_lb(self, i, lb):
        raise NotImplementedError()

    def update_ub(self, i, ub):
        raise NotImplementedError()

    def union(self, i, j, k, left_right=True, right_left=True):
        raise NotImplementedError()

    def belongs(self, elmt, i):
        raise NotImplementedError()
