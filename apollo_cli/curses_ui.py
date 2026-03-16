"""Shared curses-based UI components for Apollo CLI.

Used by `apollo tools` and `apollo skills` for interactive checklists.
Provides a curses multi-select with keyboard navigation, plus a
text-based numbered fallback for terminals without curses support.
"""
from typing import List, Set


def curses_checklist(
    title: str,
    items: List[str],
    selected: Set[int],
    *,
    cancel_returns: Set[int] | None = None,
    separators: Set[int] | None = None,
) -> Set[int]:
    """Curses multi-select checklist. Returns set of selected indices.

    Args:
        title: Header line displayed above the checklist.
        items: Display labels for each row.
        selected: Indices that start checked (pre-selected).
        cancel_returns: Returned on ESC/q. Defaults to the original *selected*.
        separators: Indices that are non-selectable section headers.
    """
    if cancel_returns is None:
        cancel_returns = set(selected)
    if separators is None:
        separators = set()

    try:
        import curses
        chosen = set(selected)
        result_holder: list = [None]

        def _draw(stdscr):
            curses.curs_set(0)
            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
                curses.init_pair(1, curses.COLOR_GREEN, -1)
                curses.init_pair(2, curses.COLOR_YELLOW, -1)
                curses.init_pair(3, 8, -1)  # dim gray

            # Start cursor on first non-separator item
            cursor = 0
            while cursor in separators and cursor < len(items):
                cursor += 1
            scroll_offset = 0

            while True:
                stdscr.clear()
                max_y, max_x = stdscr.getmaxyx()

                # Header
                try:
                    hattr = curses.A_BOLD
                    if curses.has_colors():
                        hattr |= curses.color_pair(2)
                    stdscr.addnstr(0, 0, title, max_x - 1, hattr)
                    stdscr.addnstr(
                        1, 0,
                        "  ↑↓ navigate  SPACE toggle  ENTER confirm  ESC cancel",
                        max_x - 1, curses.A_DIM,
                    )
                except curses.error:
                    pass

                # Scrollable item list
                visible_rows = max_y - 3
                if cursor < scroll_offset:
                    scroll_offset = cursor
                elif cursor >= scroll_offset + visible_rows:
                    scroll_offset = cursor - visible_rows + 1

                for draw_i, i in enumerate(
                    range(scroll_offset, min(len(items), scroll_offset + visible_rows))
                ):
                    y = draw_i + 3
                    if y >= max_y - 1:
                        break

                    if i in separators:
                        # Render separator as a non-selectable header
                        line = f"     {items[i]}"
                        attr = curses.A_BOLD
                        if curses.has_colors():
                            attr |= curses.color_pair(2)
                    else:
                        check = "✓" if i in chosen else " "
                        arrow = "→" if i == cursor else " "
                        line = f" {arrow} [{check}] {items[i]}"
                        attr = curses.A_NORMAL
                        if i == cursor:
                            attr = curses.A_BOLD
                            if curses.has_colors():
                                attr |= curses.color_pair(1)
                    try:
                        stdscr.addnstr(y, 0, line, max_x - 1, attr)
                    except curses.error:
                        pass

                stdscr.refresh()
                key = stdscr.getch()

                if key in (curses.KEY_UP, ord("k")):
                    cursor = (cursor - 1) % len(items)
                    while cursor in separators:
                        cursor = (cursor - 1) % len(items)
                elif key in (curses.KEY_DOWN, ord("j")):
                    cursor = (cursor + 1) % len(items)
                    while cursor in separators:
                        cursor = (cursor + 1) % len(items)
                elif key == ord(" "):
                    if cursor not in separators:
                        chosen.symmetric_difference_update({cursor})
                elif key in (curses.KEY_ENTER, 10, 13):
                    result_holder[0] = set(chosen)
                    return
                elif key in (27, ord("q")):
                    result_holder[0] = cancel_returns
                    return

        curses.wrapper(_draw)
        return result_holder[0] if result_holder[0] is not None else cancel_returns

    except Exception:
        return _numbered_fallback(title, items, selected, cancel_returns, separators)


def _numbered_fallback(
    title: str,
    items: List[str],
    selected: Set[int],
    cancel_returns: Set[int],
    separators: Set[int] | None = None,
) -> Set[int]:
    """Text-based toggle fallback for terminals without curses."""
    from apollo_cli.colors import Colors, color

    if separators is None:
        separators = set()
    chosen = set(selected)
    print(color(f"\n  {title}", Colors.YELLOW))
    print(color("  Toggle by number, Enter to confirm.\n", Colors.DIM))

    while True:
        for i, label in enumerate(items):
            if i in separators:
                print(color(f"\n  {label}", Colors.YELLOW))
            else:
                marker = color("[✓]", Colors.GREEN) if i in chosen else "[ ]"
                print(f"  {marker} {i + 1:>2}. {label}")
        print()
        try:
            val = input(color("  Toggle # (or Enter to confirm): ", Colors.DIM)).strip()
            if not val:
                break
            idx = int(val) - 1
            if 0 <= idx < len(items) and idx not in separators:
                chosen.symmetric_difference_update({idx})
        except (ValueError, KeyboardInterrupt, EOFError):
            return cancel_returns
        print()

    return chosen
