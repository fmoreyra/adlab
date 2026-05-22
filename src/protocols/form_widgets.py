"""
Shared Tailwind CSS classes for Django form widgets.

Use these instead of Bootstrap ``form-control``, which is not loaded in this
project and leaves inputs without visible borders.
"""

TAILWIND_INPUT_CLASS = (
    "block w-full h-10 px-3 py-2 border-2 border-gray-300 rounded-lg "
    "shadow-sm placeholder-gray-400 bg-white text-gray-900 "
    "focus:outline-none focus:ring-2 focus:ring-blue-500 "
    "focus:border-blue-500 transition-colors duration-200"
)

TAILWIND_TEXTAREA_CLASS = (
    "block w-full px-3 py-2 border-2 border-gray-300 rounded-lg "
    "shadow-sm placeholder-gray-400 bg-white text-gray-900 "
    "focus:outline-none focus:ring-2 focus:ring-blue-500 "
    "focus:border-blue-500 transition-colors duration-200 resize-y"
)
