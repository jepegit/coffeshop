import matplotlib.pyplot as plt
import numpy as np

#%% Simple plotting example

# Create some data to plot
x = np.linspace(-10, 10, 50)
y = x**2

# Plot the data
plt.figure()
plt.plot(x, y, 'r')  # The last letter determines the colour
plt.xlabel('x')
plt.ylabel(r'x$^2$')  # Can write latex formula by using $
plt.title(r'Plot of x$^2$')
plt.show()

#%% Plotting voltage vs time with cellpy

