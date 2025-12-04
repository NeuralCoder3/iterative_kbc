# Iterated Ground KBC



## Test terms


`DEBUG=1 python iter.py group.p -T "inv(inv(a))" -t 10 | tee log.txt`

The simplest example is the group axioms with the term `inv(inv(a))`, which should simplify to `a`.
However, instantiation with subterms (`a`, `inv(a)`, `inv(inv(a))`) is not sufficient to find this simplification. Other instantiations like `inv(inv(inv(a)))` are needed.

`DEBUG=1 python iter.py caviar.p -F test_term1.txt -t 10 | tee log.txt`
The `test_term1` uses the caviar rules (based on halide).
This term does not involve any constants to make it easier for twee.
There are simplifications possible like `minus(v0,v0) -> 0`.

`minus(v0,v0) = 0` is not a direct rule but a consequence found using multiple critical pairs.


## TODOs

- Better instantiation (not all subterms)