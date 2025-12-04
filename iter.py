#!/usr/bin/env python3

import sys
import subprocess
import argparse
import itertools

parser = argparse.ArgumentParser(
    description="Simplify terms using Twee",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

parser.add_argument("rule_file", help="The .p file containing the rewrite rules.")

term_group = parser.add_mutually_exclusive_group(required=True)
term_group.add_argument("-T", "--term", help="The term string to simplify.")
term_group.add_argument("-F", "--term-file", help="A file containing the term string to simplify.")

parser.add_argument( "-t", "--timeout", type=int, default=1, help="Timeout for the Twee prover in seconds.")

args = parser.parse_args()

class Formula:
    def __init__(self, id, args):
        self.id = id
        self.args = args
        self.is_var = False
        self.value = None
        if len(args) == 0:
            if id.lower().startswith("numneg") or id.lower().startswith("negnum"):
                self.value = -int(id[6:])
            elif id.lower().startswith("num"):
                self.value = int(id[3:])
            elif id == id.upper():
                self.is_var = True
        
    def __repr__(self):
        if len(self.args) == 0:
            return self.id
        else:
            return f"{self.id}({','.join(map(str, self.args))})"
        
    def __eq__(self, other):
        if not isinstance(other, Formula):
            return False
        return self.id == other.id and self.args == other.args
    
    def __hash__(self):
        return hash((self.id, tuple(self.args)))
    
    def size(self):
        if len(self.args) == 0:
            return 1
        else:
            return 1 + sum(arg.size() for arg in self.args)
        
    def __lt__(self, other):
        return str(self) < str(other)

def parse_formula(s):
    s = s.replace(" ","")
    word = ""
    while s!="" and s[0] not in ['(',')',',']:
        word += s[0]
        s = s[1:]
    if s == "":
        return Formula(word, []), s
    if s[0] == '(':
        s = s[1:]
        args = []
        while True:
            if s[0] == ')':
                s = s[1:]
                break
            else:
                arg, s = parse_formula(s)
                args.append(arg)
                if s[0] == ',':
                    s = s[1:]
        return Formula(word, args), s
    else:
        return Formula(word, []), s
    
def parse_formula_assert(s):
    term, rest = parse_formula(s)
    assert rest == "", "parsing error in '"+s+"', got rest: "+rest
    return term

def replace(term, subst):
    def replace_rec(t):
        if t.is_var and t.id in subst:
            return subst[t.id]
        else:
            new_args = []
            for i in range(len(t.args)):
                new_args.append(replace_rec(t.args[i]))
            return Formula(t.id, new_args)
    return replace_rec(term)



rule_file = args.rule_file
timeout = args.timeout


def execute_twee(twee_file:str, timeout = None, allow_gaveup = False):
    # if DEBUG env variable is set, print data to file twee_input.p
    import os
    if os.getenv("DEBUG"):
        with open("twee_input.p", "w") as f:
            for line in twee_file:
                f.write(line + "\n")
        print("Wrote Twee input to twee_input.p")
        
    if timeout is None:
        proc = subprocess.Popen(["./twee.sh", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        proc = subprocess.Popen(["./twee.sh", str(timeout), "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate(input="\n".join(twee_file).encode())
    output = out.decode() + err.decode()
    if os.getenv("DEBUG"):
        with open("twee_output.txt", "w") as f:
            f.write(output)
        print("Wrote Twee output to twee_output.txt")
        
    final_string = "Here is the final rewrite system:"
    end_string = "RESULT: CounterSatisfiable"
    end_string2 = "RESULT: GaveUp"
    assert final_string in output, "Twee did not finish properly\n"+ output
    if not allow_gaveup:
        assert end_string in output, "Twee did not finish properly\n"+ output
    output = output.split(final_string)[1]
    if end_string in output:
        output = output.split(end_string)[0]
    elif end_string2 in output:
        output = output.split(end_string2)[0]
    else:
        raise Exception("Twee did not finish properly\n"+ output)
    output = output.strip()
    return output
    
def rules_of_twee_output(output:str):
    rules = []
    for line in output.splitlines():
        line = line.strip()
        if line == "":
            continue
        if "->" not in line:
            print("Unhandled line:", line)
            continue
        lhs_str, rhs_str = line.split("->")
        lhs_str = lhs_str.strip()
        rhs_str = rhs_str.strip()
        lhs = parse_formula_assert(lhs_str)
        rhs = parse_formula_assert(rhs_str)
        rules.append((lhs, rhs))
    return rules
    


term_string = ""
if args.term:
    term_string = args.term
else: 
    try:
        with open(args.term_file, 'r') as f:
            term_string = f.read().strip()
    except FileNotFoundError:
        print(f"Error: Term file not found: {args.term_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading term file: {e}", file=sys.stderr)
        sys.exit(1)

if not term_string:
    print("Error: No term provided or term file was empty.", file=sys.stderr)
    sys.exit(1)

term = parse_formula_assert(term_string)

rules = []
with open(rule_file, "r") as f:
    for line in f.readlines():
        line = line.strip()
        if line == "" or line.startswith("%"):
            continue
        line = line.replace("cnf(", "")
        line = line.replace(").", "")
        parts = line.split(",")
        name = parts[0].strip()
        role = parts[1].strip()
        assert role == "axiom", "only axioms (rules) are supported, found: "+role
        formula_str = ",".join(parts[2:]).strip()
        lhs, rhs = formula_str.split("=")
        lhs = lhs.strip()
        rhs = rhs.strip()
        lform = parse_formula_assert(lhs)
        rform = parse_formula_assert(rhs)
        rules.append((name,(lform,rform)))
    

def collect_subterms(t):
    subterms = []
    for arg in t.args:
        subterms.extend(collect_subterms(arg))
    subterms.append(t)
    return subterms
def collect_vars(t):
    vars = set()
    if t.is_var:
        vars.add(t.id)
    for arg in t.args:
        vars.update(collect_vars(arg))
    return vars

subterms = set(collect_subterms(term))
subterms = list(sorted(subterms, key=lambda x: (x.size(), str(x))))
for st in subterms:
    assert not st.is_var

print("Initial term:", term)
print("Rules:")
for r in rules:
    print(" ", r)
print("Subterms:")
for st in subterms:
    print(" ", st)

def instantiations(vars:list[str],ground_terms:list):
    """Ground_terms ^ len(vars)"""
    if len(vars) == 0:
        yield dict()
    else:
        v = vars[0]
        for t in ground_terms:
            for subinst in instantiations(vars[1:], ground_terms):
                inst = dict(subinst)
                inst[v] = t
                yield inst
                
                
signature = {}
def collect_signature(term, signature=signature):
    if term.is_var:
        return
    arity = len(term.args)
    signature.setdefault(arity, set()).add(term.id)
    for arg in term.args:
        collect_signature(arg, signature)
        
for r in rules:
    name, (lhs, rhs) = r
    collect_signature(lhs)
    collect_signature(rhs)
collect_signature(term)

def partitions(n, k):
    """Generate all partitions of n into k positive integers."""
    if k <= 0:
        return
    if k == 1:
        if n >= 1:
            yield (n,)
        return
    for i in range(1, n - k + 2):
        for tail in partitions(n - i, k - 1):
            yield (i,) + tail
    
def enumerate_subterms(size):
    for arity in signature:
        remaining = size - 1
        if remaining < arity:
            continue
        if arity == 0:
            if size == 1:
                for func in signature[0]:
                    yield Formula(func, [])
            continue
        for parts in partitions(remaining, arity):
            assert all(part < size for part in parts)
            assert sum(parts) == remaining
            subterm_lists = []
            for part in parts:
                subterm_lists.append(list(enumerate_subterms(part)))
            for args in itertools.product(*subterm_lists):
                for func in signature[arity]:
                    yield Formula(func, list(args))
        

# needed for inv(inv(a))
# for size in range(1,5):
#     subterms.extend(enumerate_subterms(size))

sys.stdout.flush()

computed_ground_instances = set()
grounded_rules = []
ground_terms = []
for iter,s in enumerate(subterms):
    print(f"\n=== Iteration {iter}, adding subterm: {s} ===")
    ground_terms.append(s)
    for r in rules:
        name, (lhs, rhs) = r
        vars = set(collect_vars(lhs)) | set(collect_vars(rhs))
        vars = list(sorted(vars))
        for subst in instantiations(vars, ground_terms):
            # print("Considering substitution:", subst, "for rule", name)
            glhs = replace(lhs, subst)
            grhs = replace(rhs, subst)
            if glhs not in computed_ground_instances or grhs not in computed_ground_instances:
                computed_ground_instances.add(glhs)
                computed_ground_instances.add(grhs)
                print("  Adding grounded rule:", glhs, "=", grhs)
                grounded_rules.append((name, (glhs, grhs)))
    twee_file = []
    for r in grounded_rules:
        name, (lhs, rhs) = r
        twee_file.append(f"cnf({name},axiom,{lhs}={rhs}).")
    twee_file.append(f"cnf(goal,axiom,{term}=goal).")
    twee_file.append("cnf(false,conjecture,num0=num1).")
    
    
    print(f"(Current best: {term})")
    print(f"Running Twee")
    sys.stdout.flush()
    
    output = execute_twee(twee_file, None, allow_gaveup=False)
    
    new_term = term
    new_ground_rules = []
    for lhs, rhs in rules_of_twee_output(output):
        print("  Found rewrite rule:", lhs, "->", rhs)
        if rhs.id == "goal":
            if lhs.size() < new_term.size():
                new_term = lhs
        new_ground_rules.append(("r"+str(iter),(lhs, rhs)))
    
    if new_term != term:
        print("Term simplified to:", new_term)
        term = new_term
    grounded_rules = new_ground_rules
    
    
    # break
        
print("\nFinal simplified term:", term)
    
print("Try out final pass")
sys.stdout.flush()

twee_file = []
for r in grounded_rules:
    name, (lhs, rhs) = r
    twee_file.append(f"cnf({name},axiom,{lhs}={rhs}).")
for r in rules:
    name, (lhs, rhs) = r
    twee_file.append(f"cnf({name},axiom,{lhs}={rhs}).")
twee_file.append(f"cnf(goal,axiom,{term}=goal).")
twee_file.append("cnf(false,conjecture,num0=num1).")

output = execute_twee(twee_file, timeout, allow_gaveup=True)
rules = rules_of_twee_output(output)
goal_terms = []
for lhs, rhs in rules:
    if lhs.id == "goal" and "goal" not in str(rhs):
        goal_terms.append(rhs)
    if rhs.id == "goal" and "goal" not in str(lhs):
        goal_terms.append(lhs)

print("\nFinal goal terms found:")
print(min(goal_terms, key=lambda x: (x.size(), str(x))))