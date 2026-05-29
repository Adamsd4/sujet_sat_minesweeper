from itertools import product
from collections import defaultdict
import random

from cnf import Assignment, Clause, evaluate_cnf


def find_unit_clause(clauses: list[Clause]):
    for clause in clauses:
        if len(clause) == 1:
            return clause[0]
    return None


def find_pure_literal(clauses: list[Clause], variable_count: int):
    literals = {lit for clause in clauses for lit in clause}
    for lit in literals:
        if -lit not in literals:
            return lit
    return None


def choose_literal_naive(clauses):
    return clauses[0][0]


def choose_literal_dlis(clauses, epsilon=0.05):
    if random.random() < epsilon:
        clause = random.choice(clauses)
        return random.choice(clause)

    score = {}
    for clause in clauses:
        for literal in clause:
            if literal in score:
                score[literal] += 1
            else:
                score[literal] = 1
    if not score:
        return clauses[0][0]
    return max(score, key=score.get)


def choose_literal_JW(clauses):
    scores = {}
    for clause in clauses:
        weight = 2 ** -len(clause)
        for lit in clause:
            if lit in scores:
                scores[lit] += weight
            else:
                scores[lit] = weight
    if not scores:
        return clauses[0][0]
    return max(scores, key=scores.get)


def update_clause(clauses, literal, value):
    new_clauses = []
    for clause in clauses:
        new_clause = []
        valid_clause = True
        for lit in clause:
            if lit == literal or lit == -literal:
                if (lit > 0) == value:
                    valid_clause = False
                    break
                else:
                    continue

            new_clause.append(lit)

        if valid_clause:
            new_clauses.append(new_clause)
    return new_clauses


def DPLL(clauses: list[Clause], variable_count: int, assignment: Assignment | None) -> Assignment | None:
    """Implémentation de l'algorithme DPLL"""
    while True:
        if len(clauses) == 0:
            return assignment

        for clause in clauses:
            if len(clause) == 0:
                return None

        l1 = find_unit_clause(clauses)
        if l1:
            assignment[abs(l1)] = l1 > 0
            clauses = update_clause(clauses, abs(l1), l1 > 0)
            continue

        l2 = find_pure_literal(clauses, variable_count)
        if l2:
            assignment[abs(l2)] = l2 > 0
            clauses = update_clause(clauses, abs(l2), l2 > 0)
            continue

        new_l = choose_literal_naive(clauses)

        assignment_copy = assignment.copy()
        assignment_copy[abs(new_l)] = new_l > 0
        new_clauses = clauses.copy()
        new_clauses = update_clause(new_clauses, abs(new_l), new_l > 0)
        result = DPLL(new_clauses, variable_count, assignment_copy)
        if result:
            return result

        assignment_copy = assignment.copy()
        assignment_copy[abs(new_l)] = new_l < 0
        new_clauses = clauses.copy()
        new_clauses = update_clause(new_clauses, abs(new_l), new_l < 0)
        return DPLL(new_clauses, variable_count, assignment_copy)


def DPLL_conflict(clauses: list[Clause], variable_count: int, assignment: Assignment | None, limit=5000) -> Assignment | None:
    """S'arrête après un trop grand nombre de conflit"""
    conflicts = [0]

    def _dpll(clauses, assignment, conflict_limit):
        while True:
            if len(clauses) == 0:
                return assignment

            for clause in clauses:
                if len(clause) == 0:
                    conflicts[0] += 1
                    return None

            if conflicts[0] > conflict_limit:
                return None

            l1 = find_unit_clause(clauses)
            if l1:
                assignment[abs(l1)] = l1 > 0
                clauses = update_clause(clauses, abs(l1), l1 > 0)
                continue

            l2 = find_pure_literal(clauses, variable_count)
            if l2:
                assignment[abs(l2)] = l2 > 0
                clauses = update_clause(clauses, abs(l2), l2 > 0)
                continue

            new_l = choose_literal_dlis(clauses)

            assignment_copy = assignment.copy()
            assignment_copy[abs(new_l)] = new_l > 0
            new_clauses = clauses.copy()
            new_clauses = update_clause(new_clauses, abs(new_l), new_l > 0)
            result = _dpll(new_clauses, assignment_copy, conflict_limit)
            if result:
                return result

            if conflicts[0] > conflict_limit:
                return None

            assignment_copy = assignment.copy()
            assignment_copy[abs(new_l)] = new_l < 0
            new_clauses = clauses.copy()
            new_clauses = update_clause(new_clauses, abs(new_l), new_l < 0)
            return _dpll(new_clauses, assignment_copy, conflict_limit)

    result = _dpll(clauses.copy(), assignment.copy(), limit)
    if conflicts[0] <= limit:
        return result
    else:
        return "UNRESOLVED"


