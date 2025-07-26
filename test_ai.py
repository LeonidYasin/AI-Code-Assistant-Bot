#!/usr/bin/env python3
"""
Простой тест AI функций
"""

def fibonacci(n):
    """Вычисляет n-ое число Фибоначчи"""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)

def main():
    print("Числа Фибоначчи:")
    for i in range(1, 11):
        print(f"F({i}) = {fibonacci(i)}")

if __name__ == "__main__":
    main()