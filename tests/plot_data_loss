import matplotlib.pyplot as plt
import json

N = [12, 24, 36]

for n in N:
    with open(f'tests/out/results_nodes_{n}.json') as f:
        data = json.load(f)

        for strategy, res in data.items():
            x = [list(d.keys())[0] for d in res]
            y = [list(d.values())[0] for d in res]
            plt.plot(x, y, label=strategy)
            plt.xlabel('S')
            plt.ylabel('Files lost')
            plt.title('Files lost per strategy')
            plt.legend()
            print(strategy, x, y)
        plt.show()