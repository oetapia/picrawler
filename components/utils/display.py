#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Display and terminal output utilities.

Provides Unicode-safe printing and icon support with fallbacks
for terminals that don't support emoji.
"""

import sys


def safe_print(message):
    """
    Print with Unicode fallback for terminals that don't support UTF-8.
    
    Args:
        message: String message to print
    """
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode('ascii', 'replace').decode('ascii'))


def get_icon(emoji, fallback):
    """
    Return emoji or fallback for terminal compatibility.
    
    Args:
        emoji: Unicode emoji character
        fallback: ASCII fallback string
        
    Returns:
        str: Either the emoji or fallback depending on terminal support
    """
    try:
        emoji.encode(sys.stdout.encoding or 'utf-8')
        return emoji
    except (UnicodeEncodeError, AttributeError):
        return fallback


# Icon dictionary for consistent use across the application
ICONS = {
    'robot': get_icon('🤖', '[ROBOT]'),
    'forward': get_icon('➡️', '[FWD]'),
    'warning': get_icon('⚠️', '[WARN]'),
    'obstacle': get_icon('🚧', '[OBS]'),
    'tilt': get_icon('📐', '[TILT]'),
    'scan': get_icon('🔍', '[SCAN]'),
    'check': get_icon('✅', '[OK]'),
    'stop': get_icon('🛑', '[STOP]'),
    'stats': get_icon('📊', '[STATS]'),
}
