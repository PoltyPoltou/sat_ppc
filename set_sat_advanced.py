from set_sat import Set_Sat
from set_sat_interface import reverse_map


class Set_Sat_Adv(Set_Sat):
    def __init__(self):
        super().__init__()
        self.treillis = []  #  upper_bound - lower_bound

    def model_to_set_solution(self, model):
        if len(model) == 0 and len(self.cnf.clauses) != 0:
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

    def solve(self):
        self.solver.append_formula(self.cnf)
        if self.solver.solve():
            return self.solver.get_model()
        else:
            return []

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

    def latch_set(self, i, reverse: bool = False):
        '''
         defines a latch q_n function of variables x_n of set i,
         the indexes are given via array_idx\n
         example : \n
         x_n = 0 0 0 1 0 1 0 \n
         q_n = 0 0 0 1 1 1 1 \n
         with set it is lacunar
        '''
        latch_map = {}
        if len(self.set_sat_idx[i]) != 0:
            array_idx = reverse_map(
                self.set_sat_idx[i])if reverse else self.set_sat_idx[i]
            elmt_lb = None  # element of lower bound that must be taken in account in the latch
            if len(self.lbounds[i]) != 0:
                if reverse:
                    elmt_lb = max(self.lbounds[i])
                    array_idx[max(self.set_sat_idx[i].keys()) - elmt_lb] = 0
                else:
                    elmt_lb = min(self.lbounds[i])
                    array_idx[elmt_lb] = 0
            n = len(array_idx)
            if n != 0:
                key_list_ordered = list(sorted(array_idx.keys()))
                for key in key_list_ordered:
                    latch_map[key] = self.next_var()

                if elmt_lb != None:
                    self.add_clause([latch_map[key_list_ordered[0]]])
                else:
                    self.add_clause([-latch_map[key_list_ordered[0]]] +
                                    list(latch_map.values()))
                    self.add_clause(
                        [-array_idx[key_list_ordered[0]], latch_map[key_list_ordered[0]]])
                for i in range(1, n):
                    if elmt_lb == None:
                        self.add_clause(
                            [-array_idx[key_list_ordered[i]], latch_map[key_list_ordered[0]]])

                    if array_idx[key_list_ordered[i-1]] == 0:
                        self.add_clause([-latch_map[key_list_ordered[i]],
                                        latch_map[key_list_ordered[i-1]]])
                        self.add_clause([-latch_map[key_list_ordered[i]]])
                    else:
                        self.add_clause([-latch_map[key_list_ordered[i]],
                                        latch_map[key_list_ordered[i-1]]])
                        self.add_clause([-latch_map[key_list_ordered[i]],
                                        -array_idx[key_list_ordered[i-1]]])
                        self.add_clause([latch_map[key_list_ordered[i]],
                                        array_idx[key_list_ordered[i-1]],
                                        -latch_map[key_list_ordered[i-1]]])
        return latch_map
