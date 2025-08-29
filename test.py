import numpy as np


# trials - список из 1 млн. целых чисел от 0 до 999
# генерируется отдельно в тестовом файле
def monte_carlo(trials):
    # словарь, содержащий выигрышные комбинации и сумму выигрыша
    # случаи с * следует обработать в цикле с помощью
    # операции взятия остатка от деления (%)
    score = {
        999: 100,
        777: 200,
        555: 50,
        333: 15,
        111: 10
    }
    # сумма выигрыша
    balance = 0

    for i in trials:
        balance -= 1

    res = ...
    return res


if __name__ == '__main__':
    np.random.seed(42)
    trials = np.random.randint(0, 1000, 10000000)
    print(monte_carlo(trials))