import matplotlib.pyplot as plt
import json
import ast

N = [12, 24, 36]

fig, ax = plt.subplots(1, len(N), figsize=(15, 5), sharex=True, sharey=True)
fig.suptitle("Files lost per strategy", fontsize=16)

for i, n in enumerate(N):
    with open(f'tests/out/results_nodes_{n}.json') as f:
        data = json.load(f)
        ax[i].set_title(f"N = {n}")
        for strategy, res in data.items():
            x = [list(d.keys())[0] for d in res]
            y = [list(d.values())[0] for d in res]
            ax[i].plot(x, y, label=ast.literal_eval(strategy)[0], marker='o')
            ax[i].set_xlabel('S (Nodes Killed)', fontsize=9)
            ax[i].set_ylabel('Files lost', fontsize=9)
            ax[i].legend(loc='upper left', fontsize=9)
            ax[i].grid()
            print(strategy, x, y)

plt.show()

# for n in N:
#     with open(f'tests/out/results_nodes_{n}.json') as f:
#         data = json.load(f)

#         for strategy, res in data.items():
#             x = [list(d.keys())[0] for d in res]
#             y = [list(d.values())[0] for d in res]
#             plt.plot(x, y, label=strategy, marker='o')
#             plt.xlabel('S')
#             plt.ylabel('Files lost')
#             plt.title('Files lost per strategy')
#             plt.legend()
#             plt.grid()
#             print(strategy, x, y)
#         plt.show()