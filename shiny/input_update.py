from typing import Literal, Optional, Union, Tuple, TYPE_CHECKING
from datetime import date

from htmltools import TagChildArg

from .input_check_radio import CheckChoicesArg, _generate_options
from .input_numeric import NumericValueArg
from .input_select import SelectChoicesArg, _normalize_choices, _render_choices
from .input_slider import SliderValueArg, SliderStepArg, _slider_type, _as_numeric
from .utils import drop_none
from .shinysession import _require_active_session, _process_deps

if TYPE_CHECKING:
    from .shinysession import ShinySession

# -----------------------------------------------------------------------------
# input_button.py
# -----------------------------------------------------------------------------
async def update_button(
    id: str,
    *,
    label: Optional[str] = None,
    icon: TagChildArg = None,
    session: Optional["ShinySession"] = None,
):
    session = _require_active_session(session)
    # TODO: supporting a TagChildArg for label would require changes to shiny.js
    # https://github.com/rstudio/shiny/issues/1140
    msg = {"label": label, "icon": _process_deps(icon)["html"]}
    await session.send_input_message(id, drop_none(msg))


update_link = update_button

# -----------------------------------------------------------------------------
# input_check_radio.py
# -----------------------------------------------------------------------------
async def update_checkbox(
    id: str,
    *,
    label: Optional[str] = None,
    value: Optional[bool] = None,
    session: Optional["ShinySession"] = None,
):
    session = _require_active_session(session)
    msg = {"label": label, "value": value}
    await session.send_input_message(id, drop_none(msg))


async def update_checkbox_group(
    id: str,
    *,
    label: Optional[str] = None,
    choices: Optional[CheckChoicesArg] = None,
    selected: Optional[str] = None,
    inline: bool = False,
    session: Optional["ShinySession"] = None,
):
    await _update_choice_input(
        id=id,
        type="checkbox",
        label=label,
        choices=choices,
        selected=selected,
        inline=inline,
        session=session,
    )


async def update_radio_buttons(
    id: str,
    *,
    label: Optional[str] = None,
    choices: Optional[CheckChoicesArg] = None,
    selected: Optional[str] = None,
    inline: bool = False,
    session: Optional["ShinySession"] = None,
):
    await _update_choice_input(
        id=id,
        type="radio",
        label=label,
        choices=choices,
        selected=selected,
        inline=inline,
        session=session,
    )


async def _update_choice_input(
    id: str,
    *,
    type: Literal["checkbox", "radio"],
    label: Optional[str] = None,
    choices: Optional[CheckChoicesArg] = None,
    selected: Optional[str] = None,
    inline: bool = False,
    session: Optional["ShinySession"] = None,
):
    session = _require_active_session(session)
    options = None
    if choices is not None:
        options = _generate_options(
            id=id, type=type, choices=choices, selected=selected, inline=inline
        )
    msg = {"label": label, "options": _process_deps(options)["html"], "value": selected}
    await session.send_input_message(id, drop_none(msg))


# -----------------------------------------------------------------------------
# input_date.py
# -----------------------------------------------------------------------------
async def update_date(
    id: str,
    *,
    label: Optional[str] = None,
    value: Optional[date] = None,
    min: Optional[date] = None,
    max: Optional[date] = None,
    session: Optional["ShinySession"] = None,
):

    session = _require_active_session(session)
    msg = {
        "label": label,
        "value": str(value),
        "min": str(min),
        "max": str(max),
    }
    await session.send_input_message(id, drop_none(msg))


async def update_date_range(
    id: str,
    *,
    label: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
    min: Optional[date] = None,
    max: Optional[date] = None,
    session: Optional["ShinySession"] = None,
):
    session = _require_active_session(session)
    msg = {
        "label": label,
        "start": str(start),
        "end": str(end),
        "min": str(min),
        "max": str(max),
    }
    await session.send_input_message(id, drop_none(msg))


# -----------------------------------------------------------------------------
# input_numeric.py
# -----------------------------------------------------------------------------
async def update_numeric(
    id: str,
    *,
    label: Optional[str] = None,
    value: Optional[NumericValueArg] = None,
    min: Optional[NumericValueArg] = None,
    max: Optional[NumericValueArg] = None,
    step: Optional[NumericValueArg] = None,
    session: Optional["ShinySession"] = None,
):
    session = _require_active_session(session)
    msg = {
        "label": label,
        "value": value,
        "min": min,
        "max": max,
        "step": step,
    }
    await session.send_input_message(id, drop_none(msg))


# -----------------------------------------------------------------------------
# input_select.py
# -----------------------------------------------------------------------------
async def update_select(
    id: str,
    *,
    label: Optional[str] = None,
    choices: Optional[SelectChoicesArg] = None,
    selected: Optional[str] = None,
    session: Optional["ShinySession"] = None,
):
    session = _require_active_session(session)

    if choices is None:
        options = None
    else:
        option_tags = _render_choices(_normalize_choices(choices), selected)
        options = _process_deps(option_tags)["html"]

    msg = {
        "label": label,
        "options": options,
        "selected": selected,
    }
    await session.send_input_message(id, drop_none(msg))


# -----------------------------------------------------------------------------
# input_slider.py
# -----------------------------------------------------------------------------
async def update_slider(
    id: str,
    *,
    label: Optional[str] = None,
    value: Optional[
        Union[SliderValueArg, Tuple[SliderValueArg, SliderValueArg]]
    ] = None,
    min: Optional[SliderValueArg] = None,
    max: Optional[SliderValueArg] = None,
    step: Optional[SliderStepArg] = None,
    time_format: Optional[str] = None,
    timezone: Optional[str] = None,
    session: Optional["ShinySession"] = None,
):
    session = _require_active_session(session)

    # Get any non-None value to see if the `data-type` may need to change
    val = value[0] if isinstance(value, tuple) else value
    present_val = next((x for x in [val, min, max]), None)

    data_type = None if present_val is None else _slider_type(present_val)
    if time_format is None and data_type and data_type[0:4] == "date":
        time_format = "%F" if data_type == "date" else "%F %T"

    min_num = None if min is None else _as_numeric(min)
    max_num = None if max is None else _as_numeric(max)
    step_num = None if step is None else _as_numeric(step)
    val_nums = (
        None
        if value is None
        else (
            (_as_numeric(value[0]), _as_numeric(value[1]))
            if isinstance(value, tuple)
            else (_as_numeric(value), _as_numeric(value))
        )
    )

    msg = {
        "label": label,
        "value": val_nums,
        "min": min_num,
        "max": max_num,
        "step": step_num,
        "data-type": data_type,
        "time_format": time_format,
        "timezone": timezone,
    }
    await session.send_input_message(id, drop_none(msg))


# -----------------------------------------------------------------------------
# input_text.py
# -----------------------------------------------------------------------------
async def update_text(
    id: str,
    *,
    label: TagChildArg = None,
    value: TagChildArg = None,
    placeholder: TagChildArg = None,
    session: Optional["ShinySession"] = None,
):
    session = _require_active_session(session)
    msg = {"label": label, "value": value, "placeholder": placeholder}
    await session.send_input_message(id, drop_none(msg))


update_text_area = update_text


# -----------------------------------------------------------------------------
# navs.py
# -----------------------------------------------------------------------------

# TODO: provide an alias of `update_navs`?
async def nav_select(
    id: str, selected: Optional[str] = None, session: Optional["ShinySession"] = None
):
    session = _require_active_session(session)
    msg = {"value": selected}
    await session.send_input_message(id, drop_none(msg))
