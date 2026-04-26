from dataclasses import dataclass

@dataclass
class A:
    x: int = 1
    x: int = 2

print(A(x=3))