# ------------------------------------------------------------------
# Tout le code dans cette classe a été généré par Claude AI
# ------------------------------------------------------------------


class CDCLSolver:
    def __init__(self, clauses: list[list[int]], variable_count: int):
        self.variable_count = variable_count

        # Clauses (originales + apprises)
        self.clauses = [list(c) for c in clauses]

        # Assignations : variable -> valeur booléenne
        self.value: dict[int, bool] = {}

        # Niveau de décision de chaque variable
        self.level: dict[int, int] = {}

        # Antécédent de chaque variable (clause qui l'a impliquée, ou None)
        self.antecedent: dict[int, int | None] = {}  # var -> index de clause

        # Ordre des assignations (pour le backtrack)
        self.trail: list[int] = []  # liste de variables dans l'ordre d'assignation
        self.trail_lim: list[int] = []  # trail_lim[d] = index dans trail au début du niveau d

        # Niveau de décision courant
        self.decision_level = 0

        # VSIDS : score pour chaque littéral
        self.vsids_score: dict[int, float] = defaultdict(float)
        self._init_vsids()
        self.vsids_decay = 0.95
        self.vsids_bump = 1.0

        # Watched literals : clause_idx -> [lit_a, lit_b]
        # watches[lit] = liste des indices de clauses qui regardent lit
        self.watches: dict[int, list[int]] = defaultdict(list)
        self._init_watches()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_vsids(self):
        """Initialise les scores VSIDS à partir de la fréquence des littéraux."""
        for clause in self.clauses:
            for lit in clause:
                self.vsids_score[lit] += 1

    def _init_watches(self):
        """Chaque clause surveille ses deux premiers littéraux."""
        for idx, clause in enumerate(self.clauses):
            if len(clause) >= 2:
                self.watches[clause[0]].append(idx)
                self.watches[clause[1]].append(idx)
            elif len(clause) == 1:
                # Clause unitaire : sera traitée par unit propagation
                self.watches[clause[0]].append(idx)

    # ------------------------------------------------------------------
    # Assignation / désassignation
    # ------------------------------------------------------------------

    def _assign(self, var: int, value: bool, level: int, antecedent: int | None):
        if var in self.value:
            return  # déjà assignée, on ignore
        self.value[var] = value
        self.level[var] = level
        self.antecedent[var] = antecedent
        self.trail.append(var)

    def _lit_value(self, lit: int) -> bool | None:
        """Valeur d'un littéral : True/False/None si non assigné."""
        var = abs(lit)
        if var not in self.value:
            return None
        v = self.value[var]
        return v if lit > 0 else not v

    def _backtrack(self, level: int):
        """Annule toutes les assignations au-dessus de `level`."""
        while self.trail and self.level[self.trail[-1]] > level:
            var = self.trail.pop()
            del self.value[var]
            del self.level[var]
            del self.antecedent[var]
        # Restaurer trail_lim
        while self.trail_lim and self.trail_lim[-1] > len(self.trail):
            self.trail_lim.pop()
        self.decision_level = level

    # ------------------------------------------------------------------
    # Unit Propagation avec watched literals
    # ------------------------------------------------------------------

    def _propagate(self) -> int | None:
        """
        Propage toutes les clauses unitaires.
        Retourne l'index de la clause conflictuelle, ou None.
        """
        # File des littéraux à propager (ceux récemment assignés à True)
        queue_start = 0
        prop_queue = []

        # Initialiser avec les littéraux déjà vrais non encore propagés
        for var in reversed(self.trail):
            lit = var if self.value[var] else -var
            prop_queue.append(lit)
            if self.level[var] < self.decision_level:
                break  # ne re-propageons pas les anciens niveaux
        prop_queue.reverse()
        # En pratique on garde juste les nouveaux
        if self.trail_lim:
            new_start = self.trail_lim[-1]
        else:
            new_start = 0
        prop_queue = []
        for var in self.trail[new_start:]:
            lit = var if self.value[var] else -var
            prop_queue.append(lit)

        while queue_start < len(prop_queue):
            lit = prop_queue[queue_start]
            queue_start += 1
            false_lit = -lit  # ce littéral vient d'être mis à False

            # Parcourir les clauses qui surveillent false_lit
            new_watches = []
            i = 0
            clause_indices = self.watches[false_lit]
            while i < len(clause_indices):
                idx = clause_indices[i]
                clause = self.clauses[idx]

                # S'assurer que false_lit est en position 1 (convention)
                if len(clause) >= 2 and clause[0] == false_lit:
                    clause[0], clause[1] = clause[1], clause[0]

                # Si clause[0] est déjà vrai, la clause est satisfaite
                if self._lit_value(clause[0]) is True:
                    new_watches.append(idx)
                    i += 1
                    continue

                # Chercher un nouveau littéral à surveiller
                found = False
                for k in range(2, len(clause)):
                    if self._lit_value(clause[k]) is not False:
                        clause[1], clause[k] = clause[k], clause[1]
                        self.watches[clause[1]].append(idx)
                        found = True
                        break

                if found:
                    i += 1
                    continue

                # Aucun littéral libre trouvé
                new_watches.append(idx)

                if self._lit_value(clause[0]) is False:
                    # Conflit
                    self.watches[false_lit] = new_watches + clause_indices[i+1:]
                    return idx
                else:
                    # Clause unitaire : clause[0] doit être vrai
                    unit_lit = clause[0]
                    unit_var = abs(unit_lit)
                    self._assign(unit_var, unit_lit > 0, self.decision_level, idx)
                    prop_queue.append(unit_lit)

                i += 1

            self.watches[false_lit] = new_watches

        return None

    # ------------------------------------------------------------------
    # Analyse de conflit et clause learning (premier UIP)
    # ------------------------------------------------------------------

    def _conflict_analysis(self, conflict_clause_idx: int) -> tuple[list[int], int]:
        """
        Analyse le conflit et retourne (clause_apprise, niveau_backtrack).
        Implémente le premier UIP via résolution.
        """
        # Clause de travail courante
        learnt = list(self.clauses[conflict_clause_idx])

        # Compteur de littéraux au niveau de décision courant
        d = self.decision_level

        # Index dans le trail (on remonte depuis la fin)
        trail_idx = len(self.trail) - 1
        seen = set()

        while True:
            # Compter les littéraux au niveau courant dans learnt
            current_level_lits = [li for li in learnt if self.level.get(abs(li), -1) == d]

            if len(current_level_lits) == 1:
                # Premier UIP atteint
                break

            # Choisir le littéral le plus récemment assigné au niveau courant
            while abs(self.trail[trail_idx]) not in {abs(li) for li in current_level_lits}:
                trail_idx -= 1

            var = self.trail[trail_idx]
            trail_idx -= 1

            if self.antecedent[var] is None:
                break

            # Résoudre learnt avec l'antécédent de var
            ant = self.clauses[self.antecedent[var]]
            # Résolution : enlever var et -var, union du reste
            learnt_set = set(learnt)
            learnt_set.discard(var)
            learnt_set.discard(-var)
            for li in ant:
                if abs(li) != var:
                    learnt_set.add(li)
            learnt = list(learnt_set)

        # Niveau de backtrack = 2ème niveau le plus haut dans learnt
        levels = sorted(
            [self.level.get(abs(li), 0) for li in learnt],
            reverse=True
        )
        backtrack_level = levels[1] if len(levels) > 1 else 0

        return learnt, backtrack_level

    # ------------------------------------------------------------------
    # VSIDS
    # ------------------------------------------------------------------

    def _vsids_bump(self, clause: list[int]):
        """Augmente le score des littéraux d'une clause apprise."""
        for lit in clause:
            self.vsids_score[lit] += self.vsids_bump
        # Décroissance périodique
        self.vsids_bump /= self.vsids_decay

    def _pick_branching_variable(self) -> int | None:
        """Choisit le littéral non assigné avec le meilleur score VSIDS."""
        best_lit = None
        best_score = -1
        for lit, score in self.vsids_score.items():
            var = abs(lit)
            if var not in self.value and score > best_score:
                best_score = score
                best_lit = lit
        return best_lit
    

    def solve(self) -> dict[int, bool] | None:
        # Propagation initiale au niveau 0
        # Ajouter les clauses unitaires initiales
        for idx, clause in enumerate(self.clauses):
            if len(clause) == 1:
                lit = clause[0]
                var = abs(lit)
                if var not in self.value:
                    self._assign(var, lit > 0, 0, idx)

        conflict = self._propagate()
        if conflict is not None:
            return None  # UNSAT dès le départ

        while len(self.value) < self.variable_count:
            # Décision
            lit = self._pick_branching_variable()
            if lit is None:
                break

            self.decision_level += 1
            self.trail_lim.append(len(self.trail))
            var = abs(lit)
            self._assign(var, lit > 0, self.decision_level, None)

            # Propagation
            while True:
                conflict = self._propagate()
                if conflict is None:
                    break  # pas de conflit, on continue

                if self.decision_level == 0:
                    return None  # UNSAT

                # Analyse de conflit
                learnt_clause, backtrack_level = self._conflict_analysis(conflict)

                # Bumper les scores VSIDS
                self._vsids_bump(learnt_clause)

                # Ajouter la clause apprise
                self.clauses.append(learnt_clause)
                new_idx = len(self.clauses) - 1
                if len(learnt_clause) >= 2:
                    self.watches[learnt_clause[0]].append(new_idx)
                    self.watches[learnt_clause[1]].append(new_idx)
                elif len(learnt_clause) == 1:
                    self.watches[learnt_clause[0]].append(new_idx)

                # Backtrack non-chronologique
                self._backtrack(backtrack_level)
                self.decision_level = backtrack_level

                # La clause apprise est assertive : son UIP est unitaire
                unit_lit = learnt_clause[0]
                unit_var = abs(unit_lit)
                self._assign(unit_var, unit_lit > 0, self.decision_level, new_idx)

        return self.value


