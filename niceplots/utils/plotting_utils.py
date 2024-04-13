# Authors: Dominik Zuercher, Valeria Glauser
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text

from niceplots.utils.nice_logger import init_logger

logger = init_logger(__file__)


class WrapText(Text):
    """
    Wrapper around matplotlib Text Artist.
    Automatically wraps text to a certain width.
    :param width: Maximally allowed width of the text
    :param width_units: either 'pixels', 'inches' or 'figure'.
    If 'figure' or 'inches' then figure needs to be passed
    :param figure: Figure object
    """

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        text: str = "",
        width: float = 0,
        x_units: str = "display",
        y_units: str = "display",
        width_units: str = "display",
        figure: Figure | None = None,
        ax: Axes | None = None,
        **kwargs,
    ):
        # width needs to be given in display units
        if width_units == "display":
            self.width = width
        elif width_units == "figure":
            if not isinstance(figure, Figure):
                raise ValueError(
                    "If width_units=figure need to pass a valid Figure object."
                )
            self.width = figure_to_display(width, 0.0, figure)[0]
        elif width_units == "axis":
            if not isinstance(ax, Axes):
                raise ValueError(
                    "If width_units=axis need to pass a valid Axis object."
                )
        elif width_units == "inches":
            if not isinstance(figure, Figure):
                raise ValueError(
                    "If width_units=inches need to pass a valid Figure object."
                )
            self.width = inches_to_display(width, 0, figure)[0]
        else:
            raise ValueError(f"width_unit {width_units} not known")

        # x needs to be given in figure units
        if x_units == "display":
            if not isinstance(figure, Figure):
                raise ValueError(
                    "If x_units=figure need to pass a valid Figure object."
                )
            x = display_to_figure(x, 0.0, figure)[0]
        elif x_units == "figure":
            pass
        elif x_units == "axis":
            if not isinstance(ax, Axes):
                raise ValueError(
                    "If x_units=axis need to pass a valid Axis object.")
            x = axis_to_figure(x, 0.0, ax)[0]
        elif x_units == "inches":
            if not isinstance(figure, Figure):
                raise ValueError(
                    "If x_units=inches need to pass a valid Figure object."
                )
            x = inches_to_figure(x, 0.0, figure)[0]
        elif x_units == "data":
            if not isinstance(ax, Axes):
                raise ValueError(
                    "If x_units=data need to pass a valid Axis object.")
            x = data_to_figure(x, 0.0, ax)[0]
        else:
            raise ValueError(f"x_unit {x_units} not known")

        # y needs to be given in figure units
        if y_units == "display":
            if not isinstance(figure, Figure):
                raise ValueError(
                    "If y_units=figure need to pass a valid Figure object."
                )
            y = display_to_figure(0.0, y, figure)[1]
        elif y_units == "figure":
            pass
        elif y_units == "axis":
            if not isinstance(ax, Axes):
                raise ValueError(
                    "If y_units=axis need to pass a valid Axis object.")
            y = axis_to_figure(0.0, y, ax)[1]
        elif y_units == "data":
            if not isinstance(ax, Axes):
                raise ValueError(
                    "If y_units=data need to pass a valid Axis object.")
            y = data_to_figure(0.0, y, ax)[1]
        elif y_units == "inches":
            if not isinstance(figure, Figure):
                raise ValueError(
                    "If y_units=inches need to pass a valid Figure object."
                )
            y = inches_to_figure(0.0, y, figure)[1]
        else:
            raise ValueError(f"y_unit {y_units} not known")
        # Note: width must be in points because pdfrenderer is used as backend
        dpi = figure.dpi if figure is not None else 96.0
        self.width = self.width * 72.0 / dpi
        super().__init__(x=x, y=y, text=text, wrap=True, **kwargs)

    ####################################
    # Overriding matplotlib Text methods
    ####################################
    def _get_wrap_line_width(self):
        return self.width


def figure_to_display(
    width: float, height: float, figure: Figure
) -> tuple[float, float]:
    return figure.transFigure.transform((width, height))


def display_to_figure(
    width: float, height: float, figure: Figure
) -> tuple[float, float]:
    return figure.transFigure.inverted().transform((width, height))


def axis_to_figure(width: float, height: float, ax: Axes) -> tuple[float, float]:
    in_display_units = ax.transAxes.transform((width, height))
    return ax.figure.transFigure.inverted().transform(in_display_units)


def data_to_figure(width: float, height: float, ax: Axes) -> tuple[float, float]:
    in_display_units = ax.transData.transform((width, height))
    return ax.figure.transFigure.inverted().transform(in_display_units)


def inches_to_figure(
    width: float, height: float, figure: Figure
) -> tuple[float, float]:
    in_display_units = figure.dpi_scale_trans.transform((width, height))
    return figure.transFigure.inverted().transform(in_display_units)


def inches_to_display(
    width: float, height: float, figure: Figure
) -> tuple[float, float]:
    return figure.dpi_scale_trans.transform((width, height))
