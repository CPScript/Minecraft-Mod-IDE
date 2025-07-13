# Minecraft Mod IDE

A simple Integrated Development Environment for Minecraft mod development with built-in JAR compilation and project management.

## Features

### Core Development Tools
- Multi-file tabbed text editor with Java syntax highlighting
- Integrated JAR compiler with progress tracking
- Project templates for Forge, Fabric, and Bukkit mods
- File explorer with context menu operations
- Find and replace with regex support
- Auto-save functionality (30-second intervals)
- Line numbers and current line highlighting

### User Interface
- Modern dark theme with orange accents
- Animated toolbar with tooltips
- Tabbed interface for multiple files
- Status bar with project information
- Build output console with color-coded messages
- Problems panel for error tracking

### Project Management
- Create new projects from templates
- Open and manage existing projects
- File and folder creation, renaming, deletion
- Project tree navigation with lazy loading
- Copy file paths to clipboard

### Build System
- Compile Java files to JAR packages
- Configurable output directory and JAR name
- Classpath management for external dependencies
- Optional main class specification for executable JARs
- Clean build functionality
- Real-time build progress and error reporting

## System Requirements

- Python 3.7 or higher
- Java JDK 8 or higher (javac and jar tools required)
- 4GB RAM minimum
- 1GB free disk space
- Windows 10/11, macOS, or Linux

## Installation

1. Ensure Python 3.7+ is installed on your system
2. Install Java JDK and verify javac and jar are in your system PATH
3. Download the IDE source code
4. Run the application:
   ```bash
   python ide.py
   ```

## Usage

### Getting Started
1. Launch the IDE - a splash screen will check system requirements
2. Create a new project using File > New Project or the toolbar button
3. Select a project template (Basic Mod, Forge Mod, Fabric Mod, or Bukkit Plugin)
4. Choose project location and configure package name
5. Start coding in the generated Java files

### Creating Files
- Use the file explorer buttons to create new files and folders
- Right-click in the file explorer for context menu options
- File templates are automatically generated based on file type

### Building Projects
- Use Build > Compile JAR or the toolbar compile button
- Configure output directory, JAR name, and classpath as needed
- Monitor build progress in the output console
- Built JAR files include proper manifests and metadata

### Keyboard Shortcuts
- `Ctrl+N` - New file
- `Ctrl+O` - Open file
- `Ctrl+S` - Save current file
- `Ctrl+Shift+N` - New project
- `Ctrl+Shift+O` - Open project
- `Ctrl+F` - Find and replace
- `Ctrl+/` - Toggle line comments
- `Ctrl+D` - Duplicate current line
- `F5` - Compile to JAR
- `Ctrl+F5` - Quick build
- `Shift+F5` - Clean build

## Project Templates

### Basic Mod
Simple mod template with basic Java class structure and example code.

### Forge Mod
Minecraft Forge mod template with proper annotations, main class setup, and mod metadata files.

### Fabric Mod
Fabric mod template including mod.json configuration and proper project structure.

### Bukkit Plugin
Bukkit/Spigot plugin template with plugin.yml configuration and event handling examples.

## File Types Supported

- Java source files (.java) with syntax highlighting
- JSON configuration files (.json)
- XML files (.xml)
- Properties files (.properties)
- Markdown documentation (.md)
- Plain text files (.txt)

## Build Output

The IDE generates:
- Compiled JAR files with proper manifests
- Build progress reports
- Error and warning messages
- File size information
- Timestamp logging

## Configuration

Settings can be accessed through Tools > Settings and include:
- Font family and size preferences
- Editor behavior options
- Java home directory configuration
- Build system preferences
- Auto-save settings

## Troubleshooting

### Common Issues

**"javac not found" error:**
- Ensure Java JDK is installed (not just JRE)
- Add Java bin directory to your system PATH
- Restart the IDE after PATH changes

**Build fails with permission errors:**
- Check write permissions for project and output directories
- Run IDE as administrator if necessary (Windows)
- Verify disk space availability

**Syntax highlighting not working:**
- Ensure file has .java extension
- Try reopening the file
- Check file encoding (should be UTF-8)

## Limitations

- Designed specifically for Java-based Minecraft mod development
- Requires external Java JDK installation
- No integrated debugging capabilities
- No version control integration
- No code completion beyond syntax highlighting

## License

This software is provided as-is for educational and development purposes.

## Contributing

This is a standalone educational project. For issues or suggestions, please review the source code and make modifications as needed for your specific use case.
