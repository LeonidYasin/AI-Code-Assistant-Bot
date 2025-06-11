def calculate_fibonacci(n):
    """Вычисляет n-ное число Фибоначчи"""
    if n <= 0:
        return "Пожалуйста, введите положительное число"
    elif n == 1 or n == 2:
        return 1
    
    a, b = 1, 1
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b

def main():
    try:
        num = int(input("Введите номер числа Фибоначчи: "))
        result = calculate_fibonacci(num)
        print(f"{num}-е число Фибоначчи: {result}")
    except ValueError:
        print("Ошибка: Введите целое число")

if __name__ == "__main__":
    main()
