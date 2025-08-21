# Befunge-93 Interpreter

A complete implementation of the Befunge-93 programming language with an interactive GUI debugger and development environment.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation & Usage](#installation--usage)
- [Architecture](#architecture)
- [Core Components](#core-components)
- [GUI Components](#gui-components)
- [Befunge-93 Language Support](#befunge-93-language-support)
- [Development Features](#development-features)
- [File Formats](#file-formats)
- [API Reference](#api-reference)

## Overview

This project implements a full-featured Befunge-93 interpreter with real-time visualization, interactive debugging, and comprehensive development tools. Befunge is a two-dimensional, stack-based esoteric programming language where the instruction pointer moves through a grid of characters.

## Features

### Core Interpreter
- **Complete Befunge-93 compliance** - All standard opcodes supported
- **Self-modifying code** - Full `p` (put) and `g` (get) operation support
- **Extended value storage** - Handles 32-bit values beyond ASCII range
- **Wraparound navigation** - Standard torus topology for IP movement
- **Asynchronous I/O** - Non-blocking input handling for GUI integration

### Development Environment
- **Real-time visualization** - Live IP tracking and stack monitoring
- **Interactive debugging** - Breakpoints, step-by-step execution
- **Speed control** - Configurable execution speed (1-500ms delays)
- **Batch execution** - Process multiple steps per timer tick (1-50 steps)
- **Output window** - Dedicated program output with stack visualization
- **Settings persistence** - Per-file settings saved automatically

### GUI Features
- **Syntax highlighting** - Visual distinction for IP position and breakpoints
- **Interactive tooltips** - Hover over opcodes for instant documentation
- **Keyboard shortcuts** - Complete hotkey support for all operations
- **File management** - Open, save, and manage Befunge source files
- **Window docking** - Smart output window positioning

## Installation & Usage

### Requirements
- Python 3.8+
- tkinter (usually included with Python)

### Running the Interpreter

```bash
# Start with file dialog
python main.py

# Open specific file
python main.py program.bf
python main.py example.befunge
```

### Supported File Extensions
- `.bf` - Standard Befunge files
- `.befunge` - Alternative Befunge extension

## Architecture

```
befunge-interpreter/
├── core/                   # Interpreter engine
│   ├── InstructionPointer.py  # IP management and movement
│   ├── interpreter.py         # Main interpreter class
│   ├── direction.py          # Direction enum and utilities
│   ├── stack.py             # Befunge stack implementation
│   ├── ops.py               # Opcode dispatch table
│   ├── types.py             # Type definitions and enums
│   └── utils.py             # Math utilities (C-style division/modulo)
├── ui/                     # GUI components
│   ├── app.py               # Main application window
│   ├── opcode_hovertips.py  # Interactive tooltip system
│   ├── opcodes.py           # Opcode documentation
│   └── format_stack.py      # Stack display formatting
├── validate/               # Input validation
│   └── validate_load.py     # File validation utilities
└── main.py                 # Application entry point
```

## Core Components

### InstructionPointer (`core/InstructionPointer.py`)

Manages the instruction pointer state and movement within the 2D grid.

**Key Features:**
- Maintains current position (x, y) and direction
- Handles wraparound movement on 80×25 minimum grid
- Manages execution state flags (skip, string mode, I/O waiting)
- Stores original program dimensions vs. padded grid size

**Important Attributes:**
- `grid`: 2D character array representing the program
- `x`, `y`: Current IP coordinates
- `direction`: Current movement direction (Direction enum)
- `skip`: Bridge command (`#`) flag
- `string`: String mode state
- `waiting_for`: Input type expected (WaitTypes enum)

### Interpreter (`core/interpreter.py`)

The main interpreter engine implementing complete Befunge-93 semantics.

**Key Features:**
- Complete opcode support with dispatch table
- Self-modifying code via extended storage system
- Asynchronous input handling for GUI integration
- Step-by-step execution with state inspection
- Output stream management

**Extended Storage System:**
- Values > 255 or < 0 stored in `extended_storage` dictionary
- Grid displays low byte (modulo 256) for visual reference
- `g` operation retrieves full 32-bit value when available

**Execution States:**
- `RUNNING`: Normal execution
- `AWAITING_INPUT`: Waiting for user input (`&` or `~` opcodes)
- `HALTED`: Program terminated (`@` opcode)

### Stack (`core/stack.py`)

Befunge-specific stack implementation with language-appropriate semantics.

**Befunge Semantics:**
- Popping from empty stack returns 0 (no exceptions)
- Specialized operations for common Befunge patterns
- Iterator support for stack visualization
- Safe two-element operations with automatic zero-filling

### Direction System (`core/direction.py`)

Direction management for 2D program flow.

**Coordinate System:**
- Origin (0,0) at top-left
- X increases eastward, Y increases southward
- Wraparound at grid boundaries

**Direction Operations:**
- Conversion from opcode characters (`>`, `<`, `^`, `v`)
- Random direction selection for `?` opcode
- Delta calculation for movement

## GUI Components

### Main Application (`ui/app.py`)

The primary GUI application providing a complete development environment.

**Window Layout:**
- **Toolbar**: Execution controls and speed settings
- **Editor**: Main text area with syntax highlighting
- **Status Bar**: IP position, direction, and stack size
- **Input Bar**: Appears for `&` and `~` operations (hidden by default)

**Execution Controls:**
- **Run (F5)**: Start continuous execution with output window
- **Step (F10)**: Execute single instruction
- **Stop (Esc)**: Halt execution, keep output window open
- **Speed Control**: 1-500ms delay between steps
- **Batch Size**: 1-50 steps per timer tick for faster execution

**Debugging Features:**
- **Breakpoints**: Ctrl+Click to toggle at any grid position
- **Visual Highlighting**: IP position (mint green), breakpoints (orange-red)
- **Settings Persistence**: Speed, breakpoints saved per-file

### Interactive Tooltips (`ui/opcode_hovertips.py`)

Advanced hover tooltip system for opcode documentation.

**Features:**
- **Delayed Display**: 250ms delay prevents flicker during mouse movement
- **Cell Highlighting**: Visual feedback for hovered cells
- **Dynamic Positioning**: Tooltips follow mouse cursor
- **Boundary Filtering**: Only shows tooltips within original program area
- **Resource Management**: Automatic cleanup and event unbinding

### Output Window

Dedicated window for program output and debugging information.

**Layout:**
- **Left Pane**: Scrollable program output (4:1 weight)
- **Right Pane**: Live stack visualization (1:1 weight)
- **Control Bar**: Copy, save, clear, autoscroll options

**Smart Docking:**
- Automatically positions relative to main window
- Prefers right side, falls back to left or below
- Follows main window movement

## Befunge-93 Language Support

### Complete Opcode Set

| Category | Opcodes | Description |
|----------|---------|-------------|
| **Arithmetic** | `+` `-` `*` `/` `%` | Standard arithmetic with C-style division |
| **Comparison** | `` ` `` `!` | Greater-than and logical NOT |
| **Directions** | `>` `<` `^` `v` `?` | IP movement control |
| **Conditionals** | `_` `|` | Horizontal and vertical if statements |
| **Stack** | `:` `\` `$` | Duplicate, swap, pop operations |
| **I/O** | `.` `,` `&` `~` | Integer/character output and input |
| **Grid** | `g` `p` | Get and put for self-modifying code |
| **Control** | `#` `@` `"` | Bridge, halt, string mode |
| **Literals** | `0`-`9` | Push digit values |

### String Mode
- Activated/deactivated by `"` character
- All characters (except `"`) pushed as ASCII values
- Supports multi-line strings with proper grid navigation

### Self-Modifying Code
- `p` operation: Modify grid at runtime
- `g` operation: Read values from grid
- Extended storage for 32-bit values
- Grid updates trigger visual refresh

## Development Features

### Settings System
Each Befunge file gets an associated `.befmeta.json` sidecar file storing:
- Execution speed (delay_ms)
- Step batch size (steps_per_tick)  
- Breakpoint locations
- Settings version for backward compatibility

### Keyboard Shortcuts
- **Ctrl+O**: Open file
- **F5**: Run program
- **F10**: Step execution
- **Esc**: Stop execution
- **Ctrl+Click**: Toggle breakpoint

### File Validation
- Extension checking (`.bf`, `.befunge`)
- Binary file detection
- Befunge opcode presence validation
- Optional halt instruction (`@`) validation

## File Formats

### Source Files
Standard text files containing Befunge-93 source code:
```
>25*"!dlroW ,olleH">:#,_@
```

### Settings Files (`.befmeta.json`)
```json
{
  "version": 2,
  "delay_ms": 50,
  "steps_per_tick": 1,
  "breakpoints": [
    {"x": 0, "y": 0},
    {"x": 15, "y": 0}
  ]
}
```

## API Reference

### Core Classes

#### `Interpreter(code: Union[str, List[List[str]]])`
Main interpreter class.

**Methods:**
- `step() -> StepStatus`: Execute one instruction
- `reset()`: Reset to initial state
- `load(code)`: Load new program
- `provide_input(value: int)`: Supply input for `&`/`~` operations
- `view() -> ViewState`: Get immutable state snapshot

**Properties:**
- `output: str`: Complete program output
- `stack: Stack`: Execution stack
- `ip: InstructionPointer`: Instruction pointer
- `halted: bool`: Program termination state

#### `InstructionPointer(code: Union[str, Sequence[Sequence[str]]])`
Instruction pointer management.

**Methods:**
- `move() -> Tuple[int, int]`: Advance IP one step
- `change_direction(d: Direction, *, from_random: bool = False)`: Update direction

**Properties:**
- `x`, `y: int`: Current coordinates
- `direction: Direction`: Movement direction
- `grid: List[List[str]]`: Program grid
- `width`, `height: int`: Grid dimensions

#### `Stack()`
Befunge-specific stack implementation.

**Methods:**
- `push(item: int)`: Add item to top
- `pop() -> int`: Remove top item (returns 0 if empty)
- `pop_two() -> Tuple[int, int]`: Pop two items safely
- `peek() -> int`: View top item without removing
- `stack_swap()`: Swap top two items

### Enums

#### `StepStatus`
- `RUNNING`: Normal execution
- `AWAITING_INPUT`: Waiting for user input
- `HALTED`: Program terminated

#### `WaitTypes`  
- `INT`: Waiting for integer input (`&`)
- `CHAR`: Waiting for character input (`~`)

#### `Direction`
- `RIGHT`, `LEFT`, `UP`, `DOWN`: Cardinal directions
- Each has `dx`, `dy` deltas and `glyph` character

### GUI Classes

#### `App(master, interp: Interpreter, *, open_on_start: bool = True)`
Main GUI application.

**Methods:**
- `open_file()`: File selection dialog
- `load_file(src: str, path: Optional[str])`: Load program
- `run(clear_output: bool = False)`: Start execution
- `step_once()`: Single step execution
- `stop()`: Stop execution
- `open_output_window(clear: bool = True)`: Show output window

---

*This documentation reflects the current state of the codebase and will be updated as features are added or modified.*