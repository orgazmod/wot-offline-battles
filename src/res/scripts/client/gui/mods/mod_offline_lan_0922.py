from gui.mods.offline_lan_0922 import bootstrap


def _patch_clan_account_popover():
    """Guard the retail AccountPopover against an offline clan profile.

    In retail the popover reads the player's clan info and indexes into
    it.  Offline there is no clan, and the value is an empty ``set``,
    which makes ``ClanAccountProfile._getClanInfoValue`` raise
    ``TypeError: 'set' object does not support indexing``.  That
    exception aborts ``AccountPopover._populate`` halfway through, so
    the popover never registers its close handlers and appears stuck.
    Swallow the exception and return ``None``; the popover then
    finishes loading and closes normally on the next click.
    """
    try:
        from gui.clans.clan_account_profile import ClanAccountProfile
    except Exception:
        return
    original = ClanAccountProfile.__dict__.get('_getClanInfoValue')
    if original is None or getattr(original, '_offline_safe', False):
        return

    def _offline_safe_getClanInfoValue(self, *args, **kwargs):
        try:
            return original(self, *args, **kwargs)
        except (TypeError, AttributeError, KeyError, IndexError):
            return None

    _offline_safe_getClanInfoValue._offline_safe = True
    ClanAccountProfile._getClanInfoValue = _offline_safe_getClanInfoValue


# --- Crew operations popover fix -------------------------------------------
# Python 2's ``sorted()``/``list.sort()`` reject a ``cmp`` that returns a
# ``long``.  The retail crew popover uses such a ``cmp`` and aborts its
# own ``_populate``, which leaves a half-drawn artifact on screen.  We
# install an int-safe ``sorted`` for the duration of the offending method
# so the popover opens correctly on the first try (no retry, no delay).
def _patch_crew_operations_popover():
    try:
        from gui.Scaleform.daapi.view.lobby.crewOperations import (
            CrewOperationsPopOver as _module)
    except Exception:
        return
    cls = getattr(_module, 'CrewOperationsPopOver', None)
    if cls is None:
        return
    method_name = '_CrewOperationsPopOver__getReturnOperationData'
    original = cls.__dict__.get(method_name)
    if original is None or getattr(original, '_offline_safe', False):
        return

    import __builtin__
    original_sorted = __builtin__.sorted

    def _wrap_cmp(cmp_func):
        def _safe(a, b):
            result = cmp_func(a, b)
            if result is None or isinstance(result, int):
                return result
            return int(result)
        return _safe

    def _safe_sorted(iterable, cmp=None, key=None, reverse=False):
        if cmp is not None:
            cmp = _wrap_cmp(cmp)
        return original_sorted(iterable, cmp, key, reverse)

    def _offline_safe_getReturnOperationData(self, *args, **kwargs):
        # Only shadow ``sorted`` while the retail method runs.  Any
        # other code path keeps the native built-in, so performance
        # elsewhere is untouched.
        __builtin__.sorted = _safe_sorted
        try:
            return original(self, *args, **kwargs)
        finally:
            __builtin__.sorted = original_sorted

    _offline_safe_getReturnOperationData._offline_safe = True
    setattr(cls, method_name, _offline_safe_getReturnOperationData)


def init():
    bootstrap.init()
    _patch_clan_account_popover()
    _patch_crew_operations_popover()


def fini():
    bootstrap.fini()