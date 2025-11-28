cnf(id, axiom, mul(one,A) = A).
cnf(assoc, axiom, mul(mul(A,B),C)=mul(A,mul(B,C))).
cnf(inv, axiom, mul(inv(A),A)=one).

% cnf(goal, axiom, inv(inv(a)) = goal).
% cnf(false,conjecture, num0=num1).
% finds a -> goal as Equation 14


cnf(inv, conjecture, inv(inv(a)) = a).
