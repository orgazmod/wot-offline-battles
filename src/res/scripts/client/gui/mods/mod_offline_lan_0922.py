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


def init():
    bootstrap.init()
    _patch_clan_account_popover()


def fini():
    bootstrap.fini()