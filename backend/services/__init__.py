"""Service package.

Keep this package init lightweight.

Heavy service modules are imported directly from their concrete module paths so
package import does not eagerly pull tracker/export/document parsing stacks into
every backend process startup.
"""

__all__: list[str] = []
