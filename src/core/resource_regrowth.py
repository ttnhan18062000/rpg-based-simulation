"""The declared regrowth modes of a resource node kind (owner row 59).

``none`` (the default for every existing kind): the legacy rules, no wait is started when the node is emptied. ``regrow``: the harvest that
empties the node starts a bare wait of ``ResourceNodeState.respawn_cooldown`` ticks; the wait ends with no charges added and the ecology
regrowth resumes from zero.
"""
REGROW_MODE = "regrow"
