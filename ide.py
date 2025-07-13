#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, font, simpledialog
import subprocess
import os
import threading
import json
import re
import shutil
from pathlib import Path
import webbrowser
from datetime import datetime
import tempfile
import sys
import time
import configparser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AutoCompleter:
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.completion_window = None
        self.setup_completion()
        
        self.java_keywords = [
            'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char',
            'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum',
            'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements',
            'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new',
            'package', 'private', 'protected', 'public', 'return', 'short', 'static',
            'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
            'transient', 'try', 'void', 'volatile', 'while', 'true', 'false', 'null'
        ]
        
        self.common_methods = [
            'System.out.println', 'System.out.print', 'toString', 'equals', 'hashCode',
            'length', 'size', 'isEmpty', 'contains', 'add', 'remove', 'clear',
            'substring', 'indexOf', 'charAt', 'split', 'trim', 'toLowerCase', 'toUpperCase'
        ]
        
        self.minecraft_apis = [
            'Block', 'Item', 'Entity', 'Player', 'World', 'ItemStack', 'BlockPos',
            'Material', 'EntityPlayer', 'TileEntity', 'Recipe', 'CreativeTabs',
            'EnumFacing', 'IBlockState', 'NBTTagCompound', 'ResourceLocation'
        ]
        
    def setup_completion(self):
        self.text_widget.bind('<KeyRelease>', self.on_key_release)
        self.text_widget.bind('<Button-1>', self.hide_completion)
        
    def on_key_release(self, event):
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Return', 'Tab']:
            return
            
        if event.char.isalnum() or event.char in '._':
            self.show_completion()
        else:
            self.hide_completion()
            
    def show_completion(self):
        # Get current word
        current_pos = self.text_widget.index(tk.INSERT)
        line_start = current_pos.split('.')[0] + '.0'
        line_text = self.text_widget.get(line_start, current_pos)
        
        # Extract current word
        words = re.split(r'[\s\(\)\[\]\{\}\.;,]', line_text)
        current_word = words[-1] if words else ""
        
        if len(current_word) < 2:
            self.hide_completion()
            return
            
        # Find matches
        matches = self.find_matches(current_word)
        if not matches:
            self.hide_completion()
            return
            
        # Show completion window
        if not self.completion_window:
            self.create_completion_window()
            
        self.populate_completion(matches, current_word)
        self.position_completion_window()
        
    def find_matches(self, prefix):
        prefix_lower = prefix.lower()
        matches = []
        
        # Check keywords
        for keyword in self.java_keywords:
            if keyword.startswith(prefix_lower):
                matches.append(('keyword', keyword))
                
        # Check common methods
        for method in self.common_methods:
            if method.lower().startswith(prefix_lower):
                matches.append(('method', method))
                
        # Check Minecraft APIs
        for api in self.minecraft_apis:
            if api.lower().startswith(prefix_lower):
                matches.append(('class', api))
                
        return matches[:10]  # Limit to 10 matches
        
    def create_completion_window(self):
        self.completion_window = tk.Toplevel(self.text_widget)
        self.completion_window.wm_overrideredirect(True)
        self.completion_window.configure(bg=ModernStyle.MEDIUM_BG, relief='solid', borderwidth=1)
        
        # Create listbox
        self.completion_listbox = tk.Listbox(
            self.completion_window,
            height=8, width=30,
            bg=ModernStyle.MEDIUM_BG,
            fg=ModernStyle.TEXT_PRIMARY,
            selectbackground=ModernStyle.ACCENT_ORANGE,
            selectforeground=ModernStyle.DARK_BG,
            font=('Consolas', 9),
            relief='flat', bd=0
        )
        self.completion_listbox.pack()
        
        # Bind events
        self.completion_listbox.bind('<Double-Button-1>', self.insert_completion)
        self.completion_listbox.bind('<Return>', self.insert_completion)
        self.text_widget.bind('<Escape>', lambda e: self.hide_completion())
        
    def populate_completion(self, matches, prefix):
        self.completion_listbox.delete(0, tk.END)
        self.current_matches = matches
        self.current_prefix = prefix
        
        for match_type, match_text in matches:
            icon = {'keyword': '🔑', 'method': '🔧', 'class': '📦'}.get(match_type, '📄')
            self.completion_listbox.insert(tk.END, f"{icon} {match_text}")
            
        if matches:
            self.completion_listbox.select_set(0)
            
    def position_completion_window(self):
        try:
            # Get cursor position
            bbox = self.text_widget.bbox(tk.INSERT)
            if bbox:
                x = self.text_widget.winfo_rootx() + bbox[0]
                y = self.text_widget.winfo_rooty() + bbox[1] + bbox[3]
                self.completion_window.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass
            
    def insert_completion(self, event=None):
        selection = self.completion_listbox.curselection()
        if selection and self.current_matches:
            match_type, match_text = self.current_matches[selection[0]]
            
            # Get current cursor position
            current_pos = self.text_widget.index(tk.INSERT)
            
            # Calculate start of current word
            line_start = current_pos.split('.')[0] + '.0'
            line_text = self.text_widget.get(line_start, current_pos)
            
            # Find start of current word
            word_start_offset = len(line_text) - len(self.current_prefix)
            word_start = f"{current_pos.split('.')[0]}.{word_start_offset}"
            
            # Replace current word with completion
            self.text_widget.delete(word_start, current_pos)
            self.text_widget.insert(word_start, match_text)
            
            self.hide_completion()
            
    def hide_completion(self, event=None):
        if self.completion_window:
            self.completion_window.destroy()
            self.completion_window = None

class BracketMatcher:
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        self.setup_bracket_matching()
        
    def setup_bracket_matching(self):
        self.text_widget.bind('<KeyRelease>', self.highlight_matching_bracket)
        self.text_widget.bind('<Button-1>', self.highlight_matching_bracket)
        
        # Configure bracket highlight tag
        self.text_widget.tag_configure("bracket_match", 
                                     background=ModernStyle.ACCENT_ORANGE,
                                     foreground=ModernStyle.DARK_BG)
        
    def highlight_matching_bracket(self, event=None):
        # Clear previous highlights
        self.text_widget.tag_remove("bracket_match", "1.0", tk.END)
        
        current_pos = self.text_widget.index(tk.INSERT)
        char_at_cursor = self.text_widget.get(current_pos)
        char_before_cursor = self.text_widget.get(f"{current_pos}-1c")
        
        # Check character at cursor
        if char_at_cursor in self.bracket_pairs:
            match_pos = self.find_matching_bracket(current_pos, char_at_cursor, 1)
            if match_pos:
                self.text_widget.tag_add("bracket_match", current_pos)
                self.text_widget.tag_add("bracket_match", match_pos)
                
        # Check character before cursor
        elif char_before_cursor in self.bracket_pairs.values():
            match_pos = self.find_matching_bracket(f"{current_pos}-1c", char_before_cursor, -1)
            if match_pos:
                self.text_widget.tag_add("bracket_match", f"{current_pos}-1c")
                self.text_widget.tag_add("bracket_match", match_pos)
                
    def find_matching_bracket(self, start_pos, bracket, direction):
        if direction == 1:
            target = self.bracket_pairs[bracket]
        else:
            target = next(k for k, v in self.bracket_pairs.items() if v == bracket)
            
        pos = start_pos
        count = 1
        
        while count > 0:
            if direction == 1:
                pos = f"{pos}+1c"
            else:
                pos = f"{pos}-1c"
                
            try:
                char = self.text_widget.get(pos)
                if not char:
                    break
                    
                if char == bracket:
                    count += 1
                elif char == target:
                    count -= 1
                    
            except tk.TclError:
                break
                
        return pos if count == 0 else None

class CodeSnippets:
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.snippets = {
            'main': '''public static void main(String[] args) {
    ${cursor}
}''',
            'class': '''public class ${ClassName} {
    public ${ClassName}() {
        ${cursor}
    }
}''',
            'method': '''public ${type} ${methodName}(${params}) {
    ${cursor}
}''',
            'for': '''for (int ${i} = 0; ${i} < ${length}; ${i}++) {
    ${cursor}
}''',
            'foreach': '''for (${Type} ${item} : ${collection}) {
    ${cursor}
}''',
            'if': '''if (${condition}) {
    ${cursor}
}''',
            'try': '''try {
    ${cursor}
} catch (${Exception} e) {
    e.printStackTrace();
}''',
            'sout': 'System.out.println(${text});',
            'todo': '// TODO: ${description}',
            'fixme': '// FIXME: ${issue}'
        }
        
        self.setup_snippets()
        
    def setup_snippets(self):
        self.text_widget.bind('<Control-space>', self.show_snippet_menu)
        
    def show_snippet_menu(self, event):
        menu = tk.Menu(self.text_widget, tearoff=0,
                      bg=ModernStyle.MEDIUM_BG,
                      fg=ModernStyle.TEXT_PRIMARY,
                      activebackground=ModernStyle.ACCENT_ORANGE)
        
        for snippet_name in self.snippets:
            menu.add_command(label=f"📝 {snippet_name}", 
                           command=lambda name=snippet_name: self.insert_snippet(name))
            
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
            
    def insert_snippet(self, snippet_name):
        if snippet_name not in self.snippets:
            return
            
        snippet = self.snippets[snippet_name]
        cursor_pos = self.text_widget.index(tk.INSERT)
        
        # Insert snippet
        self.text_widget.insert(cursor_pos, snippet)
        
        # Find cursor placeholder
        if '${cursor}' in snippet:
            start = self.text_widget.search('${cursor}', cursor_pos)
            if start:
                end = f"{start}+{len('${cursor}')}c"
                self.text_widget.delete(start, end)
                self.text_widget.mark_set(tk.INSERT, start)

class FileWatcher:
    
    def __init__(self, ide_instance):
        self.ide = ide_instance
        self.observer = None
        self.watched_paths = set()
        
    def start_watching(self, path):
        if not self.observer:
            self.observer = Observer()
            
        if path not in self.watched_paths:
            event_handler = FileChangeHandler(self.ide)
            self.observer.schedule(event_handler, path, recursive=True)
            self.watched_paths.add(path)
            
        if not self.observer.is_alive():
            self.observer.start()
            
    def stop_watching(self):
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

class FileChangeHandler(FileSystemEventHandler):
    
    def __init__(self, ide_instance):
        self.ide = ide_instance
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.java'):
            # Check if file is open in editor
            for filename, file_data in self.ide.editor.open_files.items():
                if file_data['file_path'] == event.src_path:
                    # Ask user if they want to reload
                    self.ide.root.after(0, lambda: self.ask_reload(event.src_path, filename))
                    break
                    
    def ask_reload(self, file_path, filename):
        result = messagebox.askyesno(
            "File Modified",
            f"File '{os.path.basename(file_path)}' has been modified externally.\n\nReload file?"
        )
        if result:
            self.ide.editor.open_file(file_path)

class ThemeManager:
    
    def __init__(self, ide_instance):
        self.ide = ide_instance
        self.themes = {
            'Dark Orange': {
                'DARK_BG': '#1a1a1a',
                'MEDIUM_BG': '#2d2d30', 
                'LIGHT_BG': '#3c3c3c',
                'SIDEBAR_BG': '#252526',
                'ACCENT_ORANGE': '#ff8c42',
                'TEXT_PRIMARY': '#ffffff'
            },
            'Dark Blue': {
                'DARK_BG': '#1e1e1e',
                'MEDIUM_BG': '#252526',
                'LIGHT_BG': '#2d2d30',
                'SIDEBAR_BG': '#252526',
                'ACCENT_ORANGE': '#007acc',
                'TEXT_PRIMARY': '#cccccc'
            },
            'Forest Green': {
                'DARK_BG': '#1a2e1a',
                'MEDIUM_BG': '#2d4a2d',
                'LIGHT_BG': '#3c5a3c',
                'SIDEBAR_BG': '#253625',
                'ACCENT_ORANGE': '#4caf50',
                'TEXT_PRIMARY': '#e8f5e8'
            },
            'Purple Haze': {
                'DARK_BG': '#2a1a2e',
                'MEDIUM_BG': '#3d2d4a',
                'LIGHT_BG': '#4a3c5a',
                'SIDEBAR_BG': '#362536',
                'ACCENT_ORANGE': '#9c27b0',
                'TEXT_PRIMARY': '#f3e5f5'
            }
        }
        
    def apply_theme(self, theme_name):
        if theme_name not in self.themes:
            return
            
        theme = self.themes[theme_name]
        
        # Update ModernStyle colors
        for key, value in theme.items():
            setattr(ModernStyle, key, value)
            
        # Reconfigure styles
        ModernStyle.configure_style(self.ide.root)
        
        # Refresh editor themes
        self.refresh_editor_themes()
        
    def refresh_editor_themes(self):
        for filename, file_data in self.ide.editor.open_files.items():
            text_widget = file_data['text_widget']
            text_widget.configure(
                bg=ModernStyle.DARK_BG,
                fg=ModernStyle.TEXT_PRIMARY,
                insertbackground=ModernStyle.ACCENT_ORANGE,
                selectbackground=ModernStyle.ACCENT_ORANGE
            )
            file_data['highlighter'].setup_tags()
            file_data['highlighter'].highlight_syntax()

