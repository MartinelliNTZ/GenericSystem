# Plan: Organize HorizontalTab.py

## Issues Found

1. **Contrato 19 Violation**: Imports `BaseStyle` and `ThemeManager` directly
2. **Contrato 19 / SKILL_STYLES.md**: Uses `theme_manager.theme` instead of `AppStyles.current_theme`
3. **SKILL_STYLES.md**: Uses deprecated `AppStyles.theme_colors()["TITLE_BAR_BG"]` instead of `current_theme.TITLE_BAR`
4. **SKILL_STYLES.md**: Variable naming - uses `t` instead of `current_theme`

## Changes Needed

1. Remove imports: `BaseStyle`, `ThemeManager` (`theme_manager`)
2. Use `AppStyles._build_linear_gradient` (inherited from BaseStyle)
3. Replace `theme_manager.theme` with `AppStyles.current_theme`
4. Replace `AppStyles.theme_colors()["TITLE_BAR_BG"]` with `current_theme.TITLE_BAR`
5. Rename variable `t` to `current_theme` consistently
6. Add `_paint_error_logged` class variable reset mechanism