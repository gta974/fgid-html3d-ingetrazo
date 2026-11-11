# Display edges at opening

The export dialog's "Display edges at opening" checkbox sets the HTML's initial edge visibility, taking precedence over the first scene's saved edge style.
In Pro's prepared opening layout, each view has its own checkbox. A new split inherits its parent's choice. Exported HTML restores these choices independently, including linked-camera layouts. Older layouts without this field use the global export choice.
Subsequent scene changes may recall the scene's saved edge state. Hidden line always shows outlines; Wireframe uses its own lines.

Close IngeTrazo, replace this plugin folder, restart, and export again.
