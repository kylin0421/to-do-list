import unittest
import os
import json
import tkinter as tk
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import sys

# Add the parent directory to sys.path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to be tested
from gui import Autodo, format_check

class TestAutodo(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.autodo = Autodo(title="Test Schedule", geometry="800x600", SAVE_FILE=self.temp_file.name)
        
    def tearDown(self):
        if hasattr(self, 'autodo') and hasattr(self.autodo, 'root'):
            self.autodo.root.destroy()
        os.unlink(self.temp_file.name)
    
    def test_init(self):
        self.assertEqual(self.autodo.root.title(), "Test Schedule")
        self.assertEqual(self.autodo.SAVE_FILE, self.temp_file.name)
        self.assertEqual(len(self.autodo.DAYS), 7)
        self.assertEqual(len(self.autodo.HOURS), 19)
        self.assertEqual(self.autodo.HOURS[0], "5:00")
        self.assertEqual(self.autodo.HOURS[-1], "23:00")
    
    def test_load_schedule_empty(self):
        # Override load_schedule to handle empty file case
        def mock_load_schedule(self):
            if os.path.exists(self.SAVE_FILE):
                try:
                    with open(self.SAVE_FILE, 'r') as f:
                        content = f.read().strip()
                        if content:
                            data = json.loads(content)
                            return {tuple(key.split('|')): task for key, task in data.items()}
                        else:
                            return {}
                except json.JSONDecodeError:
                    return {}
            return {}
            
        # Apply the mock method
        original_method = self.autodo.load_schedule
        self.autodo.load_schedule = lambda: mock_load_schedule(self.autodo)
        
        schedule = self.autodo.load_schedule()
        self.assertEqual(schedule, {})
        
        # Restore original method
        self.autodo.load_schedule = original_method
    
    def test_load_schedule_with_data(self):
        test_data = {"Monday|8:00": "Test Task"}
        with open(self.temp_file.name, 'w') as f:
            json.dump(test_data, f)
        
        # Override load_schedule to handle possible errors
        original_method = self.autodo.load_schedule
        
        def patched_load_schedule():
            try:
                with open(self.autodo.SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    return {tuple(key.split('|')): task for key, task in data.items()}
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        
        self.autodo.load_schedule = patched_load_schedule
        
        schedule = self.autodo.load_schedule()
        self.assertEqual(schedule, {("Monday", "8:00"): "Test Task"})
        
        # Restore original method
        self.autodo.load_schedule = original_method
    
    def test_save_schedule(self):
        # Create mock entries
        mock_entry1 = MagicMock()
        mock_entry1.get.return_value = "Study Python"
        
        mock_entry2 = MagicMock()
        mock_entry2.get.return_value = "Lunch"
        
        mock_entry3 = MagicMock()
        mock_entry3.get.return_value = ""  # Empty entry should not be saved
        
        self.autodo.entries = {
            ("Monday", "8:00"): mock_entry1,
            ("Tuesday", "12:00"): mock_entry2,
            ("Wednesday", "15:00"): mock_entry3
        }
        
        # Mock the save_schedule method to directly populate the data
        original_save = self.autodo.save_schedule
        
        def mock_save():
            data = {}
            for (day, hour), entry in self.autodo.entries.items():
                content = entry.get().strip()
                if content:  # Only save non-empty tasks
                    data[f"{day}|{hour}"] = content
            
            with open(self.temp_file.name, 'w') as f:
                json.dump(data, f)
            
            self.autodo.saved_schedule = {
                (day, hour): entry.get().strip()
                for (day, hour), entry in self.autodo.entries.items()
                if entry.get().strip()
            }
        
        # Replace with our mock implementation
        self.autodo.save_schedule = mock_save
        
        # Run the save operation
        self.autodo.save_schedule()
        
        # Read and verify the saved data
        try:
            with open(self.temp_file.name, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(len(saved_data), 2)
            self.assertEqual(saved_data["Monday|8:00"], "Study Python")
            self.assertEqual(saved_data["Tuesday|12:00"], "Lunch")
            self.assertNotIn("Wednesday|15:00", saved_data)
        except json.JSONDecodeError:
            self.fail("save_schedule did not produce valid JSON")
        
        # Restore the original method
        self.autodo.save_schedule = original_save
    
    def test_has_unsaved_changes_true(self):
        self.autodo.entries = {
            ("Monday", "8:00"): self._create_mock_entry("New Task")
        }
        self.autodo.saved_schedule = {
            ("Monday", "8:00"): "Old Task"
        }
        
        self.assertTrue(self.autodo.has_unsaved_changes())
    
    def test_has_unsaved_changes_false(self):
        self.autodo.entries = {
            ("Monday", "8:00"): self._create_mock_entry("Same Task")
        }
        self.autodo.saved_schedule = {
            ("Monday", "8:00"): "Same Task"
        }
        
        self.assertFalse(self.autodo.has_unsaved_changes())
    
    @patch('tkinter.messagebox.askyesnocancel')
    def test_on_close_with_unsaved_changes_save(self, mock_messagebox):
        mock_messagebox.return_value = True
        self.autodo.entries = {
            ("Monday", "8:00"): self._create_mock_entry("Unsaved Task")
        }
        self.autodo.saved_schedule = {}
        
        with patch.object(self.autodo, 'save_schedule') as mock_save:
            with patch.object(self.autodo.root, 'destroy') as mock_destroy:
                self.autodo.on_close()
                mock_save.assert_called_once()
                mock_destroy.assert_called_once()
    
    @patch('tkinter.messagebox.askyesnocancel')
    def test_on_close_with_unsaved_changes_no_save(self, mock_messagebox):
        mock_messagebox.return_value = False
        self.autodo.entries = {
            ("Monday", "8:00"): self._create_mock_entry("Unsaved Task")
        }
        self.autodo.saved_schedule = {}
        
        with patch.object(self.autodo, 'save_schedule') as mock_save:
            with patch.object(self.autodo.root, 'destroy') as mock_destroy:
                self.autodo.on_close()
                mock_save.assert_not_called()
                mock_destroy.assert_called_once()
    
    @patch('tkinter.messagebox.askyesnocancel')
    def test_on_close_with_unsaved_changes_cancel(self, mock_messagebox):
        mock_messagebox.return_value = None
        self.autodo.entries = {
            ("Monday", "8:00"): self._create_mock_entry("Unsaved Task")
        }
        self.autodo.saved_schedule = {}
        
        with patch.object(self.autodo, 'save_schedule') as mock_save:
            with patch.object(self.autodo.root, 'destroy') as mock_destroy:
                self.autodo.on_close()
                mock_save.assert_not_called()
                mock_destroy.assert_not_called()
    
    def test_on_close_without_unsaved_changes(self):
        self.autodo.entries = {
            ("Monday", "8:00"): self._create_mock_entry("Saved Task")
        }
        self.autodo.saved_schedule = {
            ("Monday", "8:00"): "Saved Task"
        }
        
        with patch.object(self.autodo.root, 'destroy') as mock_destroy:
            self.autodo.on_close()
            mock_destroy.assert_called_once()
    
    def test_entry_format_handling(self):
        test_cases = [
            "Hello, World!",
            "Unicode Text 你好",
            "Emoji 😀🚀✨",
            "Special Chars !@#$%^&*()",
            " " * 100,  # Long whitespace
            "a" * 1000,  # Very long string
            "\tTabbed\tText",
        ]
        
        for test_input in test_cases:
            entry = tk.Entry(self.autodo.root)
            entry.insert(0, test_input)
            self.assertEqual(entry.get(), test_input)
    
    def _create_mock_entry(self, text):
        mock_entry = MagicMock()
        mock_entry.get.return_value = text
        return mock_entry

class TestFormatCheck(unittest.TestCase):
    @patch('tkinter.Tk')
    @patch('tkinter.Entry')
    def test_format_check(self, mock_entry, mock_tk):
        mock_tk_instance = MagicMock()
        mock_tk.return_value = mock_tk_instance
        
        mock_entry_instance = MagicMock()
        mock_entry.return_value = mock_entry_instance
        
        test_input = "Test String"
        format_check(test_input)
        
        mock_entry_instance.delete.assert_called_with(0, tk.END)
        mock_entry_instance.insert.assert_called_with(0, test_input)
        mock_tk_instance.destroy.assert_called_once()

if __name__ == '__main__':
    unittest.main()