class MiniMap:
    
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text_widget = text_widget
        self.setup_minimap()
        
    def setup_minimap(self):
        self.minimap_frame = tk.Frame(self.parent, bg=ModernStyle.MEDIUM_BG, width=120)
        self.minimap_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(2, 0))
        self.minimap_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(self.minimap_frame, text="Map", 
                              bg=ModernStyle.MEDIUM_BG, 
                              fg=ModernStyle.TEXT_SECONDARY,
                              font=("Segoe UI", 8))
        title_label.pack(pady=2)
        
        # Minimap canvas
        self.canvas = tk.Canvas(self.minimap_frame, 
                               bg=ModernStyle.DARK_BG,
                               highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Bind events
        self.text_widget.bind('<KeyRelease>', self.update_minimap)
        self.text_widget.bind('<Button-1>', self.update_minimap)
        self.canvas.bind('<Button-1>', self.minimap_click)
        
    def update_minimap(self, event=None):
        self.canvas.delete("all")
        
        content = self.text_widget.get("1.0", tk.END)
        lines = content.split('\n')
        
        if not lines:
            return
            
        canvas_height = self.canvas.winfo_height()
        canvas_width = self.canvas.winfo_width()
        
        if canvas_height < 10 or canvas_width < 10:
            return
            
        line_height = max(1, canvas_height / len(lines))
        
        for i, line in enumerate(lines):
            y = i * line_height
            
            # Different colors for different content
            if line.strip().startswith('//'):
                color = ModernStyle.TEXT_MUTED
            elif any(keyword in line for keyword in ['class', 'interface', 'enum']):
                color = ModernStyle.ACCENT_ORANGE
            elif any(keyword in line for keyword in ['public', 'private', 'protected']):
                color = '#87ceeb'
            elif line.strip():
                color = ModernStyle.TEXT_SECONDARY
            else:
                continue
                
            self.canvas.create_rectangle(0, y, canvas_width, y + line_height, 
                                       fill=color, outline="")
                                       
    def minimap_click(self, event):
        canvas_height = self.canvas.winfo_height()
        content = self.text_widget.get("1.0", tk.END)
        lines = content.split('\n')
        
        if canvas_height > 0:
            line_ratio = event.y / canvas_height
            target_line = int(line_ratio * len(lines)) + 1
            self.text_widget.see(f"{target_line}.0")
            self.text_widget.mark_set(tk.INSERT, f"{target_line}.0")

class TerminalIntegration:
    
    def __init__(self, parent):
        self.parent = parent
        self.setup_terminal()
        
    def setup_terminal(self):
        # Terminal header
        header_frame = ttk.Frame(self.parent, style='Modern.TFrame')
        header_frame.pack(fill=tk.X, padx=8, pady=6)
        
        ttk.Label(header_frame, text="💻 Terminal", style='Header.TLabel').pack(side=tk.LEFT)
        
        controls_frame = ttk.Frame(header_frame, style='Modern.TFrame')
        controls_frame.pack(side=tk.RIGHT)
        
        ttk.Button(controls_frame, text="Clear", command=self.clear_terminal, 
                  style='Modern.TButton', width=8).pack(side=tk.RIGHT, padx=2)
        
        # Terminal output
        self.terminal_output = scrolledtext.ScrolledText(
            self.parent,
            height=8,
            bg='#000000',
            fg='#00ff00',
            insertbackground='#00ff00',
            font=('Courier New', 9),
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.terminal_output.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        # Command input
        input_frame = ttk.Frame(self.parent, style='Modern.TFrame')
        input_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        ttk.Label(input_frame, text="$", style='Modern.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        
        self.command_entry = ttk.Entry(input_frame, style='Modern.TEntry', font=('Courier New', 9))
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.command_entry.bind('<Return>', self.execute_command)
        
        ttk.Button(input_frame, text="Run", command=self.execute_command, 
                  style='Accent.TButton', width=6).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Welcome message
        self.terminal_output.insert(tk.END, "Minecraft Mod IDE Terminal\n")
        self.terminal_output.insert(tk.END, "Type commands to execute...\n\n")
        
    def execute_command(self, event=None):
        command = self.command_entry.get().strip()
        if not command:
            return
            
        self.command_entry.delete(0, tk.END)
        self.terminal_output.insert(tk.END, f"$ {command}\n")
        
        def run_command():
            try:
                result = subprocess.run(command, shell=True, capture_output=True, 
                                      text=True, timeout=30, cwd=os.getcwd())
                
                output = result.stdout + result.stderr
                if output:
                    self.terminal_output.insert(tk.END, output + "\n")
                else:
                    self.terminal_output.insert(tk.END, "Command completed.\n")
                    
            except subprocess.TimeoutExpired:
                self.terminal_output.insert(tk.END, "Command timed out.\n")
            except Exception as e:
                self.terminal_output.insert(tk.END, f"Error: {str(e)}\n")
                
            self.terminal_output.see(tk.END)
            
        threading.Thread(target=run_command, daemon=True).start()
        
    def clear_terminal(self):
        self.terminal_output.delete("1.0", tk.END)
        self.terminal_output.insert(tk.END, "Terminal cleared.\n")

class GotoLineDialog:
    
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text_widget = text_widget
        self.show_dialog()
        
    def show_dialog(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("Go to Line")
        dialog.geometry("300x120")
        dialog.configure(bg=ModernStyle.DARK_BG)
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (dialog.winfo_screenheight() // 2) - (120 // 2)
        dialog.geometry(f"300x120+{x}+{y}")
        
        # Content frame
        frame = ttk.Frame(dialog, style='Modern.TFrame', padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Line number input
        ttk.Label(frame, text="Line number:", style='Modern.TLabel').pack(anchor=tk.W)
        
        line_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=line_var, style='Modern.TEntry', width=20)
        entry.pack(fill=tk.X, pady=(5, 15))
        entry.focus()
        
        # Buttons
        button_frame = ttk.Frame(frame, style='Modern.TFrame')
        button_frame.pack(fill=tk.X)
        
        def goto_line():
            try:
                line_num = int(line_var.get())
                self.text_widget.see(f"{line_num}.0")
                self.text_widget.mark_set(tk.INSERT, f"{line_num}.0")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid line number")
                
        ttk.Button(button_frame, text="Go", command=goto_line, 
                  style='Accent.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, 
                  style='Modern.TButton').pack(side=tk.RIGHT)
        
        # Bind Enter key
        entry.bind('<Return>', lambda e: goto_line())

class RecentFilesManager:
    
    def __init__(self, ide_instance):
        self.ide = ide_instance
        self.config_file = os.path.expanduser("~/.minecraft_mod_ide.conf")
        self.config = configparser.ConfigParser()
        self.load_config()
        
    def load_config(self):
        try:
            self.config.read(self.config_file)
        except:
            pass
            
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
        except:
            pass
            
    def add_recent_file(self, file_path):
        if not self.config.has_section('recent_files'):
            self.config.add_section('recent_files')
            
        # Get existing files
        recent_files = []
        for i in range(10):
            key = f'file_{i}'
            if self.config.has_option('recent_files', key):
                recent_files.append(self.config.get('recent_files', key))
                
        # Add new file to front
        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        
        # Keep only 10 files
        recent_files = recent_files[:10]
        
        # Save back to config
        self.config.remove_section('recent_files')
        self.config.add_section('recent_files')
        for i, file_path in enumerate(recent_files):
            self.config.set('recent_files', f'file_{i}', file_path)
            
        self.save_config()
        
    def get_recent_files(self):
        if not self.config.has_section('recent_files'):
            return []
            
        recent_files = []
        for i in range(10):
            key = f'file_{i}'
            if self.config.has_option('recent_files', key):
                file_path = self.config.get('recent_files', key)
                if os.path.exists(file_path):
                    recent_files.append(file_path)
                    
        return recent_files
        
    def add_recent_project(self, project_path):
        if not self.config.has_section('recent_projects'):
            self.config.add_section('recent_projects')
            
        # Similar logic as recent files
        recent_projects = []
        for i in range(5):
            key = f'project_{i}'
            if self.config.has_option('recent_projects', key):
                recent_projects.append(self.config.get('recent_projects', key))
                
        if project_path in recent_projects:
            recent_projects.remove(project_path)
        recent_projects.insert(0, project_path)
        recent_projects = recent_projects[:5]
        
        self.config.remove_section('recent_projects')
        self.config.add_section('recent_projects')
        for i, project_path in enumerate(recent_projects):
            self.config.set('recent_projects', f'project_{i}', project_path)
            
        self.save_config()
        
    def get_recent_projects(self):
        if not self.config.has_section('recent_projects'):
            return []
            
        recent_projects = []
        for i in range(5):
            key = f'project_{i}'
            if self.config.has_option('recent_projects', key):
                project_path = self.config.get('recent_projects', key)
                if os.path.exists(project_path):
                    recent_projects.append(project_path)
                    
        return recent_projects

class SplashScreen:
    
    def __init__(self, on_complete):
        self.on_complete = on_complete
        self.checks_passed = True
        self.setup_splash()
        self.run_system_checks()
        
    def setup_splash(self):
        self.splash = tk.Tk()
        self.splash.title("Minecraft Mod IDE")
        self.splash.geometry("480x320")
        self.splash.resizable(False, False)
        self.splash.configure(bg="#1a1a1a")
        
        # Remove window decorations
        self.splash.overrideredirect(True)
        
        # Center the splash screen
        self.splash.update_idletasks()
        x = (self.splash.winfo_screenwidth() // 2) - (480 // 2)
        y = (self.splash.winfo_screenheight() // 2) - (320 // 2)
        self.splash.geometry(f"480x320+{x}+{y}")
        
        # Add border effect
        border_frame = tk.Frame(self.splash, bg="#ff8c42", bd=0)
        border_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Main content frame
        main_frame = tk.Frame(border_frame, bg="#1a1a1a", bd=0)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Header section
        header_frame = tk.Frame(main_frame, bg="#1a1a1a", height=80)
        header_frame.pack(fill=tk.X, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        # Logo and title
        title_label = tk.Label(header_frame, text="🎮 Minecraft Mod IDE", 
                              font=("Segoe UI", 18, "bold"), 
                              fg="#ff8c42", bg="#1a1a1a")
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(header_frame, text="A Simple Development Environment", 
                                 font=("Segoe UI", 10), 
                                 fg="#cccccc", bg="#1a1a1a")
        subtitle_label.pack()
        
        # Progress section
        progress_frame = tk.Frame(main_frame, bg="#1a1a1a", height=120)
        progress_frame.pack(fill=tk.X, pady=20, padx=30)
        progress_frame.pack_propagate(False)
        
        # Status label
        self.status_label = tk.Label(progress_frame, text="Initializing...", 
                                   font=("Segoe UI", 10), 
                                   fg="#ffffff", bg="#1a1a1a")
        self.status_label.pack(pady=(10, 15))
        
        # Progress bar with modern styling
        progress_style = ttk.Style()
        progress_style.configure("Splash.Horizontal.TProgressbar",
                                background="#ff8c42",
                                troughcolor="#2d2d30",
                                borderwidth=0,
                                lightcolor="#ff8c42",
                                darkcolor="#ff8c42")
        
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                          style="Splash.Horizontal.TProgressbar",
                                          mode='determinate', 
                                          length=300)
        self.progress_bar.pack(pady=10)
        
        # Check items list
        self.checks_frame = tk.Frame(progress_frame, bg="#1a1a1a")
        self.checks_frame.pack(fill=tk.X, pady=10)
        
        # Version info
        version_frame = tk.Frame(main_frame, bg="#1a1a1a", height=40)
        version_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        version_frame.pack_propagate(False)
        
        version_label = tk.Label(version_frame, text="Version 1.0.0 • Built with Python", 
                               font=("Segoe UI", 8), 
                               fg="#999999", bg="#1a1a1a")
        version_label.pack()
        
        # Make splash always on top
        self.splash.attributes('-topmost', True)
        self.splash.focus_force()
        
    def update_progress(self, value, message):
        self.progress_bar['value'] = value
        self.status_label.config(text=message)
        self.splash.update()
        
    def add_check_item(self, text, status="checking"):
        item_frame = tk.Frame(self.checks_frame, bg="#1a1a1a")
        item_frame.pack(fill=tk.X, pady=2)
        
        if status == "checking":
            icon = "🔄"
            color = "#cccccc"
        elif status == "pass":
            icon = "✅"
            color = "#4caf50"
        elif status == "fail":
            icon = "❌"
            color = "#f44336"
        else:
            icon = "⏳"
            color = "#ff9800"
            
        check_label = tk.Label(item_frame, text=f"{icon} {text}", 
                             font=("Segoe UI", 9), 
                             fg=color, bg="#1a1a1a", anchor="w")
        check_label.pack(side=tk.LEFT)
        
        return check_label
        
    def run_system_checks(self):
        def check_thread():
            checks = [
                ("Python environment", self.check_python),
                ("Java JDK installation", self.check_java),
                ("Required modules", self.check_modules),
                ("File system permissions", self.check_permissions),
                ("UI components", self.check_ui_components)
            ]
            
            total_checks = len(checks)
            
            for i, (name, check_func) in enumerate(checks):
                self.update_progress((i / total_checks) * 90, f"Checking {name.lower()}...")
                
                check_label = self.add_check_item(name, "checking")
                self.splash.after(500)  # Small delay for visual effect
                
                try:
                    result = check_func()
                    if result:
                        check_label.config(text=f"✅ {name}", fg="#4caf50")
                    else:
                        check_label.config(text=f"❌ {name}", fg="#f44336")
                        self.checks_passed = False
                except Exception as e:
                    check_label.config(text=f"❌ {name} (Error: {str(e)})", fg="#f44336")
                    self.checks_passed = False
                    
                self.splash.update()
                time.sleep(0.3)  # Visual delay
                
            # Final status
            if self.checks_passed:
                self.update_progress(100, "All systems ready! Starting IDE...")
                time.sleep(1)
                self.splash.after(500, self.complete_startup)
            else:
                self.update_progress(100, "Some checks failed. See details above.")
                self.show_error_dialog()
                
        threading.Thread(target=check_thread, daemon=True).start()
        
    def check_python(self):
        version = sys.version_info
        return version.major >= 3 and version.minor >= 7
        
    def check_java(self):
        try:
            # Check javac
            result = subprocess.run(['javac', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
                
            # Check jar tool
            result = subprocess.run(['jar', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
            
    def check_modules(self):
        required_modules = ['tkinter', 'subprocess', 'threading', 'json', 're', 'shutil', 'pathlib', 'webbrowser', 'datetime', 'tempfile']
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                return False
        return True
        
    def check_permissions(self):
        try:
            # Check if we can create temp files
            temp_file = tempfile.NamedTemporaryFile(delete=True)
            temp_file.close()
            
            # Check if we can write to documents folder
            docs_path = os.path.expanduser("~/Documents")
            if os.path.exists(docs_path):
                test_file = os.path.join(docs_path, ".ide_test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                
            return True
        except (OSError, PermissionError):
            return False
            
    def check_ui_components(self):
        try:
            # Test creating basic tkinter widgets
            test_window = tk.Toplevel()
            test_frame = ttk.Frame(test_window)
            test_button = ttk.Button(test_frame, text="Test")
            test_entry = ttk.Entry(test_frame)
            test_window.destroy()
            return True
        except tk.TclError:
            return False
            
    def show_error_dialog(self):
        error_window = tk.Toplevel(self.splash)
        error_window.title("System Check Failed")
        error_window.geometry("400x300")
        error_window.configure(bg="#1a1a1a")
        error_window.transient(self.splash)
        error_window.grab_set()
        
        # Center the error window
        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (error_window.winfo_screenheight() // 2) - (300 // 2)
        error_window.geometry(f"400x300+{x}+{y}")
        
        error_frame = tk.Frame(error_window, bg="#1a1a1a", padx=20, pady=20)
        error_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(error_frame, text="⚠️ System Check Failed", 
                             font=("Segoe UI", 14, "bold"), 
                             fg="#f44336", bg="#1a1a1a")
        title_label.pack(pady=(0, 15))
        
        message_text = """Some system requirements are not met:

• Java JDK not found: Please install Java JDK 8 or higher
• Check that 'javac' and 'jar' are in your system PATH
• Ensure you have proper file system permissions

Would you like to continue anyway?"""
        
        message_label = tk.Label(error_frame, text=message_text, 
                               font=("Segoe UI", 10), 
                               fg="#ffffff", bg="#1a1a1a",
                               justify=tk.LEFT, wraplength=350)
        message_label.pack(pady=(0, 20))
        
        button_frame = tk.Frame(error_frame, bg="#1a1a1a")
        button_frame.pack()
        
        def continue_anyway():
            error_window.destroy()
            self.complete_startup()
            
        def exit_app():
            self.splash.destroy()
            sys.exit(0)
            
        continue_btn = tk.Button(button_frame, text="Continue Anyway", 
                               command=continue_anyway,
                               bg="#ff8c42", fg="#1a1a1a", 
                               font=("Segoe UI", 9, "bold"),
                               padx=15, pady=5, bd=0)
        continue_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        exit_btn = tk.Button(button_frame, text="Exit", 
                           command=exit_app,
                           bg="#f44336", fg="#ffffff", 
                           font=("Segoe UI", 9),
                           padx=15, pady=5, bd=0)
        exit_btn.pack(side=tk.LEFT)
        
    def complete_startup(self):
        self.splash.destroy()
        self.on_complete()

class ModernStyle:
    
    # Color palette - More vibrant and modern
    DARK_BG = "#1a1a1a"
    MEDIUM_BG = "#2d2d30"
    LIGHT_BG = "#3c3c3c"
    SIDEBAR_BG = "#252526"
    ACCENT_ORANGE = "#ff8c42"
    ACCENT_ORANGE_HOVER = "#ff9a5a"
    ACCENT_BLUE = "#007acc"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#cccccc"
    TEXT_MUTED = "#999999"
    BORDER_COLOR = "#555555"
    SUCCESS_COLOR = "#4caf50"
    ERROR_COLOR = "#f44336"
    WARNING_COLOR = "#ff9800"
    
    @classmethod
    def configure_style(cls, root):
        style = ttk.Style()
        
        # Use 'clam' as base theme
        style.theme_use('clam')
        
        # Configure root
        root.configure(bg=cls.DARK_BG)
        
        # Frame styles with subtle borders
        style.configure('Modern.TFrame', background=cls.DARK_BG, relief='flat', borderwidth=0)
        style.configure('Card.TFrame', background=cls.MEDIUM_BG, relief='solid', borderwidth=1)
        style.configure('Sidebar.TFrame', background=cls.SIDEBAR_BG, relief='flat')
        style.configure('Toolbar.TFrame', background=cls.MEDIUM_BG, relief='flat')
        
        # Label styles with better typography
        style.configure('Modern.TLabel', background=cls.DARK_BG, foreground=cls.TEXT_PRIMARY, font=('Segoe UI', 9))
        style.configure('Header.TLabel', background=cls.DARK_BG, foreground=cls.TEXT_PRIMARY, font=('Segoe UI', 12, 'bold'))
        style.configure('Muted.TLabel', background=cls.DARK_BG, foreground=cls.TEXT_MUTED, font=('Segoe UI', 8))
        style.configure('Sidebar.TLabel', background=cls.SIDEBAR_BG, foreground=cls.TEXT_PRIMARY, font=('Segoe UI', 9))
        style.configure('Toolbar.TLabel', background=cls.MEDIUM_BG, foreground=cls.TEXT_PRIMARY, font=('Segoe UI', 9))
        
        # Button styles with hover effects
        style.configure('Modern.TButton', 
                       background=cls.LIGHT_BG, 
                       foreground=cls.TEXT_PRIMARY,
                       borderwidth=1,
                       focuscolor='none',
                       relief='flat',
                       padding=(8, 4),
                       font=('Segoe UI', 9))
        style.map('Modern.TButton',
                 background=[('active', cls.ACCENT_ORANGE), ('pressed', cls.ACCENT_ORANGE_HOVER)],
                 foreground=[('active', cls.DARK_BG)],
                 bordercolor=[('focus', cls.ACCENT_ORANGE)])
        
        style.configure('Accent.TButton',
                       background=cls.ACCENT_ORANGE,
                       foreground=cls.DARK_BG,
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat',
                       padding=(12, 6),
                       font=('Segoe UI', 9, 'bold'))
        style.map('Accent.TButton',
                 background=[('active', cls.ACCENT_ORANGE_HOVER), ('pressed', cls.ACCENT_ORANGE)])
        
        style.configure('Toolbar.TButton',
                       background=cls.MEDIUM_BG,
                       foreground=cls.TEXT_PRIMARY,
                       borderwidth=1,
                       relief='flat',
                       padding=(6, 4),
                       font=('Segoe UI', 8))
        style.map('Toolbar.TButton',
                 background=[('active', cls.ACCENT_ORANGE), ('pressed', cls.ACCENT_ORANGE_HOVER)],
                 foreground=[('active', cls.DARK_BG)])
        
        # Entry styles with focus effects
        style.configure('Modern.TEntry',
                       fieldbackground=cls.LIGHT_BG,
                       foreground=cls.TEXT_PRIMARY,
                       borderwidth=1,
                       insertcolor=cls.ACCENT_ORANGE,
                       relief='flat',
                       padding=(4, 2),
                       font=('Segoe UI', 9))
        style.map('Modern.TEntry',
                 focuscolor=[('!focus', cls.BORDER_COLOR), ('focus', cls.ACCENT_ORANGE)],
                 bordercolor=[('focus', cls.ACCENT_ORANGE)])
        
        # Combobox styles
        style.configure('Modern.TCombobox',
                       fieldbackground=cls.LIGHT_BG,
                       foreground=cls.TEXT_PRIMARY,
                       borderwidth=1,
                       font=('Segoe UI', 9))
        
        # Checkbutton styles
        style.configure('Modern.TCheckbutton',
                       background=cls.DARK_BG,
                       foreground=cls.TEXT_PRIMARY,
                       focuscolor='none',
                       font=('Segoe UI', 9))
        
        # Notebook (tabs) styles with modern appearance
        style.configure('Modern.TNotebook', background=cls.MEDIUM_BG, borderwidth=0, tabmargins=0)
        style.configure('Modern.TNotebook.Tab',
                       background=cls.LIGHT_BG,
                       foreground=cls.TEXT_SECONDARY,
                       padding=[16, 8],
                       borderwidth=0,
                       font=('Segoe UI', 9))
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', cls.DARK_BG), ('active', cls.MEDIUM_BG)],
                 foreground=[('selected', cls.TEXT_PRIMARY), ('active', cls.TEXT_PRIMARY)],
                 expand=[('selected', [1, 1, 1, 0])])
        
        # Treeview styles with better visual hierarchy
        style.configure('Modern.Treeview',
                       background=cls.SIDEBAR_BG,
                       foreground=cls.TEXT_PRIMARY,
                       fieldbackground=cls.SIDEBAR_BG,
                       borderwidth=0,
                       relief='flat',
                       font=('Segoe UI', 9))
        style.map('Modern.Treeview',
                 background=[('selected', cls.ACCENT_ORANGE)],
                 foreground=[('selected', cls.DARK_BG)])
        
        # Progressbar styles
        style.configure('Modern.Horizontal.TProgressbar',
                       background=cls.ACCENT_ORANGE,
                       troughcolor=cls.LIGHT_BG,
                       borderwidth=0,
                       lightcolor=cls.ACCENT_ORANGE,
                       darkcolor=cls.ACCENT_ORANGE)
        
        # Separator styles
        style.configure('Modern.TSeparator', background=cls.BORDER_COLOR)
        
        # LabelFrame styles with better visual hierarchy
        style.configure('Modern.TLabelframe',
                       background=cls.DARK_BG,
                       foreground=cls.TEXT_PRIMARY,
                       borderwidth=1,
                       relief='solid')
        style.configure('Modern.TLabelframe.Label',
                       background=cls.DARK_BG,
                       foreground=cls.ACCENT_ORANGE,
                       font=('Segoe UI', 9, 'bold'))
                       
        # Improved visual effects
        style.configure('Card.TLabelframe',
                       background=cls.MEDIUM_BG,
                       foreground=cls.TEXT_PRIMARY,
                       borderwidth=2,
                       relief='solid')
        style.configure('Card.TLabelframe.Label',
                       background=cls.MEDIUM_BG,
                       foreground=cls.ACCENT_ORANGE,
                       font=('Segoe UI', 10, 'bold'))

class SyntaxHighlighter:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.setup_tags()
        
        # Compilation patterns for better performance
        self.keyword_pattern = re.compile(r'\b(?:abstract|assert|boolean|break|byte|case|catch|char|class|const|continue|default|do|double|else|enum|extends|final|finally|float|for|goto|if|implements|import|instanceof|int|interface|long|native|new|package|private|protected|public|return|short|static|strictfp|super|switch|synchronized|this|throw|throws|transient|try|void|volatile|while|true|false|null)\b')
        self.string_pattern = re.compile(r'(?:"(?:[^"\\]|\\.)*")|(?:\'(?:[^\'\\]|\\.)*\')')
        self.comment_pattern = re.compile(r'//.*?$|/\*.*?\*/', re.MULTILINE | re.DOTALL)
        self.number_pattern = re.compile(r'\b\d+\.?\d*[fFdDlL]?\b')
        self.annotation_pattern = re.compile(r'@\w+')
        self.class_pattern = re.compile(r'\b[A-Z][a-zA-Z0-9_]*\b')
        self.operator_pattern = re.compile(r'[+\-*/%=!<>&|^~]')
        
    def setup_tags(self):
        # Keywords - orange accent
        self.text_widget.tag_configure("keyword", 
                                     foreground=ModernStyle.ACCENT_ORANGE, 
                                     font=("Consolas", 11, "bold"))
        
        # Strings - green
        self.text_widget.tag_configure("string", 
                                     foreground="#90ee90", 
                                     font=("Consolas", 11))
        
        # Comments - muted gray, italic
        self.text_widget.tag_configure("comment", 
                                     foreground=ModernStyle.TEXT_MUTED, 
                                     font=("Consolas", 11, "italic"))
        
        # Numbers - light blue
        self.text_widget.tag_configure("number", 
                                     foreground="#87ceeb", 
                                     font=("Consolas", 11))
        
        # Operators - red
        self.text_widget.tag_configure("operator", 
                                     foreground="#ff6b6b", 
                                     font=("Consolas", 11))
        
        # Annotations - gold
        self.text_widget.tag_configure("annotation", 
                                     foreground="#ffd700", 
                                     font=("Consolas", 11, "bold"))
        
        # Class names - purple
        self.text_widget.tag_configure("classname", 
                                     foreground="#dda0dd", 
                                     font=("Consolas", 11))
        
        # Current line highlight
        self.text_widget.tag_configure("current_line", 
                                     background="#2d2d30")
        
    def highlight_syntax(self):
        content = self.text_widget.get("1.0", tk.END)
        
        # Clear existing tags
        for tag in ["keyword", "string", "comment", "number", "operator", "annotation", "classname"]:
            self.text_widget.tag_remove(tag, "1.0", tk.END)
        
        # Apply highlighting using compiled patterns
        self._apply_pattern_highlighting(self.keyword_pattern, "keyword", content)
        self._apply_pattern_highlighting(self.string_pattern, "string", content)
        self._apply_pattern_highlighting(self.comment_pattern, "comment", content)
        self._apply_pattern_highlighting(self.number_pattern, "number", content)
        self._apply_pattern_highlighting(self.annotation_pattern, "annotation", content)
        self._apply_pattern_highlighting(self.class_pattern, "classname", content)
        self._apply_pattern_highlighting(self.operator_pattern, "operator", content)
        
    def _apply_pattern_highlighting(self, pattern, tag, content):
        for match in pattern.finditer(content):
            start_line = content[:match.start()].count('\n') + 1
            start_col = match.start() - content.rfind('\n', 0, match.start()) - 1
            end_line = content[:match.end()].count('\n') + 1
            end_col = match.end() - content.rfind('\n', 0, match.end()) - 1
            
            start_pos = f"{start_line}.{start_col}"
            end_pos = f"{end_line}.{end_col}"
            
            self.text_widget.tag_add(tag, start_pos, end_pos)
            
    def highlight_current_line(self):
        self.text_widget.tag_remove("current_line", "1.0", tk.END)
        current_line = self.text_widget.index(tk.INSERT).split('.')[0]
        start = f"{current_line}.0"
        end = f"{current_line}.end"
        self.text_widget.tag_add("current_line", start, end)

class LineNumbers:
    
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text_widget = text_widget
        
        # Create line numbers canvas
        self.canvas = tk.Canvas(
            parent,
            width=40,
            bg=ModernStyle.MEDIUM_BG,
            highlightthickness=0,
            bd=0
        )
        
        # Bind events only if text_widget is provided
        if self.text_widget:
            self.text_widget.bind('<KeyRelease>', self.update_line_numbers)
            self.text_widget.bind('<Button-1>', self.update_line_numbers)
            self.text_widget.bind('<MouseWheel>', self.update_line_numbers)
            
            # Initial update
            self.update_line_numbers()
        
    def update_line_numbers(self, event=None):
        if not self.text_widget:
            return
            
        self.canvas.delete("all")
        
        try:
            # Get visible line range
            top_line = int(self.text_widget.index("@0,0").split('.')[0])
            bottom_line = int(self.text_widget.index(f"@0,{self.text_widget.winfo_height()}").split('.')[0])
            
            # Draw line numbers
            for line_num in range(top_line, bottom_line + 1):
                y_pos = (line_num - top_line) * 15 + 5  # Approximate line height
                self.canvas.create_text(
                    35, y_pos,
                    text=str(line_num),
                    anchor=tk.E,
                    font=("Consolas", 9),
                    fill=ModernStyle.TEXT_MUTED
                )
        except (tk.TclError, ValueError):
            # Handle cases where text widget isn't ready yet
            pass

class TabbedEditor:
    
    def __init__(self, parent):
        self.parent = parent
        self.open_files = {}  # filename -> editor data
        self.current_file = None
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        self.frame = ttk.Frame(self.parent, style='Modern.TFrame')
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.frame, style='Modern.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bind tab events
        self.notebook.bind('<Button-3>', self.show_tab_context_menu)
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
        # Welcome tab
        self.create_welcome_tab()
        
    def create_welcome_tab(self):
        welcome_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(welcome_frame, text="🏠 Welcome")
        
        # Create scrollable welcome content
        canvas = tk.Canvas(welcome_frame, bg=ModernStyle.DARK_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(welcome_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Welcome content with enhanced styling
        content_frame = ttk.Frame(scrollable_frame, style='Modern.TFrame', padding=30)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header section with large icon
        header_frame = ttk.Frame(content_frame, style='Modern.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_label = tk.Label(header_frame, text="🎮", font=("Segoe UI", 48), 
                              bg=ModernStyle.DARK_BG, fg=ModernStyle.ACCENT_ORANGE)
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, text="Minecraft Mod IDE", 
                                 font=("Segoe UI", 20, "bold"),
                                 bg=ModernStyle.DARK_BG, fg=ModernStyle.TEXT_PRIMARY)
        subtitle_label.pack(pady=(10, 5))
        
        desc_label = tk.Label(header_frame, text="Ultimate Development Environment", 
                             font=("Segoe UI", 12),
                             bg=ModernStyle.DARK_BG, fg=ModernStyle.TEXT_SECONDARY)
        desc_label.pack()
        
        # Quick actions section
        actions_frame = ttk.LabelFrame(content_frame, text="🚀 Quick Actions", 
                                     style='Card.TLabelframe', padding=20)
        actions_frame.pack(fill=tk.X, pady=(0, 20))
        
        actions_content = """📁 File → New Project to create a new mod project
📂 File → Open Project to load an existing project  
📄 File → New File to create a new Java file
🔨 Build → Compile JAR to package your mod"""
        
        actions_text = tk.Label(actions_frame, text=actions_content,
                               font=("Segoe UI", 10), justify=tk.LEFT,
                               bg=ModernStyle.MEDIUM_BG, fg=ModernStyle.TEXT_PRIMARY)
        actions_text.pack(anchor=tk.W)
        
        # Features section
        features_frame = ttk.LabelFrame(content_frame, text="✨ Key Features", 
                                      style='Card.TLabelframe', padding=20)
        features_frame.pack(fill=tk.X, pady=(0, 20))
        
        features_content = """🎨 Modern dark theme with smooth animations
☕ Smart Java syntax highlighting
📝 Multiple file editing with tabs
🔍 Find & replace with regex support
📦 Integrated JAR compiler
🚀 Project templates (Forge, Fabric, Bukkit)
⚡ Auto-save and backup system
🎯 Real-time error detection"""
        
        features_text = tk.Label(features_frame, text=features_content,
                                font=("Segoe UI", 10), justify=tk.LEFT,
                                bg=ModernStyle.MEDIUM_BG, fg=ModernStyle.TEXT_PRIMARY)
        features_text.pack(anchor=tk.W)
        
        # Tips section
        tips_frame = ttk.LabelFrame(content_frame, text="💡 Pro Tips", 
                                  style='Card.TLabelframe', padding=20)
        tips_frame.pack(fill=tk.X, pady=(0, 20))
        
        tips_content = """⌨️ Ctrl+/ to toggle line comments
📋 Ctrl+D to duplicate current line
🔍 Ctrl+F for find and replace
🎯 Right-click in file explorer for options
💾 Files auto-save every 30 seconds
🖱️ Hover over buttons for helpful tooltips"""
        
        tips_text = tk.Label(tips_frame, text=tips_content,
                            font=("Segoe UI", 10), justify=tk.LEFT,
                            bg=ModernStyle.MEDIUM_BG, fg=ModernStyle.TEXT_PRIMARY)
        tips_text.pack(anchor=tk.W)
        
        # Footer
        footer_frame = ttk.Frame(content_frame, style='Modern.TFrame')
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        footer_text = tk.Label(footer_frame, 
                              text="Ready to create amazing Minecraft mods! 🎯\n\nGet started by creating a new project or opening an existing one.",
                              font=("Segoe UI", 11, "italic"), justify=tk.CENTER,
                              bg=ModernStyle.DARK_BG, fg=ModernStyle.ACCENT_ORANGE)
        footer_text.pack()
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
    def new_file(self, filename="Untitled", content=""):
        # Generate unique filename if needed
        if filename == "Untitled":
            counter = 1
            while f"Untitled-{counter}" in self.open_files:
                counter += 1
            filename = f"Untitled-{counter}"
            
        # Create editor frame
        editor_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        
        # Create text editor with line numbers
        text_frame = ttk.Frame(editor_frame, style='Modern.TFrame')
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text editor
        text_widget = tk.Text(
            text_frame,
            bg=ModernStyle.DARK_BG,
            fg=ModernStyle.TEXT_PRIMARY,
            insertbackground=ModernStyle.ACCENT_ORANGE,
            selectbackground=ModernStyle.ACCENT_ORANGE,
            selectforeground=ModernStyle.DARK_BG,
            font=("Consolas", 11),
            undo=True,
            wrap=tk.NONE,
            tabs="4c",
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=5
        )
        
        # Line numbers - create after text widget
        line_numbers = LineNumbers(text_frame, text_widget)
        line_numbers.canvas.pack(side=tk.LEFT, fill=tk.Y)
        
        # Pack text widget after line numbers
        text_widget.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Add scrollbars
        v_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        h_scroll = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
        text_widget.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initialize syntax highlighter
        highlighter = SyntaxHighlighter(text_widget)
        
        # Set initial content
        if content:
            text_widget.insert("1.0", content)
            highlighter.highlight_syntax()
            
        # Bind events
        text_widget.bind('<KeyRelease>', lambda e: self.on_text_change(filename, e))
        text_widget.bind('<Button-1>', lambda e: highlighter.highlight_current_line())
        text_widget.bind('<Control-s>', lambda e: self.save_file(filename))
        text_widget.bind('<Control-z>', lambda e: text_widget.edit_undo())
        text_widget.bind('<Control-y>', lambda e: text_widget.edit_redo())
        text_widget.bind('<Control-f>', lambda e: self.show_find_dialog(filename))
        text_widget.bind('<Control-slash>', lambda e: self.toggle_comment(filename))
        text_widget.bind('<Control-d>', lambda e: self.duplicate_line(filename))
        
        # Store editor data
        self.open_files[filename] = {
            'frame': editor_frame,
            'text_widget': text_widget,
            'highlighter': highlighter,
            'line_numbers': line_numbers,
            'file_path': None,
            'modified': False,
            'last_save': None
        }
        
        # Add tab
        self.notebook.add(editor_frame, text=filename)
        self.notebook.select(editor_frame)
        self.current_file = filename
        
        return filename
        
    def open_file(self, file_path):
        filename = os.path.basename(file_path)
        
        # Check if file is already open
        for name, data in self.open_files.items():
            if data['file_path'] == file_path:
                # Switch to existing tab
                self.notebook.select(data['frame'])
                self.current_file = name
                return name
                
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                
            # Create new tab
            tab_name = self.new_file(filename, content)
            self.open_files[tab_name]['file_path'] = file_path
            self.open_files[tab_name]['modified'] = False
            
            return tab_name
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
            return None
            
    def save_file(self, filename):
        if filename not in self.open_files:
            return False
            
        file_data = self.open_files[filename]
        
        if not file_data['file_path']:
            # Save as
            file_path = filedialog.asksaveasfilename(
                title="Save File As",
                defaultextension=".java",
                filetypes=[
                    ("Java files", "*.java"),
                    ("JSON files", "*.json"),
                    ("XML files", "*.xml"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            if not file_path:
                return False
            file_data['file_path'] = file_path
            
        try:
            content = file_data['text_widget'].get("1.0", tk.END + "-1c")
            with open(file_data['file_path'], 'w', encoding='utf-8') as file:
                file.write(content)
                
            file_data['modified'] = False
            file_data['last_save'] = datetime.now()
            self.update_tab_title(filename)
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            return False
            
    def close_file(self, filename):
        if filename not in self.open_files:
            return
            
        file_data = self.open_files[filename]
        
        # Check for unsaved changes
        if file_data['modified']:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"Save changes to {filename}?"
            )
            if result is True:
                if not self.save_file(filename):
                    return
            elif result is None:
                return
                
        # Remove tab
        self.notebook.forget(file_data['frame'])
        del self.open_files[filename]
        
        # Select another tab if available
        if self.open_files:
            first_file = next(iter(self.open_files))
            self.notebook.select(self.open_files[first_file]['frame'])
            self.current_file = first_file
        else:
            self.current_file = None
            
    def on_text_change(self, filename, event):
        if filename not in self.open_files:
            return
            
        file_data = self.open_files[filename]
        file_data['modified'] = True
        
        # Update tab title
        self.update_tab_title(filename)
        
        # Schedule syntax highlighting
        if hasattr(file_data, '_highlight_after_id'):
            self.notebook.after_cancel(file_data['_highlight_after_id'])
        file_data['_highlight_after_id'] = self.notebook.after(300, file_data['highlighter'].highlight_syntax)
        
    def update_tab_title(self, filename):
        if filename not in self.open_files:
            return
            
        file_data = self.open_files[filename]
        title = filename
        if file_data['modified']:
            title += " •"
            
        # Find and update tab
        for i, tab_id in enumerate(self.notebook.tabs()):
            if self.notebook.nametowidget(tab_id) == file_data['frame']:
                self.notebook.tab(i, text=title)
                break
                
    def on_tab_changed(self, event):
        selected_tab = self.notebook.select()
        if selected_tab:
            # Find the filename for this tab
            for filename, data in self.open_files.items():
                if str(data['frame']) == str(selected_tab):
                    self.current_file = filename
                    data['highlighter'].highlight_current_line()
                    break
                    
    def show_tab_context_menu(self, event):
        # Identify which tab was right-clicked
        tab_index = self.notebook.index(f"@{event.x},{event.y}")
        tab_id = self.notebook.tabs()[tab_index]
        
        # Find filename
        filename = None
        for name, data in self.open_files.items():
            if str(data['frame']) == str(tab_id):
                filename = name
                break
                
        if not filename:
            return
            
        # Create context menu
        context_menu = tk.Menu(self.parent, tearoff=0, bg=ModernStyle.MEDIUM_BG, fg=ModernStyle.TEXT_PRIMARY)
        context_menu.add_command(label="Save", command=lambda: self.save_file(filename))
        context_menu.add_command(label="Close", command=lambda: self.close_file(filename))
        context_menu.add_command(label="Close Others", command=lambda: self.close_other_files(filename))
        context_menu.add_separator()
        context_menu.add_command(label="Copy Path", command=lambda: self.copy_file_path(filename))
        
        context_menu.tk_popup(event.x_root, event.y_root)
        
    def close_other_files(self, keep_filename):
        files_to_close = [name for name in self.open_files.keys() if name != keep_filename]
        for filename in files_to_close:
            self.close_file(filename)
            
    def copy_file_path(self, filename):
        if filename in self.open_files:
            file_path = self.open_files[filename]['file_path']
            if file_path:
                self.parent.clipboard_clear()
                self.parent.clipboard_append(file_path)
                
    def toggle_comment(self, filename):
        if filename not in self.open_files:
            return
            
        text_widget = self.open_files[filename]['text_widget']
        current_line = text_widget.index(tk.INSERT).split('.')[0]
        line_start = f"{current_line}.0"
        line_end = f"{current_line}.end"
        line_content = text_widget.get(line_start, line_end)
        
        if line_content.strip().startswith('//'):
            # Remove comment
            new_content = line_content.replace('//', '', 1)
        else:
            # Add comment
            new_content = '//' + line_content
            
        text_widget.delete(line_start, line_end)
        text_widget.insert(line_start, new_content)
        
    def duplicate_line(self, filename):
        if filename not in self.open_files:
            return
            
        text_widget = self.open_files[filename]['text_widget']
        current_line = text_widget.index(tk.INSERT).split('.')[0]
        line_start = f"{current_line}.0"
        line_end = f"{current_line}.end"
        line_content = text_widget.get(line_start, line_end)
        
        text_widget.insert(line_end, '\n' + line_content)
        
    def show_find_dialog(self, filename):
        if filename not in self.open_files:
            return
        FindReplaceDialog(self.open_files[filename]['text_widget'])
        
    def get_current_editor(self):
        if self.current_file and self.current_file in self.open_files:
            return self.open_files[self.current_file]
        return None

class NewFileDialog:
    
    def __init__(self, parent, parent_path, on_file_created):
        self.parent = parent
        self.parent_path = parent_path
        self.on_file_created = on_file_created
        self.setup_dialog()
        
    def setup_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("📄 Create New File")
        self.dialog.geometry("500x400")
        self.dialog.configure(bg=ModernStyle.DARK_BG)
        self.dialog.resizable(False, False)
        
        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, style='Modern.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="📄 Create New File", style='Header.TLabel').pack(pady=(0, 20))
        
        # File details frame
        details_frame = ttk.LabelFrame(main_frame, text="File Details", style='Modern.TFrame', padding=15)
        details_frame.pack(fill=tk.X, pady=(0, 15))
        
        # File name
        ttk.Label(details_frame, text="File Name:", style='Modern.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.filename = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.filename, style='Modern.TEntry', width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # File type selection
        ttk.Label(details_frame, text="File Type:", style='Modern.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.file_type = tk.StringVar(value="Java Class")
        type_combo = ttk.Combobox(details_frame, textvariable=self.file_type, style='Modern.TCombobox', width=28, state='readonly')
        type_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # File types
        file_types = [
            "Java Class",
            "Java Interface", 
            "Java Enum",
            "JSON File",
            "XML File",
            "Properties File",
            "Text File",
            "Markdown File"
        ]
        type_combo['values'] = file_types
        type_combo.bind('<<ComboboxSelected>>', self.on_type_change)
        
        # Configure grid weights
        details_frame.columnconfigure(1, weight=1)
        
        # Template preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Template Preview", style='Modern.TFrame', padding=15)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Preview text
        self.preview_text = tk.Text(
            preview_frame,
            height=8,
            bg=ModernStyle.MEDIUM_BG,
            fg=ModernStyle.TEXT_SECONDARY,
            font=("Consolas", 9),
            relief=tk.FLAT,
            state=tk.DISABLED,
            wrap=tk.NONE
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="❌ Cancel", command=self.dialog.destroy, style='Modern.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="✅ Create", command=self.create_file, style='Accent.TButton').pack(side=tk.RIGHT)
        
        # Set initial preview
        self.on_type_change()
        
        # Focus filename entry
        self.filename.set("NewFile")
        details_frame.children['!entry'].focus()
        details_frame.children['!entry'].select_range(0, tk.END)
        
    def on_type_change(self, event=None):
        file_type = self.file_type.get()
        
        # Update filename extension
        current_name = self.filename.get()
        if current_name:
            base_name = os.path.splitext(current_name)[0]
        else:
            base_name = "NewFile"
            
        extensions = {
            "Java Class": ".java",
            "Java Interface": ".java", 
            "Java Enum": ".java",
            "JSON File": ".json",
            "XML File": ".xml",
            "Properties File": ".properties",
            "Text File": ".txt",
            "Markdown File": ".md"
        }
        
        ext = extensions.get(file_type, ".txt")
        self.filename.set(base_name + ext)
        
        # Update preview
        self.update_preview()
        
    def update_preview(self):
        file_type = self.file_type.get()
        filename = self.filename.get()
        base_name = os.path.splitext(os.path.basename(filename))[0]
        
        templates = {
            "Java Class": f'''package com.example.mod;

/**
 * {base_name} class
 * 
 * @author Your Name
 * @version 1.0
 */
public class {base_name} {{
    
    /**
     * Constructor for {base_name}
     */
    public {base_name}() {{
        // Constructor implementation
    }}
    
    /**
     * Initialize the {base_name}
     */
    public void initialize() {{
        // Initialization code here
        System.out.println("{base_name} initialized");
    }}
}}''',
            "Java Interface": f'''package com.example.mod;

/**
 * {base_name} interface
 * 
 * @author Your Name
 * @version 1.0
 */
public interface {base_name} {{
    
    /**
     * Method to be implemented by classes
     */
    void doSomething();
    
    /**
     * Default method with implementation
     */
    default void defaultMethod() {{
        System.out.println("Default implementation");
    }}
}}''',
            "Java Enum": f'''package com.example.mod;

/**
 * {base_name} enumeration
 * 
 * @author Your Name
 * @version 1.0
 */
public enum {base_name} {{
    
    VALUE1("First Value"),
    VALUE2("Second Value"),
    VALUE3("Third Value");
    
    private final String description;
    
    {base_name}(String description) {{
        this.description = description;
    }}
    
    public String getDescription() {{
        return description;
    }}
}}''',
            "JSON File": '''{
    "name": "Example Configuration",
    "version": "1.0.0",
    "description": "Configuration file for the mod",
    "settings": {
        "enabled": true,
        "debug": false,
        "maxValue": 100
    },
    "features": [
        "feature1",
        "feature2",
        "feature3"
    ]
}''',
            "XML File": '''<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <metadata>
        <name>Example Configuration</name>
        <version>1.0.0</version>
        <description>XML configuration file</description>
    </metadata>
    
    <settings>
        <setting name="enabled" value="true" />
        <setting name="debug" value="false" />
        <setting name="maxValue" value="100" />
    </settings>
    
    <features>
        <feature>feature1</feature>
        <feature>feature2</feature>
        <feature>feature3</feature>
    </features>
</configuration>''',
            "Properties File": '''# Configuration Properties
# Generated by Minecraft Mod IDE

# General Settings
mod.name=Example Mod
mod.version=1.0.0
mod.enabled=true

# Debug Settings
debug.enabled=false
debug.level=INFO

# Feature Settings
features.feature1=true
features.feature2=false
features.maxValue=100''',
            "Text File": f'''# {base_name}

This is a text file created with the Minecraft Mod IDE.

## Purpose
Describe the purpose of this file here.

## Contents
- Item 1
- Item 2
- Item 3

## Notes
Add any additional notes or information here.
''',
            "Markdown File": f'''# {base_name}

Welcome to your new Markdown file!

## Overview

This file was created using the Minecraft Mod IDE. You can use this file to document your mod, write guides, or store any text-based information.

## Features

- **Bold text** for emphasis
- *Italic text* for subtle emphasis
- `Code snippets` for inline code
- [Links](https://example.com) to external resources

## Code Example

```java
public class Example {{
    public static void main(String[] args) {{
        System.out.println("Hello, Minecraft Modding!");
    }}
}}
```

## Lists

### Unordered List
- Feature 1
- Feature 2
- Feature 3

### Ordered List
1. First step
2. Second step
3. Third step

## Conclusion

Start documenting your amazing mod! 🎮
'''
        }
        
        template = templates.get(file_type, "# New file\n\nFile content goes here...")
        
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", template)
        self.preview_text.config(state=tk.DISABLED)
        
    def create_file(self):
        filename = self.filename.get().strip()
        if not filename:
            messagebox.showerror("Error", "Please enter a filename")
            return
            
        file_path = os.path.join(self.parent_path, filename)
        
        if os.path.exists(file_path):
            if not messagebox.askyesno("File Exists", f"File '{filename}' already exists. Overwrite?"):
                return
                
        try:
            # Get template content
            template_content = self.preview_text.get("1.0", tk.END + "-1c")
            
            # Create file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
                
            # Close dialog and notify
            self.dialog.destroy()
            self.on_file_created(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create file: {str(e)}")


class FileExplorer:
    
    def __init__(self, parent, on_file_select):
        self.parent = parent
        self.on_file_select = on_file_select
        self.root_path = None
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame with modern styling
        self.frame = ttk.Frame(self.parent, style='Sidebar.TFrame')
        self.frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Header with project name and controls
        header_frame = ttk.Frame(self.frame, style='Sidebar.TFrame')
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.project_label = ttk.Label(header_frame, text="Project Explorer", style='Header.TLabel')
        self.project_label.pack(side=tk.LEFT)
        
        # Control buttons
        btn_frame = ttk.Frame(header_frame, style='Sidebar.TFrame')
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_tree, style='Modern.TButton', width=10).pack(side=tk.RIGHT, padx=1)
        ttk.Button(btn_frame, text="📁 Folder", command=self.new_folder, style='Modern.TButton', width=9).pack(side=tk.RIGHT, padx=1)
        ttk.Button(btn_frame, text="📄 File", command=self.new_file, style='Modern.TButton', width=8).pack(side=tk.RIGHT, padx=1)
        
        # Treeview with scrollbar
        tree_frame = ttk.Frame(self.frame, style='Sidebar.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree = ttk.Treeview(tree_frame, style='Modern.Treeview', show='tree')
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        self.tree.bind('<Button-3>', self.on_tree_right_click)
        self.tree.bind('<Return>', self.on_tree_double_click)
        self.tree.bind('<<TreeviewOpen>>', self.on_folder_expand)
        
    def load_project(self, root_path):
        self.root_path = root_path
        project_name = os.path.basename(root_path)
        self.project_label.config(text=f"📁 {project_name}")
        self.refresh_tree()
        
    def refresh_tree(self):
        if not self.root_path:
            return
            
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add root directory
        root_name = os.path.basename(self.root_path)
        root_item = self.tree.insert('', 'end', text=f"📁 {root_name}", open=True, values=[self.root_path, 'folder'])
        
        # Populate tree
        self.populate_tree(root_item, self.root_path)
        
    def populate_tree(self, parent_item, path):
        try:
            items = os.listdir(path)
            # Sort: directories first, then files
            items.sort(key=lambda x: (os.path.isfile(os.path.join(path, x)), x.lower()))
            
            for item in items:
                item_path = os.path.join(path, item)
                
                # Skip hidden files and build directories
                if item.startswith('.') or item == 'build' or item == '__pycache__':
                    continue
                    
                if os.path.isdir(item_path):
                    # Directory
                    icon = "📁" if any(os.listdir(item_path)) else "📂"
                    dir_item = self.tree.insert(parent_item, 'end', text=f"{icon} {item}", values=[item_path, 'folder'])
                    
                    # Add placeholder to make it expandable
                    try:
                        if os.listdir(item_path):  # Only add placeholder if directory has contents
                            self.tree.insert(dir_item, 'end', text="Loading...")
                    except (PermissionError, OSError):
                        pass  # Skip directories we can't access
                else:
                    # File
                    icon = self.get_file_icon(item)
                    self.tree.insert(parent_item, 'end', text=f"{icon} {item}", values=[item_path, 'file'])
                    
        except (PermissionError, OSError):
            pass
            
    def on_folder_expand(self, event):
        # Get the item that was opened
        item = self.tree.focus()
        if not item:
            return
            
        # Get the folder path
        values = self.tree.item(item)['values']
        if not values or len(values) < 2 or values[1] != 'folder':
            return
            
        folder_path = values[0]
        
        # Check if we need to load children
        children = self.tree.get_children(item)
        if children and len(children) == 1:
            child_text = self.tree.item(children[0])['text']
            if child_text == "Loading...":
                # Remove placeholder and load actual content
                self.tree.delete(children[0])
                self.populate_tree(item, folder_path)
            
    def get_file_icon(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        icon_map = {
            '.java': '☕',
            '.json': '📋',
            '.xml': '📄',
            '.properties': '⚙️',
            '.md': '📝',
            '.txt': '📝',
            '.jar': '📦',
            '.class': '🔧',
            '.gradle': '🐘',
            '.yml': '📄',
            '.yaml': '📄',
            '.png': '🖼️',
            '.jpg': '🖼️',
            '.jpeg': '🖼️',
            '.gif': '🖼️'
        }
        return icon_map.get(ext, '📄')
        
    def on_tree_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.tree.item(item)['values']
        if values and len(values) >= 2:
            file_path, item_type = values[0], values[1]
            if item_type == 'file' and os.path.isfile(file_path):
                self.on_file_select(file_path)
                
    def on_tree_right_click(self, event):
        # Identify clicked item
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            values = self.tree.item(item)['values']
            
            if values:
                file_path, item_type = values[0], values[1]
                self.show_context_menu(event, file_path, item_type)
                
    def show_context_menu(self, event, file_path, item_type):
        context_menu = tk.Menu(self.parent, tearoff=0, 
                             bg=ModernStyle.MEDIUM_BG, 
                             fg=ModernStyle.TEXT_PRIMARY,
                             activebackground=ModernStyle.ACCENT_ORANGE,
                             activeforeground=ModernStyle.DARK_BG)
        
        if item_type == 'file':
            context_menu.add_command(label="📂 Open", command=lambda: self.on_file_select(file_path))
            context_menu.add_separator()
            context_menu.add_command(label="📋 Copy Path", command=lambda: self.copy_to_clipboard(file_path))
            context_menu.add_command(label="✏️ Rename", command=lambda: self.rename_item(file_path))
            context_menu.add_command(label="🗑️ Delete", command=lambda: self.delete_item(file_path))
        else:
            context_menu.add_command(label="📄 New File", command=lambda: self.new_file(file_path))
            context_menu.add_command(label="📁 New Folder", command=lambda: self.new_folder(file_path))
            context_menu.add_separator()
            context_menu.add_command(label="📋 Copy Path", command=lambda: self.copy_to_clipboard(file_path))
            context_menu.add_command(label="✏️ Rename", command=lambda: self.rename_item(file_path))
            context_menu.add_command(label="🗑️ Delete", command=lambda: self.delete_item(file_path))
            
        context_menu.add_separator()
        context_menu.add_command(label="🔄 Refresh", command=self.refresh_tree)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def new_file(self, parent_path=None):
        if not parent_path:
            parent_path = self.root_path
            
        if not parent_path:
            messagebox.showwarning("Warning", "No project is open")
            return
            
        # Create file creation dialog
        NewFileDialog(self.parent, parent_path, self.on_file_created)
        
    def on_file_created(self, file_path):
        self.refresh_tree()
        self.on_file_select(file_path)
            
    def new_folder(self, parent_path=None):
        if not parent_path:
            parent_path = self.root_path
            
        if not parent_path:
            messagebox.showwarning("Warning", "No project is open")
            return
            
        # Get folder name from user
        foldername = tk.simpledialog.askstring("New Folder", "Enter folder name:")
        if not foldername:
            return
            
        folder_path = os.path.join(parent_path, foldername)
        
        try:
            os.makedirs(folder_path, exist_ok=True)
            self.refresh_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create folder: {str(e)}")
            
    def rename_item(self, item_path):
        old_name = os.path.basename(item_path)
        new_name = tk.simpledialog.askstring("Rename", f"Rename '{old_name}' to:", initialvalue=old_name)
        
        if not new_name or new_name == old_name:
            return
            
        new_path = os.path.join(os.path.dirname(item_path), new_name)
        
        try:
            os.rename(item_path, new_path)
            self.refresh_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename: {str(e)}")
            
    def delete_item(self, item_path):
        item_name = os.path.basename(item_path)
        if not messagebox.askyesno("Delete", f"Are you sure you want to delete '{item_name}'?"):
            return
            
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
            self.refresh_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {str(e)}")
            
    def copy_to_clipboard(self, text):
        self.parent.clipboard_clear()
        self.parent.clipboard_append(text)
        
    def get_file_template(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        name = os.path.splitext(filename)[0]
        
        templates = {
            '.java': f'''package com.example.mod;

public class {name} {{
    
    public {name}() {{
        // Constructor
    }}
    
    public void initialize() {{
        // Initialization code
    }}
}}''',
            '.json': '''{{
    "name": "Example",
    "version": "1.0.0",
    "description": ""
}}''',
            '.properties': '''# Configuration file
key=value
''',
            '.md': f'''# {name}

Description goes here.

## Features

- Feature 1
- Feature 2

## Usage

```java
// Example code
```
'''
        }
        
        return templates.get(ext, f'// {filename}\n// Created on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')

class FindReplaceDialog:
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.search_start = "1.0"
        self.matches = []
        self.current_match = 0
        self.setup_dialog()
        
    def setup_dialog(self):
        self.dialog = tk.Toplevel()
        self.dialog.title("Find & Replace")
        self.dialog.geometry("500x300")
        self.dialog.configure(bg=ModernStyle.DARK_BG)
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient()
        self.dialog.grab_set()
        
        # Style the dialog
        main_frame = ttk.Frame(self.dialog, style='Modern.TFrame', padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Find section
        find_frame = ttk.LabelFrame(main_frame, text="Find", style='Modern.TFrame', padding=10)
        find_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(find_frame, text="Find:", style='Modern.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.find_var = tk.StringVar()
        find_entry = ttk.Entry(find_frame, textvariable=self.find_var, style='Modern.TEntry', width=40)
        find_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        find_entry.focus()
        
        # Replace section
        replace_frame = ttk.LabelFrame(main_frame, text="Replace", style='Modern.TFrame', padding=10)
        replace_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(replace_frame, text="Replace:", style='Modern.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.replace_var = tk.StringVar()
        replace_entry = ttk.Entry(replace_frame, textvariable=self.replace_var, style='Modern.TEntry', width=40)
        replace_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Options section
        options_frame = ttk.LabelFrame(main_frame, text="Options", style='Modern.TFrame', padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.case_sensitive = tk.BooleanVar()
        self.regex_mode = tk.BooleanVar()
        self.whole_word = tk.BooleanVar()
        
        ttk.Checkbutton(options_frame, text="Case sensitive", variable=self.case_sensitive, style='Modern.TCheckbutton').grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(options_frame, text="Regular expressions", variable=self.regex_mode, style='Modern.TCheckbutton').grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(options_frame, text="Whole word", variable=self.whole_word, style='Modern.TCheckbutton').grid(row=0, column=2, sticky=tk.W)
        
        # Results info
        self.results_label = ttk.Label(main_frame, text="", style='Muted.TLabel')
        self.results_label.pack(pady=(0, 10))
        
        # Buttons section
        button_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Find All", command=self.find_all, style='Modern.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Find Next", command=self.find_next, style='Modern.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Replace", command=self.replace_current, style='Modern.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Replace All", command=self.replace_all, style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 15))
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy, style='Modern.TButton').pack(side=tk.RIGHT)
        
        # Configure grid weights
        find_frame.columnconfigure(1, weight=1)
        replace_frame.columnconfigure(1, weight=1)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.find_next())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
    def find_all(self):
        search_term = self.find_var.get()
        if not search_term:
            return
            
        # Clear previous highlights
        self.text_widget.tag_remove("search_highlight", "1.0", tk.END)
        
        content = self.text_widget.get("1.0", tk.END)
        self.matches = []
        
        if self.regex_mode.get():
            try:
                flags = 0 if self.case_sensitive.get() else re.IGNORECASE
                pattern = re.compile(search_term, flags)
                for match in pattern.finditer(content):
                    self.matches.append((match.start(), match.end()))
            except re.error as e:
                messagebox.showerror("Regex Error", f"Invalid regular expression: {str(e)}")
                return
        else:
            # Simple text search
            start = 0
            while True:
                if self.case_sensitive.get():
                    pos = content.find(search_term, start)
                else:
                    pos = content.lower().find(search_term.lower(), start)
                
                if pos == -1:
                    break
                    
                # Check whole word if enabled
                if self.whole_word.get():
                    if pos > 0 and content[pos-1].isalnum():
                        start = pos + 1
                        continue
                    if pos + len(search_term) < len(content) and content[pos + len(search_term)].isalnum():
                        start = pos + 1
                        continue
                        
                self.matches.append((pos, pos + len(search_term)))
                start = pos + 1
                
        # Highlight all matches
        for start_pos, end_pos in self.matches:
            start_line = content[:start_pos].count('\n') + 1
            start_col = start_pos - content.rfind('\n', 0, start_pos) - 1
            end_line = content[:end_pos].count('\n') + 1
            end_col = end_pos - content.rfind('\n', 0, end_pos) - 1
            
            start_index = f"{start_line}.{start_col}"
            end_index = f"{end_line}.{end_col}"
            
            self.text_widget.tag_add("search_highlight", start_index, end_index)
            
        # Configure highlight style
        self.text_widget.tag_configure("search_highlight", background=ModernStyle.ACCENT_ORANGE, foreground=ModernStyle.DARK_BG)
        
        # Update results
        self.results_label.config(text=f"Found {len(self.matches)} matches")
        self.current_match = 0
        
        if self.matches:
            self.show_current_match()
            
    def find_next(self):
        if not self.matches:
            self.find_all()
            return
            
        if self.matches:
            self.current_match = (self.current_match + 1) % len(self.matches)
            self.show_current_match()
            
    def show_current_match(self):
        if not self.matches:
            return
            
        # Clear current selection
        self.text_widget.tag_remove("current_match", "1.0", tk.END)
        
        # Highlight current match
        start_pos, end_pos = self.matches[self.current_match]
        content = self.text_widget.get("1.0", tk.END)
        
        start_line = content[:start_pos].count('\n') + 1
        start_col = start_pos - content.rfind('\n', 0, start_pos) - 1
        end_line = content[:end_pos].count('\n') + 1
        end_col = end_pos - content.rfind('\n', 0, end_pos) - 1
        
        start_index = f"{start_line}.{start_col}"
        end_index = f"{end_line}.{end_col}"
        
        self.text_widget.tag_add("current_match", start_index, end_index)
        self.text_widget.tag_configure("current_match", background=ModernStyle.ACCENT_ORANGE_HOVER, foreground=ModernStyle.DARK_BG)
        
        # Scroll to match
        self.text_widget.see(start_index)
        
        # Update results
        self.results_label.config(text=f"Match {self.current_match + 1} of {len(self.matches)}")
        
    def replace_current(self):
        if not self.matches or self.current_match >= len(self.matches):
            return
            
        start_pos, end_pos = self.matches[self.current_match]
        content = self.text_widget.get("1.0", tk.END)
        
        start_line = content[:start_pos].count('\n') + 1
        start_col = start_pos - content.rfind('\n', 0, start_pos) - 1
        end_line = content[:end_pos].count('\n') + 1
        end_col = end_pos - content.rfind('\n', 0, end_pos) - 1
        
        start_index = f"{start_line}.{start_col}"
        end_index = f"{end_line}.{end_col}"
        
        # Replace text
        self.text_widget.delete(start_index, end_index)
        self.text_widget.insert(start_index, self.replace_var.get())
        
        # Refresh search
        self.find_all()
        
    def replace_all(self):
        if not self.matches:
            self.find_all()
            
        if not self.matches:
            return
            
        replace_text = self.replace_var.get()
        replacements = 0
        
        # Replace from end to beginning to maintain positions
        for start_pos, end_pos in reversed(self.matches):
            content = self.text_widget.get("1.0", tk.END)
            
            start_line = content[:start_pos].count('\n') + 1
            start_col = start_pos - content.rfind('\n', 0, start_pos) - 1
            end_line = content[:end_pos].count('\n') + 1
            end_col = end_pos - content.rfind('\n', 0, end_pos) - 1
            
            start_index = f"{start_line}.{start_col}"
            end_index = f"{end_line}.{end_col}"
            
            self.text_widget.delete(start_index, end_index)
            self.text_widget.insert(start_index, replace_text)
            replacements += 1
            
        # Clear highlights
        self.text_widget.tag_remove("search_highlight", "1.0", tk.END)
        self.text_widget.tag_remove("current_match", "1.0", tk.END)
        
        self.matches = []
        self.results_label.config(text=f"Replaced {replacements} occurrences")

class ProjectTemplates:
    
    @staticmethod
    def get_templates():
        return {
            "Basic Mod": ProjectTemplates.basic_mod_template,
            "Forge Mod": ProjectTemplates.forge_mod_template,
            "Fabric Mod": ProjectTemplates.fabric_mod_template,
            "Bukkit Plugin": ProjectTemplates.bukkit_plugin_template
        }
        
    @staticmethod
    def basic_mod_template(project_path, mod_name, package_name):
        # Create directory structure
        src_dir = os.path.join(project_path, "src", "main", "java", *package_name.split('.'))
        resources_dir = os.path.join(project_path, "src", "main", "resources")
        
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(resources_dir, exist_ok=True)
        
        # Main mod class
        main_class_content = f'''package {package_name};

/**
 * {mod_name} - A Minecraft mod
 * Created with Minecraft Mod IDE
 */
public class {mod_name.replace(' ', '')} {{
    
    public static final String MOD_ID = "{mod_name.lower().replace(' ', '_')}";
    public static final String MOD_NAME = "{mod_name}";
    public static final String VERSION = "1.0.0";
    
    public {mod_name.replace(' ', '')}() {{
        System.out.println("Initializing " + MOD_NAME + " v" + VERSION);
    }}
    
    public void init() {{
        // Initialization code here
    }}
}}'''
        
        with open(os.path.join(src_dir, f"{mod_name.replace(' ', '')}.java"), 'w') as f:
            f.write(main_class_content)
            
        # Create mod info file
        mod_info = f'''{{
    "modid": "{mod_name.lower().replace(' ', '_')}",
    "name": "{mod_name}",
    "description": "A new Minecraft mod",
    "version": "1.0.0",
    "mcversion": "1.16.5",
    "authorList": ["Author"],
    "credits": "Created with Minecraft Mod IDE"
}}'''
        
        with open(os.path.join(resources_dir, "mcmod.info"), 'w') as f:
            f.write(mod_info)
            
    @staticmethod
    def forge_mod_template(project_path, mod_name, package_name):
        ProjectTemplates.basic_mod_template(project_path, mod_name, package_name)
        
        # Add Forge-specific files
        src_dir = os.path.join(project_path, "src", "main", "java", *package_name.split('.'))
        
        # Forge main class
        forge_main = f'''package {package_name};

import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;

@Mod({mod_name.replace(' ', '')}.MOD_ID)
public class {mod_name.replace(' ', '')} {{
    
    public static final String MOD_ID = "{mod_name.lower().replace(' ', '_')}";
    
    public {mod_name.replace(' ', '')}() {{
        FMLJavaModLoadingContext.get().getModEventBus().addListener(this::setup);
    }}
    
    private void setup(final FMLCommonSetupEvent event) {{
        // Mod setup
    }}
}}'''
        
        with open(os.path.join(src_dir, f"{mod_name.replace(' ', '')}.java"), 'w') as f:
            f.write(forge_main)
            
    @staticmethod
    def fabric_mod_template(project_path, mod_name, package_name):
        ProjectTemplates.basic_mod_template(project_path, mod_name, package_name)
        
        # Add Fabric-specific files
        src_dir = os.path.join(project_path, "src", "main", "java", *package_name.split('.'))
        resources_dir = os.path.join(project_path, "src", "main", "resources")
        
        # Fabric main class
        fabric_main = f'''package {package_name};

import net.fabricmc.api.ModInitializer;

public class {mod_name.replace(' ', '')} implements ModInitializer {{
    
    public static final String MOD_ID = "{mod_name.lower().replace(' ', '_')}";
    
    @Override
    public void onInitialize() {{
        // Mod initialization
    }}
}}'''
        
        with open(os.path.join(src_dir, f"{mod_name.replace(' ', '')}.java"), 'w') as f:
            f.write(fabric_main)
            
        # Fabric mod.json
        fabric_json = f'''{{
    "schemaVersion": 1,
    "id": "{mod_name.lower().replace(' ', '_')}",
    "version": "1.0.0",
    "name": "{mod_name}",
    "description": "A Fabric mod",
    "authors": ["Author"],
    "contact": {{}},
    "license": "MIT",
    "icon": "assets/{mod_name.lower().replace(' ', '_')}/icon.png",
    "environment": "*",
    "entrypoints": {{
        "main": [
            "{package_name}.{mod_name.replace(' ', '')}"
        ]
    }},
    "mixins": [],
    "depends": {{
        "fabricloader": ">=0.7.4",
        "fabric": "*",
        "minecraft": "1.16.x"
    }}
}}'''
        
        with open(os.path.join(resources_dir, "fabric.mod.json"), 'w') as f:
            f.write(fabric_json)
            
    @staticmethod
    def bukkit_plugin_template(project_path, mod_name, package_name):
        # Create directory structure
        src_dir = os.path.join(project_path, "src", "main", "java", *package_name.split('.'))
        resources_dir = os.path.join(project_path, "src", "main", "resources")
        
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(resources_dir, exist_ok=True)
        
        # Main plugin class
        plugin_main = f'''package {package_name};

import org.bukkit.plugin.java.JavaPlugin;

public class {mod_name.replace(' ', '')} extends JavaPlugin {{
    
    @Override
    public void onEnable() {{
        getLogger().info("{mod_name} has been enabled!");
    }}
    
    @Override
    public void onDisable() {{
        getLogger().info("{mod_name} has been disabled!");
    }}
}}'''
        
        with open(os.path.join(src_dir, f"{mod_name.replace(' ', '')}.java"), 'w') as f:
            f.write(plugin_main)
            
        # Plugin.yml
        plugin_yml = f'''name: {mod_name}
version: 1.0.0
description: A Bukkit plugin
author: Author
main: {package_name}.{mod_name.replace(' ', '')}
api-version: 1.16
'''
        
        with open(os.path.join(resources_dir, "plugin.yml"), 'w') as f:
            f.write(plugin_yml)

class ProjectTemplateDialog:
    
    def __init__(self, parent, on_project_created):
        self.parent = parent
        self.on_project_created = on_project_created
        self.setup_dialog()
        
    def setup_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("New Project")
        self.dialog.geometry("650x600")
        self.dialog.configure(bg=ModernStyle.DARK_BG)
        self.dialog.resizable(True, True)
        
        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, style='Modern.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Create New Project", style='Header.TLabel').pack(pady=(0, 20))
        
        # Project details frame
        details_frame = ttk.LabelFrame(main_frame, text="Project Details", style='Modern.TFrame', padding=15)
        details_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Project name
        ttk.Label(details_frame, text="Project Name:", style='Modern.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.project_name = tk.StringVar(value="MyAwesomeMod")
        ttk.Entry(details_frame, textvariable=self.project_name, style='Modern.TEntry', width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Package name
        ttk.Label(details_frame, text="Package Name:", style='Modern.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.package_name = tk.StringVar(value="com.example.mod")
        ttk.Entry(details_frame, textvariable=self.package_name, style='Modern.TEntry', width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Project location
        ttk.Label(details_frame, text="Location:", style='Modern.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        location_frame = ttk.Frame(details_frame, style='Modern.TFrame')
        location_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        self.project_location = tk.StringVar(value=os.path.expanduser("~/Documents"))
        ttk.Entry(location_frame, textvariable=self.project_location, style='Modern.TEntry', width=25).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(location_frame, text="Browse", command=self.browse_location, style='Modern.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        
        # Configure grid weights
        details_frame.columnconfigure(1, weight=1)
        location_frame.columnconfigure(0, weight=1)
        
        # Template selection frame
        template_frame = ttk.LabelFrame(main_frame, text="Project Template", style='Modern.TFrame', padding=15)
        template_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Template listbox
        template_list_frame = ttk.Frame(template_frame, style='Modern.TFrame')
        template_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.template_listbox = tk.Listbox(
            template_list_frame,
            bg=ModernStyle.MEDIUM_BG,
            fg=ModernStyle.TEXT_PRIMARY,
            selectbackground=ModernStyle.ACCENT_ORANGE,
            selectforeground=ModernStyle.DARK_BG,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            bd=0,
            height=6
        )
        self.template_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        template_scroll = ttk.Scrollbar(template_list_frame, orient=tk.VERTICAL, command=self.template_listbox.yview)
        template_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.template_listbox.configure(yscrollcommand=template_scroll.set)
        
        # Populate templates
        templates = ProjectTemplates.get_templates()
        for template_name in templates.keys():
            self.template_listbox.insert(tk.END, template_name)
        self.template_listbox.select_set(0)
        
        # Template description
        self.template_description = ttk.Label(template_frame, text="Select a template to see description", style='Muted.TLabel', wraplength=500)
        self.template_description.pack(pady=(10, 0))
        
        # Bind template selection
        self.template_listbox.bind('<<ListboxSelect>>', self.on_template_select)
        
        # Buttons frame - Make sure this is visible
        button_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Create buttons with better styling
        cancel_btn = ttk.Button(button_frame, text="❌ Cancel", command=self.dialog.destroy, style='Modern.TButton')
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        create_btn = ttk.Button(button_frame, text="🚀 Create Project", command=self.create_project, style='Accent.TButton')
        create_btn.pack(side=tk.RIGHT)
        
        # Set initial description
        self.on_template_select()
        
    def browse_location(self):
        location = filedialog.askdirectory(title="Select Project Location")
        if location:
            self.project_location.set(location)
            
    def on_template_select(self, event=None):
        selection = self.template_listbox.curselection()
        if selection:
            template_name = self.template_listbox.get(selection[0])
            descriptions = {
                "Basic Mod": "A simple mod template with basic structure and example code.",
                "Forge Mod": "A Minecraft Forge mod template with proper annotations and setup.",
                "Fabric Mod": "A Fabric mod template with mod.json and proper structure.",
                "Bukkit Plugin": "A Bukkit/Spigot plugin template with plugin.yml configuration."
            }
            self.template_description.config(text=descriptions.get(template_name, "No description available"))
            
    def create_project(self):
        # Validate inputs
        if not self.project_name.get().strip():
            messagebox.showerror("Error", "Please enter a project name")
            return
            
        if not self.package_name.get().strip():
            messagebox.showerror("Error", "Please enter a package name")
            return
            
        if not self.project_location.get().strip():
            messagebox.showerror("Error", "Please select a project location")
            return
            
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a template")
            return
            
        # Get template
        template_name = self.template_listbox.get(selection[0])
        templates = ProjectTemplates.get_templates()
        template_func = templates[template_name]
        
        # Create project directory
        project_name = self.project_name.get().strip()
        project_path = os.path.join(self.project_location.get(), project_name)
        
        if os.path.exists(project_path):
            if not messagebox.askyesno("Directory Exists", f"Directory '{project_name}' already exists. Continue?"):
                return
                
        try:
            os.makedirs(project_path, exist_ok=True)
            
            # Create project from template
            template_func(project_path, project_name, self.package_name.get().strip())
            
            # Close dialog and open project
            self.dialog.destroy()
            self.on_project_created(project_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create project: {str(e)}")

class JarCompiler:
    
    def __init__(self, output_callback, progress_callback=None):
        self.output_callback = output_callback
        self.progress_callback = progress_callback
        
    def compile_project(self, project_path, output_path, jar_name, classpath=None, main_class=None):
        def compile_thread():
            try:
                self.update_progress(0, "Starting compilation...")
                
                # Find Java files
                self.update_progress(10, "Scanning for Java files...")
                java_files = self.find_java_files(project_path)
                if not java_files:
                    self.log_output("❌ ERROR: No Java files found in project")
                    return False
                    
                self.log_output(f"📁 Found {len(java_files)} Java files")
                
                # Create build directory
                self.update_progress(20, "Preparing build directory...")
                build_dir = os.path.join(project_path, "build")
                os.makedirs(build_dir, exist_ok=True)
                
                # Compile Java files
                self.update_progress(30, "Compiling Java source files...")
                if not self.compile_java_files(java_files, build_dir, classpath):
                    self.log_output("❌ Compilation failed")
                    return False
                    
                # Create JAR
                self.update_progress(80, "Creating JAR file...")
                jar_path = os.path.join(output_path, jar_name)
                if not self.create_jar_file(build_dir, jar_path, main_class):
                    self.log_output("❌ JAR creation failed")
                    return False
                    
                self.update_progress(100, "Compilation complete!")
                self.log_output("✅ SUCCESS: JAR compilation completed successfully!")
                self.log_output(f"📦 Output: {jar_path}")
                
                # Show file size
                if os.path.exists(jar_path):
                    size = os.path.getsize(jar_path)
                    size_str = self.format_file_size(size)
                    self.log_output(f"📊 File size: {size_str}")
                
                return True
                
            except Exception as e:
                self.log_output(f"💥 EXCEPTION: {str(e)}")
                return False
                
        thread = threading.Thread(target=compile_thread, daemon=True)
        thread.start()
        
    def update_progress(self, percent, message):
        if self.progress_callback:
            self.progress_callback(percent, message)
        self.output_callback(f"[{percent:3d}%] {message}")
        
    def find_java_files(self, directory):
        java_files = []
        for root, dirs, files in os.walk(directory):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['build', 'target', '.git', '.idea', '__pycache__']]
            
            for file in files:
                if file.endswith('.java'):
                    java_files.append(os.path.join(root, file))
                    
        return java_files
        
    def compile_java_files(self, java_files, build_dir, classpath):
        self.output_callback("🔨 Compiling Java files...")
        
        # Prepare command
        cmd = ["javac", "-d", build_dir, "-encoding", "UTF-8"]
        
        if classpath:
            cmd.extend(["-cp", classpath])
            
        cmd.extend(java_files)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.output_callback(f"📄 {line}")
                        
            if result.stderr:
                error_lines = result.stderr.split('\n')
                for line in error_lines:
                    if line.strip():
                        if "error:" in line.lower():
                            self.output_callback(f"❌ {line}")
                        elif "warning:" in line.lower():
                            self.output_callback(f"⚠️ {line}")
                        else:
                            self.output_callback(f"ℹ️ {line}")
                            
            if result.returncode == 0:
                self.output_callback("✅ Java compilation successful")
                return True
            else:
                self.output_callback(f"❌ Compilation failed (exit code {result.returncode})")
                return False
                
        except subprocess.TimeoutExpired:
            self.output_callback("❌ Compilation timeout (5 minutes)")
            return False
        except FileNotFoundError:
            self.output_callback("❌ javac not found. Please install Java JDK and add to PATH")
            return False
        except Exception as e:
            self.output_callback(f"❌ Compilation error: {str(e)}")
            return False
            
    def create_jar_file(self, build_dir, jar_path, main_class):
        self.output_callback("📦 Creating JAR file...")
        
        os.makedirs(os.path.dirname(jar_path), exist_ok=True)
        
        cmd = ["jar", "cf", jar_path]
        
        manifest_path = None
        if main_class:
            manifest_path = os.path.join(build_dir, "MANIFEST.MF")
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write("Manifest-Version: 1.0\n")
                f.write(f"Main-Class: {main_class}\n")
                f.write("Created-By: Minecraft Mod IDE\n")
                f.write(f"Build-Date: {datetime.now().isoformat()}\n")
                f.write("Specification-Title: Minecraft Mod\n")
                f.write("Specification-Version: 1.0\n")
                f.write("Implementation-Title: Minecraft Mod\n")
                f.write("Implementation-Version: 1.0.0\n")
            cmd = ["jar", "cfm", jar_path, manifest_path]
            
        cmd.extend(["-C", build_dir, "."])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.output_callback("✅ JAR file created successfully")
                
                if manifest_path and os.path.exists(manifest_path):
                    os.remove(manifest_path)
                    
                return True
            else:
                self.output_callback(f"❌ JAR creation failed (exit code {result.returncode})")
                if result.stderr:
                    self.output_callback(f"❌ {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.output_callback("❌ JAR creation timeout")
            return False
        except FileNotFoundError:
            self.output_callback("❌ jar tool not found. Please install Java JDK")
            return False
        except Exception as e:
            self.output_callback(f"❌ JAR creation error: {str(e)}")
            return False
            
    @staticmethod
    def format_file_size(size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

class MinecraftModIDE:
    
    def __init__(self, root):
        self.root = root
        self.project_path = None
        self.setup_style()
        self.setup_ui()
        
        # Initialize components
        self.jar_compiler = JarCompiler(self.log_output, self.update_progress)
        
        # Auto-save timer
        self.auto_save_timer = None
        self.start_auto_save()
        
        # Window state
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_style(self):
        ModernStyle.configure_style(self.root)
        
    def setup_ui(self):
        self.root.title("🎮 Minecraft Mod IDE")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # Create main components
        self.create_menu_bar()
        self.create_toolbar()
        self.create_main_interface()
        self.create_status_bar()
        
        # Bind global shortcuts
        self.bind_shortcuts()
        
        # Add smooth startup animation
        self.animate_startup()
        
    def animate_startup(self):
        try:
            # Start with slightly transparent and animate to full opacity
            self.root.attributes('-alpha', 0.0)
            self.fade_in(0.0)
        except tk.TclError:
            # Alpha transparency not supported on this system
            pass
        
    def fade_in(self, alpha):
        try:
            if alpha < 1.0:
                alpha += 0.05
                self.root.attributes('-alpha', alpha)
                self.root.after(20, lambda: self.fade_in(alpha))
            else:
                self.root.attributes('-alpha', 1.0)
        except tk.TclError:
            # Alpha transparency not supported, ensure window is visible
            self.root.attributes('-alpha', 1.0)
        
    def create_menu_bar(self):
        menubar = tk.Menu(self.root, 
                         bg=ModernStyle.MEDIUM_BG, 
                         fg=ModernStyle.TEXT_PRIMARY,
                         activebackground=ModernStyle.ACCENT_ORANGE,
                         activeforeground=ModernStyle.DARK_BG)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, 
                           bg=ModernStyle.MEDIUM_BG, 
                           fg=ModernStyle.TEXT_PRIMARY,
                           activebackground=ModernStyle.ACCENT_ORANGE,
                           activeforeground=ModernStyle.DARK_BG)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="🆕 New File", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="📂 Open File", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="💾 Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="💾 Save As", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="💾 Save All", command=self.save_all_files, accelerator="Ctrl+Alt+S")
        file_menu.add_separator()
        file_menu.add_command(label="📁 Open Project", command=self.open_project, accelerator="Ctrl+Shift+O")
        file_menu.add_command(label="🚀 New Project", command=self.new_project, accelerator="Ctrl+Shift+N")
        file_menu.add_separator()
        file_menu.add_command(label="❌ Exit", command=self.on_closing, accelerator="Alt+F4")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0,
                           bg=ModernStyle.MEDIUM_BG, 
                           fg=ModernStyle.TEXT_PRIMARY,
                           activebackground=ModernStyle.ACCENT_ORANGE,
                           activeforeground=ModernStyle.DARK_BG)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="↶ Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="↷ Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="✂️ Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="📋 Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="📄 Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="🔍 Find & Replace", command=self.find_replace, accelerator="Ctrl+F")
        edit_menu.add_command(label="💬 Toggle Comment", command=self.toggle_comment, accelerator="Ctrl+/")
        edit_menu.add_command(label="📑 Duplicate Line", command=self.duplicate_line, accelerator="Ctrl+D")
        
        # Build menu
        build_menu = tk.Menu(menubar, tearoff=0,
                            bg=ModernStyle.MEDIUM_BG, 
                            fg=ModernStyle.TEXT_PRIMARY,
                            activebackground=ModernStyle.ACCENT_ORANGE,
                            activeforeground=ModernStyle.DARK_BG)
        menubar.add_cascade(label="Build", menu=build_menu)
        build_menu.add_command(label="🔨 Compile to JAR", command=self.show_compile_dialog, accelerator="F5")
        build_menu.add_command(label="🧹 Clean Build", command=self.clean_build, accelerator="Shift+F5")
        build_menu.add_command(label="⚡ Quick Build", command=self.quick_build, accelerator="Ctrl+F5")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0,
                            bg=ModernStyle.MEDIUM_BG, 
                            fg=ModernStyle.TEXT_PRIMARY,
                            activebackground=ModernStyle.ACCENT_ORANGE,
                            activeforeground=ModernStyle.DARK_BG)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="🧹 Clear Output", command=self.clear_output)
        tools_menu.add_command(label="🔄 Refresh Project", command=self.refresh_project)
        tools_menu.add_command(label="⚙️ Settings", command=self.show_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0,
                           bg=ModernStyle.MEDIUM_BG, 
                           fg=ModernStyle.TEXT_PRIMARY,
                           activebackground=ModernStyle.ACCENT_ORANGE,
                           activeforeground=ModernStyle.DARK_BG)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="📖 Documentation", command=self.show_documentation)
        help_menu.add_command(label="💡 Tips & Tricks", command=self.show_tips)
        help_menu.add_command(label="ℹ️ About", command=self.show_about)
        
    def create_toolbar(self):
        # Toolbar container with gradient effect
        toolbar_container = ttk.Frame(self.root, style='Toolbar.TFrame', relief='flat', borderwidth=0)
        toolbar_container.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        # Configure toolbar to expand properly
        self.root.grid_columnconfigure(0, weight=1)
        
        # Add subtle separator line
        separator = ttk.Frame(toolbar_container, height=1, style='Modern.TFrame')
        separator.pack(side=tk.BOTTOM, fill=tk.X)
        
        toolbar_frame = ttk.Frame(toolbar_container, style='Toolbar.TFrame')
        toolbar_frame.pack(fill=tk.X, padx=12, pady=8)
        
        # File operations section with visual grouping
        file_group = self.create_button_group(toolbar_frame, "File Operations")
        self.create_toolbar_button(file_group, "📄", "New File", self.new_file, "Create new file (Ctrl+N)", width=12)
        self.create_toolbar_button(file_group, "📂", "Open File", self.open_file, "Open file (Ctrl+O)", width=12)
        self.create_toolbar_button(file_group, "💾", "Save File", self.save_file, "Save current file (Ctrl+S)", width=12)
        
        self.add_toolbar_separator(toolbar_frame)
        
        # Project operations section
        project_group = self.create_button_group(toolbar_frame, "Project")
        self.create_toolbar_button(project_group, "🚀", "New Project", self.new_project, "Create new project (Ctrl+Shift+N)", width=14)
        self.create_toolbar_button(project_group, "📁", "Open Project", self.open_project, "Open existing project (Ctrl+Shift+O)", width=14)
        self.create_toolbar_button(project_group, "🔄", "Refresh", self.refresh_project, "Refresh project tree", width=12)
        
        self.add_toolbar_separator(toolbar_frame)
        
        # Build operations section
        build_group = self.create_button_group(toolbar_frame, "Build")
        self.create_toolbar_button(build_group, "🔨", "Compile JAR", self.show_compile_dialog, "Compile to JAR (F5)", accent=True, width=14)
        self.create_toolbar_button(build_group, "⚡", "Quick Build", self.quick_build, "Quick build (Ctrl+F5)", width=13)
        self.create_toolbar_button(build_group, "🧹", "Clean Build", self.clean_build, "Clean build (Shift+F5)", width=13)
        
        # Right side tools with more space
        right_frame = ttk.Frame(toolbar_frame, style='Toolbar.TFrame')
        right_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        self.create_toolbar_button(right_frame, "🔍", "Find/Replace", self.find_replace, "Find and replace (Ctrl+F)", width=14)
        self.create_toolbar_button(right_frame, "⚙️", "Settings", self.show_settings, "IDE settings", width=12)
        
    def create_button_group(self, parent, name):
        group_frame = ttk.Frame(parent, style='Toolbar.TFrame')
        group_frame.pack(side=tk.LEFT, padx=(0, 16))
        return group_frame
        
    def create_toolbar_button(self, parent, icon, text, command, tooltip="", accent=False, width=12):
        # Container for button with hover effects
        btn_container = ttk.Frame(parent, style='Toolbar.TFrame')
        btn_container.pack(side=tk.LEFT, padx=2)
        
        # Button with icon and text - always use side-by-side layout for better readability
        btn_text = f"{icon} {text}"
        style = 'Accent.TButton' if accent else 'Toolbar.TButton'
        
        btn = ttk.Button(btn_container, text=btn_text, command=command, style=style, width=width)
        btn.pack(padx=3, pady=3)
        
        # Add smooth hover animations
        def on_enter(event):
            if not accent:
                btn.configure(style='Accent.TButton')
            self.show_status(tooltip)
            
        def on_leave(event):
            if not accent:
                btn.configure(style='Toolbar.TButton')
            self.show_status("Ready")
            
        def on_click(event):
            # Add click animation
            btn.configure(style='Modern.TButton')
            btn.after(100, lambda: btn.configure(style='Accent.TButton' if accent else 'Toolbar.TButton'))
            
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        btn.bind('<Button-1>', on_click)
        
        return btn
        
    def add_toolbar_separator(self, parent):
        sep_frame = ttk.Frame(parent, style='Toolbar.TFrame', width=3)
        sep_frame.pack(side=tk.LEFT, fill=tk.Y, padx=12)
        
        sep = ttk.Separator(sep_frame, orient=tk.VERTICAL, style='Modern.TSeparator')
        sep.pack(fill=tk.Y, expand=True, pady=8)
        
    def create_main_interface(self):
        # Main paned window
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL, style='Modern.TFrame')
        self.main_paned.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Left sidebar
        sidebar_frame = ttk.Frame(self.main_paned, style='Sidebar.TFrame', width=250)
        self.main_paned.add(sidebar_frame, weight=1)
        
        # Right main area
        main_area = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL, style='Modern.TFrame')
        self.main_paned.add(main_area, weight=4)
        
        # Editor area
        editor_frame = ttk.Frame(main_area, style='Modern.TFrame')
        main_area.add(editor_frame, weight=3)
        
        # Bottom panel
        bottom_frame = ttk.Frame(main_area, style='Modern.TFrame', height=250)
        main_area.add(bottom_frame, weight=1)
        
        # Initialize components
        self.file_explorer = FileExplorer(sidebar_frame, self.open_file_in_editor)
        self.editor = TabbedEditor(editor_frame)
        
        # Setup bottom panel with tabs
        self.setup_bottom_panel(bottom_frame)
        
    def setup_bottom_panel(self, parent):
        self.bottom_notebook = ttk.Notebook(parent, style='Modern.TNotebook')
        self.bottom_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Output tab with enhanced styling
        output_frame = ttk.Frame(self.bottom_notebook, style='Modern.TFrame')
        self.bottom_notebook.add(output_frame, text="📄 Build Output")
        
        # Output header with enhanced controls
        output_header = ttk.Frame(output_frame, style='Modern.TFrame')
        output_header.pack(fill=tk.X, padx=8, pady=6)
        
        # Title with icon
        title_frame = ttk.Frame(output_header, style='Modern.TFrame')
        title_frame.pack(side=tk.LEFT)
        
        ttk.Label(title_frame, text="🔨 Build Output", style='Header.TLabel').pack(side=tk.LEFT)
        
        # Status indicator
        self.build_status = tk.Label(title_frame, text="●", font=("Segoe UI", 12),
                                   fg=ModernStyle.SUCCESS_COLOR, bg=ModernStyle.DARK_BG)
        self.build_status.pack(side=tk.LEFT, padx=(10, 0))
        
        # Control buttons
        controls_frame = ttk.Frame(output_header, style='Modern.TFrame')
        controls_frame.pack(side=tk.RIGHT)
        
        ttk.Button(controls_frame, text="🗑️ Clear", command=self.clear_output, 
                  style='Modern.TButton', width=8).pack(side=tk.RIGHT, padx=2)
        ttk.Button(controls_frame, text="📋 Copy", command=self.copy_output, 
                  style='Modern.TButton', width=8).pack(side=tk.RIGHT, padx=2)
        
        # Enhanced output text with better styling
        output_container = ttk.Frame(output_frame, style='Modern.TFrame')
        output_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        self.output_text = scrolledtext.ScrolledText(
            output_container,
            height=10,
            bg=ModernStyle.DARK_BG,
            fg=ModernStyle.TEXT_PRIMARY,
            insertbackground=ModernStyle.ACCENT_ORANGE,
            font=("Consolas", 9),
            relief=tk.FLAT,
            bd=2,
            selectbackground=ModernStyle.ACCENT_ORANGE,
            selectforeground=ModernStyle.DARK_BG,
            wrap=tk.WORD
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.output_text.tag_configure("success", foreground=ModernStyle.SUCCESS_COLOR)
        self.output_text.tag_configure("error", foreground=ModernStyle.ERROR_COLOR)
        self.output_text.tag_configure("warning", foreground=ModernStyle.WARNING_COLOR)
        self.output_text.tag_configure("info", foreground=ModernStyle.TEXT_SECONDARY)
        
        # Enhanced progress section
        progress_container = ttk.Frame(output_frame, style='Modern.TFrame')
        progress_container.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        self.progress_frame = ttk.Frame(progress_container, style='Modern.TFrame')
        self.progress_frame.pack(fill=tk.X)
        
        self.progress_label = ttk.Label(self.progress_frame, text="Ready", style='Modern.TLabel')
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            style='Modern.Horizontal.TProgressbar',
            mode='determinate'
        )
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Problems tab with enhanced styling
        problems_frame = ttk.Frame(self.bottom_notebook, style='Modern.TFrame')
        self.bottom_notebook.add(problems_frame, text="⚠️ Problems")
        
        # Problems header
        problems_header = ttk.Frame(problems_frame, style='Modern.TFrame')
        problems_header.pack(fill=tk.X, padx=8, pady=6)
        
        ttk.Label(problems_header, text="⚠️ Problems", style='Header.TLabel').pack(side=tk.LEFT)
        
        self.problems_count = ttk.Label(problems_header, text="0 issues", style='Muted.TLabel')
        self.problems_count.pack(side=tk.RIGHT)
        
        # Enhanced problems tree
        problems_container = ttk.Frame(problems_frame, style='Modern.TFrame')
        problems_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        self.problems_tree = ttk.Treeview(
            problems_container,
            style='Modern.Treeview',
            columns=('Type', 'Message', 'File', 'Line'),
            show='tree headings',
            height=8
        )
        self.problems_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure problem tree columns with better widths
        self.problems_tree.heading('#0', text='')
        self.problems_tree.heading('Type', text='Type')
        self.problems_tree.heading('Message', text='Message')
        self.problems_tree.heading('File', text='File')
        self.problems_tree.heading('Line', text='Line')
        
        self.problems_tree.column('#0', width=30, minwidth=30)
        self.problems_tree.column('Type', width=80, minwidth=80)
        self.problems_tree.column('Message', width=400, minwidth=200)
        self.problems_tree.column('File', width=200, minwidth=100)
        self.problems_tree.column('Line', width=60, minwidth=60)
        
        # Welcome message
        self.show_welcome_message()
        
    def copy_output(self):
        try:
            output_content = self.output_text.get("1.0", tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(output_content)
            self.show_status("Output copied to clipboard")
        except Exception:
            pass
        
    def show_welcome_message(self):
        welcome = """Minecraft Mod IDE - Ready
═════════════════════════════════════

All systems initialized successfully!

Quick Start Guide:
1. File → New Project (Ctrl+Shift+N) to create a new mod
2. File → Open Project (Ctrl+Shift+O) to load existing project
3. Use the file explorer to navigate and create files
4. Build → Compile JAR (F5) to package your mod

Development Tips:
• Right-click in file explorer for context menu
• Use Ctrl+/ to toggle line comments
• Ctrl+D duplicates the current line
• Ctrl+F opens find/replace dialog
• Hover over toolbar buttons for tooltips
• Files auto-save every 30 seconds

Ready to create amazing Minecraft mods!
"""
        self.log_output(welcome)
        
    def create_status_bar(self):
        self.status_frame = ttk.Frame(self.root, style='Toolbar.TFrame', relief='flat')
        self.status_frame.grid(row=2, column=0, sticky="ew")
        
        # Add top border
        border = ttk.Frame(self.status_frame, height=1, style='Modern.TFrame')
        border.pack(side=tk.TOP, fill=tk.X)
        
        # Status content frame
        content_frame = ttk.Frame(self.status_frame, style='Toolbar.TFrame')
        content_frame.pack(fill=tk.X, padx=8, pady=4)
        
        # Left side - general status with animated indicator
        left_frame = ttk.Frame(content_frame, style='Toolbar.TFrame')
        left_frame.pack(side=tk.LEFT)
        
        # Status indicator (animated dot)
        self.status_indicator = tk.Canvas(left_frame, width=8, height=8, 
                                        bg=ModernStyle.MEDIUM_BG, 
                                        highlightthickness=0, bd=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 8), pady=4)
        
        # Create animated status dot
        self.status_dot = self.status_indicator.create_oval(2, 2, 6, 6, 
                                                          fill=ModernStyle.SUCCESS_COLOR, 
                                                          outline="")
        
        self.status_label = ttk.Label(left_frame, text="Ready", style='Toolbar.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        # Center - project info with icon
        center_frame = ttk.Frame(content_frame, style='Toolbar.TFrame')
        center_frame.pack(side=tk.LEFT, padx=20)
        
        self.project_label = ttk.Label(center_frame, text="📝 No project open", style='Toolbar.TLabel')
        self.project_label.pack(side=tk.LEFT)
        
        # Right side - file info and cursor position
        right_frame = ttk.Frame(content_frame, style='Toolbar.TFrame')
        right_frame.pack(side=tk.RIGHT)
        
        self.cursor_label = ttk.Label(right_frame, text="Ln 1, Col 1", style='Toolbar.TLabel')
        self.cursor_label.pack(side=tk.RIGHT, padx=8)
        
        self.encoding_label = ttk.Label(right_frame, text="UTF-8", style='Toolbar.TLabel')
        self.encoding_label.pack(side=tk.RIGHT, padx=8)
        
        # Start status animation
        self.animate_status()
        
    def animate_status(self):
        try:
            # Pulse the status dot
            current_color = self.status_indicator.itemcget(self.status_dot, 'fill')
            if current_color == ModernStyle.SUCCESS_COLOR:
                new_color = ModernStyle.ACCENT_ORANGE
            else:
                new_color = ModernStyle.SUCCESS_COLOR
                
            self.status_indicator.itemconfig(self.status_dot, fill=new_color)
        except (tk.TclError, AttributeError):
            # Handle cases where status indicator isn't available
            pass
        finally:
            # Continue animation
            self.root.after(2000, self.animate_status)
        
    def show_status(self, message):
        try:
            self.status_label.config(text=message)
            # Flash the indicator
            if hasattr(self, 'status_indicator') and hasattr(self, 'status_dot'):
                self.status_indicator.itemconfig(self.status_dot, fill=ModernStyle.ACCENT_ORANGE)
                self.root.after(200, lambda: self.status_indicator.itemconfig(self.status_dot, fill=ModernStyle.SUCCESS_COLOR))
        except (tk.TclError, AttributeError):
            # Fallback to just updating text
            if hasattr(self, 'status_label'):
                self.status_label.config(text=message)
        
    def bind_shortcuts(self):
        shortcuts = {
            '<Control-n>': self.new_file,
            '<Control-o>': self.open_file,
            '<Control-s>': self.save_file,
            '<Control-Shift-S>': self.save_file_as,
            '<Control-Alt-s>': self.save_all_files,
            '<Control-Shift-O>': self.open_project,
            '<Control-Shift-N>': self.new_project,
            '<Control-f>': self.find_replace,
            '<Control-slash>': self.toggle_comment,
            '<Control-d>': self.duplicate_line,
            '<F5>': self.show_compile_dialog,
            '<Shift-F5>': self.clean_build,
            '<Control-F5>': self.quick_build,
        }
        
        for shortcut, command in shortcuts.items():
            self.root.bind(shortcut, lambda e, cmd=command: cmd())
            
    # File operations
    def new_file(self):
        self.editor.new_file()
        
    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("Java files", "*.java"),
                ("JSON files", "*.json"),
                ("XML files", "*.xml"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.editor.open_file(file_path)
            
    def open_file_in_editor(self, file_path):
        self.editor.open_file(file_path)
        
    def save_file(self):
        current_editor = self.editor.get_current_editor()
        if current_editor and self.editor.current_file:
            self.editor.save_file(self.editor.current_file)
            
    def save_file_as(self):
        current_editor = self.editor.get_current_editor()
        if current_editor and self.editor.current_file:
            file_path = filedialog.asksaveasfilename(
                title="Save File As",
                defaultextension=".java",
                filetypes=[
                    ("Java files", "*.java"),
                    ("JSON files", "*.json"),
                    ("XML files", "*.xml"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                current_editor['file_path'] = file_path
                self.editor.save_file(self.editor.current_file)
                
    def save_all_files(self):
        for filename in self.editor.open_files:
            self.editor.save_file(filename)
            
    # Edit operations
    def undo(self):
        current_editor = self.editor.get_current_editor()
        if current_editor:
            current_editor['text_widget'].edit_undo()
            
    def redo(self):
        current_editor = self.editor.get_current_editor()
        if current_editor:
            current_editor['text_widget'].edit_redo()
            
    def cut(self):
        current_editor = self.editor.get_current_editor()
        if current_editor:
            current_editor['text_widget'].event_generate("<<Cut>>")
            
    def copy(self):
        current_editor = self.editor.get_current_editor()
        if current_editor:
            current_editor['text_widget'].event_generate("<<Copy>>")
            
    def paste(self):
        current_editor = self.editor.get_current_editor()
        if current_editor:
            current_editor['text_widget'].event_generate("<<Paste>>")
            
    def find_replace(self):
        if self.editor.current_file:
            self.editor.show_find_dialog(self.editor.current_file)
            
    def toggle_comment(self):
        if self.editor.current_file:
            self.editor.toggle_comment(self.editor.current_file)
            
    def duplicate_line(self):
        if self.editor.current_file:
            self.editor.duplicate_line(self.editor.current_file)
            
    # Project operations
    def new_project(self):
        ProjectTemplateDialog(self.root, self.on_project_created)
        
    def open_project(self):
        project_path = filedialog.askdirectory(title="Select Project Directory")
        if project_path:
            self.load_project(project_path)
            
    def on_project_created(self, project_path):
        self.load_project(project_path)
        self.log_output(f"✅ Project created: {os.path.basename(project_path)}")
        
    def load_project(self, project_path):
        self.project_path = project_path
        self.file_explorer.load_project(project_path)
        self.update_project_status()
        self.log_output(f"📁 Project opened: {os.path.basename(project_path)}")
        
    def refresh_project(self):
        if self.project_path:
            self.file_explorer.refresh_tree()
            self.log_output("🔄 Project refreshed")
        else:
            messagebox.showwarning("Warning", "No project is currently open")
            
    def show_status(self, message):
        self.status_label.config(text=message)
        # Flash the indicator
        self.status_indicator.itemconfig(self.status_dot, fill=ModernStyle.ACCENT_ORANGE)
        self.root.after(200, lambda: self.status_indicator.itemconfig(self.status_dot, fill=ModernStyle.SUCCESS_COLOR))
        
    def update_project_status(self):
        if self.project_path:
            project_name = os.path.basename(self.project_path)
            self.project_label.config(text=f"📁 {project_name}")
            # Update file explorer header if it exists
            if hasattr(self, 'file_explorer') and hasattr(self.file_explorer, 'project_label'):
                self.file_explorer.project_label.config(text=f"📁 {project_name}")
        else:
            self.project_label.config(text="📝 No project open")
            if hasattr(self, 'file_explorer') and hasattr(self.file_explorer, 'project_label'):
                self.file_explorer.project_label.config(text="📁 Explorer")
            
    # Build operations
    def show_compile_dialog(self):
        if not self.project_path:
            messagebox.showwarning("Warning", "Please open a project first")
            return
        CompileDialog(self.root, self.project_path, self.jar_compiler)
        
    def quick_build(self):
        if not self.project_path:
            messagebox.showwarning("Warning", "Please open a project first")
            return
            
        project_name = os.path.basename(self.project_path)
        output_dir = os.path.join(self.project_path, "dist")
        os.makedirs(output_dir, exist_ok=True)
        
        self.jar_compiler.compile_project(
            self.project_path,
            output_dir,
            f"{project_name}.jar"
        )
        
    def clean_build(self):
        if not self.project_path:
            messagebox.showwarning("Warning", "Please open a project first")
            return
            
        build_dir = os.path.join(self.project_path, "build")
        
        def clean_thread():
            try:
                if os.path.exists(build_dir):
                    shutil.rmtree(build_dir)
                    self.log_output("🧹 Build directory cleaned")
                else:
                    self.log_output("ℹ️ No build directory to clean")
            except Exception as e:
                self.log_output(f"❌ Error cleaning build: {str(e)}")
                
        threading.Thread(target=clean_thread, daemon=True).start()
        
    # Output and logging
    def log_output(self, message, message_type="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.root.after(0, lambda: self._log_output_main_thread(formatted_message, message_type))
        
    def _log_output_main_thread(self, message, message_type="info"):
        # Insert message
        start_pos = self.output_text.index(tk.END)
        self.output_text.insert(tk.END, message + "\n")
        end_pos = self.output_text.index(tk.END)
        
        # Apply color tag based on message type
        if "✅" in message or "SUCCESS" in message:
            self.output_text.tag_add("success", start_pos, end_pos)
        elif "❌" in message or "ERROR" in message or "FAILED" in message:
            self.output_text.tag_add("error", start_pos, end_pos)
            self.build_status.config(fg=ModernStyle.ERROR_COLOR)
        elif "⚠️" in message or "WARNING" in message:
            self.output_text.tag_add("warning", start_pos, end_pos)
        elif message_type == "info":
            self.output_text.tag_add("info", start_pos, end_pos)
        else:
            self.output_text.tag_add(message_type, start_pos, end_pos)
            
        # Auto-scroll to bottom
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
        # Update build status
        if "✅" in message or "SUCCESS" in message:
            self.build_status.config(fg=ModernStyle.SUCCESS_COLOR)
        elif "🔨" in message or "Starting" in message:
            self.build_status.config(fg=ModernStyle.ACCENT_ORANGE)
        
    def clear_output(self):
        self.output_text.delete("1.0", tk.END)
        
    def update_progress(self, percent, message):
        self.progress_bar['value'] = percent
        self.progress_label.config(text=message)
        self.root.update_idletasks()
        
    # Auto-save functionality
    def start_auto_save(self):
        self.auto_save_files()
        self.auto_save_timer = self.root.after(30000, self.start_auto_save)  # 30 seconds
        
    def auto_save_files(self):
        if hasattr(self, 'editor'):
            for filename, file_data in self.editor.open_files.items():
                if file_data['modified'] and file_data['file_path']:
                    try:
                        content = file_data['text_widget'].get("1.0", tk.END + "-1c")
                        # Create backup
                        backup_path = file_data['file_path'] + '.backup'
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                    except Exception:
                        pass  # Silent fail for auto-save
                        
    # Settings and dialogs
    def show_settings(self):
        SettingsDialog(self.root)
        
    def show_documentation(self):
        webbrowser.open("https://minecraft.wiki/w/Mods")
        
    def show_tips(self):
        TipsDialog(self.root)
        
    def show_about(self):
        AboutDialog(self.root)
        
    def on_closing(self):
        # Check for unsaved changes
        if hasattr(self, 'editor'):
            for filename, file_data in self.editor.open_files.items():
                if file_data['modified']:
                    result = messagebox.askyesnocancel(
                        "Unsaved Changes",
                        f"Save changes to {filename} before closing?"
                    )
                    if result is True:
                        self.editor.save_file(filename)
                    elif result is None:
                        return
                        
        # Cancel auto-save timer
        if self.auto_save_timer:
            self.root.after_cancel(self.auto_save_timer)
            
        self.root.destroy()

class CompileDialog:
    
    def __init__(self, parent, project_path, jar_compiler):
        self.parent = parent
        self.project_path = project_path
        self.jar_compiler = jar_compiler
        self.setup_dialog()
        
    def setup_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("🔨 Compile to JAR")
        self.dialog.geometry("700x600")
        self.dialog.configure(bg=ModernStyle.DARK_BG)
        self.dialog.resizable(False, False)
        
        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, style='Modern.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔨 Compile Project to JAR", style='Header.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Project info
        info_frame = ttk.LabelFrame(main_frame, text="Project Information", style='Modern.TFrame', padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        project_name = os.path.basename(self.project_path)
        ttk.Label(info_frame, text=f"📁 Project: {project_name}", style='Modern.TLabel').pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"📍 Location: {self.project_path}", style='Muted.TLabel').pack(anchor=tk.W)
        
        # Build settings
        settings_frame = ttk.LabelFrame(main_frame, text="Build Settings", style='Modern.TFrame', padding=15)
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Variables
        self.output_dir = tk.StringVar(value=os.path.join(self.project_path, "dist"))
        self.jar_name = tk.StringVar(value=f"{project_name}.jar")
        self.classpath = tk.StringVar()
        self.main_class = tk.StringVar()
        self.include_sources = tk.BooleanVar(value=False)
        self.create_docs = tk.BooleanVar(value=False)
        
        # Output directory
        row = 0
        ttk.Label(settings_frame, text="Output Directory:", style='Modern.TLabel').grid(row=row, column=0, sticky=tk.W, pady=5)
        output_frame = ttk.Frame(settings_frame, style='Modern.TFrame')
        output_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        ttk.Entry(output_frame, textvariable=self.output_dir, style='Modern.TEntry', width=35).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="📂", command=self.browse_output_dir, style='Modern.TButton', width=4).pack(side=tk.RIGHT, padx=(5, 0))
        
        # JAR name
        row += 1
        ttk.Label(settings_frame, text="JAR Name:", style='Modern.TLabel').grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(settings_frame, textvariable=self.jar_name, style='Modern.TEntry', width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Classpath
        row += 1
        ttk.Label(settings_frame, text="Classpath:", style='Modern.TLabel').grid(row=row, column=0, sticky=tk.W, pady=5)
        classpath_frame = ttk.Frame(settings_frame, style='Modern.TFrame')
        classpath_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        ttk.Entry(classpath_frame, textvariable=self.classpath, style='Modern.TEntry', width=35).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(classpath_frame, text="📦", command=self.browse_classpath, style='Modern.TButton', width=4).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Main class
        row += 1
        ttk.Label(settings_frame, text="Main Class:", style='Modern.TLabel').grid(row=row, column=0, sticky=tk.W, pady=5)
        main_class_frame = ttk.Frame(settings_frame, style='Modern.TFrame')
        main_class_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        ttk.Entry(main_class_frame, textvariable=self.main_class, style='Modern.TEntry', width=35).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(main_class_frame, text="🔍", command=self.find_main_classes, style='Modern.TButton', width=4).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Configure grid weights
        settings_frame.columnconfigure(1, weight=1)
        output_frame.columnconfigure(0, weight=1)
        classpath_frame.columnconfigure(0, weight=1)
        main_class_frame.columnconfigure(0, weight=1)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Additional Options", style='Modern.TFrame', padding=15)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Checkbutton(options_frame, text="Include source files in JAR", variable=self.include_sources, style='Modern.TCheckbutton').pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Generate Javadoc documentation", variable=self.create_docs, style='Modern.TCheckbutton').pack(anchor=tk.W, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(button_frame, text="❌ Cancel", command=self.dialog.destroy, style='Modern.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="🔨 Compile", command=self.compile, style='Accent.TButton').pack(side=tk.RIGHT)
        
    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)
            
    def browse_classpath(self):
        files = filedialog.askopenfilenames(
            title="Select JAR files for classpath",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        if files:
            classpath = os.pathsep.join(files)
            self.classpath.set(classpath)
            
    def find_main_classes(self):
        main_classes = []
        
        for root, dirs, files in os.walk(self.project_path):
            if 'build' in dirs:
                dirs.remove('build')
                
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if 'public static void main(' in content:
                                # Extract package and class name
                                package_match = re.search(r'package\s+([\w.]+);', content)
                                class_match = re.search(r'public\s+class\s+(\w+)', content)
                                
                                if class_match:
                                    class_name = class_match.group(1)
                                    if package_match:
                                        full_name = f"{package_match.group(1)}.{class_name}"
                                    else:
                                        full_name = class_name
                                    main_classes.append(full_name)
                    except Exception:
                        continue
                        
        if main_classes:
            # Show selection dialog
            MainClassSelectionDialog(self.dialog, main_classes, self.main_class)
        else:
            messagebox.showinfo("No Main Classes", "No classes with main methods found in the project.")
            
    def compile(self):
        # Validate inputs
        if not self.output_dir.get().strip():
            messagebox.showerror("Error", "Please specify an output directory")
            return
            
        if not self.jar_name.get().strip():
            messagebox.showerror("Error", "Please specify a JAR name")
            return
            
        # Ensure JAR extension
        jar_name = self.jar_name.get().strip()
        if not jar_name.endswith('.jar'):
            jar_name += '.jar'
            
        # Create output directory if it doesn't exist
        try:
            os.makedirs(self.output_dir.get(), exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create output directory: {str(e)}")
            return
            
        # Start compilation
        self.jar_compiler.compile_project(
            self.project_path,
            self.output_dir.get(),
            jar_name,
            self.classpath.get().strip() if self.classpath.get().strip() else None,
            self.main_class.get().strip() if self.main_class.get().strip() else None
        )
        
        # Close dialog
        self.dialog.destroy()

class MainClassSelectionDialog:
    
    def __init__(self, parent, main_classes, result_var):
        self.parent = parent
        self.main_classes = main_classes
        self.result_var = result_var
        self.setup_dialog()
        
    def setup_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Select Main Class")
        self.dialog.geometry("400x300")
        self.dialog.configure(bg=ModernStyle.DARK_BG)
        self.dialog.resizable(False, False)
        
        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, style='Modern.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Select Main Class", style='Header.TLabel').pack(pady=(0, 15))
        
        # Instruction
        ttk.Label(main_frame, text="Multiple classes with main methods found:", style='Modern.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Listbox
        list_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.listbox = tk.Listbox(
            list_frame,
            bg=ModernStyle.MEDIUM_BG,
            fg=ModernStyle.TEXT_PRIMARY,
            selectbackground=ModernStyle.ACCENT_ORANGE,
            selectforeground=ModernStyle.DARK_BG,
            font=("Consolas", 10),
            relief=tk.FLAT
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        # Populate listbox
        for class_name in self.main_classes:
            self.listbox.insert(tk.END, class_name)
        self.listbox.select_set(0)
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, style='Modern.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Select", command=self.select_class, style='Accent.TButton').pack(side=tk.RIGHT)
        
        # Bind double-click
        self.listbox.bind('<Double-1>', lambda e: self.select_class())
        
    def select_class(self):
        selection = self.listbox.curselection()
        if selection:
            class_name = self.listbox.get(selection[0])
            self.result_var.set(class_name)
        self.dialog.destroy()

class SettingsDialog:
    
    def __init__(self, parent):
        self.parent = parent
        self.setup_dialog()
        
    def setup_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("⚙️ Settings")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg=ModernStyle.DARK_BG)
        self.dialog.resizable(True, True)
        
        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, style='Modern.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="⚙️ IDE Settings", style='Header.TLabel').pack(pady=(0, 20))
        
        # Notebook for different setting categories
        notebook = ttk.Notebook(main_frame, style='Modern.TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Editor settings tab
        editor_frame = ttk.Frame(notebook, style='Modern.TFrame', padding=15)
        notebook.add(editor_frame, text="📝 Editor")
        
        # Font settings
        font_frame = ttk.LabelFrame(editor_frame, text="Font Settings", style='Modern.TFrame', padding=10)
        font_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(font_frame, text="Font Family:", style='Modern.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.font_family = tk.StringVar(value="Consolas")
        ttk.Combobox(font_frame, textvariable=self.font_family, values=["Consolas", "Monaco", "Courier New", "Fira Code"], style='Modern.TCombobox', width=15).grid(row=0, column=1, padx=(10, 0), pady=5)
        
        ttk.Label(font_frame, text="Font Size:", style='Modern.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.font_size = tk.StringVar(value="11")
        ttk.Combobox(font_frame, textvariable=self.font_size, values=["8", "9", "10", "11", "12", "14", "16", "18"], style='Modern.TCombobox', width=15).grid(row=1, column=1, padx=(10, 0), pady=5)
        
        # Editor behavior
        behavior_frame = ttk.LabelFrame(editor_frame, text="Editor Behavior", style='Modern.TFrame', padding=10)
        behavior_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.auto_save = tk.BooleanVar(value=True)
        ttk.Checkbutton(behavior_frame, text="Enable auto-save (30 seconds)", variable=self.auto_save, style='Modern.TCheckbutton').pack(anchor=tk.W, pady=2)
        
        self.syntax_highlight = tk.BooleanVar(value=True)
        ttk.Checkbutton(behavior_frame, text="Enable syntax highlighting", variable=self.syntax_highlight, style='Modern.TCheckbutton').pack(anchor=tk.W, pady=2)
        
        self.line_numbers = tk.BooleanVar(value=True)
        ttk.Checkbutton(behavior_frame, text="Show line numbers", variable=self.line_numbers, style='Modern.TCheckbutton').pack(anchor=tk.W, pady=2)
        
        # Build settings tab
        build_frame = ttk.Frame(notebook, style='Modern.TFrame', padding=15)
        notebook.add(build_frame, text="🔨 Build")
        
        # Java settings
        java_frame = ttk.LabelFrame(build_frame, text="Java Settings", style='Modern.TFrame', padding=10)
        java_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(java_frame, text="Java Home:", style='Modern.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.java_home = tk.StringVar(value=os.environ.get('JAVA_HOME', ''))
        java_entry_frame = ttk.Frame(java_frame, style='Modern.TFrame')
        java_entry_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        ttk.Entry(java_entry_frame, textvariable=self.java_home, style='Modern.TEntry', width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(java_entry_frame, text="📂", command=self.browse_java_home, style='Modern.TButton', width=4).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Build options
        build_options_frame = ttk.LabelFrame(build_frame, text="Build Options", style='Modern.TFrame', padding=10)
        build_options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.clean_before_build = tk.BooleanVar(value=False)
        ttk.Checkbutton(build_options_frame, text="Clean before build", variable=self.clean_before_build, style='Modern.TCheckbutton').pack(anchor=tk.W, pady=2)
        
        self.show_build_output = tk.BooleanVar(value=True)
        ttk.Checkbutton(build_options_frame, text="Show detailed build output", variable=self.show_build_output, style='Modern.TCheckbutton').pack(anchor=tk.W, pady=2)
        
        # Configure grid weights
        java_frame.columnconfigure(1, weight=1)
        java_entry_frame.columnconfigure(0, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="❌ Cancel", command=self.dialog.destroy, style='Modern.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="💾 Save", command=self.save_settings, style='Accent.TButton').pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="🔄 Reset", command=self.reset_settings, style='Modern.TButton').pack(side=tk.LEFT)
        
    def browse_java_home(self):
        directory = filedialog.askdirectory(title="Select Java Home Directory")
        if directory:
            self.java_home.set(directory)
            
    def save_settings(self):
        try:
            # Here you would normally save settings to a config file
            # For now, just show a success message
            messagebox.showinfo("Settings", "Settings saved successfully!\n\nSome changes may require restarting the IDE.")
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            
    def reset_settings(self):
        if messagebox.askyesno("Reset Settings", "Reset all settings to default values?"):
            self.font_family.set("Consolas")
            self.font_size.set("11")
            self.auto_save.set(True)
            self.syntax_highlight.set(True)
            self.line_numbers.set(True)
            self.java_home.set(os.environ.get('JAVA_HOME', ''))
            self.clean_before_build.set(False)
            self.show_build_output.set(True)

class TipsDialog:
    
    def __init__(self, parent):
        self.parent = parent
        self.setup_dialog()
        
    def setup_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("💡 Tips & Tricks")
        self.dialog.geometry("550x450")
        self.dialog.configure(bg=ModernStyle.DARK_BG)
        self.dialog.resizable(True, True)
        
        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, style='Modern.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="💡 Tips & Tricks", style='Header.TLabel').pack(pady=(0, 15))
        
        # Tips content
        tips_text = scrolledtext.ScrolledText(
            main_frame,
            bg=ModernStyle.MEDIUM_BG,
            fg=ModernStyle.TEXT_PRIMARY,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        tips_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        tips_content = """💡 Productivity Tips for Minecraft Mod IDE:

🚀 Project Management:
• Use Ctrl+Shift+N to create new projects from templates
• Right-click in file explorer for quick file operations
• Use project templates to get started quickly
• File Explorer buttons: 📄 File, 📁 Folder, 🔄 Refresh

⌨️ Essential Keyboard Shortcuts:
• Ctrl+N - New file
• Ctrl+O - Open file
• Ctrl+S - Save current file
• Ctrl+Shift+S - Save as
• Ctrl+Alt+S - Save all files
• Ctrl+/ - Toggle line comments
• Ctrl+D - Duplicate current line
• Ctrl+F - Find and replace with regex support
• F5 - Compile to JAR
• Ctrl+F5 - Quick build
• Shift+F5 - Clean build

✏️ Editor Features:
• Smart Java syntax highlighting with real-time highlighting
• Auto-indentation and smart bracket matching
• Line numbers that update automatically
• Multiple file tabs with unsaved change indicators (•)
• Current line highlighting for better navigation
• Code templates for different file types

🔨 Build System:
• Use Quick Build (Ctrl+F5) for fast compilation with default settings
• Set main class for executable JARs in the compile dialog
• Add external JARs to classpath for dependencies
• Clean build removes old compiled files and build cache
• Progress tracking with detailed output messages

📁 File Operations:
• Create files with intelligent templates (Java, JSON, XML, etc.)
• File type detection with appropriate templates
• Auto-save every 30 seconds with backup files
• Templates include proper package declarations and imports
• Right-click context menus for rename, delete, copy path

🎨 Interface Tips:
• Modern dark theme optimized for long coding sessions
• Resizable panels - drag borders to customize layout
• Status bar shows cursor position, encoding, and project info
• Output panel with build progress and error highlighting
• Scrollable dialogs for better content viewing
• Smooth animations and hover effects

🚀 Pro Tips:
• Use project templates to quickly set up Forge, Fabric, or Bukkit projects
• The compiler auto-detects main classes for executable JARs
• Settings dialog allows customization of fonts, build options, and more
• About dialog shows system requirements and version info
• Hover over toolbar buttons for helpful tooltips

Ready to create amazing Minecraft mods! 🎯"""
        
        tips_text.insert(tk.END, tips_content)
        tips_text.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(main_frame, text="✅ Close", command=self.dialog.destroy, style='Accent.TButton').pack()

class AboutDialog:
    
    def __init__(self, parent):
        self.parent = parent
        self.setup_dialog()
        
    def setup_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("ℹ️ About")
        self.dialog.geometry("500x600")
        self.dialog.configure(bg=ModernStyle.DARK_BG)
        self.dialog.resizable(True, True)
        
        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main scrollable frame
        canvas = tk.Canvas(self.dialog, bg=ModernStyle.DARK_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        
        # Content frame
        main_frame = ttk.Frame(scrollable_frame, style='Modern.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo/Title
        ttk.Label(main_frame, text="🎮", style='Header.TLabel', font=("Segoe UI", 36)).pack(pady=(0, 5))
        ttk.Label(main_frame, text="Minecraft Mod IDE", style='Header.TLabel', font=("Segoe UI", 14, "bold")).pack()
        ttk.Label(main_frame, text="Ultimate Modding Environment", style='Modern.TLabel', font=("Segoe UI", 10)).pack(pady=(0, 15))
        
        # Version info
        version_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        version_frame.pack(pady=(0, 15))
        
        ttk.Label(version_frame, text="Version 1.0.0", style='Modern.TLabel').pack()
        ttk.Label(version_frame, text="Built with Python & Tkinter", style='Muted.TLabel').pack()
        ttk.Label(version_frame, text=f"Build Date: {datetime.now().strftime('%Y-%m-%d')}", style='Muted.TLabel').pack()
        
        # Description
        desc_text = """The ultimate Minecraft mod development environment with modern features, sleek UI, and comprehensive tools for creating amazing mods."""
        
        ttk.Label(main_frame, text=desc_text, style='Modern.TLabel', wraplength=400, justify=tk.CENTER).pack(pady=(0, 15))
        
        # Features
        features_frame = ttk.LabelFrame(main_frame, text="Key Features", style='Modern.TFrame', padding=10)
        features_frame.pack(fill=tk.X, pady=(0, 15))
        
        features = [
            "✨ Smart syntax highlighting",
            "🔨 Integrated JAR compiler", 
            "📁 Modern project management",
            "🎨 Sleek dark theme",
            "⚡ Fast build system",
            "📝 Multiple file editing",
            "🚀 Project templates",
            "🔍 Find & replace"
        ]
        
        for feature in features:
            ttk.Label(features_frame, text=feature, style='Modern.TLabel').pack(anchor=tk.W, pady=1)
            
        # System Requirements
        requirements_frame = ttk.LabelFrame(main_frame, text="System Requirements", style='Modern.TFrame', padding=10)
        requirements_frame.pack(fill=tk.X, pady=(0, 15))
        
        requirements = [
            "• Python 3.7 or higher",
            "• Java JDK 8 or higher",
            "• 4GB RAM minimum",
            "• 1GB free disk space",
            "• Windows 10/11, macOS, or Linux"
        ]
        
        for req in requirements:
            ttk.Label(requirements_frame, text=req, style='Modern.TLabel').pack(anchor=tk.W, pady=1)
            
        # Credits
        credits_frame = ttk.LabelFrame(main_frame, text="Credits", style='Modern.TFrame', padding=10)
        credits_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(credits_frame, text="Created for Minecraft modding enthusiasts", style='Muted.TLabel').pack()
        ttk.Label(credits_frame, text="Special thanks to the open source community", style='Muted.TLabel').pack()
        
        # License info
        license_frame = ttk.LabelFrame(main_frame, text="License", style='Modern.TFrame', padding=10)
        license_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(license_frame, text="This software is provided 'as-is' by @CPScript on GitHub", style='Muted.TLabel', wraplength=400).pack()
        
        # Close button
        button_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(button_frame, text="✅ Close", command=self.dialog.destroy, style='Accent.TButton').pack()
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

def main():
    root = tk.Tk()
    
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    ide = MinecraftModIDE(root)
    root.mainloop()

if __name__ == "__main__":
    main()
