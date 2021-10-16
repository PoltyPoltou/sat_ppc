class a:
    def __init__(self) -> None:
        self.foo()

    def foo(self):
        print(10)


class b(a):
    def __init__(self) -> None:
        super().__init__()
        pass

    def foo(self):
        print(5)


a()
b()
