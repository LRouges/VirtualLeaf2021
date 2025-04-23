# Custom Context-Awareness Instructions for VirtualLeaf2021

When answering questions always check for relevant implementations in both the `src/library` and `src/GUI` directories.

## Core Library Files (`src/library`)

### Cell Structures
- `cellbase.cpp/h` - Base cell implementation
- `wallelement.cpp/h` - Wall element components
- `wallbase.cpp/h` - Base wall implementation
- `nodebase.cpp/h` - Node base structures

### Math and Utilities
- `vector.cpp/h` - Vector mathematics
- `matrix.cpp/h` - Matrix operations
- `random.cpp/h` - Random number generation
- `parameter.cpp/h` - Parameter handling
- `parse.cpp/h` - Parsing functionality

### Visualization and Messaging
- `output.cpp/h` - Output handling
- `warning.cpp/h` - Warning system
- `UniqueMessage.cpp/h` - Message handling

### Plugin System
- `simplugin.cpp/h` - Plugin implementation
- `vleafmodel.h` - Leaf model definitions

## GUI Implementation (`src/GUI`)

### GUI Elements
- `wall.cpp/h` - Wall visualization implementation
- `cell.cpp/h` - Cell visualization
- `wallitem.cpp/h` - Wall item rendering
- `node.cpp/h` - Node visualization
- `nodeitem.cpp/h` - Node item rendering

### Visualization Components
- `canvas.cpp/h` - Main canvas implementation
- `mainbase.cpp/h` - Main window base
- `VirtualLeaf.cpp` - Main application

### Simulation Components
- `tissuegenerator.cpp/h` - Tissue generation
- `forwardeuler.cpp/h` - Forward Euler integration
- `rungekutta.cpp/h` - Runge-Kutta integration

### UI Dialogs
- `transporterdialog.cpp/h` - Transport settings dialog
- `OptionFileDialog.cpp/h` - Option file handling
- `pardialog.cpp/h` - Parameter dialog

When answering questions, always check both the core implementation files in `src/library` and their GUI counterparts in `src/GUI`. Reference specific code patterns from these files, noting the connection between core functionality and its visualization.