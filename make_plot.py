import matplotlib.pyplot as plt
import numpy as np

#%% Simple plotting example

# Create some data to plot
x = np.linspace(-5, 5, 50)
y1 = 2*x
y2 = x**2
y3 = 2*x**2

# Plot the data
plt.figure()
plt.plot(x, y1, 'r--', x, y2, 'b.', x, y3, 'g^')  # Plot y1 with red dashes, y2 with blue dots and y3 with green triangles
# Adding x and y labels
plt.xlabel('x')
plt.ylabel('y')  #
plt.title(r'Plot of x$^2$')  # Adding title, can write TeX equation by adding $
plt.legend(['2x', r'x$^2$', r'2x$^2$'])
plt.show()
