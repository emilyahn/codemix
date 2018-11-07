# -*- coding: utf-8 -*-
import itertools

import numpy as np
from matplotlib import pyplot as plt


randn = np.random.randn


VALUES = [
	[0.8, 0.07, 0.06, 0.07],
	[0.33, 0.35, 0.10, 0.22],
	[0.54, 0.16, 0.13, 0.17],
	[0.38, 0.19, 0.07, 0.36],
	[0.47, 0.19, 0.09, 0.25]
]

cm = np.array(VALUES)
cmap = plt.cm.Blues
size = 6
# fig, ax = subplots(figsize=(size, size))
plt.figure(figsize=(size, size))
plt.imshow(cm, interpolation='nearest', cmap=cmap)
plt.title("Normalized Strategy Matrix")
plt.colorbar()
# x_ticks = np.arange(len(classes))

x_labels = ["SP gram", "EN gram", u"SP → EN", u"EN → SP"]
y_labels = ["SP gram", " EN gram", u"SP → EN", u"EN → SP", "Random"]
plt.xticks(np.arange(len(x_labels)), x_labels, rotation=45)
plt.yticks(np.arange(len(y_labels)), y_labels)

fmt = '.2f'  # if normalize else 'd'
thresh = cm.max() / 2.
for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
	plt.text(j, i, format(cm[i, j], fmt),
			 horizontalalignment="center",
			 # verticalalignment="center",
			 color="white" if cm[i, j] > thresh else "black")

plt.tight_layout()
plt.ylabel('Agent Strategy')
plt.xlabel('User Strategy')
plt.show()
