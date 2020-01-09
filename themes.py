"""Libraries for theme and font management on the PyPortal

Author: Nina Zakharenko
"""
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from displayio import Group


class PlaceholderLabel(Label):
    """
    A Label that supports optional
    placeholder text.

    Useful for displaying text while waiting for
    values to be fetched from the internet.
    """

    def __init__(self, x, y, font, color, text=None, placeholder=None, glyphs=3):
        super().__init__(font, text=text or placeholder, max_glyphs=glyphs)

        self.x = x
        self.y = y
        self.color = color


class Fonts:
    """
    Represents a collection of initialized fonts that
    can be accessed by name.
    """

    def __init__(
        self, *font_names, default=None, font_dir="/fonts", load_glyphs=b"0123456789"
    ):
        """
        Create a new collection of bitmap fonts.

        Args:
            font_names (list): List of font names, mapped to a *.bdf
                bitmap font file in the font_dir directory.
            default (str, optional): Name of the default font file.
                Defaults to None.
            font_dir (str, optional): Directory where font files are located.
                Defaults to "/fonts".
            load_glyphs (bytes, optional): Optional glyph characters to pre-load.
                Defaults to b"0123456789".

        Raises:
            ValueError: If no font_names are provided.
        """
        if not font_names:
            raise ValueError("Must provide at least one font name to Fonts.")

        self.fonts = {}

        for font_name in font_names:
            font = bitmap_font.load_font("{}/{}.bdf".format(font_dir, font_name))
            if load_glyphs:
                font.load_glyphs(load_glyphs)
            self.fonts[font_name] = font

        self.default = self.fonts[default] if default else None

    def __getitem__(self, key):
        return self.fonts[key]


class BaseTheme:
    """
    A base class representing a theme that can be displayed
    on the PyPortal, with a background, a font, a text
    color, and a single display group.

    In the future, this class can be extended to suppport
    multiple display groups.

    TODO NZ: consider reading the font file-names straight
    from the directory.
    """

    fonts = Fonts(
        "Helvetica-Bold-36",
        default="Helvetica-Bold-36",
    )

    def __init__(self, background_image, font=None, bg_dir="/bgs", color=0xFFFFFF):
        """
        Create a new Base Theme.

        Args:
            background_image (str): Background image file name, with
                the file to be found as a *.bmp file in the bg_dir directory.
            font (str, optional): Which font name to use. Defaults to None.
            bg_dir (str, optional): Background image file directory. Defaults to /bgs.
            color (int, optional): Font color, in hexadecimal. Defaults to 0xFFFFFF.
        """
        self.color = color
        self.font = self.fonts[font] if font else self.fonts.default
        self.bg = "{}/{}.bmp".format(bg_dir, background_image)
        self.display = None
        self.display_pos = None

    def apply(self, pyportal):
        """
        Show the current theme on the PyPortal display.

        Args:
            pyportal (adafruit_pyportal.PyPortal): PyPortal instance.
        """
        if self.display:
            self.display_pos = len(pyportal.splash)
            pyportal.splash.append(self.display)

        pyportal.set_background(self.bg)

    def clear(self, pyportal):
        """
        Clear the current theme from the PyPortal display.

        Args:
            pyportal (adafruit_pyportal.PyPortal): PyPortal instance.
        """
        if self.display:
            pyportal.splash.pop(self.display_pos)
            self.display_pos = None


class EventTheme(BaseTheme):
    """
    A Theme for an event countdown date.

    The theme supports days, hours, and minutes labels
    at the provided positions on the provided axis, but
    can easily be extended in the future.

    Raises:
        ValueError: Provide either an x or a
            y axis for the text labels.
    """

    placeholder = "--"
    formatter = "{:>2}"
    label_positions = {"days": 0, "hours": 1, "mins": 2}

    def __init__(self, *args, pos, x_axis=None, y_axis=None, **kwargs):
        """
        Given a series of positions for the time labels and an axis
        (either an x or a y), create a new theme representing an
        event countdown.

        Args:
            pos (tuple): A tuple of (int, int, int) representing positions
                for the days, hours, and minutes labels.
            x_axis (int, optional): The x axis on which to place labels.
                Either the x_axis or y_axis is optional, but not both.
                Defaults to None.
            y_axis (int, optional): The y axis on which to place labels.
                Either the x_axis or y_axis is optional, but not both.
                Defaults to None.
        """
        super().__init__(*args, **kwargs)
        self._create_labels(x_axis, y_axis, *pos)

    def _create_labels(self, x_axis, y_axis, days_pos, hours_pos, mins_pos):
        if not (x_axis or y_axis) or (x_axis and y_axis):
            raise ValueError(
                "Must provide either an x or y axis for text labels, not both."
            )

        self.display = Group(max_size=3)

        x_positions = [x_axis] * 3 if x_axis else [days_pos, hours_pos, mins_pos]
        y_positions = [y_axis] * 3 if y_axis else [days_pos, hours_pos, mins_pos]

        for x, y in zip(x_positions, y_positions):
            label = PlaceholderLabel(
                x, y, placeholder=self.placeholder, font=self.font, color=self.color
            )
            self.display.append(label)

    def _update_label(self, label, new_value):
        pos = self.label_positions[label]
        old_value = self.display[pos].text
        if new_value != old_value:
            self.display[pos].text = new_value

    def update_time(self, days, hours, mins):
        """
        Update the time displayed.

        Args:
            days (int): Days
            hours (int): Hours
            mins (int): Minutes
        """
        self._update_label("days", self.formatter.format(days))
        self._update_label("hours", self.formatter.format(hours))
        self._update_label("mins", self.formatter.format(mins))

    @property
    def days(self):
        return self.display[self.label_positions["days"]].text

    @property
    def hours(self):
        return self.display[self.label_positions["hours"]].text

    @property
    def mins(self):
        return self.display[self.label_positions["mins"]].text


class ThemeManager:
    """
    Manages a collection of themes, and
    switches between them on a given PyPortal.
    """

    def __init__(self, themes):
        self.themes = themes

    def initialize(self, pyportal):
        """
        Initialize the PyPortal with the default theme.

        Args:
            pyportal (adafruit_pyportal.PyPortal):
                A PyPortal instance.
        """
        self.current_pos = 0
        self.current_theme = None
        self._switch_themes(pyportal)

        print("Setting initial theme.")

    def next_theme(self, pyportal):
        """
        Change the PyPortal display to the next theme.

        Args:
            pyportal (adafruit_pyportal.PyPortal):
                A PyPortal instance.
        """
        self.current_pos = (self.current_pos + 1) % len(self.themes)
        self._switch_themes(pyportal)

        print("Switching to next theme.")

    def prev_theme(self, pyportal):
        """
        Change the PyPortal display to the previous theme.

        Args:
            pyportal (adafruit_pyportal.PyPortal):
                A PyPortal instance.
        """
        self.current_pos = (self.current_pos - 1) % len(self.themes)
        self._switch_themes(pyportal)

        print("Switching to previous theme.")

    def _switch_themes(self, pyportal):
        next_theme = self.themes[self.current_pos]

        if self.current_theme:
            next_theme.update_time(
                self.current_theme.days,
                self.current_theme.hours,
                self.current_theme.mins,
            )
            self.current_theme.clear(pyportal)

        self.current_theme = next_theme
        self.current_theme.apply(pyportal)

        print("Setting theme to: ", self.current_theme.bg)


themes = ThemeManager([
    EventTheme("pycascades", pos=(40, 130, 240), y_axis=200),
    EventTheme("pycascades2", pos=(25, 130, 250), y_axis=50),
])
