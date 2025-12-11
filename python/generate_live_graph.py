# generate_live_graph.py
import matplotlib.pyplot as plt
import pandas as pd
df = pd.read_json('results.json')
multi = df[df['server'] == 'multi']
plt.plot(multi['clients'], multi['throughput_rps'], 'r-o')
plt.title('Throughput Live')
plt.xlabel('Clients'); plt.ylabel('Req/s')
plt.savefig('figures/THROUGHPUT_LIVE.png', dpi=150)
plt.close()
print("Graph live généré !")
