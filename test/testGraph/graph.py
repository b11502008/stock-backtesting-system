import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def plot_graph(container_widget, selected, x_start, x_end):
    # 移除先前圖形
    for i in reversed(range(container_widget.layout().count())):
        widget_to_remove = container_widget.layout().itemAt(i).widget()
        container_widget.layout().removeWidget(widget_to_remove)
        widget_to_remove.setParent(None)

    # 畫圖
    fig = Figure(figsize=(5, 3))
    ax = fig.add_subplot(111)
    x = np.linspace(x_start, x_end, 100)
    if selected == "sin":
        y = np.sin(x)
    elif selected == "cos":
        y = np.cos(x)
    elif selected == "linear":
        y = x
    ax.plot(x, y)
    ax.set_title("Line Chart")

    canvas = FigureCanvas(fig)
    container_widget.layout().addWidget(canvas)
