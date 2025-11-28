cnf(id, axiom, mul(one,A) = A).
cnf(assoc, axiom, mul(mul(A,B),C)=mul(A,mul(B,C))).
cnf(inv, axiom, mul(inv(A),A)=one).