"""Render a compact image from the meteo.pl UM4 meteogram data."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import unicodedata

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1200
HEIGHT = 720
LEFT = 88
RIGHT = 34
TOP = 112
BOTTOM = 56


def render_meteogram(forecast: dict, location: str) -> bytes:
    """Render temperature, precipitation, cloud and wind charts as PNG."""
    data = forecast.get("data", {})
    series = data.get("airtmp_point", {})
    temperatures = series.get("data", [])
    if not temperatures:
        raise ValueError("Prognoza meteo.pl nie zawiera temperatury")

    count = len(temperatures)
    first_timestamp = int(series.get("first_timestamp", 0))
    interval = int(series.get("interval", 3600))
    times = [
        datetime.fromtimestamp(first_timestamp + index * interval, timezone.utc)
        for index in range(count)
    ]

    image = Image.new("RGB", (WIDTH, HEIGHT), "#101820")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.load_default(size=19)
        small = ImageFont.load_default(size=15)
    except TypeError:  # Pillow < 10.1 does not accept a size here.
        font = small = ImageFont.load_default()
    white = "#f2f6fa"
    muted = "#9baab6"

    _draw_text(draw, (LEFT, 28), f"Meteogram UM4 - {location}", fill=white, font=font)
    start = times[0].strftime("%d.%m %H:%M UTC")
    end = times[-1].strftime("%d.%m %H:%M UTC")
    _draw_text(draw, (LEFT, 54), f"{start} -- {end} - Zrodlo: meteo.pl / ICM UW", fill=muted, font=small)

    gap = 12
    panel_height = (HEIGHT - TOP - BOTTOM - gap * 3) // 4
    panels = [
        ("Temperatura (C)", TOP, panel_height),
        ("Opad (mm/h) i prawdopodobienstwo (%)", TOP + panel_height + gap, panel_height),
        ("Zachmurzenie (%)", TOP + (panel_height + gap) * 2, panel_height),
        ("Wiatr (m/s)", TOP + (panel_height + gap) * 3, panel_height),
    ]
    for label, top, height in panels:
        draw.rounded_rectangle(
            (LEFT, top, WIDTH - RIGHT, top + height), radius=10, fill="#17232d"
        )
        _draw_text(draw, (LEFT + 14, top + 9), label, fill=muted, font=small)

    plot_left = LEFT + 58
    plot_right = WIDTH - RIGHT - 14
    plot_width = plot_right - plot_left
    plot_top = panels[0][1] + 27
    plot_bottom = panels[0][1] + panels[0][2] - 12
    lows = data.get("airtmp_min", {}).get("data", [])
    highs = data.get("airtmp_max", {}).get("data", [])
    _draw_line_panel(
        draw,
        plot_left,
        plot_right,
        plot_top,
        plot_bottom,
        temperatures,
        min(lows or temperatures) - 2,
        max(highs or temperatures) + 2,
        "#ffc857",
        font,
        spread=(lows, highs),
    )

    precipitation = data.get("pcpttl_aver", {}).get("data", [])
    probability = data.get("pcpttlprob_point", {}).get("data", [])
    top, height = panels[1][1], panels[1][2]
    chart_top, chart_bottom = top + 29, top + height - 12
    chart_height = chart_bottom - chart_top
    _draw_grid(draw, plot_left, plot_right, chart_top, chart_bottom, 0, 100, font)
    _draw_bars(draw, plot_left, plot_width, chart_top, chart_bottom, precipitation, "#46b4e8", 10)
    _draw_line(
        draw,
        plot_left,
        plot_width,
        chart_top,
        chart_height,
        probability,
        0,
        100,
        "#f18fba",
    )

    clouds = data.get("cldtot_aver", {}).get("data", [])
    top, height = panels[2][1], panels[2][2]
    chart_top, chart_bottom = top + 29, top + height - 12
    _draw_line_panel(
        draw,
        plot_left,
        plot_right,
        chart_top,
        chart_bottom,
        clouds,
        0,
        100,
        "#91a8bd",
        font,
    )

    wind = data.get("wind10_sd_true_prev_point", {}).get("data", [])
    gusts = data.get("wind_gust_max", {}).get("data", [])
    top, height = panels[3][1], panels[3][2]
    chart_top, chart_bottom = top + 29, top + height - 22
    _draw_line_panel(
        draw,
        plot_left,
        plot_right,
        chart_top,
        chart_bottom,
        wind,
        0,
        max(5, max(gusts or wind or [5]) + 2),
        "#6bd3a5",
        font,
        secondary=(gusts, "#63a7ff"),
    )
    _draw_time_labels(draw, plot_left, plot_right, panels[3][1] + height - 17, times, font)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _draw_grid(draw, left, right, top, bottom, low, high, font):
    for step in range(3):
        y = top + (bottom - top) * step / 2
        draw.line((left, y, right, y), fill="#2c3a45", width=1)
    _draw_text(draw, (LEFT + 8, top), f"{high:g}", fill="#9baab6", font=font)
    _draw_text(draw, (LEFT + 8, bottom - 10), f"{low:g}", fill="#9baab6", font=font)


def _xy(index, count, left, top, width, height, value, low, high):
    x = left + (width * index / max(1, count - 1))
    y = top + height - (max(low, min(high, value)) - low) * height / max(0.1, high - low)
    return (int(x), int(y))


def _draw_line(draw, left, width, top, height, values, low, high, color):
    if len(values) < 2:
        return
    points = [_xy(i, len(values), left, top, width, height, value, low, high) for i, value in enumerate(values)]
    draw.line(points, fill=color, width=3, joint="curve")


def _draw_line_panel(draw, left, right, top, bottom, values, low, high, color, font, spread=None, secondary=None):
    _draw_grid(draw, left, right, top, bottom, low, high, font)
    width, height = right - left, bottom - top
    if spread and spread[0] and spread[1]:
        count = min(len(values), len(spread[0]), len(spread[1]))
        upper = [_xy(i, count, left, top, width, height, spread[1][i], low, high) for i in range(count)]
        lower = [_xy(i, count, left, top, width, height, spread[0][i], low, high) for i in reversed(range(count))]
        draw.polygon(upper + lower, fill="#33465a")
    _draw_line(draw, left, width, top, height, values, low, high, color)
    if secondary and secondary[0]:
        _draw_line(draw, left, width, top, height, secondary[0], low, high, secondary[1])


def _draw_bars(draw, left, width, top, bottom, values, color, max_value):
    if not values:
        return
    count = len(values)
    step = width / count
    chart_height = bottom - top
    for index, value in enumerate(values):
        bar_height = chart_height * max(0, float(value or 0)) / max_value
        x1 = left + index * step + 1
        x2 = left + (index + 1) * step - 1
        draw.rectangle((x1, bottom - bar_height, x2, bottom), fill=color)


def _draw_time_labels(draw, left, right, y, times, font):
    if not times:
        return
    for index in range(0, len(times), max(1, len(times) // 8)):
        x = left + (right - left) * index / max(1, len(times) - 1)
        _draw_text(draw, (int(x), y), times[index].strftime("%d.%m %H:%M"), fill="#9baab6", font=font)


def _draw_text(draw, position, text, *, fill, font):
    """Draw text using Pillow's bundled font without OS font dependencies."""
    normalized = text.replace("Ł", "L").replace("ł", "l")
    ascii_text = unicodedata.normalize("NFKD", normalized).encode("ascii", "ignore").decode()
    draw.text(position, ascii_text, fill=fill, font=font)