def solve_CDCL(clauses, variable_count):
    solver = CDCLSolver(clauses, variable_count)
    result = solver.solve()
    if result is None:
        return None
    # Compléter les variables non assignées arbitrairement
    for v in range(1, variable_count + 1):
        if v not in result:
            result[v] = True
    return result


def brute_force(clauses: list[Clause], variable_count: int):
    # Baseline: try all assignments in lexicographic order.
    for values in product([False, True], repeat=variable_count):
        assignment = {index + 1: value for index, value in enumerate(values)}
        if evaluate_cnf(clauses, assignment) is True:
            return assignment
    return None


def solve(clauses: list[Clause], variable_count: int, debug=None) -> Assignment | None:
    """Return one satisfying assignment, or None if unsatisfiable.

    Baseline: brute force. This is useful only for tiny boards and should be
    replaced by DPLL, CDCL-inspired search, or an SMT-style engine.
    """

    # return brute_force(clauses, variable_count)
    return DPLL_conflict(clauses, variable_count, {})
    # return solve_CDCL(clauses, variable_count)


def is_satisfiable_with(clauses: list[Clause], variable_count: int, assumptions: dict[int, bool], debug=None) -> bool:
    # Turn assumptions into unit clauses, then solve the restricted formula.
    assumed_clauses = [((variable if value else -variable),) for variable, value in assumptions.items()] + clauses
    # return solve(assumed_clauses, variable_count, debug) is not None
    return solve(assumed_clauses, variable_count, debug)
